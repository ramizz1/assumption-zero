"""
Competitor merger.

Finds and merges duplicate Competitor entries discovered by different
research providers or AI perspectives using name similarity.
"""
from __future__ import annotations

from typing import List

from assumption_zero.schemas import Competitor


def _normalize(name: str) -> str:
    """Lower-case, strip whitespace and common suffixes."""
    name = name.lower().strip()
    for suffix in [" inc", " llc", " ltd", " corp", " ai", ".com", ".io"]:
        name = name.removesuffix(suffix)
    return name.strip()


def _similar(a: str, b: str) -> bool:
    """Return True if two competitor names appear to be the same product."""
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return True
    # One is a prefix of the other (e.g. "Otter" vs "Otter.ai")
    if na.startswith(nb) or nb.startswith(na):
        return True
    return False


def _merge_two(primary: Competitor, duplicate: Competitor) -> Competitor:
    """Merge duplicate into primary, combining lists and keeping best data."""
    combined_evidence = list(dict.fromkeys(primary.evidence_ids + duplicate.evidence_ids))

    return Competitor(
        name=primary.name,
        url=primary.url or duplicate.url,
        competitor_type=primary.competitor_type,
        description=primary.description or duplicate.description,
        target_user=primary.target_user or duplicate.target_user,
        pricing_evidence=primary.pricing_evidence or duplicate.pricing_evidence,
        strengths=list(dict.fromkeys(primary.strengths + duplicate.strengths)),
        weaknesses=list(dict.fromkeys(primary.weaknesses + duplicate.weaknesses)),
        complaints=list(dict.fromkeys(primary.complaints + duplicate.complaints)),
        differentiation=list(dict.fromkeys(primary.differentiation + duplicate.differentiation)),
        evidence_ids=combined_evidence,
        confidence=primary.confidence,
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

    return merged
