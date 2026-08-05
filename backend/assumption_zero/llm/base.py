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
        "You are a rigorous Market Analyst evaluating startup ideas. You MUST structure your analysis into 3 DISTINCT SUB-SECTIONS:\n"
        "1. [MARKET SIZING & TAM/SAM/SOM]: Provide explicit volume formulas, addressable users, and regional market size.\n"
        "2. [DEMAND & CUSTOMER PAIN]: Evaluate problem severity, search query signals, and customer willingness to switch.\n"
        "3. [MONETIZATION & PRICING POWER]: Analyze premium listing boosts, VIP badges, store subscriptions, and ad revenue."
    ),
    PerspectiveName.SKEPTICAL_INVESTOR: (
        "You are a Skeptical VC Partner identifying fatal flaws. You MUST structure your analysis into 3 DISTINCT SUB-SECTIONS:\n"
        "1. [COMPETITIVE MOAT & SWITCHING COSTS]: Challenge defensibility vs entrenched leaders and user lock-in barriers.\n"
        "2. [UNIT ECONOMICS & CAC/LTV]: Evaluate customer acquisition costs across paid channels vs lifetime value payback limits.\n"
        "3. [LIQUIDITY & FATAL RISKS]: Analyze two-sided marketplace cold start, seller churn, and failure modes."
    ),
    PerspectiveName.PRACTICAL_BUILDER: (
        "You are a Practical Product Builder designing execution strategy. You MUST structure your analysis into 3 DISTINCT SUB-SECTIONS:\n"
        "1. [90-DAY GTM ROADMAP]: Define Month 1 launch scope, Month 2 seller seeding, and Month 3 VIP boost rollout.\n"
        "2. [TECH ARCHITECTURE & INFRA]: Assess Vercel/Railway frontend/backend, Cloudflare R2 storage, and AI API costs.\n"
        "3. [TRUST, SAFETY & COMPLIANCE]: Outline phone OTP verification, seller rating system, safe chat, and legal compliance."
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

Analyze this idea from your assigned perspective using the evidence provided above and the user's detailed specification.
Evaluate the business model, pricing strategy, customer willingness to pay, unit economics (CAC vs LTV), TAM/SAM/SOM estimates, competitive moats, trust & safety rules, and 90-day launch roadmap thoroughly in key_findings, risks, and opportunities.

EXHAUSTIVE ANALYSIS REQUIREMENTS:
1. **Business Model & Unit Economics**: Evaluate monetization streams (premium listings, VIP badges, boost fees, store subscriptions, banner ads) and pricing power.
2. **TAM/SAM/SOM Calculation**: Provide explicit market size formulas, conservative vs optimistic scenarios in local currency (AZN/USD).
3. **Go-to-Market Strategy**: Provide 90-day launch milestones for acquiring the first 100, 1,000, 10,000, and 50,000 active users.
4. **Competitive Matrix**: Profile top competitors ({idea.known_competitors or 'Tap.az, Lalafo, Facebook Marketplace'}) with strengths, weaknesses, and defensible moats.
5. **Trust, Safety & Legal**: Outline identity verification, fraud detection, and legal compliance considerations.

CRITICAL CITATION & FACTUAL RULES:
1. Only cite evidence IDs from the list above (e.g. [E001]). Never cite IDs not in the list.
2. Base every factual claim on a cited evidence ID or user prompt specification.
3. If evidence is missing for a specific market statistic, state "Requires customer discovery validation".

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
        Uses intelligent pattern extraction for name, geography, competitors, and problem.
        """
        import re

        text = raw_text.strip()

        # 1. Extract Name (look for **Name**, "Name", 'Name', or keywords after 'for', 'called', 'named')
        name = ""
        bold_matches = re.findall(r"\*\*([^*]{2,35})\*\*", text)
        if bold_matches:
            for bm in bold_matches:
                if not bm.lower().startswith(("product", "core", "business", "current", "required", "competit", "summary")):
                    name = bm.strip()
                    break

        if not name:
            for_matches = re.findall(r"(?:for|called|named|app|platform|service|project)\s+([A-Z0-9\u0400-\u04FF\u0100-\u017F][A-Za-z0-9\.\-\_\u0400-\u04FF\u0100-\u017F]{2,25})", text, re.IGNORECASE)
            if for_matches:
                name = for_matches[0].strip()

        if not name:
            clean_first = re.sub(r"^(act as a|create a|analyze|please analyze|i want to build|build a|design a)\s+.*?\s+(?:for|on|about)\s+", "", text.splitlines()[0], flags=re.IGNORECASE)
            clean_words = clean_first.strip("#* ").split()
            name = " ".join(clean_words[:3]) if clean_words else "New Idea"

        # 2. Extract Geography
        geography = "global"
        geo_keywords = ["Azerbaijan", "Azerbaijani", "United States", "US", "UK", "Europe", "Turkey", "Germany", "India", "Canada"]
        for g in geo_keywords:
            if g.lower() in text.lower():
                geography = "Azerbaijan" if g.lower() in ("azerbaijan", "azerbaijani") else g
                break

        # 3. Extract Competitors mentioned in text
        comps_found = []
        for comp_name in ["Tap.az", "Lalafo", "Turbo.az", "Bina.az", "Facebook Marketplace", "Instagram", "Otter.ai", "Fireflies.ai", "Stylebook", "Whering"]:
            if comp_name.lower() in text.lower():
                comps_found.append(comp_name)

        known_competitors = ", ".join(comps_found) if comps_found else None

        # 4. Extract Description & Problem
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.strip().startswith(("#", "Act as", "Create a"))]
        desc = paragraphs[0][:300] if paragraphs else text[:300]
        prob = paragraphs[1][:400] if len(paragraphs) > 1 else desc

        return IdeaInput(
            name=name[:60],
            description=desc,
            problem=prob,
            target_customer=f"Users and buyers in {geography}",
            geography=geography,
            known_competitors=known_competitors,
            additional_context=text[:3000],
        )
