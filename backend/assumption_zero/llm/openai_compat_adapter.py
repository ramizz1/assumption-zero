"""
OpenAI-compatible adapter.

Works with any API following the OpenAI Chat Completions spec:
  - OpenAI (gpt-4o, gpt-4o-mini)
  - Together AI
  - Groq
  - Anyscale
  - vLLM self-hosted
  - LM Studio
  - and many others

Configure:
  AI_PROVIDER=openai_compat
  OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
  OPENAI_COMPATIBLE_API_KEY=your-key
  OPENAI_COMPATIBLE_MODEL=gpt-4o-mini
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from assumption_zero.config import get_settings
from assumption_zero.llm.base import (
    PERSPECTIVE_SYSTEM_PROMPTS,
    LLMAdapter,
    PerspectiveOutput,
    build_analysis_prompt,
    build_clarification_messages,
)
from assumption_zero.llm.model_catalog import catalog_model_ids, completion_content, ordered_models
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName, Recommendation

logger = logging.getLogger(__name__)

_VALID_RECOMMENDATIONS = {r.value for r in Recommendation}
_PREFERRED_CHAT_MODELS = (
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-4o",
    "deepseek-chat",
    "mistral-small-latest",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
)


def _parse_output(raw: str, perspective_name: PerspectiveName, model_id: str) -> PerspectiveOutput:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        text = text.removeprefix("json")
        text = text.rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            raise ValueError(f"OpenAI-compat response is not JSON: {text[:200]}")

    rec = data.get("recommendation", "Test First")
    if rec not in _VALID_RECOMMENDATIONS:
        rec = "Test First"

    return PerspectiveOutput(
        perspective_name=perspective_name,
        model_id=model_id,
        summary=data.get("summary", ""),
        key_findings=data.get("key_findings", []),
        risks=data.get("risks", []),
        opportunities=data.get("opportunities", []),
        recommendation=Recommendation(rec),
        dimension_scores=data.get("dimension_scores", {}),
        cited_evidence_ids=data.get("cited_evidence_ids", []),
        competitors=data.get("competitors", []),
        most_dangerous_assumption=data.get("most_dangerous_assumption", ""),
        reasoning=data.get("reasoning", ""),
    )


class OpenAICompatAdapter(LLMAdapter):
    """OpenAI Chat Completions-compatible adapter.

    Works with: OpenAI (ChatGPT), Anthropic (via proxy), Together AI,
    Anyscale, LM Studio, vLLM, and any OpenAI-spec endpoint.

    Configure via .env or pass at runtime via CLI flags:
      OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
      OPENAI_COMPATIBLE_API_KEY=sk-...
      OPENAI_COMPATIBLE_MODEL=gpt-4o-mini
    """

    # Well-known provider base URLs for convenience
    KNOWN_PROVIDERS: dict = {
        "openai": "https://api.openai.com/v1",
        "together": "https://api.together.xyz/v1",
        "anyscale": "https://api.endpoints.anyscale.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "mistral": "https://api.mistral.ai/v1",
        "cohere": "https://api.cohere.ai/compatibility/v1",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ) -> None:
        import os

        self._settings = get_settings()
        self._base_url = (
            base_url
            or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
            or self._settings.openai_compatible_base_url
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self._api_key = (
            api_key
            or os.environ.get("OPENAI_COMPATIBLE_API_KEY")
            or self._settings.openai_compatible_api_key
            or ""
        ).strip()
        self._model = (
            model
            or os.environ.get("OPENAI_COMPATIBLE_MODEL")
            or self._settings.openai_compatible_model
            or "auto"
        )

    async def _models(self, client: httpx.AsyncClient) -> list[str]:
        discovered: list[str] = []
        try:
            response = await client.get(f"{self._base_url}/models")
            if response.status_code == 401:
                raise RuntimeError("AI provider rejected the API key (HTTP 401).")
            if response.status_code == 200:
                discovered = catalog_model_ids(response.json())
        except RuntimeError:
            raise
        except Exception as exc:
            logger.info(
                "OpenAI-compatible model discovery unavailable (%s); using configured fallbacks",
                type(exc).__name__,
            )

        models = ordered_models(
            discovered,
            configured=None if self._model.casefold() == "auto" else self._model,
            preferred=_PREFERRED_CHAT_MODELS,
        )
        # Bound retries for catalogs that contain hundreds of historical models.
        return (models or list(_PREFERRED_CHAT_MODELS))[:12]

    @property
    def model_id(self) -> str:
        return f"openai-compat/{self._model}"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key and self._base_url)

    def _headers(self) -> dict:
        if not self._api_key:
            raise RuntimeError(
                "No API key set for openai_compat provider. "
                "Set OPENAI_COMPATIBLE_API_KEY in .env or pass --api-key on the CLI."
            )
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
    ) -> tuple[str, str]:
        url = f"{self._base_url}/chat/completions"
        last_status: int | None = None
        async with httpx.AsyncClient(
            timeout=max(60.0, float(self._settings.request_timeout)),
            headers=self._headers(),
        ) as client:
            models_to_try = await self._models(client)
            for model_name in models_to_try:
                payload: dict[str, Any] = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.3,
                }
                # JSON mode is useful for analysis, but only send it to OpenAI's
                # own endpoint where support is known.
                if json_mode and "api.openai.com" in self._base_url:
                    payload["response_format"] = {"type": "json_object"}
                try:
                    resp = await client.post(url, json=payload)
                except Exception as exc:
                    logger.info(
                        "OpenAI-compatible request transport failed (%s)", type(exc).__name__
                    )
                    continue
                last_status = resp.status_code
                if resp.status_code == 401:
                    raise RuntimeError("AI provider rejected the API key (HTTP 401).")
                if resp.status_code >= 400:
                    logger.info(
                        "OpenAI-compatible model %s unavailable (HTTP %s); trying next model",
                        model_name,
                        resp.status_code,
                    )
                    continue
                data = resp.json()
                content = completion_content(data)
                if content:
                    actual_model = str(data.get("model") or model_name)
                    logger.info("OpenAI-compatible provider selected model %s", actual_model)
                    return content, actual_model

        if last_status in (402, 429):
            raise RuntimeError(f"AI provider quota or rate limit exceeded (HTTP {last_status}).")
        if last_status and last_status >= 400:
            raise RuntimeError(f"AI provider request failed (HTTP {last_status}).")
        raise RuntimeError("AI provider returned an empty response.")

    async def verify_connection(self) -> str:
        _, model = await self._chat([{"role": "user", "content": "Reply with OK only."}])
        return model

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: list[EvidenceItem],
    ) -> PerspectiveOutput:
        messages = [
            {"role": "system", "content": PERSPECTIVE_SYSTEM_PROMPTS[perspective_name]},
            {
                "role": "user",
                "content": build_analysis_prompt(perspective_name.value, idea, evidence),
            },
        ]
        try:
            raw, actual_model = await self._chat(messages, json_mode=True)
        except Exception as exc:
            logger.error("OpenAI-compat API error for %s: %s", perspective_name.value, exc)
            raise

        try:
            return _parse_output(raw, perspective_name, f"openai-compat/{actual_model}")
        except Exception as exc:
            raise ValueError(f"OpenAI-compat returned unparseable output: {exc}") from exc

    async def clarify_idea(self, idea: IdeaInput) -> str:
        try:
            raw, _ = await self._chat(build_clarification_messages(idea))
            return raw.strip()
        except Exception as exc:
            logger.warning("OpenAI-compat clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"
