"""
Opportunity Score calculator — pure Python, no AI involved.

Weights must sum exactly to 100. This is enforced at import time.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from assumption_zero.schemas import (
    AnalysisPerspective,
    ConfidenceLevel,
    DimensionScore,
    EvidenceItem,
    IdeaInput,
    OpportunityScore,
)

# Canonical dimension weights — must sum to 100
DIMENSION_WEIGHTS: Dict[str, int] = {
    "problem_evidence": 20,
    "demand_signals": 20,
    "competitive_gap": 15,
    "distribution_feasibility": 15,
    "unit_economics": 15,
    "founder_fit": 10,
    "legal_operational_risk": 5,
}

DIMENSION_DISPLAY_NAMES: Dict[str, str] = {
    "problem_evidence": "Problem Evidence",
    "demand_signals": "Demand Signals",
    "competitive_gap": "Competitive Gap",
    "distribution_feasibility": "Distribution Feasibility",
    "unit_economics": "Unit Economics",
    "founder_fit": "Founder / Project Fit",
    "legal_operational_risk": "Legal & Operational Risk",
}

# Alias mapping for LLM output variations
DIMENSION_ALIASES: Dict[str, str] = {
    "problem_validation": "problem_evidence",
    "problem_fit": "problem_evidence",
    "problem": "problem_evidence",
    "demand": "demand_signals",
    "demand_signal": "demand_signals",
    "demand_evidence": "demand_signals",
    "competitive_advantage": "competitive_gap",
    "competition": "competitive_gap",
    "moat": "competitive_gap",
    "distribution": "distribution_feasibility",
    "go_to_market": "distribution_feasibility",
    "channel": "distribution_feasibility",
    "unit_econ": "unit_economics",
    "economics": "unit_economics",
    "monetization": "unit_economics",
    "founder": "founder_fit",
    "team": "founder_fit",
    "founder_experience": "founder_fit",
    "legal": "legal_operational_risk",
    "compliance": "legal_operational_risk",
    "regulatory": "legal_operational_risk",
    "operational_risk": "legal_operational_risk",
}

# Verify at module load — tests also assert this
assert sum(DIMENSION_WEIGHTS.values()) == 100, (
    f"DIMENSION_WEIGHTS must sum to 100, got {sum(DIMENSION_WEIGHTS.values())}"
)


def _normalize_dimension_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """Map alias dimension keys to canonical keys."""
    normalized: Dict[str, float] = {}
    for key, val in scores.items():
        canonical_key = DIMENSION_ALIASES.get(key.lower(), key.lower())
        if canonical_key in DIMENSION_WEIGHTS:
            try:
                normalized[canonical_key] = max(0.0, min(100.0, float(val)))
            except (ValueError, TypeError):
                pass
    return normalized


def _avg_dimension_scores(perspectives: List[AnalysisPerspective]) -> Dict[str, float]:
    """Average raw dimension scores across all perspectives."""
    sums: Dict[str, List[float]] = {k: [] for k in DIMENSION_WEIGHTS}

    for p in perspectives:
        norm_scores = _normalize_dimension_scores(p.dimension_scores)
        for dim in DIMENSION_WEIGHTS:
            val = norm_scores.get(dim)
            if val is not None:
                sums[dim].append(val)

    return {
        dim: (sum(vals) / len(vals)) if vals else 50.0  # 50 = neutral when unknown
        for dim, vals in sums.items()
    }


def _confidence_from_evidence(
    evidence: List[EvidenceItem],
    supporting_ids: List[str],
    contradicting_ids: List[str],
) -> ConfidenceLevel:
    if not evidence or not supporting_ids:
        return ConfidenceLevel.LOW
    if len(supporting_ids) >= 3:
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MEDIUM


def _find_evidence_for_dimension(
    dim: str,
    perspectives: List[AnalysisPerspective],
) -> tuple[List[str], List[str]]:
    """Collect supporting and contradicting evidence IDs across perspectives for a dimension."""
    supporting: set[str] = set()
    contradicting: set[str] = set()

    for p in perspectives:
        norm_scores = _normalize_dimension_scores(p.dimension_scores)
        score = norm_scores.get(dim, 50.0)
        if score >= 55:
            supporting.update(p.cited_evidence_ids[:3])
        elif score <= 40:
            contradicting.update(p.cited_evidence_ids[:3])

    return sorted(supporting), sorted(contradicting)


def _dimension_explanation(dim: str, raw: float, idea: IdeaInput) -> str:
    """Generate a short evidence-based explanation for a dimension score."""
    name = DIMENSION_DISPLAY_NAMES[dim]
    level = "strong" if raw >= 65 else ("moderate" if raw >= 45 else "weak")
    return (
        f"{name}: {level} signal (score {raw:.0f}/100). "
        "See cited evidence for details."
    )


def calculate_opportunity_score(
    perspectives: List[AnalysisPerspective],
    evidence: List[EvidenceItem],
    idea: IdeaInput,
) -> OpportunityScore:
    """
    Calculate the Opportunity Score from perspective dimension scores.

    - Averages raw scores across perspectives
    - Applies fixed weights (pure Python math)
    - Returns full breakdown with supporting/contradicting evidence per dimension
    """
    avg_raw = _avg_dimension_scores(perspectives)

    dimensions: List[DimensionScore] = []
    total_weighted = 0.0

    for dim, weight in DIMENSION_WEIGHTS.items():
        raw_val = avg_raw.get(dim, 50.0)
        weighted_val = (raw_val * weight) / 100.0
        total_weighted += weighted_val

        supporting, contradicting = _find_evidence_for_dimension(dim, perspectives)
        conf = _confidence_from_evidence(evidence, supporting, contradicting)
        explanation = _dimension_explanation(dim, raw_val, idea)

        dimensions.append(
            DimensionScore(
                dimension=dim,
                display_name=DIMENSION_DISPLAY_NAMES[dim],
                weight=weight,
                raw_score=round(raw_val, 1),
                weighted_score=round(weighted_val, 1),
                confidence=conf,
                explanation=explanation,
                supporting_evidence_ids=supporting,
                contradicting_evidence_ids=contradicting,
            )
        )

    return OpportunityScore(
        total=round(total_weighted, 1),
        dimensions=dimensions,
    )
