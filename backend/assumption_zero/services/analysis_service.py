"""
Analysis service — builds and runs the engine, persists results.

This is the bridge between the API/CLI layer and the shared analysis engine.
It handles:
  - Building the engine with configured providers and LLM
  - Persisting progress to the database
  - Returning fully typed AnalysisResult objects
"""
from __future__ import annotations

import json
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
from assumption_zero.models import AnalysisRecord, get_async_session_maker
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
    STAGE_DESCRIPTIONS,
)

logger = logging.getLogger(__name__)


def build_llm_adapter(provider_override: Optional[str] = None) -> LLMAdapter:
    """Build the configured LLM adapter."""
    settings = get_settings()
    provider = provider_override or settings.ai_provider

    if provider == "beta":
        adapter: LLMAdapter = BetaAdapter()
        # Beta is always available (built-in key), no fallback needed
    elif provider == "openrouter":
        adapter = OpenRouterAdapter()
        if not adapter.is_available:
            logger.warning("OpenRouter selected but not configured — falling back to Beta")
            adapter = BetaAdapter()
    elif provider == "ollama":
        adapter = OllamaAdapter()
        if not adapter.is_available:
            logger.warning("Ollama selected but OLLAMA_BASE_URL not set — falling back to Beta")
            adapter = BetaAdapter()
    else:
        adapter = MockAdapter()

    logger.info("LLM adapter: %s", adapter.model_id)
    return adapter


def build_research_providers(
    requested: Optional[List[str]] = None,
) -> List[ResearchProvider]:
    """Build all enabled research providers."""
    all_providers: List[ResearchProvider] = [
        GitHubProvider(),
        HackerNewsProvider(),
        WikipediaProvider(),
        RedditProvider(),
        SearXNGProvider(),  # Only active when SEARXNG_BASE_URL is configured
    ]

    if requested:
        # Filter to only the requested providers
        name_map = {p.name.lower(): p for p in all_providers}
        return [name_map[r.lower()] for r in requested if r.lower() in name_map]

    available = [p for p in all_providers if p.is_available]
    logger.info("Research providers: %s", [p.name for p in available])
    return available


async def create_analysis(
    idea: IdeaInput,
    ai_provider_override: Optional[str] = None,
    research_providers_override: Optional[List[str]] = None,
    is_demo: bool = False,
) -> str:
    """
    Create a new analysis record in the database and return its ID.
    The actual analysis runs asynchronously via run_analysis().
    """
    analysis_id = str(uuid.uuid4())
    SessionMaker = get_async_session_maker()

    async with SessionMaker() as session:
        record = AnalysisRecord(
            id=analysis_id,
            status=AnalysisStatus.PENDING.value,
            stage=AnalysisStage.CLARIFYING_IDEA.value,
            created_at=datetime.utcnow(),
            input_data=idea.model_dump_json(),
            is_demo=is_demo,
        )
        session.add(record)
        await session.commit()

    logger.info("Created analysis %s", analysis_id)
    return analysis_id


async def run_analysis(
    analysis_id: str,
    idea: IdeaInput,
    ai_provider_override: Optional[str] = None,
    research_providers_override: Optional[List[str]] = None,
    is_demo: bool = False,
) -> None:
    """
    Run the full analysis pipeline for an existing record.
    Updates the database record as stages progress.
    Called as a FastAPI BackgroundTask.
    """
    SessionMaker = get_async_session_maker()

    async def progress_callback(stage: AnalysisStage, desc: str) -> None:
        async with SessionMaker() as session:
            record = await session.get(AnalysisRecord, analysis_id)
            if record:
                record.status = AnalysisStatus.RUNNING.value
                record.stage = stage.value
                await session.commit()

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

        async with SessionMaker() as session:
            record = await session.get(AnalysisRecord, analysis_id)
            if record:
                record.status = AnalysisStatus.COMPLETE.value
                record.stage = AnalysisStage.COMPLETE.value
                record.completed_at = datetime.utcnow()
                record.set_result(result.model_dump(mode="json"))
                await session.commit()

        logger.info("Analysis %s complete", analysis_id)

    except Exception as exc:
        logger.exception("Analysis %s failed: %s", analysis_id, exc)
        async with SessionMaker() as session:
            record = await session.get(AnalysisRecord, analysis_id)
            if record:
                record.status = AnalysisStatus.FAILED.value
                record.error_message = str(exc)
                await session.commit()


async def get_analysis(analysis_id: str) -> Optional[AnalysisResult]:
    """Retrieve a full AnalysisResult from the database."""
    SessionMaker = get_async_session_maker()
    async with SessionMaker() as session:
        record = await session.get(AnalysisRecord, analysis_id)
        if not record:
            return None

        # Build a minimal result from the record (for progress polling)
        idea_data = json.loads(record.input_data)
        idea = IdeaInput(**idea_data)

        if record.result_data:
            raw = json.loads(record.result_data)
            return AnalysisResult(**raw)

        # Analysis still in progress
        return AnalysisResult(
            analysis_id=analysis_id,
            status=AnalysisStatus(record.status),
            stage=AnalysisStage(record.stage),
            stage_description=STAGE_DESCRIPTIONS.get(record.stage, ""),
            created_at=record.created_at,
            completed_at=record.completed_at,
            idea_input=idea,
            is_demo=record.is_demo,
            error_message=record.error_message,
        )


async def list_analyses() -> List[AnalysisListItem]:
    """List all analyses ordered by creation date descending."""
    from sqlalchemy import select, desc

    SessionMaker = get_async_session_maker()
    async with SessionMaker() as session:
        stmt = select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(50)
        result = await session.execute(stmt)
        records = result.scalars().all()

    items: List[AnalysisListItem] = []
    for record in records:
        idea_data = json.loads(record.input_data)
        score: Optional[float] = None
        rec = None
        if record.result_data:
            raw = json.loads(record.result_data)
            score_data = raw.get("opportunity_score")
            if score_data:
                score = score_data.get("total")
            rec_val = raw.get("recommendation")
            if rec_val:
                from assumption_zero.schemas import Recommendation
                rec = Recommendation(rec_val)
        items.append(
            AnalysisListItem(
                analysis_id=record.id,
                status=AnalysisStatus(record.status),
                stage=AnalysisStage(record.stage),
                created_at=record.created_at,
                completed_at=record.completed_at,
                idea_name=idea_data.get("name", "Unknown"),
                is_demo=record.is_demo,
                opportunity_score=score,
                recommendation=rec,
            )
        )
    return items


async def delete_analysis(analysis_id: str) -> bool:
    """Delete an analysis. Returns True if found and deleted."""
    SessionMaker = get_async_session_maker()
    async with SessionMaker() as session:
        record = await session.get(AnalysisRecord, analysis_id)
        if not record:
            return False
        await session.delete(record)
        await session.commit()
    return True
