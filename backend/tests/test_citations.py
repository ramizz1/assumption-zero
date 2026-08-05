"""Tests for citation validator."""
from __future__ import annotations

from assumption_zero.analysis.citation_validator import validate_citations
from assumption_zero.schemas import AnalysisPerspective, PerspectiveName, Recommendation


def _make_perspective(name, cited, invalid=None):
    return AnalysisPerspective(
        perspective_name=name,
        perspective_display=name.value,
        model_id="mock",
        summary="Test perspective",
        key_findings=[],
        risks=[],
        opportunities=[],
        recommendation=Recommendation.TEST_FIRST,
        cited_evidence_ids=list(cited),
        invalid_citations=list(invalid or []),
        dimension_scores={},
        most_dangerous_assumption="",
    )


def test_valid_citations_are_kept(sample_evidence):
    p = _make_perspective(PerspectiveName.MARKET_ANALYST, ["E001", "E002"])
    validate_citations([p], sample_evidence)
    assert "E001" in p.cited_evidence_ids
    assert "E002" in p.cited_evidence_ids


def test_invalid_citations_are_moved(sample_evidence):
    """Citations to nonexistent evidence IDs must be moved to invalid_citations."""
    p = _make_perspective(PerspectiveName.MARKET_ANALYST, ["E001", "E999", "FAKE"])
    validate_citations([p], sample_evidence)
    assert "E001" in p.cited_evidence_ids
    assert "E999" in p.invalid_citations
    assert "FAKE" in p.invalid_citations
    assert "E999" not in p.cited_evidence_ids


def test_empty_evidence_makes_all_invalid(sample_evidence):
    p = _make_perspective(PerspectiveName.SKEPTICAL_INVESTOR, ["E001", "E002", "E003"])
    validate_citations([p], [])
    assert p.cited_evidence_ids == []
    assert set(p.invalid_citations) == {"E001", "E002", "E003"}


def test_no_citations_stays_empty(sample_evidence):
    p = _make_perspective(PerspectiveName.PRACTICAL_BUILDER, [])
    validate_citations([p], sample_evidence)
    assert p.cited_evidence_ids == []
    assert p.invalid_citations == []
