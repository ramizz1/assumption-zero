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

from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.config import get_settings
from assumption_zero.llm.base import LLMAdapter
from assumption_zero.llm.beta_adapter import BetaAdapter
from assumption_zero.llm.mock_adapter import MockAdapter
from assumption_zero.llm.openrouter_adapter import OpenRouterAdapter
from assumption_zero.research.base import ResearchProvider
from assumption_zero.research.github_provider import GitHubProvider
from assumption_zero.research.hackernews_provider import HackerNewsProvider
from assumption_zero.research.reddit_provider import RedditProvider
from assumption_zero.research.searxng_provider import SearXNGProvider
from assumption_zero.research.wikipedia_provider import WikipediaProvider
from assumption_zero.schemas import (
    AnalysisListItem,
    AnalysisResult,
    AnalysisStage,
    AnalysisStatus,
    IdeaInput,
    Recommendation,
    STAGE_DESCRIPTIONS,
)
import assumption_zero.storage as store

from assumption_zero.research.web_search_provider import WebSearchProvider
from assumption_zero.research.news_provider import NewsSearchProvider
from assumption_zero.research.arxiv_provider import ArxivProvider

logger = logging.getLogger(__name__)


# ── LLM adapter factory ───────────────────────────────────────────────────────


from assumption_zero.llm.groq_adapter import GroqAdapter
from assumption_zero.llm.hybrid_adapter import HybridLLMAdapter
from assumption_zero.llm.openai_compat_adapter import OpenAICompatAdapter
from assumption_zero.llm.ollama_adapter import OllamaAdapter
from assumption_zero.llm.opencode_adapter import OpencodeAdapter


def build_llm_adapter(
    provider_override: Optional[str] = None,
    api_key_override: Optional[str] = None,
    model_override: Optional[str] = None,
    base_url_override: Optional[str] = None,
) -> LLMAdapter:
    """Return the configured LLM adapter.

    Args:
        provider_override: Force a specific provider (openai_compat, groq, openrouter, ollama, opencode, etc.)
        api_key_override:  Inject an API key at runtime (skips .env for this call).
        model_override:    Override the model name (e.g. gpt-4o, claude-3-haiku, llama3.2, etc.)
        base_url_override: Override the base URL (for openai_compat, ollama, or opencode endpoints).
    """
    import os
    settings = get_settings()
    provider = (provider_override or settings.ai_provider).lower()

    # If a custom key/model/url was provided at runtime, inject via env so adapters pick them up.
    if api_key_override:
        os.environ["OPENAI_COMPATIBLE_API_KEY"] = api_key_override
        os.environ["OPENROUTER_API_KEY"] = api_key_override
        os.environ["OPENCODE_API_KEY"] = api_key_override
    if model_override:
        os.environ["OPENAI_COMPATIBLE_MODEL"] = model_override
        os.environ["OLLAMA_MODEL"] = model_override
        os.environ["OPENCODE_MODEL"] = model_override
    if base_url_override:
        os.environ["OPENAI_COMPATIBLE_BASE_URL"] = base_url_override
        os.environ["OLLAMA_BASE_URL"] = base_url_override
        os.environ["OPENCODE_BASE_URL"] = base_url_override

    groq = GroqAdapter()
    openrouter = OpenRouterAdapter()

    if provider in ("openai_compat", "openai", "custom"):
        compat = OpenAICompatAdapter()
        if compat.is_available:
            adapter: LLMAdapter = compat
        else:
            logger.warning("openai_compat provider selected but key/URL not set — falling back to hybrid")
            adapter = HybridLLMAdapter(groq, openrouter) if (groq.is_available and openrouter.is_available) else (groq if groq.is_available else openrouter)
    elif provider == "ollama":
        adapter = OllamaAdapter()
    elif provider == "opencode":
        opencode = OpencodeAdapter()
        if opencode.is_available:
            adapter = opencode
        else:
            logger.warning("opencode provider selected but OPENCODE_API_KEY not set — falling back to hybrid")
            adapter = HybridLLMAdapter(groq, openrouter) if (groq.is_available and openrouter.is_available) else (groq if groq.is_available else openrouter)
    elif provider in ("hybrid", "auto", "dual"):
        adapter = HybridLLMAdapter(groq, openrouter)
    elif provider == "groq":
        if openrouter.is_available:
            adapter = HybridLLMAdapter(groq, openrouter)
        else:
            adapter = groq
    elif provider == "openrouter":
        if groq.is_available:
            adapter = HybridLLMAdapter(groq, openrouter)
        else:
            adapter = openrouter
    elif provider == "beta":
        if groq.is_available and openrouter.is_available:
            adapter = HybridLLMAdapter(groq, openrouter)
        elif groq.is_available:
            adapter = groq
        elif openrouter.is_available:
            adapter = openrouter
        else:
            adapter = BetaAdapter()
    else:
        adapter = BetaAdapter()

    logger.info("LLM adapter: %s", adapter.model_id)
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
    is_demo: bool = False,
) -> None:
    """Run the full analysis pipeline. Called as a FastAPI BackgroundTask."""

    import os
    if openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    if opencode_api_key:
        os.environ["OPENCODE_API_KEY"] = opencode_api_key
    if openai_api_key:
        os.environ["OPENAI_COMPATIBLE_API_KEY"] = openai_api_key
    if custom_base_url:
        os.environ["OPENAI_COMPATIBLE_BASE_URL"] = custom_base_url
    if ollama_base_url:
        os.environ["OLLAMA_BASE_URL"] = ollama_base_url

    async def progress_callback(stage: AnalysisStage, desc: str) -> None:
        store.update_stage(analysis_id, "running", stage.value)

    try:
        llm = build_llm_adapter(ai_provider_override)
        providers = build_research_providers(research_providers_override)
        engine = AnalysisEngine(providers=providers, llm_adapter=llm)

        result = await engine.run(
            idea=idea,
            analysis_id=analysis_id,
            progress_callback=progress_callback,
            is_demo=is_demo,
        )

        store.complete_record(analysis_id, result.model_dump(mode="json"))
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
        if status_clean and row_status.lower() != status_clean:
            continue

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
