"""Coverage for deterministic regional analysis and research-depth controls."""
from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest

from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.analysis.query_generator import generate_queries
from assumption_zero.analysis.regional_analysis import generate_regional_analysis
from assumption_zero.llm.mock_adapter import MockAdapter
from assumption_zero.schemas import (
    AnalysisStatus,
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    ReliabilityLevel,
    ResearchDepth,
)


def _idea() -> IdeaInput:
    return IdeaInput(
        name="ClinicFlow",
        description="Appointment and follow-up software for independent dental clinics.",
        problem="Independent clinics lose patients because booking and follow-up are manual.",
        target_customer="Independent dental clinics",
        geography="Azerbaijan",
        market_language="Azerbaijani and Russian",
        currency="AZN",
        industry="Dental services",
        business_model="Monthly subscription",
        price="99 AZN per month",
    )


def _evidence(
    evidence_id: str,
    evidence_type: EvidenceType,
    title: str,
    source: str,
    query: str,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        title=title,
        url=f"https://example.com/{evidence_id}",
        evidence_origin=source,
        source_name=source,
        retrieval_date=datetime.now(UTC).date(),
        passage=f"Azerbaijan market evidence: {title}",
        search_query=query,
        evidence_type=evidence_type,
        reliability=ReliabilityLevel.HIGH,
        relevance_score=0.9,
        retrieval_timestamp=datetime.now(UTC),
    )


def test_regional_analysis_counts_only_market_specific_evidence():
    idea = _idea()
    items = [
        _evidence("E001", EvidenceType.DEMAND, "Clinic digitization survey", "Statistics agency", "dental Azerbaijan"),
        _evidence("E002", EvidenceType.PRICING, "Local clinic software prices", "Trade directory", "pricing Azerbaijan AZN"),
        _evidence("E003", EvidenceType.REGULATORY, "Patient data rules", "Health regulator", "health privacy Azerbaijan"),
        _evidence("E004", EvidenceType.DISTRIBUTION, "Dental association directory", "Dental association", "clinics Azerbaijan"),
        EvidenceItem(
            **{
                **_evidence("E005", EvidenceType.DEMAND, "US dental software demand", "US report", "dental software US").model_dump(),
                "passage": "United States clinics increased software purchases.",
            }
        ),
    ]

    result = generate_regional_analysis(idea, items)

    assert result.geography == "Azerbaijan"
    assert result.evidence_count == 4
    assert result.source_count == 4
    assert result.demand_score > 0
    assert [signal.evidence_id for signal in result.demand_signals] == ["E001"]
    assert result.pricing_signals[0].evidence_id == "E002"
    assert result.regulatory_signals[0].evidence_id == "E003"
    assert result.distribution_signals[0].evidence_id == "E004"
    assert all("E005" != signal.evidence_id for signal in result.demand_signals)


@pytest.mark.parametrize(
    ("depth", "queries_per_type", "perspective_count"),
    [
        (ResearchDepth.STANDARD, 1, 3),
        (ResearchDepth.DEEP, 2, 4),
        (ResearchDepth.EXHAUSTIVE, 4, 5),
    ],
)
@pytest.mark.asyncio
async def test_research_depth_controls_query_and_perspective_volume(
    depth: ResearchDepth,
    queries_per_type: int,
    perspective_count: int,
):
    engine = AnalysisEngine([], MockAdapter(), research_depth=depth)
    selected = engine._select_queries(generate_queries(_idea()))
    counts = Counter(item["type"] for item in selected)

    assert counts
    assert max(counts.values()) <= queries_per_type

    result = await engine.run(_idea(), f"depth-{depth.value}")
    assert result.status == AnalysisStatus.COMPLETE
    assert len(result.perspectives) == perspective_count
    assert result.research_coverage is not None
    assert result.research_coverage.depth == depth
    assert result.research_coverage.queries_executed == len(selected)


@pytest.mark.asyncio
async def test_no_key_parser_uses_only_user_supplied_competitors_and_region():
    parsed = await MockAdapter().parse_raw_prompt(
        """Name: ClinicFlow
Description: Appointment and follow-up software for independent dental clinics.
Problem: Clinics lose repeat patients because booking and follow-up are manual.
Target customer: Independent dental clinics
Geography: Azerbaijan
Market language: Azerbaijani and Russian
Currency: AZN
Competitors: DentSoft, Manual spreadsheets
Business model: Monthly subscription
Price: 99 AZN per month"""
    )

    assert parsed.name == "ClinicFlow"
    assert parsed.geography == "Azerbaijan"
    assert parsed.market_language == "Azerbaijani and Russian"
    assert parsed.currency == "AZN"
    assert parsed.known_competitors == "DentSoft, Manual spreadsheets"
    assert "Tap.az" not in parsed.model_dump_json()
