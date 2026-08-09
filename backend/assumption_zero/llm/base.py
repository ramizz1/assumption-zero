"""
Abstract base class and shared data types for all LLM adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from pydantic import BaseModel, Field, field_validator

from assumption_zero.schemas import (
    EvidenceItem,
    IdeaInput,
    CompetitorType,
    PerspectiveName,
    Recommendation,
)


class DiscoveredCompetitor(BaseModel):
    """A compact, evidence-grounded competitor proposed by an AI perspective."""

    name: str = Field(min_length=2, max_length=80)
    competitor_type: CompetitorType = CompetitorType.DIRECT
    description: str = Field(default="", max_length=500)
    target_user: str = Field(default="", max_length=200)
    pricing_evidence: str | None = Field(default=None, max_length=300)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    complaints: List[str] = Field(default_factory=list)
    differentiation: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)

    @field_validator("competitor_type", mode="before")
    @classmethod
    def normalize_competitor_type(cls, value: object) -> CompetitorType:
        normalized = str(value or "direct").casefold().strip()
        if normalized in {"indirect", "substitute", "alternative", "open_source", "oss", "manual", "status_quo"}:
            return CompetitorType.INDIRECT
        return CompetitorType.DIRECT


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
    competitors: List[DiscoveredCompetitor] = Field(default_factory=list)

    @field_validator("competitors", mode="before")
    @classmethod
    def discard_malformed_competitors(cls, value: object) -> List[DiscoveredCompetitor]:
        """One malformed AI candidate must not invalidate the full perspective."""
        if not isinstance(value, list):
            return []
        valid: List[DiscoveredCompetitor] = []
        for item in value[:20]:
            try:
                valid.append(DiscoveredCompetitor.model_validate(item))
            except (TypeError, ValueError):
                continue
        return valid


# System prompt templates injected before each perspective prompt
PERSPECTIVE_SYSTEM_PROMPTS: Dict[str, str] = {
    PerspectiveName.MARKET_ANALYST: (
        "You are a rigorous Market Analyst evaluating startup ideas. You MUST structure your analysis into 3 DISTINCT SUB-SECTIONS:\n"
        "1. [MARKET SIZING & TAM/SAM/SOM]: Provide explicit addressable market size formulas (TAM/SAM/SOM), key demographics, and regional volume estimates.\n"
        "2. [DEMAND & CUSTOMER PAIN]: Evaluate problem severity, customer pain intensity, search demand signals, and switching willingness from current solutions.\n"
        "3. [MONETIZATION & PRICING POWER]: Analyze business model viability, pricing strategy, revenue streams, and customer willingness to pay."
    ),
    PerspectiveName.SKEPTICAL_INVESTOR: (
        "You are a Skeptical VC Partner stress-testing startup ideas. You MUST structure your analysis into 3 DISTINCT SUB-SECTIONS:\n"
        "1. [COMPETITIVE MOAT & SWITCHING COSTS]: Challenge defensibility vs entrenched competitors, user lock-in barriers, and what stops copying.\n"
        "2. [UNIT ECONOMICS & CAC/LTV]: Scrutinize customer acquisition costs, lifetime value, payback periods, and margin sustainability.\n"
        "3. [FATAL RISKS & FAILURE MODES]: Identify the top 3 ways this startup fails — distribution, timing, regulation, or technology risks."
    ),
    PerspectiveName.PRACTICAL_BUILDER: (
        "You are an ultra-pragmatic Technical Product Architect. Your mandate is EXTREME MVP MINIMALISM & RIGOROUS VALIDATION.\n"
        "You MUST structure your analysis into 3 DISTINCT SUB-SECTIONS:\n"
        "1. [SCOPE NARROWING & CORE MVP HYPOTHESIS]: Strip 80% of proposed features to define the single narrowest testable MVP hypothesis that can be validated in under 7 days without building full web infrastructure.\n"
        "2. [7-DAY & 30-DAY EXECUTION ROADMAP]: Define concrete, lightweight deliverables for Week 1 (Zero-Code Concierge / Smoke Test) and Month 1 (Manual Delivery to 3 Paid Users). DO NOT output ASCII markdown tables — use clean bullet points.\n"
        "3. [PIVOT, NARROW, OR ABANDON KILL-CRITERIA]: Define exact numerical decision thresholds that instruct the founder whether to BUILD, PIVOT, NARROW SCOPE, or ABANDON the idea immediately."
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
    """Build the user-facing analysis prompt with evidence injected (compacted for fast, low-token inference)."""
    # Do not let general market results crowd competitor evidence out of the
    # model context. Keep a balanced, deterministic evidence selection.
    priority_types = {"competitor", "oss_alternative", "pricing", "complaint"}
    priority = [e for e in evidence if e.evidence_type.value in priority_types]
    compact_evidence = priority[:24]
    selected_ids = {e.evidence_id for e in compact_evidence}
    compact_evidence.extend(
        e for e in evidence
        if e.evidence_id not in selected_ids
    )
    compact_evidence = compact_evidence[:40]
    evidence_block = "\n".join(
        f"[{e.evidence_id}] {e.title[:90]}\n"
        f"  Source: {e.source_name} | Type: {e.evidence_type.value}\n"
        f"  Passage: {e.passage[:220]}\n"
        for e in compact_evidence
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
Evaluate the business model, pricing strategy, customer willingness to pay, unit economics (CAC vs LTV), TAM/SAM/SOM estimates, competitive moats, and 90-day launch roadmap thoroughly in key_findings, risks, and opportunities.

EXHAUSTIVE ANALYSIS REQUIREMENTS:
1. **Business Model & Unit Economics**: Evaluate monetization streams specific to this product type, pricing tiers, and long-term margin structure.
2. **TAM/SAM/SOM Calculation**: Provide explicit market size formulas for this specific problem domain and geography.
3. **Go-to-Market Strategy**: Provide 90-day launch milestones for acquiring the first 100, 1,000, and 10,000 target customers.
4. **Competitive Matrix**: Profile top competitors ({idea.known_competitors or 'existing alternatives in this space'}) with strengths, weaknesses, and defensible moats.
5. **Trust, Safety & Legal**: Outline data security, identity verification, and legal compliance considerations specific to this product.

COMPETITOR DISCOVERY REQUIREMENTS:
1. Identify direct products, indirect substitutes, open-source alternatives, and the status-quo/manual workflow when the evidence names them.
2. Add a competitor only when at least one cited evidence item explicitly names that product or service. Never invent a company, URL, feature, price, or market share.
3. Every competitor must include its supporting `evidence_ids`. Omit unsupported known competitors instead of treating user input as independent proof.
4. Use `direct` when it solves substantially the same job for the same buyer; use `indirect` for substitutes, open-source tools, platforms, or manual workflows.
5. For unknown attributes use an empty string/list. Potential differentiation must be labelled as a hypothesis unless directly supported by evidence.

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
  "competitors": [
    {{
      "name": "Evidence-backed product name",
      "competitor_type": "direct | indirect",
      "description": "What it does, grounded in the cited evidence",
      "target_user": "Evidence-backed target user or empty string",
      "pricing_evidence": "Evidence-backed price or null",
      "strengths": ["Evidence-backed strength"],
      "weaknesses": ["Evidence-backed weakness"],
      "complaints": ["Evidence-backed complaint"],
      "differentiation": ["Hypothesis: a testable gap the startup could validate"],
      "evidence_ids": ["E001"]
    }}
  ],
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
        from assumption_zero.schemas import is_gibberish

        text = raw_text.strip()
        if is_gibberish(text):
            raise ValueError(
                "The input text appears to be random characters or gibberish. Please enter a valid product or business idea."
            )

        # 1. Extract Name (look for **Name**, "Name", 'Name', or keywords after 'called', 'named', 'project')
        name = ""
        bold_matches = re.findall(r"\*\*([^*]{3,35})\*\*", text)
        if bold_matches:
            for bm in bold_matches:
                if not bm.lower().startswith(("product", "core", "business", "current", "required", "competit", "summary")):
                    if len(bm.strip()) >= 4:
                        name = bm.strip()
                        break

        if not name or len(name) < 4:
            called_matches = re.findall(r"(?:called|named|project|app|product|service)\s+([A-Z0-9\u0400-\u04FF\u0100-\u017F][A-Za-z0-9\.\-\_\u0400-\u04FF\u0100-\u017F]{3,25})", text, re.IGNORECASE)
            if called_matches:
                name = called_matches[0].strip()

        if not name or len(name) < 4:
            clean_words = text.splitlines()[0].strip("#* ").split()
            valid_words = [w for w in clean_words if not w.lower().startswith(("act", "create", "analyze", "please", "i", "want", "build"))]
            name = " ".join(valid_words[:4]).strip() if valid_words else "New Startup Idea"
            if len(name) < 4:
                name = "New Startup Idea"

        # 2. Extract Geography
        geography = "global"
        geo_map = {
            "azerbaijan": "Azerbaijan", "azerbaijani": "Azerbaijan",
            "united states": "United States", "usa": "United States", " us ": "United States",
            "united kingdom": "United Kingdom", " uk ": "United Kingdom",
            "europe": "Europe", "turkey": "Turkey", "germany": "Germany",
            "india": "India", "canada": "Canada", "australia": "Australia",
            "nigeria": "Nigeria", "brazil": "Brazil", "france": "France",
        }
        text_lower = text.lower()
        for kw, geo in geo_map.items():
            if kw in text_lower:
                geography = geo
                break

        # 3. Extract Competitors — scan text for quoted or named tools
        comps_found = []
        # Known competitor names to auto-detect
        known_comp_list = [
            "Tap.az", "Lalafo", "Turbo.az", "Bina.az",
            "Facebook Marketplace", "Instagram", "Otter.ai", "Fireflies.ai",
            "Stylebook", "Whering", "Grammarly", "Notion", "Slack", "Jira",
            "Qualys", "Tenable", "Rapid7", "Snyk", "SonarQube", "Checkmarx",
            "GitHub", "GitLab", "Vercel", "Stripe", "Twilio", "Zapier",
        ]
        for comp_name in known_comp_list:
            if comp_name.lower() in text_lower:
                comps_found.append(comp_name)
        # Also detect quoted names in "competitors: X, Y, Z" pattern
        comp_patterns = re.findall(r"(?:competitors?|alternatives?|competing with|vs\.?)\s*[:\-]?\s*([A-Z][\w\.]+(?:,\s*[A-Z][\w\.]+)*)", text, re.IGNORECASE)
        for cp in comp_patterns:
            for c in cp.split(","):
                c = c.strip()
                if c and c not in comps_found:
                    comps_found.append(c)

        known_competitors = ", ".join(comps_found[:8]) if comps_found else None

        # 4. Extract target customer from text
        cust_match = re.search(
            r"(?:target customer|target user|audience|for|serving|used by)[:\s]+([^.\n]{5,80})",
            text, re.IGNORECASE
        )
        if cust_match:
            target_customer = cust_match.group(1).strip().rstrip(",;")
        else:
            # Infer from product description
            target_customer = f"{name} target users"

        # 5. Extract Description & Problem
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.strip().startswith(("#", "Act as", "Create a"))]
        desc = paragraphs[0][:300] if paragraphs else text[:300]
        prob = paragraphs[1][:400] if len(paragraphs) > 1 else desc

        return IdeaInput(
            name=name[:60],
            description=desc,
            problem=prob,
            target_customer=target_customer[:120],
            geography=geography,
            known_competitors=known_competitors,
            additional_context=text[:3000],
        )
