import json
import logging
from typing import List

from pydantic import BaseModel, Field

from assumption_zero.llm.base import LLMAdapter
from assumption_zero.schemas import AnalysisPerspective, IdeaInput

logger = logging.getLogger(__name__)

class HermesSynthesisOutput(BaseModel):
    opportunity_score: float = Field(ge=0.0, le=100.0)
    recommendation: str
    most_dangerous_assumption: str

async def run_hermes_synthesis(
    llm_adapter: LLMAdapter,
    idea: IdeaInput,
    perspectives: List[AnalysisPerspective]
) -> HermesSynthesisOutput:
    """
    Acts as the Assumption Zero Master Brain.
    Takes the outputs of the 3 sub-agents and synthesizes them into a final score,
    recommendation, and most dangerous assumption.
    """
    perspectives_text = ""
    for p in perspectives:
        perspectives_text += f"\n--- {p.perspective_display} ---\n"
        perspectives_text += f"Summary: {p.summary}\n"
        perspectives_text += f"Recommendation: {p.recommendation}\n"
        perspectives_text += f"Most Dangerous Assumption: {p.most_dangerous_assumption}\n"
        perspectives_text += "Dimension Scores:\n"
        for dim, score in p.dimension_scores.items():
            perspectives_text += f"  - {dim}: {score}\n"
        perspectives_text += "Risks:\n"
        for r in p.risks:
            perspectives_text += f"  - {r}\n"
        perspectives_text += "Opportunities:\n"
        for o in p.opportunities:
            perspectives_text += f"  - {o}\n"

    system_prompt = (
        "You are the Assumption Zero Master Brain, the final orchestrator of a multi-agent startup analysis engine. "
        "Your job is to read the reports of your 3 sub-agents (Market Analyst, Skeptical Investor, Practical Builder) "
        "and synthesize their findings into a definitive final conclusion."
    )
    
    user_prompt = f"""
## The Startup Idea
**Name:** {idea.name}
**Problem:** {idea.problem}
**Target Customer:** {idea.target_customer}
**Geography:** {idea.geography}

## Sub-Agent Reports
{perspectives_text}

## Your Task
Synthesize these perspectives. Determine the final "opportunity_score" (0-100) based on a holistic review of all their scores. 
Determine the final "recommendation" (must be exactly one of: "Build", "Test First", "Pivot", "Avoid").
Determine the single "most_dangerous_assumption" across all reports.

Respond with EXACTLY this JSON format and nothing else:
{{
  "opportunity_score": 75.0,
  "recommendation": "Test First",
  "most_dangerous_assumption": "The target customers are not willing to pay for this solution."
}}
"""
    
    # We use the raw API call of the adapter
    try:
        raw_response = await llm_adapter._call_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )
        data = json.loads(raw_response)
        
        return HermesSynthesisOutput(
            opportunity_score=float(data.get("opportunity_score", 50.0)),
            recommendation=str(data.get("recommendation", "Test First")),
            most_dangerous_assumption=str(data.get("most_dangerous_assumption", "Validation required."))
        )
    except Exception as e:
        logger.error(f"Assumption Zero Brain synthesis failed: {e}")
        # Fallback to defaults
        return HermesSynthesisOutput(
            opportunity_score=50.0,
            recommendation="Test First",
            most_dangerous_assumption="Failed to synthesize assumptions."
        )
