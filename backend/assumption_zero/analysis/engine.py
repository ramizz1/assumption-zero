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
import re
from collections import Counter
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Awaitable
from urllib.parse import urlparse

from assumption_zero.analysis.citation_validator import validate_citations
from assumption_zero.analysis.competitor_merger import merge_competitors
from assumption_zero.analysis.confidence import calculate_evidence_confidence
from assumption_zero.analysis.disagreement import detect_disagreements
from assumption_zero.analysis.experiment_generator import generate_experiments
from assumption_zero.analysis.founder_toolkit import generate_founder_toolkit
from assumption_zero.analysis.query_generator import generate_queries
from assumption_zero.analysis.regional_analysis import generate_regional_analysis
from assumption_zero.analysis.scoring import calculate_opportunity_score
from assumption_zero.llm.base import DiscoveredCompetitor, LLMAdapter, PerspectiveOutput
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
    ResearchCoverage,
    ResearchDepth,
    STAGE_DESCRIPTIONS,
    ValidationExperiment,
)

logger = logging.getLogger(__name__)

_DEPTH_PRESETS = {
    ResearchDepth.STANDARD: {"queries_per_type": 1, "max_results": 3, "max_evidence": 50, "concurrency": 12},
    ResearchDepth.DEEP: {"queries_per_type": 2, "max_results": 5, "max_evidence": 100, "concurrency": 20},
    ResearchDepth.EXHAUSTIVE: {"queries_per_type": 4, "max_results": 8, "max_evidence": 200, "concurrency": 24},
}

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


IGNORE_COMPETITOR_WORDS = {
    "idk", "none", "no", "n/a", "unknown", "nothing", "no idea",
    "dont know", "don't know", "na",
}

_AGGREGATOR_HOSTS = {
    "alternativeto.net", "capterra.com", "crunchbase.com", "duckduckgo.com",
    "facebook.com", "g2.com", "github.com", "linkedin.com", "medium.com",
    "producthunt.com", "reddit.com", "techcrunch.com", "wikipedia.org",
    "x.com", "youtube.com",
}

_GENERIC_COMPETITOR_TITLES = (
    "best ", "top ", "alternatives", "competitors", "comparison", "review",
    "software for", "tools for", "how to", "what is", "why ", "guide to",
)


def _normalized_name(value: str) -> str:
    """Normalize a product name for conservative equality and mention checks."""
    normalized = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    words = normalized.split()
    if words and words[-1] in {"ai", "app", "com", "io", "inc", "llc", "ltd", "corp"}:
        words.pop()
    return " ".join(words)


def _brand_from_url(url: str) -> str:
    """Return a plausible brand from an official product URL, never an aggregator."""
    try:
        host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
    except ValueError:
        return ""
    if not host or any(host == item or host.endswith(f".{item}") for item in _AGGREGATOR_HOSTS):
        return ""
    label = host.split(".")[0]
    if len(label) < 2 or label in {"app", "blog", "docs", "help", "news"}:
        return ""
    return " ".join(part.capitalize() for part in label.split("-") if part)


def _clean_competitor_name(title: str, url: str = "") -> str:
    """Extract a clean brand name from search result title, stripping forum headers."""
    original = title.strip()
    name = re.sub(r"^\[[^\]]+\]\s*", "", original).strip()
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

    # Prefer the official domain when a web result title is a snippet rather
    # than a product name (for example: "[otter.ai] AI meeting notes...").
    domain_brand = _brand_from_url(url)
    bracket_match = re.match(r"^\[([^\]]+)\]", original)
    if domain_brand:
        actual_host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
        bracket_is_official = False
        if bracket_match:
            bracket_host = bracket_match.group(1).casefold().removeprefix("www.")
            bracket_is_official = bracket_host == actual_host
        title_starts_with_brand = _normalized_name(name).startswith(_normalized_name(domain_brand))
        if bracket_is_official or title_starts_with_brand:
            name = domain_brand

    # Filter out raw repository paths, listicles, questions, and junk names.
    if "/" in name or name.startswith(("-", "http", "www", "Skip to")):
        return ""

    words = name.split()
    lowered = name.casefold()
    if (
        len(words) > 4
        or (words and words[0].isdigit())
        or lowered.startswith(("as a", "the ", "i ", "cost-effective", "show hn", "launch hn"))
        or any(pattern in lowered for pattern in _GENERIC_COMPETITOR_TITLES)
    ):
        return ""

    return name.strip()


def _extract_competitors_from_evidence(evidence: List[EvidenceItem], idea: Optional[IdeaInput] = None) -> List[Competitor]:
    """
    Parse competitor information from evidence items and user-declared competitors.
    Returns Competitor objects that will be merged.
    """
    competitors: List[Competitor] = []
    # 1. Include user-specified competitors directly
    if idea and idea.known_competitors:
        for raw_comp in idea.known_competitors.split(","):
            cname = raw_comp.strip()
            if not cname or cname.lower() in IGNORE_COMPETITOR_WORDS:
                continue
            matching_items = [e for e in evidence if _evidence_mentions(cname, e)]
            matching_ev = [e.evidence_id for e in matching_items]
            matching_passages = [e.passage for e in matching_items]
            desc = (
                matching_passages[0][:300]
                if matching_passages
                else "User-supplied competitor; independent evidence was not found in this research run."
            )
            independent_sources = {e.source_name for e in matching_items}
            confidence = (
                ConfidenceLevel.HIGH if len(independent_sources) >= 2
                else ConfidenceLevel.MEDIUM if matching_items
                else ConfidenceLevel.LOW
            )

            competitors.append(
                Competitor(
                    name=cname,
                    url=next((e.url for e in matching_items if not e.url.startswith("demo://")), ""),
                    competitor_type=CompetitorType.DIRECT,
                    description=desc,
                    target_user="Not established in collected evidence",
                    pricing_evidence=None,
                    strengths=[],
                    weaknesses=[],
                    complaints=[],
                    differentiation=[f"Hypothesis: validate a meaningful switching reason versus {cname}"],
                    evidence_ids=matching_ev[:5],
                    confidence=confidence,
                )
            )

    # 2. Parse from evidence items of type COMPETITOR
    for item in evidence:
        if item.evidence_type not in (EvidenceType.COMPETITOR, EvidenceType.OSS_ALTERNATIVE):
            continue

        clean_name = _clean_competitor_name(item.title, item.url)
        if not clean_name or clean_name.lower() in IGNORE_COMPETITOR_WORDS:
            continue
        if idea and _normalized_name(clean_name) == _normalized_name(idea.name):
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
                target_user="Not established in collected evidence",
                pricing_evidence=None,
                strengths=[],
                weaknesses=[],
                complaints=[],
                differentiation=[],
                evidence_ids=[item.evidence_id],
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

    return competitors


def _evidence_mentions(name: str, item: EvidenceItem) -> bool:
    """Return whether an evidence item actually names the candidate product."""
    needle = _normalized_name(name)
    if len(needle) < 2:
        return False
    haystack = _normalized_name(
        f"{item.title} {item.passage} {urlparse(item.url).hostname or ''}"
    )
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack))


def _validated_ai_competitors(
    candidates: List[DiscoveredCompetitor],
    evidence: List[EvidenceItem],
    idea: IdeaInput,
) -> List[Competitor]:
    """Accept AI competitors only when cited evidence explicitly names them."""
    by_id = {item.evidence_id: item for item in evidence}
    accepted: List[Competitor] = []

    for candidate in candidates:
        if _normalized_name(candidate.name) == _normalized_name(idea.name):
            continue
        cited_items = [
            by_id[eid] for eid in dict.fromkeys(candidate.evidence_ids)
            if eid in by_id and _evidence_mentions(candidate.name, by_id[eid])
        ]
        if not cited_items:
            logger.info("Rejected unsupported AI competitor: %s", candidate.name)
            continue

        source_count = len({item.source_name for item in cited_items})
        confidence = ConfidenceLevel.HIGH if source_count >= 2 else ConfidenceLevel.MEDIUM
        pricing_markers = (
            re.findall(r"(?:[$€£]\s?\d+(?:[.,]\d+)?)|(?:\b\d+(?:[.,]\d+)?\s?%\b)", candidate.pricing_evidence or "")
            + re.findall(r"\b(?:free|freemium|custom pricing)\b", candidate.pricing_evidence or "", re.I)
        )
        cited_pricing_text = " ".join(item.passage for item in cited_items).casefold()
        pricing_supported = bool(candidate.pricing_evidence) and (
            any(item.evidence_type == EvidenceType.PRICING for item in cited_items)
            or any(marker.casefold().replace(" ", "") in cited_pricing_text.replace(" ", "") for marker in pricing_markers)
        )
        differentiation = [
            value if value.casefold().startswith("hypothesis:") else f"Hypothesis: {value}"
            for value in candidate.differentiation[:4]
            if value.strip()
        ]

        accepted.append(
            Competitor(
                name=candidate.name.strip(),
                url=next((item.url for item in cited_items if not item.url.startswith("demo://")), ""),
                competitor_type=candidate.competitor_type,
                description=(candidate.description or cited_items[0].passage)[:500],
                target_user=candidate.target_user or "Not established in collected evidence",
                pricing_evidence=candidate.pricing_evidence if pricing_supported else None,
                strengths=candidate.strengths[:5],
                weaknesses=candidate.weaknesses[:5],
                complaints=candidate.complaints[:5],
                differentiation=differentiation,
                evidence_ids=[item.evidence_id for item in cited_items],
                confidence=confidence,
            )
        )

    return accepted


def _select_recommendation(perspectives: List[AnalysisPerspective], confidence: ConfidenceLevel) -> Recommendation:
    """Majority vote across perspectives. Tie → Test First.
    Downgrade Build to Test First if evidence confidence is low.
    """
    if not perspectives:
        return Recommendation.TEST_FIRST
    counts = Counter(p.recommendation.value for p in perspectives)
    most_common = counts.most_common(1)[0][0]
    rec = Recommendation(most_common)
    
    if rec == Recommendation.BUILD and confidence == ConfidenceLevel.LOW:
        return Recommendation.TEST_FIRST
        
    return rec


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
    competitors: Optional[List[Competitor]] = None,
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
    if not competitors:
        missing.append("No evidence-grounded competitors found; run targeted customer and category research")
    elif not any(competitor.evidence_ids for competitor in competitors):
        missing.append("Competitors are user-supplied but not independently verified by collected evidence")
    elif len({eid for competitor in competitors for eid in competitor.evidence_ids}) < 2:
        missing.append("Competitor coverage relies on a single evidence item; verify with another independent source")

    return list(dict.fromkeys(missing))


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
        max_evidence: Optional[int] = None,
        queries_per_type: Optional[int] = None,
        research_depth: ResearchDepth | str = ResearchDepth.DEEP,
    ) -> None:
        self._research_depth = ResearchDepth(research_depth)
        preset = _DEPTH_PRESETS[self._research_depth]
        self._providers = [p for p in providers if p.is_available]
        self._llm = llm_adapter
        self._max_evidence = max_evidence or preset["max_evidence"]
        self._queries_per_type = queries_per_type or preset["queries_per_type"]
        self._max_results_per_query = preset["max_results"]
        self._max_concurrent_searches = preset["concurrency"]

        logger.info(
            "AnalysisEngine ready: providers=%s, llm=%s, depth=%s",
            [p.name for p in self._providers],
            llm_adapter.model_id,
            self._research_depth.value,
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
        generated_queries = generate_queries(idea)
        all_queries = self._select_queries(generated_queries)
        logger.info(
            "Generated %d research queries; executing %d balanced queries",
            len(generated_queries),
            len(all_queries),
        )

        # ── Stage 3: Collect evidence ─────────────────────────────
        await _progress(AnalysisStage.COLLECTING_EVIDENCE)
        raw_evidence = await self._collect_evidence(
            all_queries, idea, provider_errors
        )
        evidence = _assign_evidence_ids(raw_evidence)[: self._max_evidence]
        logger.info("Collected %d unique evidence items", len(evidence))
        regional_analysis = generate_regional_analysis(idea, evidence)
        research_coverage = ResearchCoverage(
            depth=self._research_depth,
            queries_generated=len(generated_queries),
            queries_executed=len(all_queries),
            providers_used=[provider.name for provider in self._providers],
            evidence_collected=len(evidence),
            regional_evidence_count=regional_analysis.evidence_count,
        )

        # ── Stage 4: Find competitors ─────────────────────────────
        await _progress(AnalysisStage.FINDING_COMPETITORS)
        raw_competitors = _extract_competitors_from_evidence(evidence, idea)
        competitors = merge_competitors(raw_competitors)
        logger.info("Found %d competitors after merging", len(competitors))

        # ── Stage 5: Run AI perspectives ──────────────────────────
        await _progress(AnalysisStage.RUNNING_PERSPECTIVES)
        perspectives, models_used, ai_competitor_candidates = await self._run_perspectives(
            idea, evidence, provider_errors
        )

        # AI adds semantic extraction (names buried in passages), but every
        # candidate passes a deterministic evidence-name check before display.
        ai_competitors = _validated_ai_competitors(
            ai_competitor_candidates, evidence, idea
        )
        competitors = merge_competitors(competitors + ai_competitors)[:20]
        logger.info(
            "Competitor profile complete: %d verified/declared entries (%d AI-supported)",
            len(competitors), len(ai_competitors),
        )

        if not perspectives:
            err = provider_errors[0] if provider_errors else "AI perspective analysis failed."
            logger.error("Analysis failed: no perspectives generated. Error: %s", err)
            return AnalysisResult(
                analysis_id=analysis_id,
                status=AnalysisStatus.FAILED,
                stage=AnalysisStage.COMPLETE,
                created_at=datetime.utcnow(),
                idea_input=idea,
                interpreted_idea=interpreted_idea,
                evidence=evidence,
                competitors=competitors,
                perspectives=[],
                opportunity_score=None,
                evidence_confidence=None,
                recommendation=None,
                most_dangerous_assumption="",
                strongest_supporting="",
                strongest_contradicting="",
                missing_information=[],
                experiments=[],
                founder_toolkit=None,
                regional_analysis=regional_analysis,
                research_coverage=research_coverage,
                disagreements=[],
                models_used=[],
                provider_errors=provider_errors,
                error_message=err,
                is_demo=is_demo,
            )

        # ── Stage 6: Validate citations ───────────────────────────
        await _progress(AnalysisStage.CHECKING_CITATIONS)
        perspectives = validate_citations(perspectives, evidence)

        # ── Stage 7: Calculate scores ─────────────────────────────
        await _progress(AnalysisStage.CALCULATING_SCORES)
        
        opportunity_score = calculate_opportunity_score(perspectives, evidence, idea)
        evidence_confidence = calculate_evidence_confidence(perspectives=perspectives, evidence=evidence)
        recommendation = _select_recommendation(perspectives, evidence_confidence)

        # ── Stage 8: Generate experiments ─────────────────────────
        await _progress(AnalysisStage.GENERATING_EXPERIMENTS)
        experiments = generate_experiments(idea, perspectives, evidence)
        founder_toolkit = generate_founder_toolkit(idea, recommendation, experiments)

        # ── Synthesis ─────────────────────────────────────────────
        disagreements = detect_disagreements(perspectives)
        most_dangerous = _select_most_dangerous_assumption(perspectives)
        strongest_sup = _find_strongest(evidence, good=True)
        strongest_con = _find_strongest(evidence, good=False)
        missing_info = _collect_missing_info(perspectives, evidence, competitors)

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
            founder_toolkit=founder_toolkit,
            regional_analysis=regional_analysis,
            research_coverage=research_coverage,
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

        semaphore = asyncio.Semaphore(self._max_concurrent_searches)

        async def limited_search(provider, query_info):
            async with semaphore:
                return await self._safe_search(
                    provider,
                    query_info["query"],
                    query_info["type"],
                    idea,
                )

        tasks = []
        for query_info in queries:
            for provider in self._providers:
                tasks.append(limited_search(provider, query_info))

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
            return await provider.search(
                query,
                query_type,
                idea,
                max_results=self._max_results_per_query,
            )
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
    ) -> tuple[List[AnalysisPerspective], List[str], List[DiscoveredCompetitor]]:
        """Run three to five independent perspectives based on research depth."""
        perspective_names = [
            PerspectiveName.MARKET_ANALYST,
            PerspectiveName.SKEPTICAL_INVESTOR,
            PerspectiveName.PRACTICAL_BUILDER,
        ]
        if self._research_depth in (ResearchDepth.DEEP, ResearchDepth.EXHAUSTIVE):
            perspective_names.insert(1, PerspectiveName.REGIONAL_STRATEGIST)
        if self._research_depth == ResearchDepth.EXHAUSTIVE:
            perspective_names.insert(-1, PerspectiveName.CUSTOMER_RESEARCHER)

        tasks = [
            self._safe_perspective(name, idea, evidence, errors)
            for name in perspective_names
        ]
        outputs: List[Optional[PerspectiveOutput]] = await asyncio.gather(*tasks)

        perspectives: List[AnalysisPerspective] = []
        models_used: List[str] = []
        competitor_candidates: List[DiscoveredCompetitor] = []

        for name, output in zip(perspective_names, outputs):
            if output is None:
                continue
            competitor_candidates.extend(output.competitors)
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

        return perspectives, models_used, competitor_candidates

    def _select_queries(self, queries: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Take a bounded number of queries from every evidence category."""
        selected: List[Dict[str, str]] = []
        counts: Counter = Counter()
        for query in queries:
            query_type = query["type"]
            if counts[query_type] >= self._queries_per_type:
                continue
            selected.append(query)
            counts[query_type] += 1
        return selected

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
