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

import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status

from assumption_zero import __version__
from assumption_zero.config import get_settings, is_public_http_url
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
    PromptAnalysisRequest,
)
from assumption_zero.services.analysis_service import (
    build_llm_adapter,
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


@router.post("/verify-keys", response_model=dict)
async def verify_keys_endpoint(body: dict) -> dict:
    """Verify if the selected AI provider credentials/endpoints are valid."""
    provider = body.get("provider", "mock")
    groq_api_key = body.get("groqKey") or body.get("groq_api_key")
    openrouter_api_key = body.get("openrouterKey") or body.get("openrouter_api_key")
    opencode_api_key = body.get("opencodeKey") or body.get("opencode_api_key")
    openai_api_key = body.get("openaiKey") or body.get("openai_api_key")
    ollama_base_url = body.get("ollamaUrl") or body.get("ollama_base_url")
    custom_base_url = body.get("customUrl") or body.get("custom_base_url")

    api_key_override = None
    base_url_override = None
    if provider == "groq":
        api_key_override = groq_api_key
    elif provider == "openrouter":
        api_key_override = openrouter_api_key
    elif provider == "opencode":
        api_key_override = opencode_api_key
    elif provider in ("openai", "openai_compat", "custom"):
        api_key_override = openai_api_key
        base_url_override = custom_base_url
    elif provider == "ollama":
        base_url_override = ollama_base_url

    # Require explicit API key for providers that require authentication
    key_required_providers = ("groq", "openrouter", "opencode", "openai", "openai_compat", "custom")
    settings = get_settings()

    if settings.ssrf_protection_enabled and base_url_override:
        if not is_public_http_url(base_url_override):
            raise HTTPException(
                status_code=400,
                detail="Only public HTTP(S) provider URLs are allowed in hosted mode.",
            )

    if provider in key_required_providers:
        env_key = None
        if provider == "groq":
            env_key = settings.groq_api_key
        elif provider == "openrouter":
            env_key = settings.openrouter_api_key
        elif provider == "opencode":
            env_key = settings.opencode_api_key
        elif provider in ("openai", "openai_compat", "custom"):
            env_key = settings.openai_compatible_api_key

        effective_key = api_key_override or env_key
        if not effective_key or not effective_key.strip():
            raise HTTPException(
                status_code=400,
                detail=f"API key is missing for {provider.upper()}. Please enter your API key before testing connection.",
            )

    try:
        llm = build_llm_adapter(
            provider_override=provider,
            api_key_override=api_key_override,
            base_url_override=base_url_override,
        )
        if provider in key_required_providers and not llm.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid API key or endpoint for {provider.upper()}.",
            )

        return {
            "status": "ok",
            "provider": provider,
            "message": (
                f"Successfully validated {provider.upper()} configuration. "
                "Live connectivity is confirmed when an analysis starts."
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Connection verification failed for {provider}: {exc}",
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
        groq_api_key=body.groq_api_key,
        opencode_api_key=body.opencode_api_key,
        openai_api_key=body.openai_api_key,
        custom_base_url=body.custom_base_url,
        ollama_base_url=body.ollama_base_url,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    return {"analysis_id": analysis_id, "status": "pending"}


@router.post("/analyses/from-prompt", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_from_prompt_endpoint(
    request: Request,
    body: PromptAnalysisRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Analyze a startup idea from a single freeform text prompt."""
    
    # Provider-specific key resolution based on requested ai_provider
    api_key_override = None
    base_url_override = None
    if body.ai_provider == "groq" and body.groq_api_key:
        api_key_override = body.groq_api_key
    elif body.ai_provider == "openrouter" and body.openrouter_api_key:
        api_key_override = body.openrouter_api_key
    elif body.ai_provider == "opencode" and body.opencode_api_key:
        api_key_override = body.opencode_api_key
    elif body.ai_provider in ("openai", "openai_compat", "custom") and body.openai_api_key:
        api_key_override = body.openai_api_key
        base_url_override = body.custom_base_url
    elif body.ai_provider == "ollama":
        base_url_override = body.ollama_base_url

    # SSRF Protection
    from assumption_zero.config import get_settings
    settings = get_settings()
    if settings.ssrf_protection_enabled and base_url_override:
        if not is_public_http_url(base_url_override):
            raise HTTPException(
                status_code=400,
                detail="Only public HTTP(S) provider URLs are allowed in hosted mode.",
            )

    try:
        llm = build_llm_adapter(
            provider_override=body.ai_provider,
            api_key_override=api_key_override,
            base_url_override=base_url_override
        )
        parsed_idea = await llm.parse_raw_prompt(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=f"No AI tokens available: {exc}")
    except Exception as exc:
        logger.error("Error creating analysis from prompt: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to process prompt: {exc}")

    analysis_id = await create_analysis(
        idea=parsed_idea,
        ai_provider_override=body.ai_provider,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=parsed_idea,
        ai_provider_override=body.ai_provider,
        openrouter_api_key=body.openrouter_api_key,
        groq_api_key=body.groq_api_key,
        opencode_api_key=body.opencode_api_key,
        openai_api_key=body.openai_api_key,
        custom_base_url=body.custom_base_url,
        ollama_base_url=body.ollama_base_url,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    return {"analysis_id": analysis_id, "status": "pending", "parsed_idea": parsed_idea.model_dump(mode="json")}


@router.get("/analyses", response_model=List[AnalysisListItem])
async def list_analyses_endpoint(
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=100),
) -> List[AnalysisListItem]:
    return await list_analyses(search=search, status_filter=status, limit=limit)


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
