"""Shared fixtures for all tests."""
from __future__ import annotations

import pytest
from datetime import date, datetime

from assumption_zero.schemas import (
    AnalysisPerspective,
    CompetitorType,
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    PerspectiveName,
    Recommendation,
    ReliabilityLevel,
)


@pytest.fixture
def sample_idea() -> IdeaInput:
    return IdeaInput(
        name="TestProduct",
        description="A test product for unit tests",
        problem="Test users struggle with testing things manually",
        target_customer="QA engineers at small software companies",
        geography="United States",
        business_model="SaaS",
        price="$29/month",
        founder_skills="Software developer",
        budget="$10,000",
        known_competitors="Manual testing",
    )


@pytest.fixture
def sample_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_id="E001",
            title="Test Evidence Item 1",
            url="https://example.com/e1",
            source_name="GitHub",
            publication_date=date(2023, 6, 1),
            retrieval_date=date(2023, 10, 1),
            passage="Strong demand for test automation tools among small teams.",
            search_query="test automation tools",
            evidence_type=EvidenceType.DEMAND,
            reliability=ReliabilityLevel.HIGH,
            relevance_score=0.9,
            retrieval_timestamp=datetime(2023, 10, 1),
            is_demo=False,
        ),
        EvidenceItem(
            evidence_id="E002",
            title="Competitor Analysis",
            url="https://example.com/e2",
            source_name="Hacker News",
            publication_date=date(2023, 3, 15),
            retrieval_date=date(2023, 10, 1),
            passage="Existing solutions are too expensive for small companies.",
            search_query="test automation competitors",
            evidence_type=EvidenceType.COMPETITOR,
            reliability=ReliabilityLevel.MEDIUM,
            relevance_score=0.75,
            retrieval_timestamp=datetime(2023, 10, 1),
            is_demo=False,
        ),
        EvidenceItem(
            evidence_id="E003",
            title="Regulatory Concern",
            url="https://example.com/e3",
            source_name="Wikipedia",
            publication_date=date(2022, 11, 1),
            retrieval_date=date(2023, 10, 1),
            passage="No specific regulations apply to this space.",
            search_query="test automation regulations",
            evidence_type=EvidenceType.REGULATORY,
            reliability=ReliabilityLevel.MEDIUM,
            relevance_score=0.5,
            retrieval_timestamp=datetime(2023, 10, 1),
            is_demo=False,
        ),
    ]


@pytest.fixture
def sample_perspectives(sample_evidence) -> list[AnalysisPerspective]:
    return [
        AnalysisPerspective(
            perspective_name=PerspectiveName.MARKET_ANALYST,
            perspective_display="Market Analyst",
            model_id="mock",
            summary="Good market opportunity based on evidence",
            key_findings=["Strong demand [E001]", "Affordable gap exists [E002]"],
            risks=["Competition from established players [E002]"],
            opportunities=["Underserved small teams"],
            recommendation=Recommendation.TEST_FIRST,
            cited_evidence_ids=["E001", "E002"],
            invalid_citations=[],
            dimension_scores={
                "problem_evidence": 70.0,
                "demand_signals": 65.0,
                "competitive_gap": 55.0,
                "distribution_feasibility": 50.0,
                "unit_economics": 60.0,
                "founder_fit": 55.0,
                "legal_operational_risk": 80.0,
            },
            most_dangerous_assumption="Customers will pay for automation",
        ),
        AnalysisPerspective(
            perspective_name=PerspectiveName.SKEPTICAL_INVESTOR,
            perspective_display="Skeptical Investor",
            model_id="mock",
            summary="Market is crowded, differentiation is unclear",
            key_findings=["Many existing solutions [E002]"],
            risks=["High switching costs", "Established players dominate"],
            opportunities=[],
            recommendation=Recommendation.PIVOT,
            cited_evidence_ids=["E002"],
            invalid_citations=[],
            dimension_scores={
                "problem_evidence": 50.0,
                "demand_signals": 45.0,
                "competitive_gap": 30.0,
                "distribution_feasibility": 35.0,
                "unit_economics": 40.0,
                "founder_fit": 45.0,
                "legal_operational_risk": 70.0,
            },
            most_dangerous_assumption="We can beat established players on price",
        ),
        AnalysisPerspective(
            perspective_name=PerspectiveName.PRACTICAL_BUILDER,
            perspective_display="Practical Builder",
            model_id="mock",
            summary="Technically feasible with available budget",
            key_findings=["Existing open source components help [E001]"],
            risks=["Sales cycle unknown"],
            opportunities=["Can build MVP in 3 months"],
            recommendation=Recommendation.TEST_FIRST,
            cited_evidence_ids=["E001"],
            invalid_citations=[],
            dimension_scores={
                "problem_evidence": 65.0,
                "demand_signals": 60.0,
                "competitive_gap": 50.0,
                "distribution_feasibility": 55.0,
                "unit_economics": 65.0,
                "founder_fit": 70.0,
                "legal_operational_risk": 75.0,
            },
            most_dangerous_assumption="Small team will buy without enterprise features",
        ),
    ]
