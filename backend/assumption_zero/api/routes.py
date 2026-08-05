"""
FastAPI route definitions for Assumption Zero.

Routes:
  GET  /api/health
  POST /api/analyses
  GET  /api/analyses
  GET  /api/analyses/{analysis_id}
  DELETE /api/analyses/{analysis_id}
  POST /api/demo
"""
from __future__ import annotations

import json
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

from assumption_zero import __version__
from assumption_zero.config import get_settings
from assumption_zero.research.github_provider import GitHubProvider
from assumption_zero.research.hackernews_provider import HackerNewsProvider
from assumption_zero.research.reddit_provider import RedditProvider
from assumption_zero.research.searxng_provider import SearXNGProvider
from assumption_zero.research.wikipedia_provider import WikipediaProvider
from assumption_zero.schemas import (
    AnalysisCreateRequest,
    AnalysisListItem,
    AnalysisResult,
    HealthResponse,
    IdeaInput,
)
from assumption_zero.services.analysis_service import (
    create_analysis,
    delete_analysis,
    get_analysis,
    list_analyses,
    run_analysis,
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

# ── Demo idea ─────────────────────────────────────────────────────
# When users click "Run Example Analysis", this idea goes through the
# REAL pipeline — no hardcoded responses.
DEMO_IDEA = IdeaInput(
    name="LegalMind Local",
    description="A privacy-first AI meeting summarizer that runs entirely on-device for small legal firms",
    problem=(
        "Legal professionals have confidential client meetings that cannot be transcribed "
        "using cloud AI tools due to attorney-client privilege and data sovereignty concerns. "
        "Existing tools like Otter.ai send audio to remote servers, creating compliance risks."
    ),
    target_customer="Solo practitioners and small law firms (1–20 attorneys)",
    geography="United States",
    business_model="SaaS subscription per seat, installed locally",
    price="$49/month per attorney",
    founder_skills="Full-stack developer, 5 years experience, some ML background",
    budget="$15,000 runway for 6 months",
    known_competitors="Otter.ai, Fireflies.ai, Whisper (open source), Tactiq",
    additional_context=(
        "Planning to use OpenAI Whisper for transcription and a local Llama model for "
        "summarization. Initial target is solo practitioners who already use case management software."
    ),
)


def _available_providers() -> List[str]:
    providers = [GitHubProvider(), HackerNewsProvider(), WikipediaProvider(), RedditProvider()]
    sx = SearXNGProvider()
    if sx.is_available:
        providers.append(sx)
    return [p.name for p in providers if p.is_available]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        ai_provider=settings.ai_provider,
        research_providers=_available_providers(),
        demo_mode=settings.ai_provider == "mock",
    )


@router.post("/analyses", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_endpoint(
    request: Request,
    body: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Start a new analysis. Returns immediately with analysis_id; poll GET /analyses/{id}."""
    analysis_id = await create_analysis(
        idea=body.idea,
        ai_provider_override=body.ai_provider,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=body.idea,
        ai_provider_override=body.ai_provider,
        openrouter_api_key=body.openrouter_api_key,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    return {"analysis_id": analysis_id, "status": "pending"}


@router.get("/analyses", response_model=List[AnalysisListItem])
async def list_analyses_endpoint() -> List[AnalysisListItem]:
    return await list_analyses()


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_endpoint(analysis_id: str) -> AnalysisResult:
    result = await get_analysis(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id!r} not found")
    return result


@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_endpoint(analysis_id: str) -> None:
    deleted = await delete_analysis(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id!r} not found")


@router.post("/demo", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def demo_endpoint(background_tasks: BackgroundTasks) -> dict:
    """
    Start a demo analysis using the example idea (LegalMind Local).
    Runs through the REAL research and AI pipeline — no fake data.
    """
    analysis_id = await create_analysis(
        idea=DEMO_IDEA,
        is_demo=True,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=DEMO_IDEA,
        is_demo=True,
    )
    return {"analysis_id": analysis_id, "status": "pending", "demo": True}
