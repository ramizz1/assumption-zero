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
from assumption_zero.llm.ollama_adapter import OllamaAdapter
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


def build_llm_adapter(provider_override: Optional[str] = None) -> LLMAdapter:
    """Return the configured LLM adapter."""
    settings = get_settings()
    provider = provider_override or settings.ai_provider

    if provider == "beta":
        adapter: LLMAdapter = BetaAdapter()
    elif provider == "openrouter":
        adapter = OpenRouterAdapter()
        if not adapter.is_available:
            logger.warning("OpenRouter not configured — falling back to Beta")
            adapter = BetaAdapter()
    elif provider == "ollama":
        adapter = OllamaAdapter()
        if not adapter.is_available:
            logger.warning("Ollama not available — falling back to Beta")
            adapter = BetaAdapter()
    else:
        adapter = MockAdapter()

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
    research_providers_override: Optional[List[str]] = None,
    is_demo: bool = False,
) -> None:
    """Run the full analysis pipeline. Called as a FastAPI BackgroundTask."""

    if openrouter_api_key:
        import os
        os.environ["OPENROUTER_API_KEY"] = openrouter_api_key

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
    idea = IdeaInput(**input_data)

    # Full result available
    result_data = store.get_result(analysis_id)
    if result_data:
        return AnalysisResult(**result_data)

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


async def list_analyses() -> List[AnalysisListItem]:
    """Return all analyses as list items, newest first."""
    rows = store.list_records()
    items: List[AnalysisListItem] = []

    for row in rows:
        score: Optional[float] = None
        rec: Optional[Recommendation] = None

        result_data = store.get_result(row["id"])
        if result_data:
            score_obj = result_data.get("opportunity_score")
            if score_obj:
                score = score_obj.get("total")
            rec_val = result_data.get("recommendation")
            if rec_val:
                rec = Recommendation(rec_val)

        items.append(
            AnalysisListItem(
                analysis_id=row["id"],
                status=AnalysisStatus(row.get("status", "pending")),
                stage=AnalysisStage(row.get("stage", "clarifying_idea")),
                created_at=_parse_dt(row.get("created_at")),
                completed_at=_parse_dt(row.get("completed_at")) if row.get("completed_at") else None,
                idea_name=row.get("idea_name", "Unknown"),
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
