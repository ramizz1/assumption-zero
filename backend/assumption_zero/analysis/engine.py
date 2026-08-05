"""
Analysis Engine — the heart of Assumption Zero.

Orchestrates the full analysis pipeline:
  1. Clarify idea
  2. Generate research queries
  3. Collect evidence (all providers in parallel)
  4. Find competitors from evidence
  5. Run AI perspectives (3 independent roles)
  6. Validate citations
  7. Calculate scores
  8. Generate experiments
  9. Detect disagreements

The engine is shared by both the FastAPI backend and the CLI.
It has no direct dependency on HTTP or database layers.
"""
from __future__ import annotations

import asyncio
import logging
from collections import Counter
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Awaitable

from assumption_zero.analysis.citation_validator import validate_citations
from assumption_zero.analysis.competitor_merger import merge_competitors
from assumption_zero.analysis.confidence import calculate_evidence_confidence
from assumption_zero.analysis.disagreement import detect_disagreements
from assumption_zero.analysis.experiment_generator import generate_experiments
from assumption_zero.analysis.query_generator import generate_queries
from assumption_zero.analysis.scoring import calculate_opportunity_score
from assumption_zero.llm.base import LLMAdapter, PerspectiveOutput
from assumption_zero.research.base import ResearchProvider
from assumption_zero.schemas import (
    AnalysisPerspective,
    AnalysisResult,
    AnalysisStage,
    AnalysisStatus,
    Competitor,
    CompetitorType,
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    ModelDisagreement,
    PERSPECTIVE_DISPLAY,
    PerspectiveName,
    Recommendation,
    STAGE_DESCRIPTIONS,
    ValidationExperiment,
)

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[AnalysisStage, str], Awaitable[None]]]


def _assign_evidence_ids(items: List[EvidenceItem]) -> List[EvidenceItem]:
    """
    Assign stable sequential E001, E002, ... IDs to all evidence items.
    Deduplicates by URL before assigning IDs.
    """
    seen_urls: set[str] = set()
    unique: List[EvidenceItem] = []
    for item in items:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique.append(item)

    for i, item in enumerate(unique, start=1):
        item.evidence_id = f"E{i:03d}"

    return unique


def _clean_competitor_name(title: str) -> str:
    """Extract a clean brand name from search result title, stripping forum headers."""
    name = title.strip()
    for prefix in ("[GitHub]", "[HN]", "[Reddit r/", "[Wikipedia]", "[News -", "Web ("):
        if name.startswith(prefix):
            name = name.split("]", 1)[-1].strip() if "]" in name else name
            break

    # Handle Show HN / Launch HN
    if "Show HN:" in name:
        name = name.split("Show HN:", 1)[-1].strip()
    elif "Launch HN:" in name:
        name = name.split("Launch HN:", 1)[-1].strip()

    # Split by separator (-, |, –, :) to get brand name
    for sep in (" – ", " - ", " | ", ": "):
        if sep in name:
            candidate = name.split(sep)[0].strip()
            if 2 <= len(candidate) <= 35:
                name = candidate
                break

    # If name looks like a long sentence, skip or truncate
    words = name.split()
    if len(words) > 5 or name.lower().startswith(("as a", "the ", "i ", "how ", "why ", "cost-effective")):
        return ""

    return name.strip()


def _extract_competitors_from_evidence(evidence: List[EvidenceItem], idea: Optional[IdeaInput] = None) -> List[Competitor]:
    """
    Parse competitor information from evidence items and user-declared competitors.
    Returns Competitor objects that will be merged.
    """
    competitors: List[Competitor] = []
    IGNORE_COMPETITOR_WORDS = {"idk", "none", "no", "n/a", "unknown", "nothing", "no idea", "dont know", "don't know", "na"}

    # 1. Include user-specified competitors directly
    if idea and idea.known_competitors:
        for raw_comp in idea.known_competitors.split(","):
            cname = raw_comp.strip()
            if not cname or cname.lower() in IGNORE_COMPETITOR_WORDS:
                continue
            matching_ev = [
                e.evidence_id for e in evidence
                if cname.lower() in e.title.lower() or cname.lower() in e.passage.lower() or cname.lower() in e.search_query.lower()
            ]
            matching_passages = [
                e.passage for e in evidence
                if cname.lower() in e.title.lower() or cname.lower() in e.passage.lower()
            ]
            desc = matching_passages[0][:300] if matching_passages else f"Direct competitor in {idea.geography} for {idea.name}"

            competitors.append(
                Competitor(
                    name=cname,
                    url=f"https://{cname}" if "." in cname and not cname.startswith("http") else "",
                    competitor_type=CompetitorType.DIRECT,
                    description=desc,
                    target_user=f"Target customers in {idea.geography}",
                    pricing_evidence="See evidence items for fee structure details",
                    strengths=["Established market brand & user base"],
                    weaknesses=["High pricing or feature gaps reported"],
                    complaints=[],
                    differentiation=[f"Differentiation required vs {cname}"],
                    evidence_ids=matching_ev[:5],
                    confidence=ConfidenceLevel.HIGH,
                )
            )

    # 2. Parse from evidence items of type COMPETITOR
    for item in evidence:
        if item.evidence_type not in (EvidenceType.COMPETITOR, EvidenceType.OSS_ALTERNATIVE):
            continue

        clean_name = _clean_competitor_name(item.title)
        if not clean_name or clean_name.lower() in IGNORE_COMPETITOR_WORDS:
            continue

        comp_type = (
            CompetitorType.INDIRECT
            if item.evidence_type == EvidenceType.OSS_ALTERNATIVE
            else CompetitorType.DIRECT
        )

        competitors.append(
            Competitor(
                name=clean_name[:50],
                url=item.url if not item.url.startswith("demo://") else "",
                competitor_type=comp_type,
                description=item.passage[:300],
                target_user="Market users",
                pricing_evidence=None,
                strengths=[],
                weaknesses=[],
                complaints=[],
                differentiation=["Differentiation evidence collected"],
                evidence_ids=[item.evidence_id],
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    return competitors


def _select_recommendation(perspectives: List[AnalysisPerspective]) -> Recommendation:
    """Majority vote across perspectives. Tie → Test First."""
    if not perspectives:
        return Recommendation.TEST_FIRST
    counts = Counter(p.recommendation.value for p in perspectives)
    most_common = counts.most_common(1)[0][0]
    return Recommendation(most_common)


def _select_most_dangerous_assumption(perspectives: List[AnalysisPerspective]) -> str:
    """Pick the most dangerous assumption — prefer the skeptic's view."""
    for p in perspectives:
        if p.perspective_name == PerspectiveName.SKEPTICAL_INVESTOR and p.most_dangerous_assumption:
            return p.most_dangerous_assumption
    for p in perspectives:
        if p.most_dangerous_assumption:
            return p.most_dangerous_assumption
    return "Insufficient evidence — run customer interviews to identify assumptions."


def _find_strongest(
    evidence: List[EvidenceItem],
    good: bool,
) -> str:
    """Return the passage from the most relevant supporting or contradicting evidence."""
    ev_type_filter = (
        [EvidenceType.DEMAND, EvidenceType.COMPLAINT]
        if good
        else [EvidenceType.FAILED_PRODUCT, EvidenceType.FAILURE_REASON, EvidenceType.COMPETITOR]
    )
    candidates = [
        e for e in evidence
        if e.evidence_type in ev_type_filter
    ]
    if not candidates:
        candidates = [e for e in evidence if e.relevance_score >= 0.7]
    if not candidates:
        return "Insufficient evidence"
    best = max(candidates, key=lambda e: e.relevance_score)
    return f"[{best.evidence_id}] {best.title}: {best.passage[:200]}"


def _collect_missing_info(
    perspectives: List[AnalysisPerspective],
    evidence: List[EvidenceItem],
) -> List[str]:
    missing: List[str] = []

    if not evidence:
        missing.append("No research evidence collected — configure research providers (SearXNG, GitHub, etc.)")

    # Collect from dimension missing_information (populated by scoring)
    for p in perspectives:
        if "No AI provider" in p.summary or "template analysis" in p.summary.lower():
            missing.append("Configure a real AI provider (Gemini, Ollama, OpenAI-compatible) for qualitative analysis")
            break

    if not any(e.evidence_type == EvidenceType.PRICING for e in evidence):
        missing.append("No competitor pricing evidence found")
    if not any(e.evidence_type == EvidenceType.DEMAND for e in evidence):
        missing.append("No direct demand signal evidence found")
    if not any(e.evidence_type == EvidenceType.REGULATORY for e in evidence):
        missing.append("No regulatory/compliance evidence found for this geography")

    return list(dict.fromkeys(missing))  # deduplicate


class AnalysisEngine:
    """
    The shared analysis engine.

    Usage:
        engine = AnalysisEngine(providers=[...], llm_adapter=...)
        result = await engine.run(idea)
    """

    def __init__(
        self,
        providers: List[ResearchProvider],
        llm_adapter: LLMAdapter,
        max_evidence: int = 50,
        queries_per_type: int = 2,
    ) -> None:
        self._providers = [p for p in providers if p.is_available]
        self._llm = llm_adapter
        self._max_evidence = max_evidence
        self._queries_per_type = queries_per_type

        logger.info(
            "AnalysisEngine ready: providers=%s, llm=%s",
            [p.name for p in self._providers],
            llm_adapter.model_id,
        )

    async def run(
        self,
        idea: IdeaInput,
        analysis_id: str = "local",
        progress_callback: ProgressCallback = None,
        is_demo: bool = False,
    ) -> AnalysisResult:
        """Run the full analysis pipeline and return a complete AnalysisResult."""

        provider_errors: List[str] = []

        async def _progress(stage: AnalysisStage) -> None:
            desc = STAGE_DESCRIPTIONS.get(stage, "")
            logger.info("[%s] %s", stage.value, desc)
            if progress_callback:
                await progress_callback(stage, desc)

        # ── Stage 1: Clarify idea ──────────────────────────────────
        await _progress(AnalysisStage.CLARIFYING_IDEA)
        try:
            interpreted_idea = await self._llm.clarify_idea(idea)
        except Exception as exc:
            logger.warning("Idea clarification failed: %s", exc)
            interpreted_idea = f"{idea.name}: {idea.description}"
            provider_errors.append(f"Idea clarification: {exc}")

        # ── Stage 2: Generate research queries ────────────────────
        await _progress(AnalysisStage.GENERATING_QUERIES)
        all_queries = generate_queries(idea)
        logger.info("Generated %d research queries", len(all_queries))

        # ── Stage 3: Collect evidence ─────────────────────────────
        await _progress(AnalysisStage.COLLECTING_EVIDENCE)
        raw_evidence = await self._collect_evidence(
            all_queries, idea, provider_errors
        )
        evidence = _assign_evidence_ids(raw_evidence)[: self._max_evidence]
        logger.info("Collected %d unique evidence items", len(evidence))

        # ── Stage 4: Find competitors ─────────────────────────────
        await _progress(AnalysisStage.FINDING_COMPETITORS)
        raw_competitors = _extract_competitors_from_evidence(evidence, idea)
        competitors = merge_competitors(raw_competitors)
        logger.info("Found %d competitors after merging", len(competitors))

        # ── Stage 5: Run AI perspectives ──────────────────────────
        await _progress(AnalysisStage.RUNNING_PERSPECTIVES)
        perspectives, models_used = await self._run_perspectives(
            idea, evidence, provider_errors
        )

        # ── Stage 6: Validate citations ───────────────────────────
        await _progress(AnalysisStage.CHECKING_CITATIONS)
        perspectives = validate_citations(perspectives, evidence)

        # ── Stage 7: Calculate scores ─────────────────────────────
        await _progress(AnalysisStage.CALCULATING_SCORES)
        opportunity_score = calculate_opportunity_score(perspectives, evidence, idea)
        evidence_confidence = calculate_evidence_confidence(perspectives=perspectives, evidence=evidence)
        recommendation = _select_recommendation(perspectives)

        # ── Stage 8: Generate experiments ─────────────────────────
        await _progress(AnalysisStage.GENERATING_EXPERIMENTS)
        experiments = generate_experiments(idea, perspectives, evidence)

        # ── Synthesis ─────────────────────────────────────────────
        disagreements = detect_disagreements(perspectives)
        most_dangerous = _select_most_dangerous_assumption(perspectives)
        strongest_sup = _find_strongest(evidence, good=True)
        strongest_con = _find_strongest(evidence, good=False)
        missing_info = _collect_missing_info(perspectives, evidence)

        await _progress(AnalysisStage.COMPLETE)

        return AnalysisResult(
            analysis_id=analysis_id,
            status=AnalysisStatus.COMPLETE,
            stage=AnalysisStage.COMPLETE,
            stage_description=STAGE_DESCRIPTIONS[AnalysisStage.COMPLETE],
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            idea_input=idea,
            interpreted_idea=interpreted_idea,
            evidence=evidence,
            competitors=competitors,
            perspectives=perspectives,
            opportunity_score=opportunity_score,
            evidence_confidence=evidence_confidence,
            recommendation=recommendation,
            most_dangerous_assumption=most_dangerous,
            strongest_supporting=strongest_sup,
            strongest_contradicting=strongest_con,
            missing_information=missing_info,
            experiments=experiments,
            disagreements=disagreements,
            models_used=models_used,
            provider_errors=provider_errors,
            is_demo=is_demo,
        )

    async def _collect_evidence(
        self,
        queries: List[Dict[str, str]],
        idea: IdeaInput,
        errors: List[str],
    ) -> List[EvidenceItem]:
        """Run all queries against all available providers concurrently."""
        if not self._providers:
            errors.append(
                "No research providers available. "
                "Configure SearXNG, GitHub token, or ensure internet access."
            )
            return []

        tasks = []
        for query_info in queries:
            for provider in self._providers:
                tasks.append(
                    self._safe_search(
                        provider,
                        query_info["query"],
                        query_info["type"],
                        idea,
                    )
                )

        # Run all concurrently; failures are caught inside _safe_search
        results = await asyncio.gather(*tasks, return_exceptions=False)
        all_items: List[EvidenceItem] = []
        for batch in results:
            all_items.extend(batch)

        return all_items

    async def _safe_search(
        self,
        provider: ResearchProvider,
        query: str,
        query_type: str,
        idea: IdeaInput,
    ) -> List[EvidenceItem]:
        """Run a single provider search, catching all exceptions."""
        try:
            return await provider.search(query, query_type, idea, max_results=5)
        except Exception as exc:
            logger.warning(
                "Provider %s failed for query %r: %s",
                provider.name, query, exc,
            )
            return []

    async def _run_perspectives(
        self,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
        errors: List[str],
    ) -> tuple[List[AnalysisPerspective], List[str]]:
        """Run three independent perspective analyses."""
        perspective_names = [
            PerspectiveName.MARKET_ANALYST,
            PerspectiveName.SKEPTICAL_INVESTOR,
            PerspectiveName.PRACTICAL_BUILDER,
        ]

        tasks = [
            self._safe_perspective(name, idea, evidence, errors)
            for name in perspective_names
        ]
        outputs: List[Optional[PerspectiveOutput]] = await asyncio.gather(*tasks)

        perspectives: List[AnalysisPerspective] = []
        models_used: List[str] = []

        for name, output in zip(perspective_names, outputs):
            if output is None:
                continue
            perspectives.append(
                AnalysisPerspective(
                    perspective_name=name,
                    perspective_display=PERSPECTIVE_DISPLAY[name],
                    model_id=output.model_id,
                    summary=output.summary,
                    key_findings=output.key_findings,
                    risks=output.risks,
                    opportunities=output.opportunities,
                    recommendation=output.recommendation,
                    cited_evidence_ids=output.cited_evidence_ids,
                    invalid_citations=[],
                    dimension_scores=output.dimension_scores,
                    most_dangerous_assumption=output.most_dangerous_assumption,
                )
            )
            if output.model_id not in models_used:
                models_used.append(output.model_id)

        return perspectives, models_used

    async def _safe_perspective(
        self,
        name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
        errors: List[str],
    ) -> Optional[PerspectiveOutput]:
        try:
            return await self._llm.analyze_perspective(name, idea, evidence)
        except Exception as exc:
            err_msg = f"Perspective {name.value} failed ({self._llm.model_id}): {exc}"
            logger.error(err_msg)
            errors.append(err_msg)
            return None
