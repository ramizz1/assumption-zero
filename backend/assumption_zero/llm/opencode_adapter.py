"""
OpenCode LLM adapter — connect to OpenCode AI API.

https://opencode.ai
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from assumption_zero.config import get_settings
from assumption_zero.llm.base import (
    PERSPECTIVE_SYSTEM_PROMPTS,
    UNTRUSTED_CONTENT_RULES,
    LLMAdapter,
    PerspectiveOutput,
    build_analysis_prompt,
    build_clarification_messages,
    build_raw_idea_message,
)
from assumption_zero.llm.model_catalog import catalog_model_ids, completion_content, ordered_models
from assumption_zero.llm.openrouter_adapter import _parse_output, _repair_and_parse_json
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://opencode.ai/zen/v1"
_LEGACY_BASE_URLS = {
    "https://opencode.ai/api/v1",
}
_DEFAULT_MODEL = "auto"
_PREFERRED_CHAT_MODELS = [
    "nemotron-3-ultra-free",
    "nemotron-3.5-lightning-free",
    "mimo-v2.5-free",
    "ling-3.0-flash-fin-free",
    "big-pickle",
]


def _is_opencode_chat_model(model_id: str) -> bool:
    """Keep models served by Zen's OpenAI-compatible chat endpoint."""
    normalized = model_id.casefold()
    return normalized == "big-pickle" or normalized.endswith("-free") or normalized.startswith(
        ("deepseek-", "glm-", "kimi-", "minimax-")
    )


class OpencodeAdapter(LLMAdapter):
    """
    Adapter for OpenCode AI API endpoint.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ) -> None:
        self._settings = get_settings()
        self._api_key_override = api_key
        self._model_override = model
        self._base_url_override = base_url

    def _api_key(self) -> str:
        key = (
            self._api_key_override
            or os.getenv("OPENCODE_API_KEY")
            or getattr(self._settings, "opencode_api_key", None)
            or ""
        )
        return key.strip()

    def _base_url(self) -> str:
        url = (
            self._base_url_override
            or os.getenv("OPENCODE_BASE_URL")
            or getattr(self._settings, "opencode_base_url", None)
            or _DEFAULT_BASE_URL
        )
        normalized = url.rstrip("/")
        # Existing deployments may still carry the old documented URL in an
        # environment variable. Migrate it in memory so a new key works now.
        return _DEFAULT_BASE_URL if normalized in _LEGACY_BASE_URLS else normalized

    def _model(self) -> str:
        return (
            self._model_override
            or os.getenv("OPENCODE_MODEL")
            or getattr(self._settings, "opencode_model", None)
            or _DEFAULT_MODEL
        )

    async def _models(self, client: httpx.AsyncClient) -> list[str]:
        discovered: list[str] = []
        try:
            response = await client.get(f"{self._base_url()}/models")
            if response.status_code == 401:
                raise RuntimeError("AI provider rejected the API key (HTTP 401).")
            if response.status_code == 200:
                discovered = catalog_model_ids(response.json())
        except RuntimeError:
            raise
        except Exception as exc:
            logger.info(
                "OpenCode model discovery unavailable (%s); using safe fallbacks",
                type(exc).__name__,
            )

        configured = self._model()
        models = ordered_models(
            discovered,
            configured=None if configured.casefold() == "auto" else configured,
            preferred=_PREFERRED_CHAT_MODELS,
            compatible=_is_opencode_chat_model,
        )
        return models or list(_PREFERRED_CHAT_MODELS)

    @property
    def model_id(self) -> str:
        return f"opencode/{self._model()}"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key())

    def _headers(self) -> dict[str, str]:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError(
                "OpenCode API key is missing. Set OPENCODE_API_KEY in your .env file or environment."
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _chat(self, messages: list[dict[str, str]]) -> tuple[str, str]:
        base = self._base_url()
        url = f"{base}/chat/completions"
        timeout = max(60.0, float(self._settings.request_timeout))
        last_status: int | None = None

        async with httpx.AsyncClient(timeout=timeout, headers=self._headers()) as client:
            models_to_try = await self._models(client)
            for model_name in models_to_try:
                payload: dict[str, Any] = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.2,
                }
                try:
                    resp = await client.post(url, json=payload)
                except Exception as exc:
                    logger.info("OpenCode request transport failed (%s)", type(exc).__name__)
                    continue
                last_status = resp.status_code
                if resp.status_code == 401:
                    raise RuntimeError("AI provider rejected the API key (HTTP 401).")
                if resp.status_code >= 400:
                    logger.info(
                        "OpenCode model %s unavailable (HTTP %s); trying next model",
                        model_name,
                        resp.status_code,
                    )
                    continue
                data = resp.json()
                content = completion_content(data)
                if content:
                    actual_model = str(data.get("model") or model_name)
                    logger.info("OpenCode selected model %s", actual_model)
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
        raw, actual_model = await self._chat(messages)
        return _parse_output(raw, perspective_name, f"opencode/{actual_model}")

    async def clarify_idea(self, idea: IdeaInput) -> str:
        try:
            raw, _ = await self._chat(build_clarification_messages(idea))
            return raw.strip()
        except Exception as exc:
            logger.debug("OpenCode clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        """Parse freeform prompt text into structured IdeaInput using OpenCode AI."""
        from assumption_zero.schemas import is_gibberish

        if is_gibberish(raw_text):
            raise ValueError(
                "The input text appears to be random characters or gibberish. Please enter a valid product or business idea."
            )
        system_prompt = (
            f"{UNTRUSTED_CONTENT_RULES}\n\n"
            "Convert the untrusted startup-idea data into a JSON object matching this schema EXACTLY:\n"
            "{\n"
            '  "name": "Short product name (max 5 words)",\n'
            '  "description": "1 sentence description",\n'
            '  "problem": "Clear problem statement",\n'
            '  "target_customer": "Target audience",\n'
            '  "geography": "Geographic target, e.g. global or specific country",\n'
            '  "business_model": "Monetization model or null",\n'
            '  "price": "Pricing details if mentioned or null",\n'
            '  "founder_skills": "Skills if mentioned or null",\n'
            '  "budget": "Budget if mentioned or null",\n'
            '  "known_competitors": "Competitors if mentioned or null",\n'
            '  "unfair_advantage": "Moat if mentioned or null",\n'
            '  "key_assumptions": "Core assumption if mentioned or null"\n'
            "}\n"
            "Output ONLY valid JSON."
        )

        try:
            raw_response, _ = await self._chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": build_raw_idea_message(raw_text)},
            ])
            parsed_data = _repair_and_parse_json(raw_response)
            parsed_data["name"] = parsed_data.get("name") or "New Idea"
            parsed_data["description"] = parsed_data.get("description") or raw_text[:200]
            parsed_data["problem"] = parsed_data.get("problem") or raw_text[:300]
            parsed_data["target_customer"] = parsed_data.get("target_customer") or "Target users"
            parsed_data["geography"] = parsed_data.get("geography") or "global"
            parsed_data["additional_context"] = raw_text

            return IdeaInput(**parsed_data)
        except Exception as exc:
            logger.debug("OpenCode parse_raw_prompt failed (%s) — using fallback extractor", exc)
            return await super().parse_raw_prompt(raw_text)
