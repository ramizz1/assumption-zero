import pytest
from datetime import date, datetime

from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.schemas import (
    IdeaInput, AnalysisStage, AnalysisStatus, Recommendation,
    EvidenceItem, EvidenceType, ReliabilityLevel,
)
from assumption_zero.llm.base import DiscoveredCompetitor, LLMAdapter, PerspectiveOutput
from assumption_zero.research.base import ResearchProvider

class MockAdapter(LLMAdapter):
    @property
    def name(self) -> str:
        return "mock"
        
    @property
    def is_available(self) -> bool:
        return True
        
    @property
    def model_id(self) -> str:
        return "mock-model"
        
    async def analyze_perspective(self, perspective_name, idea, evidence):
        return PerspectiveOutput(
            perspective_name=perspective_name,
            reasoning="mock reasoning",
            model_id="mock-1.0",
            summary="mock summary",
            key_findings=["finding 1"],
            risks=["risk 1"],
            opportunities=["opp 1"],
            recommendation=Recommendation.TEST_FIRST,
            cited_evidence_ids=[],
            dimension_scores={
                "urgency": 5, "willingness_to_pay": 5, "market_size": 5,
                "competition": 5, "moat": 5, "technical_feasibility": 5, "founder_fit": 5
            },
            most_dangerous_assumption="mock assumption"
        )
        
    async def _call_api(self, system_prompt, user_prompt, temperature):
        return "{}"

class MockProvider(ResearchProvider):
    @property
    def name(self) -> str:
        return "mock_provider"
        
    @property
    def is_available(self) -> bool:
        return True
        
    async def search(self, query, query_type, idea, max_results):
        return []


class CompetitorProvider(MockProvider):
    async def search(self, query, query_type, idea, max_results):
        if query_type != "competitor":
            return []
        return [
            EvidenceItem(
                evidence_id="provider-id",
                title="Otter.ai meeting assistant",
                url="https://otter.ai/product",
                evidence_origin="Test research",
                source_name="Test research",
                retrieval_date=date.today(),
                passage="Otter.ai provides automated meeting transcription and summaries.",
                search_query=query,
                evidence_type=EvidenceType.COMPETITOR,
                reliability=ReliabilityLevel.MEDIUM,
                relevance_score=0.9,
                retrieval_timestamp=datetime.utcnow(),
            )
        ]


class CompetitorAIAdapter(MockAdapter):
    async def analyze_perspective(self, perspective_name, idea, evidence):
        output = await super().analyze_perspective(perspective_name, idea, evidence)
        output.competitors = [
            DiscoveredCompetitor(
                name="Otter.ai",
                description="Automated meeting transcription and summaries.",
                competitor_type="direct",
                differentiation=["Legal review and compliance workflow"],
                evidence_ids=["E001"],
            )
        ]
        return output

@pytest.mark.asyncio
async def test_engine_end_to_end():
    idea = IdeaInput(
        name="Valid Startup Idea Name",
        description="A comprehensive description of a valid startup idea.",
        problem="This is a detailed problem statement.",
        target_customer="Target customers in the enterprise sector.",
        geography="United States"
    )
    
    engine = AnalysisEngine(
        providers=[MockProvider()],
        llm_adapter=MockAdapter()
    )
    
    stages_hit = []
    async def progress_cb(stage, desc):
        stages_hit.append(stage)
        
    result = await engine.run(idea, "test-id", progress_callback=progress_cb)
    
    assert result.status == AnalysisStatus.COMPLETE
    assert result.stage == AnalysisStage.COMPLETE
    
    # Prove it returns an OpportunityScore
    assert hasattr(result, "opportunity_score")
    
    # Prove it has 7 dimensions
    dimensions = result.opportunity_score.dimensions
    assert len(dimensions) == 7
    
    # Contains experiments
    assert hasattr(result, "experiments")
    assert isinstance(result.experiments, list)

    # Contains an actionable founder operating plan
    assert result.founder_toolkit is not None
    assert len(result.founder_toolkit.roadmap) == 4
    assert result.founder_toolkit.decision_rules
    
    # Serializes successfully
    serialized = result.model_dump(mode="json")
    assert isinstance(serialized, dict)
    assert serialized["status"] == "complete"


@pytest.mark.asyncio
async def test_ai_competitor_survives_grounded_end_to_end_pipeline():
    idea = IdeaInput(
        name="Legal Meeting Briefs",
        description="Meeting transcription and summaries for legal teams.",
        problem="Small law firms lose time preparing meeting notes.",
        target_customer="Small law firms",
        geography="United States",
    )
    engine = AnalysisEngine(
        providers=[CompetitorProvider()],
        llm_adapter=CompetitorAIAdapter(),
    )

    result = await engine.run(idea, "competitor-test")

    assert len(result.competitors) == 1
    competitor = result.competitors[0]
    assert competitor.name == "Otter.ai"
    assert competitor.url == "https://otter.ai/product"
    assert competitor.evidence_ids == ["E001"]
    assert competitor.differentiation == [
        "Hypothesis: Legal review and compliance workflow"
    ]
    assert result.model_dump(mode="json")["competitors"][0]["confidence"] == "medium"
