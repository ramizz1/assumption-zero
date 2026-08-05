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

# Verify at module load — tests also assert this
assert sum(DIMENSION_WEIGHTS.values()) == 100, (
    f"DIMENSION_WEIGHTS must sum to 100, got {sum(DIMENSION_WEIGHTS.values())}"
)


def _avg_dimension_scores(perspectives: List[AnalysisPerspective]) -> Dict[str, float]:
    """Average raw dimension scores across all perspectives."""
    sums: Dict[str, List[float]] = {k: [] for k in DIMENSION_WEIGHTS}

    for p in perspectives:
        for dim in DIMENSION_WEIGHTS:
            val = p.dimension_scores.get(dim)
            if val is not None:
                sums[dim].append(float(val))

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
        score = p.dimension_scores.get(dim, 50.0)
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
        "See cited evidence for details — configure an AI provider for qualitative explanation."
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

    No AI model is involved in the mathematical calculation.
    """
    avg_raw = _avg_dimension_scores(perspectives)

    dimensions: List[DimensionScore] = []
    total_weighted = 0.0

    for dim, weight in DIMENSION_WEIGHTS.items():
        raw = avg_raw[dim]
        weighted = (raw / 100.0) * weight
        total_weighted += weighted

        sup_ids, con_ids = _find_evidence_for_dimension(dim, perspectives)
        conf = _confidence_from_evidence(evidence, sup_ids, con_ids)

        missing: List[str] = []
        if not sup_ids and not con_ids:
            missing.append(f"No evidence found for {DIMENSION_DISPLAY_NAMES[dim].lower()}")

        dimensions.append(
            DimensionScore(
                dimension=dim,
                display_name=DIMENSION_DISPLAY_NAMES[dim],
                raw_score=round(raw, 1),
                weight=weight,
                weighted_score=round(weighted, 2),
                explanation=_dimension_explanation(dim, raw, idea),
                supporting_evidence_ids=sup_ids,
                contradicting_evidence_ids=con_ids,
                confidence=conf,
                missing_information=missing,
            )
        )

    return OpportunityScore(
        total=round(total_weighted, 1),
        dimensions=dimensions,
    )
