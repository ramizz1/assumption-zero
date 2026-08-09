"""
Competitor merger.

Finds and merges duplicate Competitor entries discovered by different
research providers or AI perspectives using name similarity.
"""
from __future__ import annotations

import re
from typing import List

from assumption_zero.schemas import Competitor, CompetitorType, ConfidenceLevel


_CONFIDENCE_RANK = {
    ConfidenceLevel.LOW: 0,
    ConfidenceLevel.MEDIUM: 1,
    ConfidenceLevel.HIGH: 2,
}


def _normalize(name: str) -> str:
    """Lower-case, strip whitespace and common suffixes."""
    name = re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()
    parts = name.split()
    if parts and parts[-1] in {"inc", "llc", "ltd", "corp", "ai", "app", "com", "io"}:
        parts.pop()
    return " ".join(parts)


def _similar(a: str, b: str) -> bool:
    """Return True if two competitor names appear to be the same product."""
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return True
    # Intentionally avoid prefix matching: "Acme" and "Acme Analytics" may be
    # separate products. Common legal/domain suffixes are handled above.
    return False


def _merge_two(primary: Competitor, duplicate: Competitor) -> Competitor:
    """Merge duplicate into primary, combining lists and keeping best data."""
    best = max(
        (primary, duplicate),
        key=lambda comp: (
            _CONFIDENCE_RANK[comp.confidence],
            len(comp.evidence_ids),
            bool(comp.url),
            len(comp.description),
        ),
    )
    other = duplicate if best is primary else primary
    display_name = max(
        (primary, duplicate),
        key=lambda comp: (
            _CONFIDENCE_RANK[comp.confidence],
            "." in comp.name,
            len(comp.name),
        ),
    ).name
    combined_evidence = list(dict.fromkeys(primary.evidence_ids + duplicate.evidence_ids))

    return Competitor(
        name=display_name,
        url=best.url or other.url,
        competitor_type=(
            CompetitorType.DIRECT
            if CompetitorType.DIRECT in {primary.competitor_type, duplicate.competitor_type}
            else CompetitorType.INDIRECT
        ),
        description=best.description or other.description,
        target_user=best.target_user or other.target_user,
        pricing_evidence=best.pricing_evidence or other.pricing_evidence,
        strengths=list(dict.fromkeys(primary.strengths + duplicate.strengths)),
        weaknesses=list(dict.fromkeys(primary.weaknesses + duplicate.weaknesses)),
        complaints=list(dict.fromkeys(primary.complaints + duplicate.complaints)),
        differentiation=list(dict.fromkeys(primary.differentiation + duplicate.differentiation)),
        evidence_ids=combined_evidence,
        confidence=best.confidence,
    )


def merge_competitors(competitors: List[Competitor]) -> List[Competitor]:
    """
    Merge near-duplicate competitors.

    Input: list may contain duplicates from different providers.
    Output: deduplicated list with combined evidence.
    """
    merged: List[Competitor] = []

    for comp in competitors:
        matched = False
        for i, existing in enumerate(merged):
            if _similar(existing.name, comp.name):
                merged[i] = _merge_two(existing, comp)
                matched = True
                break
        if not matched:
            merged.append(comp)

    return sorted(
        merged,
        key=lambda comp: (
            -_CONFIDENCE_RANK[comp.confidence],
            -len(comp.evidence_ids),
            comp.name.casefold(),
        ),
    )
