"""
Tests for the competitor merger.
"""
from __future__ import annotations

from assumption_zero.analysis.competitor_merger import merge_competitors
from assumption_zero.schemas import Competitor, CompetitorType, ConfidenceLevel


def _comp(name, url="https://example.com", evidence_ids=None) -> Competitor:
    return Competitor(
        name=name,
        url=url,
        competitor_type=CompetitorType.DIRECT,
        description=f"Description of {name}",
        target_user="Test user",
        strengths=["strength1"],
        weaknesses=["weakness1"],
        complaints=[],
        differentiation=["diff1"],
        evidence_ids=evidence_ids or [],
        confidence=ConfidenceLevel.LOW,
    )


def test_exact_duplicates_merged():
    comps = [
        _comp("Otter.ai", evidence_ids=["E001"]),
        _comp("Otter.ai", evidence_ids=["E002"]),
    ]
    merged = merge_competitors(comps)
    assert len(merged) == 1
    assert "E001" in merged[0].evidence_ids
    assert "E002" in merged[0].evidence_ids


def test_name_variant_merged():
    """'Otter' and 'Otter.ai' should be treated as the same company."""
    comps = [
        _comp("Otter", evidence_ids=["E001"]),
        _comp("Otter.ai", evidence_ids=["E002"]),
    ]
    merged = merge_competitors(comps)
    assert len(merged) == 1


def test_different_companies_not_merged():
    comps = [
        _comp("Otter.ai", evidence_ids=["E001"]),
        _comp("Fireflies.ai", evidence_ids=["E002"]),
    ]
    merged = merge_competitors(comps)
    assert len(merged) == 2


def test_empty_list():
    assert merge_competitors([]) == []


def test_single_competitor():
    comps = [_comp("Otter.ai", evidence_ids=["E001"])]
    merged = merge_competitors(comps)
    assert len(merged) == 1


def test_evidence_ids_deduplicated():
    comps = [
        _comp("Otter.ai", evidence_ids=["E001", "E002"]),
        _comp("Otter.ai", evidence_ids=["E002", "E003"]),
    ]
    merged = merge_competitors(comps)
    assert len(merged) == 1
    # E002 should appear only once
    assert merged[0].evidence_ids.count("E002") == 1
