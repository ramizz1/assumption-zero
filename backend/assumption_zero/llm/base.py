"""
Abstract base class and shared data types for all LLM adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from pydantic import BaseModel

from assumption_zero.schemas import (
    EvidenceItem,
    IdeaInput,
    PerspectiveName,
    Recommendation,
)


class PerspectiveOutput(BaseModel):
    """Structured output from one AI perspective run."""

    perspective_name: PerspectiveName
    model_id: str
    summary: str
    key_findings: List[str]
    risks: List[str]
    opportunities: List[str]
    recommendation: Recommendation
    dimension_scores: Dict[str, float]  # dimension key -> raw score 0-100
    cited_evidence_ids: List[str]
    most_dangerous_assumption: str
    reasoning: str  # Chain-of-thought; not shown to end-users by default


# System prompt templates injected before each perspective prompt
PERSPECTIVE_SYSTEM_PROMPTS: Dict[str, str] = {
    PerspectiveName.MARKET_ANALYST: (
        "You are a rigorous Market Analyst and Venture Strategist evaluating startup ideas based solely on "
        "the provided evidence. Your job: assess market demand, willingness to pay, pricing power, monetization feasibility, "
        "TAM/SAM, market timing, customer acquisition dynamics, and business model sustainability. "
        "Pay special attention to unit economics, paywall placement, freemium conversion potential, and revenue expansion opportunities. "
        "Do NOT invent information. If evidence is missing, say so explicitly."
    ),
    PerspectiveName.SKEPTICAL_INVESTOR: (
        "You are a Skeptical VC Partner whose job is to DISPROVE the startup idea and find fatal business model flaws. "
        "Examine unit economics, CAC vs LTV ratios, price sensitivity, customer churn risks, margin compression, "
        "competitive moats, switching costs, and distribution bottlenecks. "
        "Challenge every monetization assumption. Only acknowledge strengths if the evidence is compelling. Do NOT invent information."
    ),
    PerspectiveName.PRACTICAL_BUILDER: (
        "You are a Practical Product Builder evaluating MVP build costs and monetization execution. "
        "Assess infrastructure overhead per user, cost-to-serve, technical complexity, paywall implementation feasibility, "
        "founder skills & budget alignment vs burn rate, and the leanest MVP that validates willingness-to-pay. "
        "Do NOT invent information."
    ),
}

DIMENSION_KEYS = [
    "problem_evidence",
    "demand_signals",
    "competitive_gap",
    "distribution_feasibility",
    "unit_economics",
    "founder_fit",
    "legal_operational_risk",
]


def build_analysis_prompt(
    perspective_name: str,
    idea: IdeaInput,
    evidence: List[EvidenceItem],
) -> str:
    """Build the user-facing analysis prompt with evidence injected."""
    evidence_block = "\n".join(
        f"[{e.evidence_id}] {e.title}\n"
        f"  Source: {e.source_name} | Type: {e.evidence_type.value} | "
        f"Reliability: {e.reliability.value}\n"
        f"  Passage: {e.passage}\n"
        f"  URL: {e.url}\n"
        for e in evidence
    )

    return f"""
## Idea Under Analysis

**Name:** {idea.name}
**Description:** {idea.description}
**Problem:** {idea.problem}
**Target Customer:** {idea.target_customer}
**Geography:** {idea.geography}
**Business Model:** {idea.business_model or 'Not specified'}
**Price:** {idea.price or 'Not specified'}
**Founder Skills:** {idea.founder_skills or 'Not specified'}
**Budget:** {idea.budget or 'Not specified'}
**Known Competitors:** {idea.known_competitors or 'Not specified'}
**Unfair Advantage / Moat:** {getattr(idea, 'unfair_advantage', None) or 'Not specified'}
**Core Unvalidated Assumptions:** {getattr(idea, 'key_assumptions', None) or 'Not specified'}
**Additional Context:** {idea.additional_context or 'None'}

## Collected Evidence

{evidence_block if evidence_block else 'No evidence collected. State "Insufficient evidence" for all claims.'}

## Your Task ({perspective_name.replace("_", " ").title()})

Analyze this idea from your assigned perspective using ONLY the evidence provided above.
Evaluate the business model, pricing strategy, customer willingness to pay, unit economics (CAC vs LTV), and monetization risks thoroughly in key_findings and risks.

CRITICAL RULES:
1. Only cite evidence IDs from the list above (e.g. [E001]). Never cite IDs not in the list.
2. If you lack evidence for a claim, write "Insufficient evidence" — never invent facts.
3. Evaluate the business model viability explicitly in your key findings & risks.
4. Base every factual claim on a cited evidence ID.

Respond with a JSON object matching EXACTLY this schema:
{{
  "summary": "3-4 sentence executive summary evaluating problem, business model, and competitive reality",
  "key_findings": ["finding 1 [E001]", "finding 2 [E002]"],
  "risks": ["risk 1", "risk 2"],
  "opportunities": ["opportunity 1", "opportunity 2"],
  "recommendation": "Build | Test First | Pivot | Avoid",
  "dimension_scores": {{
    "problem_evidence": 0-100,
    "demand_signals": 0-100,
    "competitive_gap": 0-100,
    "distribution_feasibility": 0-100,
    "unit_economics": 0-100,
    "founder_fit": 0-100,
    "legal_operational_risk": 0-100
  }},
  "cited_evidence_ids": ["E001", "E002"],
  "most_dangerous_assumption": "The single most dangerous unvalidated assumption",
  "reasoning": "Step-by-step reasoning that led to your scores"
}}
"""


class LLMAdapter(ABC):
    """Base class for all LLM provider adapters."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Human-readable model identifier, e.g. 'gemini-1.5-flash'."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the adapter is configured and ready."""
        ...

    @abstractmethod
    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        """
        Run a single perspective analysis and return structured output.

        If the model returns invalid JSON, attempt one repair.
        If repair fails, raise an exception — the engine handles fallback.
        """
        ...

    async def clarify_idea(self, idea: IdeaInput) -> str:
        """
        Return a brief structured interpretation of the idea (1-2 paragraphs).
        Adapters may override for better formatting; default returns a formatted string.
        """
        return (
            f"Analyzing: {idea.name}\n"
            f"Problem: {idea.problem}\n"
            f"Customer: {idea.target_customer} in {idea.geography}\n"
            f"Model: {idea.business_model or 'Not specified'}"
        )

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        """
        Parse a single natural language text prompt into a structured IdeaInput.
        """
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        first_line = lines[0] if lines else raw_text[:50]
        words = first_line.split()
        name = " ".join(words[:4]) if words else "New Idea"

        return IdeaInput(
            name=name[:100],
            description=raw_text[:300],
            problem=raw_text[:500],
            target_customer="Target users & buyers",
            geography="global",
            additional_context=raw_text,
        )
