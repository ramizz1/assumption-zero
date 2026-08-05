"""
Pydantic schemas shared across the API, CLI, and analysis engine.

These are the canonical data types for Assumption Zero. All analysis
components produce and consume these types.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

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


STAGE_DESCRIPTIONS: Dict[str, str] = {
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
    SKEPTICAL_INVESTOR = "skeptical_investor"
    PRACTICAL_BUILDER = "practical_builder"


PERSPECTIVE_DISPLAY: Dict[str, str] = {
    PerspectiveName.MARKET_ANALYST: "Market Analyst",
    PerspectiveName.SKEPTICAL_INVESTOR: "Skeptical Investor",
    PerspectiveName.PRACTICAL_BUILDER: "Practical Builder",
}


class CompetitorType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"


# ─────────────────────────────────────────────────────────────────────────────
# Idea Input
# ─────────────────────────────────────────────────────────────────────────────

import re


def is_gibberish(text: str) -> bool:
    """Check if text appears to be random keystrokes or gibberish."""
    s = text.strip()
    if not s or len(s) < 3:
        return True

    words = [w for w in re.split(r"\s+", s) if len(w) > 0]
    vowels = set("aeiouyAEIOUYаеëиоуыэюяАЕЁИОУЫЭЮЯəöğıüƏÖĞIÜ")

    if len(words) == 1 and len(s) >= 7:
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
        ..., min_length=5, max_length=2000,
        description="Required: What problem does this solve?"
    )
    target_customer: str = Field(
        ..., min_length=3, max_length=500,
        description="Required: Who is this for?"
    )
    geography: str = Field(
        ..., min_length=2, max_length=200,
        description="Required: Target market geography"
    )
    business_model: Optional[str] = Field(None, max_length=500)
    price: Optional[str] = Field(None, max_length=200, description="Expected price or pricing model")
    founder_skills: Optional[str] = Field(None, max_length=1000)
    budget: Optional[str] = Field(None, max_length=200, description="Available runway or budget")
    known_competitors: Optional[str] = Field(None, max_length=500)
    unfair_advantage: Optional[str] = Field(None, max_length=1000, description="Unique advantage, distribution channel, or IP")
    key_assumptions: Optional[str] = Field(None, max_length=1000, description="1-2 core assumptions that must be true for success")
    additional_context: Optional[str] = Field(None, max_length=3000)

    @field_validator("name", "description", "problem")
    @classmethod
    def validate_not_gibberish(cls, v: str) -> str:
        if is_gibberish(v):
            raise ValueError(
                f"Invalid startup prompt '{v[:30]}': The input text appears to be random characters or gibberish. "
                "Please enter a clear product or business idea."
            )
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    """A single piece of collected evidence. Every factual claim must cite an evidence ID."""

    evidence_id: str  # E001, E002, etc. — stable identifier
    title: str
    url: str  # Use demo:// URIs for fixture data; never fabricate real URLs
    source_name: str
    publication_date: Optional[date] = None
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
    pricing_evidence: Optional[str] = None  # Must cite evidence; never fabricate
    strengths: List[str] = []
    weaknesses: List[str] = []
    complaints: List[str] = []
    differentiation: List[str] = []  # How the idea could differentiate
    evidence_ids: List[str] = []
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
    supporting_evidence_ids: List[str] = []
    contradicting_evidence_ids: List[str] = []
    confidence: ConfidenceLevel
    missing_information: List[str] = []


class OpportunityScore(BaseModel):
    total: float = Field(ge=0.0, le=100.0)
    dimensions: List[DimensionScore]


# ─────────────────────────────────────────────────────────────────────────────
# Analysis Perspectives
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisPerspective(BaseModel):
    perspective_name: PerspectiveName
    perspective_display: str
    model_id: str
    summary: str
    key_findings: List[str] = []
    risks: List[str] = []
    opportunities: List[str] = []
    recommendation: Recommendation
    cited_evidence_ids: List[str] = []
    invalid_citations: List[str] = []  # Citations to nonexistent evidence IDs
    dimension_scores: Dict[str, float] = {}  # raw score 0-100 per dimension key
    most_dangerous_assumption: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Model Disagreement
# ─────────────────────────────────────────────────────────────────────────────

class DisagreementPosition(BaseModel):
    perspective: str
    model_id: str
    position: str
    evidence_ids: List[str] = []


class ModelDisagreement(BaseModel):
    topic: str
    positions: List[DisagreementPosition]
    stronger_position: Optional[str] = None
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


# ─────────────────────────────────────────────────────────────────────────────
# Full Analysis Result
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisResult(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    stage: AnalysisStage
    stage_description: str = ""
    created_at: datetime
    completed_at: Optional[datetime] = None
    idea_input: IdeaInput

    # Set after clarification stage
    interpreted_idea: Optional[str] = None

    # Set after evidence collection
    evidence: List[EvidenceItem] = []
    provider_errors: List[str] = []

    # Set after competitor identification
    competitors: List[Competitor] = []

    # Set after AI perspective runs
    perspectives: List[AnalysisPerspective] = []
    models_used: List[str] = []

    # Set after scoring
    opportunity_score: Optional[OpportunityScore] = None
    evidence_confidence: Optional[ConfidenceLevel] = None
    recommendation: Optional[Recommendation] = None
    most_dangerous_assumption: Optional[str] = None
    strongest_supporting: Optional[str] = None
    strongest_contradicting: Optional[str] = None
    missing_information: List[str] = []

    # Set after experiment generation
    experiments: List[ValidationExperiment] = []

    # Set after disagreement detection
    disagreements: List[ModelDisagreement] = []

    is_demo: bool = False
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# API Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisCreateRequest(BaseModel):
    idea: IdeaInput
    ai_provider: Optional[str] = None  # Overrides the configured provider for this run
    openrouter_api_key: Optional[str] = None  # Custom OpenRouter API key for this run
    research_providers: Optional[List[str]] = None  # Pin specific providers; None = all enabled


class PromptAnalysisRequest(BaseModel):
    prompt: str
    ai_provider: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    research_providers: Optional[List[str]] = None


class AnalysisListItem(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    stage: AnalysisStage
    created_at: datetime
    completed_at: Optional[datetime]
    idea_name: str
    is_demo: bool
    opportunity_score: Optional[float]
    recommendation: Optional[Recommendation]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    ai_provider: str
    research_providers: List[str]
    demo_mode: bool
