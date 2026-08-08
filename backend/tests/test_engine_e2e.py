import pytest
from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.schemas import IdeaInput, AnalysisStage, AnalysisStatus, Recommendation
from assumption_zero.llm.base import LLMAdapter, PerspectiveOutput
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
    
    # Serializes successfully
    serialized = result.model_dump(mode="json")
    assert isinstance(serialized, dict)
    assert serialized["status"] == "complete"
