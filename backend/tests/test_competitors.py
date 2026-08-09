"""
Tests for the competitor merger.
"""
from __future__ import annotations

from datetime import date, datetime

from assumption_zero.analysis.engine import (
    _extract_competitors_from_evidence,
    _validated_ai_competitors,
)
from assumption_zero.analysis.competitor_merger import merge_competitors
from assumption_zero.llm.base import DiscoveredCompetitor
from assumption_zero.schemas import (
    Competitor,
    CompetitorType,
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    ReliabilityLevel,
)


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


def _idea(known_competitors=None) -> IdeaInput:
    return IdeaInput(
        name="Clear Meeting Notes",
        description="Meeting transcription and summaries for legal teams.",
        problem="Legal teams lose time creating accurate meeting notes.",
        target_customer="Small law firms",
        geography="United States",
        known_competitors=known_competitors,
    )


def _evidence(
    evidence_id: str,
    passage: str,
    *,
    source: str = "Web Search",
    evidence_type: EvidenceType = EvidenceType.COMPETITOR,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        title="Otter.ai meeting assistant",
        url="https://otter.ai/product",
        evidence_origin=source,
        source_name=source,
        retrieval_date=date.today(),
        passage=passage,
        search_query="meeting transcription competitors",
        evidence_type=evidence_type,
        reliability=ReliabilityLevel.MEDIUM,
        relevance_score=0.9,
        retrieval_timestamp=datetime.utcnow(),
    )


def test_ai_competitor_requires_real_supporting_citation():
    candidate = DiscoveredCompetitor(
        name="InventedCo",
        description="An invented competitor",
        evidence_ids=["E001"],
    )
    evidence = _evidence("E001", "Otter.ai provides meeting transcription.")
    evidence.search_query = "InventedCo competitors"
    accepted = _validated_ai_competitors(
        [candidate],
        [evidence],
        _idea(),
    )
    assert accepted == []


def test_ai_competitor_is_grounded_and_uses_evidence_url():
    candidate = DiscoveredCompetitor(
        name="Otter.ai",
        description="AI meeting transcription",
        pricing_evidence="$99 per month",
        differentiation=["Legal-specific review workflow"],
        evidence_ids=["E001"],
    )
    accepted = _validated_ai_competitors(
        [candidate],
        [_evidence("E001", "Otter.ai provides meeting transcription but this source has no price.")],
        _idea(),
    )
    assert len(accepted) == 1
    assert accepted[0].url == "https://otter.ai/product"
    assert accepted[0].evidence_ids == ["E001"]
    assert accepted[0].confidence == ConfidenceLevel.MEDIUM
    assert accepted[0].pricing_evidence is None
    assert accepted[0].differentiation[0].startswith("Hypothesis:")


def test_user_competitor_without_evidence_is_low_confidence_and_has_no_fake_url():
    competitors = _extract_competitors_from_evidence([], _idea("Otter.ai"))
    assert len(competitors) == 1
    assert competitors[0].confidence == ConfidenceLevel.LOW
    assert competitors[0].url == ""
    assert competitors[0].evidence_ids == []
    assert "not found" in competitors[0].description


def test_prefix_names_are_not_accidentally_merged():
    merged = merge_competitors([_comp("Acme"), _comp("Acme Analytics")])
    assert len(merged) == 2


def test_merge_promotes_better_supported_entry():
    low = _comp("Otter", evidence_ids=[])
    high = _comp("Otter.ai", evidence_ids=["E001", "E002"])
    high.confidence = ConfidenceLevel.HIGH
    high.url = "https://otter.ai"
    merged = merge_competitors([low, high])
    assert len(merged) == 1
    assert merged[0].confidence == ConfidenceLevel.HIGH
    assert merged[0].url == "https://otter.ai"
