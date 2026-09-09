"""
Ollama LLM adapter — run local models via Ollama.

Allows connecting to any local Ollama instance (http://localhost:11434).
Supports models like llama3.2, llama3.3, mistral, deepseek-r1, qwen2.5, phi3, etc.
"""

from __future__ import annotations

import logging
import os

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

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2"


class OllamaAdapter(LLMAdapter):
    """
    Adapter for local Ollama instances.
    Attempts OpenAI-compatible /v1/chat/completions endpoint first, falling back to /api/chat.
    """

    def __init__(self, model: str | None = None, base_url: str | None = None, **kwargs) -> None:
        self._settings = get_settings()
        self._model_override = model
        self._base_url_override = base_url

    def _base_url(self) -> str:
        url = (
            self._base_url_override
            or os.getenv("OLLAMA_BASE_URL")
            or self._settings.ollama_base_url
            or _DEFAULT_BASE_URL
        )
        return url.rstrip("/")

    def _model(self) -> str:
        return (
            self._model_override
            or os.getenv("OLLAMA_MODEL")
            or self._settings.ollama_model
            or _DEFAULT_MODEL
        )

    async def _models(self, client: httpx.AsyncClient) -> list[str]:
        base = self._base_url()
        discovered_with_size: list[tuple[str, int]] = []
        try:
            response = await client.get(f"{base}/api/tags")
            if response.status_code == 200:
                data = response.json()
                for item in data.get("models", []) if isinstance(data, dict) else []:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name") or item.get("model")
                    if isinstance(name, str) and name.strip():
                        discovered_with_size.append((name.strip(), int(item.get("size") or 0)))
        except Exception as exc:
            logger.info("Ollama model discovery via /api/tags failed (%s)", type(exc).__name__)

        if not discovered_with_size:
            try:
                response = await client.get(f"{base}/v1/models")
                if response.status_code == 200:
                    discovered_with_size = [
                        (model_id, 0) for model_id in catalog_model_ids(response.json())
                    ]
            except Exception as exc:
                logger.info("Ollama model discovery via /v1/models failed (%s)", type(exc).__name__)

        # Larger installed models are generally the strongest local choice. An
        # explicit model remains first and every other installed model is fallback.
        discovered = [
            name for name, _size in sorted(discovered_with_size, key=lambda item: item[1], reverse=True)
        ]
        configured = self._model()
        models = ordered_models(
            discovered,
            configured=None if configured.casefold() == "auto" else configured,
        )
        return models or [_DEFAULT_MODEL]

    @property
    def model_id(self) -> str:
        return f"ollama/{self._model()}"

    @property
    def is_available(self) -> bool:
        # Local Ollama is assumed available if base_url is set
        return bool(self._base_url())

    async def _chat(self, messages: list[dict[str, str]]) -> tuple[str, str]:
        base = self._base_url()
        timeout = max(90.0, float(self._settings.request_timeout))
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=timeout) as client:
            models_to_try = await self._models(client)
            for model_name in models_to_try:
                # Attempt 1: OpenAI-compatible endpoint available in modern Ollama.
                try:
                    resp = await client.post(
                        f"{base}/v1/chat/completions",
                        json={
                            "model": model_name,
                            "messages": messages,
                            "temperature": 0.2,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        content = completion_content(data)
                        if content:
                            actual_model = str(data.get("model") or model_name)
                            logger.info("Ollama selected model %s", actual_model)
                            return content, actual_model
                except Exception as exc:
                    last_error = exc

                # Attempt 2: Native Ollama endpoint.
                try:
                    resp = await client.post(
                        f"{base}/api/chat",
                        json={
                            "model": model_name,
                            "messages": messages,
                            "stream": False,
                            "options": {"temperature": 0.2},
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        message = data.get("message", {}) if isinstance(data, dict) else {}
                        content = message.get("content") if isinstance(message, dict) else None
                        if isinstance(content, str) and content.strip():
                            logger.info("Ollama selected model %s", model_name)
                            return content, model_name
                    last_error = RuntimeError(f"Ollama request failed (HTTP {resp.status_code}).")
                except Exception as exc:
                    last_error = exc
                logger.info("Ollama model %s could not answer; trying next installed model", model_name)

        raise RuntimeError(
            "Could not connect to Ollama or no installed text model could answer. "
            f"Ensure Ollama is running and at least one model is pulled. ({type(last_error).__name__})"
        )

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
        return _parse_output(raw, perspective_name, f"ollama/{actual_model}")

    async def clarify_idea(self, idea: IdeaInput) -> str:
        try:
            raw, _ = await self._chat(build_clarification_messages(idea))
            return raw.strip()
        except Exception as exc:
            logger.debug("Ollama clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        """Parse freeform prompt text into structured IdeaInput using local Ollama model."""
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
        except (RuntimeError, httpx.HTTPError):
            raise
        except Exception as exc:
            logger.debug("Ollama prompt structure unusable (%s); extracting supplied fields", type(exc).__name__)
            return await super().parse_raw_prompt(raw_text)
