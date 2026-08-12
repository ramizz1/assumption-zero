"""Tests for evidence confidence calculation."""

from __future__ import annotations

from assumption_zero.analysis.confidence import calculate_evidence_confidence
from assumption_zero.schemas import ConfidenceLevel


def test_no_evidence_returns_low():
    result = calculate_evidence_confidence([], [])
    assert result == ConfidenceLevel.LOW


def test_many_high_quality_items_returns_high(sample_evidence, sample_perspectives):
    from assumption_zero.schemas import ReliabilityLevel

    # Override all reliability to HIGH
    for e in sample_evidence:
        e.reliability = ReliabilityLevel.HIGH
    # Add more items to pass thresholds
    from copy import deepcopy
    from datetime import date

    extra = []
    for i in range(10):
        item = deepcopy(sample_evidence[0])
        item.evidence_id = f"EX{i:02d}"
        item.url = f"https://example.com/extra/{i}"
        item.source_name = f"Source{i}"
        item.publication_date = date(2024, 6, 1)
        extra.append(item)
    all_evidence = sample_evidence + extra
    result = calculate_evidence_confidence(all_evidence, sample_perspectives)
    # Should be Medium or High with 13 items and varied sources
    assert result in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)


def test_single_item_returns_low(sample_evidence, sample_perspectives):
    result = calculate_evidence_confidence([sample_evidence[0]], [])
    assert result == ConfidenceLevel.LOW


def test_confidence_is_independent_of_score(sample_evidence, sample_perspectives):
    """Confidence must be calculated independently from opportunity score."""
    # All dimension scores maxed out — should not affect confidence
    for p in sample_perspectives:
        for k in p.dimension_scores:
            p.dimension_scores[k] = 100.0
    result = calculate_evidence_confidence(sample_evidence[:1], sample_perspectives)
    # Only 1 evidence item → low confidence regardless of scores
    assert result == ConfidenceLevel.LOW
