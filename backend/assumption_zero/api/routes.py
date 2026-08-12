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
    DemoAnalysisRequest,
    HealthResponse,
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
# The public example is served from a curated browser bundle and never enters
# the live provider pipeline.
def _available_providers() -> list[str]:
    providers = [GitHubProvider(), HackerNewsProvider(), WikipediaProvider(), RedditProvider()]
    sx = SearXNGProvider()
    if sx.is_available:
        providers.append(sx)
    return [p.name for p in providers if p.is_available]


ProviderRequest = AnalysisCreateRequest | DemoAnalysisRequest | PromptAnalysisRequest


def _llm_options(body: ProviderRequest) -> tuple[str | None, str | None, str | None]:
    """Resolve the provider and only the credential that belongs to it.

    In Auto mode, a runtime/browser key takes priority over server-side
    discovery so a key entered by the user is never silently ignored.
    """
    provider = body.ai_provider
    if provider in (None, "auto"):
        if body.groq_api_key:
            provider = "groq"
        elif body.openrouter_api_key:
            provider = "openrouter"
        elif body.opencode_api_key:
            provider = "opencode"
        elif body.openai_api_key:
            provider = "openai_compat"

    api_key = None
    base_url = None
    if provider == "groq":
        api_key = body.groq_api_key
    elif provider == "openrouter":
        api_key = body.openrouter_api_key
    elif provider == "opencode":
        api_key = body.opencode_api_key
    elif provider in ("openai", "openai_compat", "custom"):
        api_key = body.openai_api_key
        base_url = body.custom_base_url
    elif provider == "ollama":
        base_url = body.ollama_base_url
    return provider, api_key, base_url


def _validate_selected_provider(body: ProviderRequest) -> str | None:
    """Reject an unconfigured explicit provider before starting a long research run."""
    provider, api_key, base_url = _llm_options(body)
    if provider == "mock":
        raise HTTPException(
            status_code=400,
            detail="Real analyses require a configured AI provider. Mock mode is not allowed.",
        )
    try:
        build_llm_adapter(
            provider_override=provider,
            api_key_override=api_key,
            base_url_override=base_url,
            allow_mock_fallback=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return provider


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

    if provider in ("auto", "beta"):
        if groq_api_key:
            provider = "groq"
        elif openrouter_api_key:
            provider = "openrouter"
        elif opencode_api_key:
            provider = "opencode"
        elif openai_api_key:
            provider = "openai_compat"
        else:
            provider = "auto"

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
            allow_mock_fallback=False,
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
    provider = _validate_selected_provider(body)
    analysis_id = await create_analysis(
        idea=body.idea,
        ai_provider_override=provider,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=body.idea,
        ai_provider_override=provider,
        openrouter_api_key=body.openrouter_api_key,
        groq_api_key=body.groq_api_key,
        opencode_api_key=body.opencode_api_key,
        openai_api_key=body.openai_api_key,
        custom_base_url=body.custom_base_url,
        ollama_base_url=body.ollama_base_url,
        research_providers_override=body.research_providers,
        research_depth=body.research_depth,
        is_demo=False,
    )
    return {"analysis_id": analysis_id, "status": "pending"}


async def _run_analysis_in_request(
    body: ProviderRequest,
    idea,
    provider: str | None,
) -> AnalysisResult:
    """Complete an analysis within one request for serverless production hosts."""
    analysis_id = await create_analysis(
        idea=idea,
        ai_provider_override=provider,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    await run_analysis(
        analysis_id=analysis_id,
        idea=idea,
        ai_provider_override=provider,
        openrouter_api_key=body.openrouter_api_key,
        groq_api_key=body.groq_api_key,
        opencode_api_key=body.opencode_api_key,
        openai_api_key=body.openai_api_key,
        custom_base_url=body.custom_base_url,
        ollama_base_url=body.ollama_base_url,
        research_providers_override=body.research_providers,
        research_depth=body.research_depth,
        is_demo=False,
    )
    result = await get_analysis(analysis_id)
    if result is None:
        raise HTTPException(
            status_code=500,
            detail="The analysis finished without a readable report. Please try again.",
        )
    return result


@router.post("/analyses/sync", response_model=AnalysisResult)
async def create_analysis_sync_endpoint(body: AnalysisCreateRequest) -> AnalysisResult:
    """Run a real AI analysis synchronously so the host cannot drop background work."""
    provider = _validate_selected_provider(body)
    return await _run_analysis_in_request(body, body.idea, provider)


@router.post("/analyses/from-prompt", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_from_prompt_endpoint(
    request: Request,
    body: PromptAnalysisRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Analyze a startup idea from a single freeform text prompt."""

    provider, api_key_override, base_url_override = _llm_options(body)

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
            provider_override=provider,
            api_key_override=api_key_override,
            base_url_override=base_url_override,
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
        ai_provider_override=provider,
        research_providers_override=body.research_providers,
        is_demo=False,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=parsed_idea,
        ai_provider_override=provider,
        openrouter_api_key=body.openrouter_api_key,
        groq_api_key=body.groq_api_key,
        opencode_api_key=body.opencode_api_key,
        openai_api_key=body.openai_api_key,
        custom_base_url=body.custom_base_url,
        ollama_base_url=body.ollama_base_url,
        research_providers_override=body.research_providers,
        research_depth=body.research_depth,
        is_demo=False,
    )
    return {
        "analysis_id": analysis_id,
        "status": "pending",
        "parsed_idea": parsed_idea.model_dump(mode="json"),
    }


@router.post("/analyses/from-prompt/sync", response_model=AnalysisResult)
async def create_analysis_from_prompt_sync_endpoint(
    body: PromptAnalysisRequest,
) -> AnalysisResult:
    """Parse a prompt with real AI, then return the completed analysis."""
    provider, api_key_override, base_url_override = _llm_options(body)
    settings = get_settings()
    if settings.ssrf_protection_enabled and base_url_override:
        if not is_public_http_url(base_url_override):
            raise HTTPException(
                status_code=400,
                detail="Only public HTTP(S) provider URLs are allowed in hosted mode.",
            )
    try:
        llm = build_llm_adapter(
            provider_override=provider,
            api_key_override=api_key_override,
            base_url_override=base_url_override,
            allow_mock_fallback=False,
        )
        parsed_idea = await llm.parse_raw_prompt(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=429,
            detail=f"AI provider could not complete the request: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Prompt parsing failed")
        raise HTTPException(
            status_code=502,
            detail="The selected AI provider could not process this prompt. Verify the key and try again.",
        ) from exc
    return await _run_analysis_in_request(body, parsed_idea, provider)


@router.get("/analyses", response_model=list[AnalysisListItem])
async def list_analyses_endpoint(
    search: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=100),
) -> list[AnalysisListItem]:
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


@router.post("/demo", response_model=dict)
async def demo_endpoint(body: DemoAnalysisRequest | None = None) -> dict:
    """
    Return the browser-bundled example identifier without calling AI.

    The public example is intentionally precomputed so evaluating the interface
    never consumes the user's provider quota.
    """
    return {
        "analysis_id": "demo-legalmind-local",
        "status": "complete",
        "demo": True,
        "bundled": True,
    }
