"""Evidence gates for final product recommendations."""

from copy import deepcopy

from assumption_zero.analysis.engine import _select_recommendation
from assumption_zero.schemas import (
    Competitor,
    CompetitorType,
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    Recommendation,
    RegionalMarketAnalysis,
)


def _region(confidence: ConfidenceLevel) -> RegionalMarketAnalysis:
    return RegionalMarketAnalysis(
        geography="United States",
        demand_score=70,
        confidence=confidence,
        evidence_count=4,
        source_count=3,
        summary="Regional demand is supported by multiple independent sources.",
    )


def _verified_competitor() -> Competitor:
    return Competitor(
        name="VerifiedCo",
        url="https://verified.example",
        competitor_type=CompetitorType.DIRECT,
        description="A verified competing product.",
        target_user="Small teams",
        evidence_ids=["E002"],
        confidence=ConfidenceLevel.MEDIUM,
    )


def _second_demand_source(item: EvidenceItem) -> EvidenceItem:
    second = item.model_copy(deep=True)
    second.evidence_id = "E010"
    second.url = "https://independent.example/demand"
    second.source_name = "Independent Survey"
    second.evidence_origin = "Independent Survey"
    second.evidence_type = EvidenceType.DEMAND
    second.relevance_score = 0.85
    return second


def test_build_is_downgraded_when_regional_evidence_is_weak(sample_perspectives, sample_evidence):
    perspectives = deepcopy(sample_perspectives)
    for perspective in perspectives:
        perspective.recommendation = Recommendation.BUILD
    evidence = sample_evidence + [_second_demand_source(sample_evidence[0])]

    result = _select_recommendation(
        perspectives,
        ConfidenceLevel.HIGH,
        evidence,
        [_verified_competitor()],
        _region(ConfidenceLevel.LOW),
    )

    assert result == Recommendation.TEST_FIRST


def test_build_requires_and_accepts_complete_independent_support(
    sample_perspectives, sample_evidence
):
    perspectives = deepcopy(sample_perspectives)
    for perspective in perspectives:
        perspective.recommendation = Recommendation.BUILD
    evidence = sample_evidence + [_second_demand_source(sample_evidence[0])]

    result = _select_recommendation(
        perspectives,
        ConfidenceLevel.HIGH,
        evidence,
        [_verified_competitor()],
        _region(ConfidenceLevel.MEDIUM),
    )

    assert result == Recommendation.BUILD


def test_tied_perspectives_default_to_test_first(sample_perspectives, sample_evidence):
    perspectives = deepcopy(sample_perspectives[:2])
    perspectives[0].recommendation = Recommendation.BUILD
    perspectives[1].recommendation = Recommendation.PIVOT

    result = _select_recommendation(
        perspectives,
        ConfidenceLevel.HIGH,
        sample_evidence,
        [_verified_competitor()],
        _region(ConfidenceLevel.HIGH),
    )

    assert result == Recommendation.TEST_FIRST
