"""
Model disagreement detector.

Identifies topics where the three perspectives reach different conclusions,
presents both positions with supporting evidence, and flags items that
require human research.
"""
from __future__ import annotations

from typing import List

from assumption_zero.schemas import (
    AnalysisPerspective,
    DisagreementPosition,
    ModelDisagreement,
    Recommendation,
)


def detect_disagreements(
    perspectives: List[AnalysisPerspective],
) -> List[ModelDisagreement]:
    """Detect meaningful disagreements across perspectives and return them."""
    if len(perspectives) < 2:
        return []

    disagreements: List[ModelDisagreement] = []

    # ── Recommendation disagreement ───────────────────────────────
    recs = [p.recommendation for p in perspectives]
    if len(set(recs)) > 1:
        positions = [
            DisagreementPosition(
                perspective=p.perspective_display,
                model_id=p.model_id,
                position=f"Recommendation: {p.recommendation.value}",
                evidence_ids=p.cited_evidence_ids[:3],
            )
            for p in perspectives
        ]
        rec_values = [r.value for r in recs]
        # Stronger position = most common recommendation
        from collections import Counter
        most_common = Counter(rec_values).most_common(1)[0][0]
        disagreements.append(
            ModelDisagreement(
                topic="Overall Recommendation",
                positions=positions,
                stronger_position=most_common,
                requires_human_research=True,
            )
        )

    # ── Dimension score disagreements ─────────────────────────────
    from assumption_zero.analysis.scoring import DIMENSION_WEIGHTS, DIMENSION_DISPLAY_NAMES

    for dim in DIMENSION_WEIGHTS:
        scores = [p.dimension_scores.get(dim) for p in perspectives]
        valid_scores = [s for s in scores if s is not None]
        if len(valid_scores) < 2:
            continue

        score_range = max(valid_scores) - min(valid_scores)
        if score_range < 25:
            # Scores are close enough — not a meaningful disagreement
            continue

        positions = [
            DisagreementPosition(
                perspective=p.perspective_display,
                model_id=p.model_id,
                position=(
                    f"Score: {p.dimension_scores.get(dim, 'N/A'):.0f}/100"
                    if p.dimension_scores.get(dim) is not None
                    else "No score"
                ),
                evidence_ids=p.cited_evidence_ids[:2],
            )
            for p in perspectives
            if p.dimension_scores.get(dim) is not None
        ]

        if len(positions) >= 2:
            high_scorer = max(positions, key=lambda pos: float(pos.position.split(":")[1].split("/")[0].strip()) if ":" in pos.position else 0)
            disagreements.append(
                ModelDisagreement(
                    topic=f"{DIMENSION_DISPLAY_NAMES[dim]} Assessment",
                    positions=positions,
                    stronger_position=high_scorer.perspective,
                    requires_human_research=score_range >= 40,
                )
            )

    # ── Dangerous assumption disagreement ─────────────────────────
    assumptions = [p.most_dangerous_assumption for p in perspectives if p.most_dangerous_assumption]
    if len(set(assumptions)) > 1:
        positions = [
            DisagreementPosition(
                perspective=p.perspective_display,
                model_id=p.model_id,
                position=p.most_dangerous_assumption,
                evidence_ids=[],
            )
            for p in perspectives
            if p.most_dangerous_assumption
        ]
        if len(positions) >= 2:
            disagreements.append(
                ModelDisagreement(
                    topic="Most Dangerous Assumption",
                    positions=positions,
                    stronger_position=None,
                    requires_human_research=True,
                )
            )

    return disagreements
