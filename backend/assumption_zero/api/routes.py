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

import asyncio
import json
import logging
import time
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from pydantic import SecretStr
from starlette.responses import StreamingResponse

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
    VerifyKeysRequest,
)
from assumption_zero.security import (
    OWNER_HEADER,
    hash_owner_token,
    public_provider_error,
    public_provider_status,
    redact_sensitive_text,
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
ANALYSIS_DEADLINE_SECONDS = 240
HEARTBEAT_SECONDS = 10


async def _probe_provider_connection(
    provider: str,
    api_key: str | None,
    base_url: str | None,
) -> str:
    """Verify credentials and prove that one selected model can generate text."""
    normalized = provider.casefold()
    try:
        key_name = "openai_compat" if normalized in ("openai", "custom") else normalized
        adapter = build_llm_adapter(
            provider_override=normalized,
            api_key_override=api_key,
            api_keys={key_name: api_key},
            base_url_override=base_url,
            allow_mock_fallback=False,
        )
        async with asyncio.timeout(45):
            model = await adapter.verify_connection()
        logger.info("Provider %s verified with model %s", normalized, model)
        return model
    except HTTPException:
        raise
    except Exception as exc:
        logger.info("Provider connectivity check failed for %s: %s", normalized, type(exc).__name__)
        raise HTTPException(
            status_code=public_provider_status(exc),
            detail=public_provider_error(exc),
        ) from None


# ── Demo idea ─────────────────────────────────────────────────────
# The public example is served from a curated browser bundle and never enters
# the live provider pipeline.
def _available_providers() -> list[str]:
    providers = [GitHubProvider(), HackerNewsProvider(), WikipediaProvider(), RedditProvider()]
    sx = SearXNGProvider()
    if sx.is_available:
        providers.append(sx)
    return [p.name for p in providers if p.is_available]


ProviderRequest = (
    AnalysisCreateRequest | DemoAnalysisRequest | PromptAnalysisRequest | VerifyKeysRequest
)


def _secret_value(value: SecretStr | None) -> str | None:
    return value.get_secret_value() if value else None


def _provider_keys(body: ProviderRequest) -> dict[str, str | None]:
    """Return an isolated credential map; values are used only in memory."""
    return {
        "groq": _secret_value(body.groq_api_key),
        "openrouter": _secret_value(body.openrouter_api_key),
        "opencode": _secret_value(body.opencode_api_key),
        "openai_compat": _secret_value(body.openai_api_key),
    }


def require_owner_hash(
    owner_token: Annotated[str | None, Header(alias=OWNER_HEADER)] = None,
) -> str:
    try:
        return hash_owner_token(owner_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _llm_options(body: ProviderRequest) -> tuple[str | None, str | None, str | None]:
    """Resolve an explicit provider override without collapsing Auto mode."""
    provider = body.ai_provider or "auto"

    api_key = None
    base_url = None
    if provider == "groq":
        api_key = _secret_value(body.groq_api_key)
    elif provider == "openrouter":
        api_key = _secret_value(body.openrouter_api_key)
    elif provider == "opencode":
        api_key = _secret_value(body.opencode_api_key)
    elif provider in ("openai", "openai_compat", "custom"):
        api_key = _secret_value(body.openai_api_key)
        base_url = body.custom_base_url
    elif provider == "ollama":
        base_url = body.ollama_base_url
    if base_url:
        settings = get_settings()
        configured_base = (
            settings.ollama_base_url
            if provider == "ollama"
            else settings.openai_compatible_base_url
        )
        # A request repeating the server's configured URL is not a runtime
        # override. Ignore it so the safe default works with the web form.
        if configured_base and base_url.rstrip("/") == configured_base.rstrip("/"):
            base_url = None
    return provider, api_key, base_url


def _validate_runtime_provider_url(base_url: str | None) -> None:
    if not base_url:
        return
    settings = get_settings()
    if not settings.allow_runtime_provider_urls:
        raise HTTPException(
            status_code=400,
            detail="Runtime provider URL overrides are disabled on this deployment.",
        )
    if settings.ssrf_protection_enabled and not is_public_http_url(base_url):
        raise HTTPException(
            status_code=400,
            detail="Only public HTTP(S) provider URLs are allowed in hosted mode.",
        )


def _validate_selected_provider(body: ProviderRequest) -> str | None:
    """Reject an unconfigured explicit provider before starting a long research run."""
    provider, api_key, base_url = _llm_options(body)
    _validate_runtime_provider_url(base_url)
    if provider == "mock":
        raise HTTPException(
            status_code=400,
            detail="Real analyses require a configured AI provider. Mock mode is not allowed.",
        )
    try:
        build_llm_adapter(
            provider_override=provider,
            api_key_override=api_key,
            api_keys=_provider_keys(body),
            base_url_override=base_url,
            allow_mock_fallback=False,
        )
    except ValueError as exc:
        logger.warning(
            "Provider selection failed for %s: %s",
            provider,
            redact_sensitive_text(exc),
        )
        raise HTTPException(status_code=400, detail=public_provider_error(exc)) from None
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
async def verify_keys_endpoint(
    body: VerifyKeysRequest,
    owner_hash: str = Depends(require_owner_hash),
) -> dict:
    """Verify if the selected AI provider credentials/endpoints are valid."""
    del owner_hash  # The dependency enforces a valid capability; no value is persisted here.
    provider = body.ai_provider or "mock"
    groq_api_key = _secret_value(body.groq_api_key)
    openrouter_api_key = _secret_value(body.openrouter_api_key)
    opencode_api_key = _secret_value(body.opencode_api_key)
    openai_api_key = _secret_value(body.openai_api_key)

    if provider in ("auto", "beta", "hybrid", "dual"):
        settings = get_settings()
        probes = [
            ("groq", groq_api_key or settings.groq_api_key, None),
            ("openrouter", openrouter_api_key or settings.openrouter_api_key, None),
            ("opencode", opencode_api_key or settings.opencode_api_key, None),
            (
                "openai_compat",
                openai_api_key or settings.openai_compatible_api_key,
                settings.openai_compatible_base_url,
            ),
        ]
        configured = [probe for probe in probes if probe[1]]
        if not configured:
            raise HTTPException(
                status_code=400,
                detail="Add at least one AI provider key before testing Auto mode.",
            )

        connected: list[str] = []
        last_error: HTTPException | None = None
        for probe_provider, probe_key, probe_url in configured:
            try:
                model = await _probe_provider_connection(probe_provider, probe_key, probe_url)
                connected.append(
                    f"{probe_provider.replace('_compat', '').upper()} ({model})"
                )
            except HTTPException as exc:
                last_error = exc
        if connected:
            return {
                "status": "ok",
                "provider": provider,
                "message": (
                    f"Automatic failover is ready across {', '.join(connected)}. "
                    "Each connection completed a minimal live response."
                ),
            }
        raise last_error or HTTPException(
            status_code=400,
            detail="No configured AI provider accepted its connection test.",
        )

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
        _, _, base_url_override = _llm_options(body)
    elif provider == "ollama":
        _, _, base_url_override = _llm_options(body)

    # Require explicit API key for providers that require authentication
    key_required_providers = ("groq", "openrouter", "opencode", "openai", "openai_compat", "custom")
    settings = get_settings()

    _validate_runtime_provider_url(base_url_override)

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
            api_keys=_provider_keys(body),
            base_url_override=base_url_override,
            allow_mock_fallback=False,
        )
        if provider in key_required_providers and not llm.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid API key or endpoint for {provider.upper()}.",
            )

        if provider != "mock":
            verified_model = await _probe_provider_connection(
                provider=provider,
                api_key=effective_key if provider in key_required_providers else api_key_override,
                base_url=base_url_override,
            )
        else:
            verified_model = llm.model_id

        return {
            "status": "ok",
            "provider": provider,
            "message": (
                "The deterministic baseline is ready; no external AI provider was contacted."
                if provider == "mock"
                else f"Connected to {provider.upper()} successfully using {verified_model}."
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "Provider verification failed for %s: %s",
            provider,
            redact_sensitive_text(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=public_provider_error(exc),
        ) from None


@router.post("/analyses", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_endpoint(
    body: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    owner_hash: str = Depends(require_owner_hash),
) -> dict:
    """Start a new analysis. Returns immediately with analysis_id; poll GET /analyses/{id}."""
    provider = _validate_selected_provider(body)
    analysis_id = await create_analysis(
        idea=body.idea,
        ai_provider_override=provider,
        research_providers_override=body.research_providers,
        is_demo=False,
        owner_hash=owner_hash,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=body.idea,
        ai_provider_override=provider,
        openrouter_api_key=_secret_value(body.openrouter_api_key),
        groq_api_key=_secret_value(body.groq_api_key),
        opencode_api_key=_secret_value(body.opencode_api_key),
        openai_api_key=_secret_value(body.openai_api_key),
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
    owner_hash: str,
) -> AnalysisResult:
    """Complete an analysis within one request for serverless production hosts."""
    analysis_id = await create_analysis(
        idea=idea,
        ai_provider_override=provider,
        research_providers_override=body.research_providers,
        is_demo=False,
        owner_hash=owner_hash,
    )
    await run_analysis(
        analysis_id=analysis_id,
        idea=idea,
        ai_provider_override=provider,
        openrouter_api_key=_secret_value(body.openrouter_api_key),
        groq_api_key=_secret_value(body.groq_api_key),
        opencode_api_key=_secret_value(body.opencode_api_key),
        openai_api_key=_secret_value(body.openai_api_key),
        custom_base_url=body.custom_base_url,
        ollama_base_url=body.ollama_base_url,
        research_providers_override=body.research_providers,
        research_depth=body.research_depth,
        is_demo=False,
    )
    result = await get_analysis(analysis_id, owner_hash=owner_hash)
    if result is None:
        raise HTTPException(
            status_code=500,
            detail="The analysis finished without a readable report. Please try again.",
        )
    return result


@router.post("/analyses/sync", response_model=AnalysisResult)
async def create_analysis_sync_endpoint(
    body: AnalysisCreateRequest,
    owner_hash: str = Depends(require_owner_hash),
) -> AnalysisResult:
    """Run a real AI analysis synchronously so the host cannot drop background work."""
    provider = _validate_selected_provider(body)
    return await _run_analysis_in_request(body, body.idea, provider, owner_hash)


@router.post("/analyses/from-prompt", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_from_prompt_endpoint(
    body: PromptAnalysisRequest,
    background_tasks: BackgroundTasks,
    owner_hash: str = Depends(require_owner_hash),
) -> dict:
    """Analyze a startup idea from a single freeform text prompt."""

    provider, api_key_override, base_url_override = _llm_options(body)

    _validate_runtime_provider_url(base_url_override)

    try:
        llm = build_llm_adapter(
            provider_override=provider,
            api_key_override=api_key_override,
            api_keys=_provider_keys(body),
            base_url_override=base_url_override,
        )
        parsed_idea = await llm.parse_raw_prompt(body.prompt)
    except ValueError as exc:
        logger.info("Prompt validation failed: %s", redact_sensitive_text(exc))
        raise HTTPException(
            status_code=400,
            detail="The startup idea could not be parsed. Add the customer, problem, and solution.",
        ) from None
    except RuntimeError as exc:
        logger.warning("Prompt provider unavailable: %s", redact_sensitive_text(exc))
        raise HTTPException(
            status_code=public_provider_status(exc),
            detail=public_provider_error(exc),
        ) from None
    except Exception as exc:
        logger.error("Prompt parsing failed: %s", redact_sensitive_text(exc))
        raise HTTPException(
            status_code=500,
            detail="The startup idea could not be parsed. Try the structured form instead.",
        ) from None

    analysis_id = await create_analysis(
        idea=parsed_idea,
        ai_provider_override=provider,
        research_providers_override=body.research_providers,
        is_demo=False,
        owner_hash=owner_hash,
    )
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        idea=parsed_idea,
        ai_provider_override=provider,
        openrouter_api_key=_secret_value(body.openrouter_api_key),
        groq_api_key=_secret_value(body.groq_api_key),
        opencode_api_key=_secret_value(body.opencode_api_key),
        openai_api_key=_secret_value(body.openai_api_key),
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
    owner_hash: str = Depends(require_owner_hash),
) -> AnalysisResult:
    """Parse a prompt with real AI, then return the completed analysis."""
    provider, api_key_override, base_url_override = _llm_options(body)
    _validate_runtime_provider_url(base_url_override)
    try:
        llm = build_llm_adapter(
            provider_override=provider,
            api_key_override=api_key_override,
            api_keys=_provider_keys(body),
            base_url_override=base_url_override,
            allow_mock_fallback=False,
        )
        parsed_idea = await llm.parse_raw_prompt(body.prompt)
    except ValueError as exc:
        logger.info("Prompt validation failed: %s", redact_sensitive_text(exc))
        raise HTTPException(
            status_code=400,
            detail="The startup idea could not be parsed. Add the customer, problem, and solution.",
        ) from None
    except RuntimeError as exc:
        logger.warning("Prompt provider unavailable: %s", redact_sensitive_text(exc))
        raise HTTPException(
            status_code=public_provider_status(exc),
            detail=public_provider_error(exc),
        ) from None
    except Exception as exc:
        logger.error("Prompt parsing failed: %s", redact_sensitive_text(exc))
        raise HTTPException(
            status_code=502,
            detail="The selected AI provider could not process this prompt. Verify the key and try again.",
        ) from None
    return await _run_analysis_in_request(body, parsed_idea, provider, owner_hash)


def _stream_analysis(body: AnalysisCreateRequest | PromptAnalysisRequest, owner_hash: str):
    provider = _validate_selected_provider(body)

    async def events():
        started = time.monotonic()
        queue: asyncio.Queue[dict] = asyncio.Queue()

        async def progress(stage, description):
            await queue.put({"type": "progress", "stage": getattr(stage, "value", stage),
                             "description": description})

        async def work():
            try:
                async with asyncio.timeout(ANALYSIS_DEADLINE_SECONDS):
                    if isinstance(body, PromptAnalysisRequest):
                        await progress("parsing_idea", "Understanding your idea")
                        _, key, base = _llm_options(body)
                        llm = build_llm_adapter(provider_override=provider, api_key_override=key,
                                                api_keys=_provider_keys(body), base_url_override=base,
                                                allow_mock_fallback=False)
                        idea = await llm.parse_raw_prompt(body.prompt)
                    else:
                        idea = body.idea
                    analysis_id = await create_analysis(idea=idea, owner_hash=owner_hash)
                    result = await run_analysis(
                        analysis_id=analysis_id, idea=idea, ai_provider_override=provider,
                        openrouter_api_key=_secret_value(body.openrouter_api_key),
                        groq_api_key=_secret_value(body.groq_api_key),
                        opencode_api_key=_secret_value(body.opencode_api_key),
                        openai_api_key=_secret_value(body.openai_api_key),
                        custom_base_url=body.custom_base_url, ollama_base_url=body.ollama_base_url,
                        research_providers_override=body.research_providers,
                        research_depth=body.research_depth, progress_callback=progress,
                    )
                    if result.status == "failed":
                        await queue.put({"type": "error", "message": result.error_message})
                    else:
                        await queue.put({"type": "result", "result": result.model_dump(mode="json")})
            except TimeoutError:
                logger.warning("Analysis request exceeded its deadline")
                await queue.put({"type": "error", "message":
                                 "Analysis exceeded four minutes. Try Standard research or another provider."})
            except Exception as exc:
                logger.warning("Analysis stream failed: %s", redact_sensitive_text(exc))
                await queue.put({"type": "error", "message": public_provider_error(exc)})

        worker = asyncio.create_task(work())
        try:
            yield json.dumps({"type": "progress", "stage": "starting_analysis",
                              "description": "Starting your analysis", "elapsed_seconds": 0}) + "\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except TimeoutError:
                    event = {"type": "heartbeat"}
                event["elapsed_seconds"] = round(time.monotonic() - started, 1)
                yield json.dumps(event) + "\n"
                if event["type"] in {"result", "error"}:
                    break
        finally:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

    return StreamingResponse(events(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@router.post("/analyses/stream")
async def stream_structured_analysis(
    body: AnalysisCreateRequest, owner_hash: str = Depends(require_owner_hash),
):
    return _stream_analysis(body, owner_hash)


@router.post("/analyses/from-prompt/stream")
async def stream_prompt_analysis(
    body: PromptAnalysisRequest, owner_hash: str = Depends(require_owner_hash),
):
    return _stream_analysis(body, owner_hash)


@router.get("/analyses", response_model=list[AnalysisListItem])
async def list_analyses_endpoint(
    search: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=100),
    owner_hash: str = Depends(require_owner_hash),
) -> list[AnalysisListItem]:
    return await list_analyses(
        search=search,
        status_filter=status,
        limit=limit,
        owner_hash=owner_hash,
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_endpoint(
    analysis_id: str,
    owner_hash: str = Depends(require_owner_hash),
) -> AnalysisResult:
    result = await get_analysis(analysis_id, owner_hash=owner_hash)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_endpoint(
    analysis_id: str,
    owner_hash: str = Depends(require_owner_hash),
) -> None:
    deleted = await delete_analysis(analysis_id, owner_hash=owner_hash)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")


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
