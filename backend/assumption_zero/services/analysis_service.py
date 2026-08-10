"""
Analysis service — orchestrates research, AI, scoring, and file-based persistence.

Storage: CSV metadata + JSON files under ./azero_data/
No database required.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional

import assumption_zero.storage as store
from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.config import get_settings, is_public_http_url
from assumption_zero.llm.base import LLMAdapter
from assumption_zero.llm.mock_adapter import MockAdapter
from assumption_zero.llm.openrouter_adapter import OpenRouterAdapter
from assumption_zero.research.arxiv_provider import ArxivProvider
from assumption_zero.research.base import ResearchProvider
from assumption_zero.research.github_provider import GitHubProvider
from assumption_zero.research.hackernews_provider import HackerNewsProvider
from assumption_zero.research.news_provider import NewsSearchProvider
from assumption_zero.research.reddit_provider import RedditProvider
from assumption_zero.research.searxng_provider import SearXNGProvider
from assumption_zero.research.web_search_provider import WebSearchProvider
from assumption_zero.research.wikipedia_provider import WikipediaProvider
from assumption_zero.schemas import (
    STAGE_DESCRIPTIONS,
    AnalysisListItem,
    AnalysisResult,
    AnalysisStage,
    AnalysisStatus,
    IdeaInput,
    Recommendation,
    ResearchDepth,
)

logger = logging.getLogger(__name__)


# ── LLM adapter factory ───────────────────────────────────────────────────────


from assumption_zero.llm.fallback_adapter import FallbackChainAdapter
from assumption_zero.llm.groq_adapter import GroqAdapter
from assumption_zero.llm.ollama_adapter import OllamaAdapter
from assumption_zero.llm.openai_compat_adapter import OpenAICompatAdapter
from assumption_zero.llm.opencode_adapter import OpencodeAdapter


def build_llm_adapter(
    provider_override: Optional[str] = None,
    api_key_override: Optional[str] = None,
    model_override: Optional[str] = None,
    base_url_override: Optional[str] = None,
) -> LLMAdapter:
    """Return the configured LLM adapter.

    Explicit providers are strict. ``auto`` may try multiple configured AI
    providers and finally return the labeled deterministic evidence baseline.

    Args:
        provider_override: Force a specific provider (groq, openrouter, openai_compat, opencode, ollama, mock)
        api_key_override:  Inject an API key at runtime.
        model_override:    Override the model name.
        base_url_override: Override base URL.
    """
    settings = get_settings()
    provider = (provider_override or settings.ai_provider).lower()

    # Instantiate candidate adapters with injected key/URL overrides
    groq = GroqAdapter(api_key=api_key_override, model=model_override)
    openrouter = OpenRouterAdapter(api_key=api_key_override, model=model_override)
    openai_compat = OpenAICompatAdapter(api_key=api_key_override, model=model_override, base_url=base_url_override)
    opencode = OpencodeAdapter(api_key=api_key_override, model=model_override, base_url=base_url_override)
    ollama = OllamaAdapter(model=model_override, base_url=base_url_override)
    mock = MockAdapter()

    # An explicitly selected provider is strict: never disguise a failed AI
    # request as a successful deterministic baseline report. Automatic mode is
    # the only mode that may move between providers and finally use MockAdapter.
    candidates: List[LLMAdapter] = []

    if provider == "groq":
        candidates = [groq]
    elif provider == "openrouter":
        candidates = [openrouter]
    elif provider in ("openai_compat", "openai", "custom"):
        candidates = [openai_compat]
    elif provider == "opencode":
        candidates = [opencode]
    elif provider == "ollama":
        candidates = [ollama]
    elif provider == "mock":
        candidates = [mock]
    else:
        # Default chain priority: Groq -> OpenRouter -> OpenAI -> OpenCode -> Ollama -> Mock
        candidates = [groq, openrouter, openai_compat, opencode, ollama, mock]

    # Filter to available adapters
    available = [a for a in candidates if a.is_available]
    if not available:
        raise ValueError(
            f"AI provider '{provider}' is not configured. Add its API key or endpoint, "
            "or select Auto to allow the labeled evidence baseline."
        )

    if len(available) == 1:
        adapter = available[0]
    else:
        adapter = FallbackChainAdapter(available)

    logger.info("Built LLM adapter chain: %s (Primary: %s)", adapter.model_id, provider)
    return adapter


# ── Research provider factory ─────────────────────────────────────────────────


def build_research_providers(
    requested: Optional[List[str]] = None,
) -> List[ResearchProvider]:
    """Return all enabled research providers."""
    all_providers: List[ResearchProvider] = [
        WebSearchProvider(),
        NewsSearchProvider(),
        ArxivProvider(),
        GitHubProvider(),
        HackerNewsProvider(),
        WikipediaProvider(),
        RedditProvider(),
        SearXNGProvider(),
    ]

    if requested:
        name_map = {p.name.lower(): p for p in all_providers}
        return [name_map[r.lower()] for r in requested if r.lower() in name_map]

    available = [p for p in all_providers if p.is_available]
    logger.info("Research providers: %s", [p.name for p in available])
    return available


# ── CRUD operations ───────────────────────────────────────────────────────────


async def create_analysis(
    idea: IdeaInput,
    ai_provider_override: Optional[str] = None,
    research_providers_override: Optional[List[str]] = None,
    is_demo: bool = False,
) -> str:
    """Create a new analysis record and return its ID."""
    analysis_id = str(uuid.uuid4())
    store.create_record(
        analysis_id=analysis_id,
        idea_name=idea.name or "Unnamed Idea",
        input_data=idea.model_dump(mode="json"),
        is_demo=is_demo,
    )
    logger.info("Created analysis %s", analysis_id)
    return analysis_id


async def run_analysis(
    analysis_id: str,
    idea: IdeaInput,
    ai_provider_override: Optional[str] = None,
    openrouter_api_key: Optional[str] = None,
    groq_api_key: Optional[str] = None,
    opencode_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    custom_base_url: Optional[str] = None,
    ollama_base_url: Optional[str] = None,
    research_providers_override: Optional[List[str]] = None,
    research_depth: ResearchDepth = ResearchDepth.DEEP,
    is_demo: bool = False,
) -> None:
    """Run the full analysis pipeline. Called as a FastAPI BackgroundTask."""

    api_key_override = None
    base_url_override = None
    
    if ai_provider_override == "groq" and groq_api_key:
        api_key_override = groq_api_key
    elif ai_provider_override == "openrouter" and openrouter_api_key:
        api_key_override = openrouter_api_key
    elif ai_provider_override == "opencode" and opencode_api_key:
        api_key_override = opencode_api_key
    elif ai_provider_override in ("openai", "openai_compat", "custom") and openai_api_key:
        api_key_override = openai_api_key
        base_url_override = custom_base_url
    elif ai_provider_override == "ollama":
        base_url_override = ollama_base_url

    settings = get_settings()
    if settings.ssrf_protection_enabled and base_url_override:
        if not is_public_http_url(base_url_override):
            store.fail_record(
                analysis_id,
                "Only public HTTP(S) provider URLs are allowed in hosted mode.",
            )
            return

    async def progress_callback(stage: AnalysisStage, desc: str) -> None:
        store.update_stage(analysis_id, "running", stage.value)

    try:
        llm = build_llm_adapter(
            provider_override=ai_provider_override,
            api_key_override=api_key_override,
            base_url_override=base_url_override
        )
        providers = build_research_providers(research_providers_override)
        engine = AnalysisEngine(
            providers=providers,
            llm_adapter=llm,
            research_depth=research_depth,
        )

        result = await engine.run(
            idea=idea,
            analysis_id=analysis_id,
            progress_callback=progress_callback,
            is_demo=is_demo,
        )

        store.complete_record(analysis_id, result.model_dump(mode="json"))
        if result.status == AnalysisStatus.FAILED:
            store.fail_record(analysis_id, result.error_message or "Analysis failed")
        logger.info("Analysis %s complete", analysis_id)

    except Exception as exc:
        logger.exception("Analysis %s failed: %s", analysis_id, exc)
        store.fail_record(analysis_id, str(exc))


async def get_analysis(analysis_id: str) -> Optional[AnalysisResult]:
    """Retrieve a full AnalysisResult (in-progress or complete)."""
    row = store.get_record(analysis_id)
    if not row:
        return None

    input_data = store.get_input(analysis_id)
    if not input_data:
        return None
    # Use model_construct to skip validators — data was already validated on submission.
    # Re-validating on read causes crashes for legacy entries with short/common names.
    try:
        idea = IdeaInput.model_construct(**input_data)
    except Exception:
        idea = IdeaInput.model_construct(**{k: v for k, v in input_data.items() if v is not None})

    # Full result available — patch idea_input to skip re-validation of stored names
    result_data = store.get_result(analysis_id)
    if result_data:
        try:
            patched = dict(result_data)
            idea_data = patched.get("idea_input") or input_data or {}
            patched["idea_input"] = IdeaInput.from_storage(idea_data)
            return AnalysisResult(**patched)
        except Exception:
            pass
        return None

    # Still in progress — return minimal status object
    created = _parse_dt(row.get("created_at"))
    completed = _parse_dt(row.get("completed_at")) if row.get("completed_at") else None
    stage_val = row.get("stage", "clarifying_idea")

    return AnalysisResult(
        analysis_id=analysis_id,
        status=AnalysisStatus(row.get("status", "pending")),
        stage=AnalysisStage(stage_val),
        stage_description=STAGE_DESCRIPTIONS.get(stage_val, ""),
        created_at=created,
        completed_at=completed,
        idea_input=idea,
        is_demo=row.get("is_demo", "false") == "true",
        error_message=row.get("error_message") or None,
    )


async def list_analyses(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
) -> List[AnalysisListItem]:
    """Return all analyses as list items, newest first."""
    rows = store.list_records(limit=limit)
    items: List[AnalysisListItem] = []

    search_clean = search.strip().lower() if search else None
    status_clean = status_filter.strip().lower() if status_filter else None

    for row in rows:
        row_id = row.get("id", "")
        idea_name = row.get("idea_name", "Unknown")

        if search_clean:
            if search_clean not in row_id.lower() and search_clean not in idea_name.lower():
                continue

        row_status = row.get("status", "pending")
        score: Optional[float] = None
        rec: Optional[Recommendation] = None

        result_data = store.get_result(row_id)
        if result_data:
            score_obj = result_data.get("opportunity_score")
            if isinstance(score_obj, dict):
                score = score_obj.get("total")
            elif isinstance(score_obj, (int, float)):
                score = float(score_obj)

            rec_val = result_data.get("recommendation")
            if rec_val:
                try:
                    rec = Recommendation(rec_val)
                except ValueError:
                    rec = None

        if status_clean:
            normalized_filter = status_clean.replace(" ", "_")
            normalized_rec = rec.value.lower().replace(" ", "_") if rec else None
            if normalized_filter in {"build", "test_first", "pivot", "avoid"}:
                if normalized_rec != normalized_filter:
                    continue
            elif row_status.lower() != normalized_filter:
                continue

        # Safe Enum parsing
        try:
            parsed_status = AnalysisStatus(row_status)
        except ValueError:
            parsed_status = AnalysisStatus.PENDING

        try:
            parsed_stage = AnalysisStage(row.get("stage", "clarifying_idea"))
        except ValueError:
            parsed_stage = AnalysisStage.CLARIFYING_IDEA

        items.append(
            AnalysisListItem(
                analysis_id=row_id,
                status=parsed_status,
                stage=parsed_stage,
                created_at=_parse_dt(row.get("created_at")) or datetime.utcnow(),
                completed_at=_parse_dt(row.get("completed_at")) if row.get("completed_at") else None,
                idea_name=idea_name,
                is_demo=row.get("is_demo", "false") == "true",
                opportunity_score=score,
                recommendation=rec,
            )
        )

    return items


async def delete_analysis(analysis_id: str) -> bool:
    """Delete an analysis. Returns True if found and deleted."""
    return store.delete_record(analysis_id)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
