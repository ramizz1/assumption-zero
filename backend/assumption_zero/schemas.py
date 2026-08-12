"""
Pydantic schemas shared across the API, CLI, and analysis engine.

These are the canonical data types for Assumption Zero. All analysis
components produce and consume these types.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceType(str, Enum):
    COMPETITOR = "competitor"
    DEMAND = "demand"
    COMPLAINT = "complaint"
    PRICING = "pricing"
    REGULATORY = "regulatory"
    MARKET_DIRECTION = "market_direction"
    DISTRIBUTION = "distribution"
    FAILED_PRODUCT = "failed_product"
    GEOGRAPHIC = "geographic"
    OSS_ALTERNATIVE = "oss_alternative"
    MANUAL_WORKFLOW = "manual_workflow"
    FAILURE_REASON = "failure_reason"
    GENERAL = "general"


class ReliabilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class ResearchDepth(str, Enum):
    STANDARD = "standard"
    DEEP = "deep"
    EXHAUSTIVE = "exhaustive"


class AnalysisStage(str, Enum):
    CLARIFYING_IDEA = "clarifying_idea"
    GENERATING_QUERIES = "generating_queries"
    COLLECTING_EVIDENCE = "collecting_evidence"
    FINDING_COMPETITORS = "finding_competitors"
    RUNNING_PERSPECTIVES = "running_perspectives"
    CHECKING_CITATIONS = "checking_citations"
    CALCULATING_SCORES = "calculating_scores"
    GENERATING_EXPERIMENTS = "generating_experiments"
    COMPLETE = "complete"


STAGE_DESCRIPTIONS: dict[str, str] = {
    AnalysisStage.CLARIFYING_IDEA: "Interpreting your idea and identifying key assumptions",
    AnalysisStage.GENERATING_QUERIES: "Generating targeted research queries",
    AnalysisStage.COLLECTING_EVIDENCE: "Collecting market evidence from research providers",
    AnalysisStage.FINDING_COMPETITORS: "Identifying and profiling competitors",
    AnalysisStage.RUNNING_PERSPECTIVES: "Running independent AI analysis perspectives",
    AnalysisStage.CHECKING_CITATIONS: "Validating evidence citations",
    AnalysisStage.CALCULATING_SCORES: "Calculating Opportunity Score and Evidence Confidence",
    AnalysisStage.GENERATING_EXPERIMENTS: "Generating validation experiments",
    AnalysisStage.COMPLETE: "Analysis complete",
}


class Recommendation(str, Enum):
    BUILD = "Build"
    TEST_FIRST = "Test First"
    PIVOT = "Pivot"
    AVOID = "Avoid"


class PerspectiveName(str, Enum):
    MARKET_ANALYST = "market_analyst"
    REGIONAL_STRATEGIST = "regional_strategist"
    SKEPTICAL_INVESTOR = "skeptical_investor"
    CUSTOMER_RESEARCHER = "customer_researcher"
    PRACTICAL_BUILDER = "practical_builder"


PERSPECTIVE_DISPLAY: dict[str, str] = {
    PerspectiveName.MARKET_ANALYST: "Market Analyst",
    PerspectiveName.REGIONAL_STRATEGIST: "Regional Market Strategist",
    PerspectiveName.SKEPTICAL_INVESTOR: "Skeptical Investor",
    PerspectiveName.CUSTOMER_RESEARCHER: "Customer Researcher",
    PerspectiveName.PRACTICAL_BUILDER: "Practical Builder",
}


class CompetitorType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"


# ─────────────────────────────────────────────────────────────────────────────
# Idea Input
# ─────────────────────────────────────────────────────────────────────────────


def is_gibberish(text: str) -> bool:
    """Check if text appears to be random keystrokes, gibberish, or generic non-ideas."""
    s = text.strip()
    if not s or len(s) < 4:
        return True

    lower = s.lower().strip("!?.#* \t\n")
    non_idea_words = {
        "idk",
        "unknown",
        "nothing",
        "test",
        "none",
        "n/a",
        "na",
        "no",
        "asdf",
        "foo",
        "bar",
        "qwerty",
        "whatever",
        "stuff",
        "thing",
        "something",
        "abc",
        "xyz",
        "123",
        "hello",
        "hi",
        "bye",
        "temp",
        "tmp",
        "demo",
        "sample",
    }
    if lower in non_idea_words:
        return True

    words = [w for w in re.split(r"\s+", s) if len(w) > 0]
    if len(words) == 1 and lower in non_idea_words:
        return True

    if len(words) <= 2 and len(s) < 12 and lower in non_idea_words:
        return True

    vowels = set("aeiouyAEIOUYаеëиоуыэюяАЕЁИОУЫЭЮЯəöğıüƏÖĞIÜ")

    if len(words) == 1 and len(s) >= 6:
        vowel_count = sum(1 for c in s if c in vowels)
        if vowel_count / len(s) < 0.12:
            return True

    if len(words) <= 2:
        for w in words:
            if len(w) >= 6:
                v_count = sum(1 for c in w if c in vowels)
                if v_count / len(w) < 0.12:
                    return True

    return False


class IdeaInput(BaseModel):
    """The user's startup or MVP idea. problem, target_customer, and geography are required."""

    name: str = Field(..., min_length=1, max_length=200, description="Product or idea name")
    description: str = Field(..., min_length=1, max_length=2000, description="Brief description")
    problem: str = Field(
        ..., min_length=5, max_length=2000, description="Required: What problem does this solve?"
    )
    target_customer: str = Field(
        ..., min_length=3, max_length=500, description="Required: Who is this for?"
    )
    geography: str = Field(
        ..., min_length=2, max_length=200, description="Required: Target market geography"
    )
    market_language: str | None = Field(
        None, max_length=100, description="Primary language used by target customers"
    )
    currency: str | None = Field(None, max_length=50, description="Currency used for local pricing")
    industry: str | None = Field(None, max_length=200, description="Industry or vertical")
    startup_stage: str | None = Field(
        None, max_length=100, description="Idea, validation, MVP, beta, or revenue stage"
    )
    solution: str | None = Field(
        None, max_length=1500, description="How the product solves the problem"
    )
    business_model: str | None = Field(None, max_length=500)
    price: str | None = Field(None, max_length=200, description="Expected price or pricing model")
    founder_skills: str | None = Field(None, max_length=1000)
    team: str | None = Field(None, max_length=500, description="Current team size and roles")
    budget: str | None = Field(None, max_length=200, description="Available runway or budget")
    launch_timeline: str | None = Field(
        None, max_length=200, description="Desired validation or launch timeline"
    )
    revenue_goal: str | None = Field(
        None, max_length=200, description="Initial revenue or customer goal"
    )
    acquisition_channels: str | None = Field(
        None, max_length=1000, description="Channels available for reaching early customers"
    )
    known_competitors: str | None = Field(None, max_length=500)
    unfair_advantage: str | None = Field(
        None, max_length=1000, description="Unique advantage, distribution channel, or IP"
    )
    key_assumptions: str | None = Field(
        None, max_length=1000, description="1-2 core assumptions that must be true for success"
    )
    regulatory_constraints: str | None = Field(
        None, max_length=1000, description="Legal, compliance, privacy, or operational constraints"
    )
    additional_context: str | None = Field(None, max_length=3000)

    @field_validator("name", "description", "problem")
    @classmethod
    def validate_not_gibberish(cls, v: str) -> str:
        if is_gibberish(v):
            raise ValueError(
                f"Invalid startup prompt '{v[:30]}': The input text appears to be random characters or gibberish. "
                "Please enter a clear product or business idea."
            )
        return v

    @classmethod
    def from_storage(cls, data: dict) -> IdeaInput:
        """Deserialize from persisted storage, bypassing the gibberish validator.
        Data was already validated at submission time — re-validating on read
        incorrectly rejects short/common-word names that were accepted when stored."""
        return cls.model_construct(**data)


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceItem(BaseModel):
    """A single piece of collected evidence. Every factual claim must cite an evidence ID."""

    evidence_id: str  # E001, E002, etc. — stable identifier
    title: str
    url: str  # Use demo:// URIs for fixture data; never fabricate real URLs
    evidence_origin: str = "Unknown"  # e.g. 'Reddit - r/startups' or 'GitHub - assumption-zero'
    source_name: str
    publication_date: date | None = None
    retrieval_date: date
    passage: str  # Short extracted passage, never paraphrased
    search_query: str
    evidence_type: EvidenceType
    reliability: ReliabilityLevel
    relevance_score: float = Field(ge=0.0, le=1.0)
    retrieval_timestamp: datetime
    is_demo: bool = False  # True for fixture/demo data

    def short_citation(self) -> str:
        return f"[{self.evidence_id}]"


# ─────────────────────────────────────────────────────────────────────────────
# Competitors
# ─────────────────────────────────────────────────────────────────────────────


class Competitor(BaseModel):
    name: str
    url: str
    competitor_type: CompetitorType
    description: str
    target_user: str
    pricing_evidence: str | None = None  # Must cite evidence; never fabricate
    strengths: list[str] = []
    weaknesses: list[str] = []
    complaints: list[str] = []
    differentiation: list[str] = []  # How the idea could differentiate
    evidence_ids: list[str] = []
    confidence: ConfidenceLevel


# ─────────────────────────────────────────────────────────────────────────────
# Opportunity Score
# ─────────────────────────────────────────────────────────────────────────────


class DimensionScore(BaseModel):
    dimension: str
    display_name: str
    raw_score: float = Field(ge=0.0, le=100.0)
    weight: int
    weighted_score: float
    explanation: str
    supporting_evidence_ids: list[str] = []
    contradicting_evidence_ids: list[str] = []
    confidence: ConfidenceLevel
    missing_information: list[str] = []


class OpportunityScore(BaseModel):
    total: float = Field(ge=0.0, le=100.0)
    dimensions: list[DimensionScore]


# ─────────────────────────────────────────────────────────────────────────────
# Analysis Perspectives
# ─────────────────────────────────────────────────────────────────────────────


class AnalysisPerspective(BaseModel):
    perspective_name: PerspectiveName
    perspective_display: str
    model_id: str
    summary: str
    key_findings: list[str] = []
    risks: list[str] = []
    opportunities: list[str] = []
    recommendation: Recommendation
    cited_evidence_ids: list[str] = []
    invalid_citations: list[str] = []  # Citations to nonexistent evidence IDs
    dimension_scores: dict[str, float] = {}  # raw score 0-100 per dimension key
    most_dangerous_assumption: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Model Disagreement
# ─────────────────────────────────────────────────────────────────────────────


class DisagreementPosition(BaseModel):
    perspective: str
    model_id: str
    position: str
    evidence_ids: list[str] = []


class ModelDisagreement(BaseModel):
    topic: str
    positions: list[DisagreementPosition]
    stronger_position: str | None = None
    requires_human_research: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Validation Experiments
# ─────────────────────────────────────────────────────────────────────────────


class ValidationExperiment(BaseModel):
    title: str
    assumption_tested: str
    why_it_matters: str
    procedure: str
    estimated_time: str
    estimated_cost_range: str
    success_threshold: str
    failure_threshold: str
    decision_after: str
    legal_ethical: str
    priority: int = Field(ge=1, le=5)  # 1 = highest priority / lowest cost


class FounderAction(BaseModel):
    """A time-boxed operating milestone with a measurable exit condition."""

    phase: str
    objective: str
    actions: list[str] = []
    success_metric: str
    stop_condition: str
    budget_hint: str


class FounderToolkit(BaseModel):
    """Deterministic, actionable business-starting playbook derived from an analysis."""

    one_sentence_pitch: str
    ideal_customer_profile: str
    beachhead_market: str
    recommended_channels: list[str] = []
    key_metrics: list[str] = []
    roadmap: list[FounderAction] = []
    interview_questions: list[str] = []
    decision_rules: list[str] = []


class RegionalEvidenceSignal(BaseModel):
    evidence_id: str
    category: str
    title: str
    source_name: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class RegionalMarketAnalysis(BaseModel):
    """Evidence-only analysis of demand and operating conditions in the target region."""

    geography: str
    demand_score: float = Field(ge=0.0, le=100.0)
    confidence: ConfidenceLevel
    evidence_count: int = 0
    source_count: int = 0
    summary: str
    demand_signals: list[RegionalEvidenceSignal] = []
    pricing_signals: list[RegionalEvidenceSignal] = []
    regulatory_signals: list[RegionalEvidenceSignal] = []
    distribution_signals: list[RegionalEvidenceSignal] = []
    localization_requirements: list[str] = []
    research_gaps: list[str] = []


class ResearchCoverage(BaseModel):
    depth: ResearchDepth
    queries_generated: int
    queries_executed: int
    providers_used: list[str] = []
    evidence_collected: int
    regional_evidence_count: int


# ─────────────────────────────────────────────────────────────────────────────
# Full Analysis Result
# ─────────────────────────────────────────────────────────────────────────────


class AnalysisResult(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    stage: AnalysisStage
    stage_description: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    idea_input: IdeaInput

    # Set after clarification stage
    interpreted_idea: str | None = None

    # Set after evidence collection
    evidence: list[EvidenceItem] = []
    provider_errors: list[str] = []

    # Set after competitor identification
    competitors: list[Competitor] = []

    # Set after AI perspective runs
    perspectives: list[AnalysisPerspective] = []
    models_used: list[str] = []

    # Set after scoring
    opportunity_score: OpportunityScore | None = None
    evidence_confidence: ConfidenceLevel | None = None
    recommendation: Recommendation | None = None
    most_dangerous_assumption: str | None = None
    strongest_supporting: str | None = None
    strongest_contradicting: str | None = None
    missing_information: list[str] = []

    # Set after experiment generation
    experiments: list[ValidationExperiment] = []
    founder_toolkit: FounderToolkit | None = None
    regional_analysis: RegionalMarketAnalysis | None = None
    research_coverage: ResearchCoverage | None = None

    # Set after disagreement detection
    disagreements: list[ModelDisagreement] = []

    is_demo: bool = False
    error_message: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# API Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────


class AnalysisCreateRequest(BaseModel):
    idea: IdeaInput
    ai_provider: str | None = None  # Overrides the configured provider for this run
    openrouter_api_key: str | None = None  # Custom OpenRouter API key for this run
    groq_api_key: str | None = None  # Custom Groq API key for this run
    opencode_api_key: str | None = None
    openai_api_key: str | None = None
    custom_base_url: str | None = None
    ollama_base_url: str | None = None
    research_providers: list[str] | None = None  # Pin specific providers; None = all enabled
    research_depth: ResearchDepth = ResearchDepth.DEEP

    @field_validator("ai_provider")
    @classmethod
    def validate_requested_provider(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        allowed = {
            "auto",
            "beta",
            "mock",
            "groq",
            "openrouter",
            "opencode",
            "openai",
            "openai_compat",
            "custom",
            "ollama",
            "hybrid",
            "dual",
        }
        if normalized not in allowed:
            raise ValueError(f"Unsupported AI provider: {value!r}")
        return normalized


class DemoAnalysisRequest(BaseModel):
    """Provider options for running the canonical example idea."""

    ai_provider: str | None = None
    openrouter_api_key: str | None = None
    groq_api_key: str | None = None
    opencode_api_key: str | None = None
    openai_api_key: str | None = None
    custom_base_url: str | None = None
    ollama_base_url: str | None = None
    research_providers: list[str] | None = None
    research_depth: ResearchDepth = ResearchDepth.DEEP

    @field_validator("ai_provider")
    @classmethod
    def validate_requested_provider(cls, value: str | None) -> str | None:
        return AnalysisCreateRequest.validate_requested_provider(value)


class PromptAnalysisRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    ai_provider: str | None = None
    openrouter_api_key: str | None = None
    groq_api_key: str | None = None
    opencode_api_key: str | None = None
    openai_api_key: str | None = None
    custom_base_url: str | None = None
    ollama_base_url: str | None = None
    research_providers: list[str] | None = None
    research_depth: ResearchDepth = ResearchDepth.DEEP

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 20 or is_gibberish(normalized):
            raise ValueError(
                "The startup idea appears too vague or like gibberish. Describe the customer, "
                "their problem, and the proposed solution."
            )
        return normalized

    @field_validator("ai_provider")
    @classmethod
    def validate_requested_provider(cls, value: str | None) -> str | None:
        return AnalysisCreateRequest.validate_requested_provider(value)


class AnalysisListItem(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    stage: AnalysisStage
    created_at: datetime
    completed_at: datetime | None
    idea_name: str
    is_demo: bool
    opportunity_score: float | None
    recommendation: Recommendation | None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    ai_provider: str
    research_providers: list[str]
    demo_mode: bool
