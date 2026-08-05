"""
Mock LLM adapter — fallback when no real AI provider is configured.

This adapter does NOT produce fake hardcoded results.
It applies deterministic scoring heuristics to the REAL collected evidence.
The output is clearly labelled as "Template Analysis" so users know to
configure a real AI provider (Gemini, Ollama, or OpenAI-compatible) for
deeper qualitative reasoning.

No data is invented. Every score is derived from the actual evidence.
"""
from __future__ import annotations

import logging
from typing import List

from assumption_zero.llm.base import (
    DIMENSION_KEYS,
    LLMAdapter,
    PerspectiveOutput,
)
from assumption_zero.schemas import (
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    PerspectiveName,
    Recommendation,
    ReliabilityLevel,
)

logger = logging.getLogger(__name__)


def _count(evidence: List[EvidenceItem], ev_type: EvidenceType) -> int:
    return sum(1 for e in evidence if e.evidence_type == ev_type)


def _avg_relevance(evidence: List[EvidenceItem], ev_type: EvidenceType) -> float:
    items = [e.relevance_score for e in evidence if e.evidence_type == ev_type]
    return sum(items) / len(items) if items else 0.0


def _high_reliability_count(evidence: List[EvidenceItem]) -> int:
    return sum(1 for e in evidence if e.reliability == ReliabilityLevel.HIGH)


def _compute_scores(
    perspective: PerspectiveName,
    evidence: List[EvidenceItem],
    idea: IdeaInput,
) -> dict[str, float]:
    """
    Derive dimension scores from the real collected evidence.
    Returns raw scores (0-100) per dimension.
    """
    n = len(evidence)
    if n == 0:
        # No evidence — all scores are low but not zero (idea may still be viable)
        return {k: 30.0 for k in DIMENSION_KEYS}

    # Evidence presence signals
    demand_count = _count(evidence, EvidenceType.DEMAND)
    complaint_count = _count(evidence, EvidenceType.COMPLAINT)
    competitor_count = _count(evidence, EvidenceType.COMPETITOR)
    regulatory_count = _count(evidence, EvidenceType.REGULATORY)
    distribution_count = _count(evidence, EvidenceType.DISTRIBUTION)
    failed_count = _count(evidence, EvidenceType.FAILED_PRODUCT)
    oss_count = _count(evidence, EvidenceType.OSS_ALTERNATIVE)

    high_rel = _high_reliability_count(evidence)
    high_rel_ratio = high_rel / n

    # ── Problem evidence ──────────────────────────────────────────
    problem_score = min(100.0, (demand_count + complaint_count) * 15 + high_rel_ratio * 20)

    # ── Demand signals ────────────────────────────────────────────
    demand_score = min(100.0, demand_count * 18 + _avg_relevance(evidence, EvidenceType.DEMAND) * 30)

    # ── Competitive gap ───────────────────────────────────────────
    # Fewer entrenched competitors = higher gap; many OSS alternatives = lower gap
    if perspective == PerspectiveName.SKEPTICAL_INVESTOR:
        # Skeptic views competitors as threats
        competitive_score = max(10.0, 80 - competitor_count * 12 - oss_count * 8)
    else:
        competitive_score = max(15.0, 70 - competitor_count * 8 - oss_count * 5)

    # ── Distribution feasibility ──────────────────────────────────
    if distribution_count > 0:
        dist_score = min(80.0, 50 + distribution_count * 10)
    else:
        dist_score = 45.0  # Unknown without evidence

    # ── Unit economics ────────────────────────────────────────────
    has_price = bool(idea.price)
    has_budget = bool(idea.budget)
    econ_score = 50.0
    if has_price:
        econ_score += 15
    if has_budget:
        econ_score += 10
    if failed_count > 0:
        econ_score -= failed_count * 8  # Prior failures hint at economic problems
    econ_score = max(10.0, min(85.0, econ_score))

    # ── Founder fit ───────────────────────────────────────────────
    has_skills = bool(idea.founder_skills)
    fit_score = 55.0 if has_skills else 40.0
    if perspective == PerspectiveName.PRACTICAL_BUILDER:
        fit_score += 5  # Builder perspective gives slight benefit of doubt

    # ── Legal / operational risk ──────────────────────────────────
    # Higher regulatory items = more risk = LOWER score for this dimension
    # (Lower score in risk dimension = higher risk, used inversely in display)
    legal_score = max(10.0, 80 - regulatory_count * 15 - failed_count * 10)

    # Adjust all scores by perspective bias
    if perspective == PerspectiveName.MARKET_ANALYST:
        # Market analyst: moderate, evidence-led
        multipliers = {
            "problem_evidence": 1.0,
            "demand_signals": 1.1,
            "competitive_gap": 0.95,
            "distribution_feasibility": 1.0,
            "unit_economics": 1.0,
            "founder_fit": 0.95,
            "legal_operational_risk": 1.0,
        }
    elif perspective == PerspectiveName.SKEPTICAL_INVESTOR:
        # Skeptic: lowers most scores, especially competition and economics
        multipliers = {
            "problem_evidence": 0.9,
            "demand_signals": 0.85,
            "competitive_gap": 0.75,
            "distribution_feasibility": 0.8,
            "unit_economics": 0.8,
            "founder_fit": 0.85,
            "legal_operational_risk": 0.8,
        }
    else:  # PRACTICAL_BUILDER
        # Builder: optimistic on feasibility, critical on distribution
        multipliers = {
            "problem_evidence": 1.0,
            "demand_signals": 0.95,
            "competitive_gap": 1.05,
            "distribution_feasibility": 0.85,
            "unit_economics": 0.9,
            "founder_fit": 1.1,
            "legal_operational_risk": 1.0,
        }

    raw = {
        "problem_evidence": problem_score,
        "demand_signals": demand_score,
        "competitive_gap": competitive_score,
        "distribution_feasibility": dist_score,
        "unit_economics": econ_score,
        "founder_fit": fit_score,
        "legal_operational_risk": legal_score,
    }

    return {k: min(100.0, max(0.0, round(v * multipliers[k], 1))) for k, v in raw.items()}


def _recommendation_from_avg(avg: float) -> Recommendation:
    if avg >= 68:
        return Recommendation.BUILD
    if avg >= 50:
        return Recommendation.TEST_FIRST
    if avg >= 35:
        return Recommendation.PIVOT
    return Recommendation.AVOID


def _findings(perspective: PerspectiveName, evidence: List[EvidenceItem], idea: IdeaInput) -> list[str]:
    findings = []
    if not evidence:
        findings.append("No research evidence collected — configure research providers for a real analysis.")
        return findings

    competitors = [e for e in evidence if e.evidence_type == EvidenceType.COMPETITOR]
    demand = [e for e in evidence if e.evidence_type == EvidenceType.DEMAND]
    regulatory = [e for e in evidence if e.evidence_type == EvidenceType.REGULATORY]
    complaints = [e for e in evidence if e.evidence_type == EvidenceType.COMPLAINT]

    if competitors:
        ids = ", ".join(f"[{c.evidence_id}]" for c in competitors[:3])
        findings.append(f"{len(competitors)} direct or indirect competitor(s) found in research {ids}.")
    if demand:
        ids = ", ".join(f"[{d.evidence_id}]" for d in demand[:3])
        findings.append(f"{len(demand)} demand signal(s) identified {ids}.")
    if complaints:
        ids = ", ".join(f"[{c.evidence_id}]" for c in complaints[:2])
        findings.append(f"Customer complaints about existing solutions found {ids}.")
    if regulatory:
        ids = ", ".join(f"[{r.evidence_id}]" for r in regulatory[:2])
        findings.append(f"Regulatory or compliance considerations noted {ids}.")
    if not findings:
        findings.append(
            f"Configure an AI provider (Gemini, Ollama, or OpenAI-compatible) "
            "for detailed qualitative findings."
        )
    return findings


class MockAdapter(LLMAdapter):
    """
    Template-based analysis from real evidence.

    Uses deterministic heuristics on collected evidence to score each dimension.
    Configure a real AI provider in .env for qualitative reasoning.
    """

    @property
    def model_id(self) -> str:
        return "template-analysis-v1 (no AI configured)"

    @property
    def is_available(self) -> bool:
        return True  # Always available as fallback

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        logger.info(
            "MockAdapter: running template analysis for perspective=%s on %d evidence items",
            perspective_name.value,
            len(evidence),
        )

        scores = _compute_scores(perspective_name, evidence, idea)
        avg_score = sum(scores.values()) / len(scores)
        recommendation = _recommendation_from_avg(avg_score)
        findings = _findings(perspective_name, evidence, idea)
        cited = [e.evidence_id for e in evidence[:10]]

        if perspective_name == PerspectiveName.MARKET_ANALYST:
            summary = (
                f"Template analysis of {idea.name} as Market Analyst. "
                f"{len(evidence)} evidence items collected across "
                f"{len(set(e.source_name for e in evidence))} sources. "
                "Configure a real AI provider for qualitative market analysis."
            )
            risks = ["No AI provider configured — qualitative risk assessment unavailable."]
            opportunities = [
                f"Problem statement targets {idea.target_customer} — verify demand with customer interviews.",
            ]
            mda = f"Unvalidated assumption: customers in {idea.geography} will pay {idea.price or 'the proposed price'}"
        elif perspective_name == PerspectiveName.SKEPTICAL_INVESTOR:
            summary = (
                f"Template skeptical review of {idea.name}. "
                f"{len([e for e in evidence if e.evidence_type == EvidenceType.COMPETITOR])} "
                "competitor(s) found. Configure a real AI provider for a full investment-grade critique."
            )
            risks = [
                "Competitor landscape not fully analyzed — configure AI provider.",
                "Switching costs and distribution challenges require qualitative assessment.",
            ]
            opportunities = []
            mda = "Distribution: how will this product reach customers cost-effectively?"
        else:  # PRACTICAL_BUILDER
            summary = (
                f"Template builder assessment of {idea.name}. "
                f"Founder skills: {idea.founder_skills or 'not specified'}. "
                "Configure a real AI provider for MVP scope recommendations."
            )
            risks = [
                "Technical feasibility requires AI-assisted assessment — configure provider.",
            ]
            opportunities = [
                "A minimal walkthrough demo can be built before full AI analysis.",
            ]
            mda = f"Budget {idea.budget or 'unknown'} may not cover full MVP build — validate assumptions cheaply first."

        return PerspectiveOutput(
            perspective_name=perspective_name,
            model_id=self.model_id,
            summary=summary,
            key_findings=findings,
            risks=risks,
            opportunities=opportunities,
            recommendation=recommendation,
            dimension_scores=scores,
            cited_evidence_ids=cited,
            most_dangerous_assumption=mda,
            reasoning=(
                f"Heuristic scoring: {len(evidence)} evidence items, "
                f"avg dimension score={avg_score:.1f}"
            ),
        )

    async def clarify_idea(self, idea: IdeaInput) -> str:
        return (
            f"**{idea.name}** — {idea.description}\n\n"
            f"**Problem:** {idea.problem}\n"
            f"**Target:** {idea.target_customer} in {idea.geography}\n"
            f"**Model:** {idea.business_model or 'Not specified'} | "
            f"**Price:** {idea.price or 'Not specified'}\n\n"
            "_Note: Configure Gemini, Ollama, or an OpenAI-compatible endpoint "
            "for AI-powered qualitative interpretation._"
        )
