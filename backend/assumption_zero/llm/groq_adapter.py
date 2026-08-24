"""
Groq LLM adapter — ultra-fast Llama 3.3 inference.

Groq provides 200,000 tokens/day on its free tier.
https://console.groq.com/keys
"""

from __future__ import annotations

import asyncio
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
from assumption_zero.llm.openrouter_adapter import _parse_output, _repair_and_parse_json
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName

logger = logging.getLogger(__name__)

_GROQ_BASE = "https://api.groq.com/openai/v1"
_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
]


class GroqAdapter(LLMAdapter):
    """
    Groq adapter for ultra-fast Llama 3.3 inference.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None, **kwargs) -> None:
        self._settings = get_settings()
        self._api_key_override = api_key
        self._model_override = model
        self._request_slots = asyncio.Semaphore(2)

    def _api_key(self) -> str:
        key = (
            self._api_key_override or os.getenv("GROQ_API_KEY") or self._settings.groq_api_key or ""
        )
        return key.strip()

    def _model(self) -> str:
        return self._model_override or self._settings.groq_model or _DEFAULT_MODEL

    @property
    def model_id(self) -> str:
        return f"groq/{self._model()}"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key())

    def _headers(self) -> dict[str, str]:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError(
                "Groq API key is missing. Please set GROQ_API_KEY in your .env file or get a free key at https://console.groq.com/keys"
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _chat(self, messages: list[dict[str, str]]) -> tuple[str, str]:
        url = f"{_GROQ_BASE}/chat/completions"
        primary = self._model()
        models_to_try = [primary] + [m for m in _FALLBACK_MODELS if m != primary]

        last_error: Exception | None = None
        timeout = max(30.0, float(self._settings.request_timeout))

        async with self._request_slots:
            async with httpx.AsyncClient(
                timeout=timeout,
                headers=self._headers(),
            ) as client:
                for model_name in models_to_try:
                    payload: dict[str, Any] = {
                        "model": model_name,
                        "messages": messages,
                        "temperature": 0.2,
                    }
                    try:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                content = data["choices"][0]["message"]["content"]
                                if content:
                                    return content, str(data.get("model") or model_name)
                            if "error" in data:
                                err_msg = data["error"].get("message", str(data["error"]))
                                logger.debug("Groq model %s error payload: %s", model_name, err_msg)
                                last_error = RuntimeError(
                                    f"Groq model {model_name} error: {err_msg}"
                                )
                                continue
                        elif resp.status_code == 401:
                            raise RuntimeError(
                                "Groq API key is invalid or unauthorized (HTTP 401). "
                                "Please check your GROQ_API_KEY at https://console.groq.com/keys"
                            )
                        elif resp.status_code in (402, 429):
                            logger.debug(
                                "Groq model %s rate limited (HTTP %s) — trying fallback model...",
                                model_name,
                                resp.status_code,
                            )
                            last_error = RuntimeError(
                                f"Groq API quota or rate limit exceeded on {model_name} "
                                f"(HTTP {resp.status_code})."
                            )
                            continue
                        else:
                            error_msg = f"HTTP {resp.status_code} for {model_name}"
                            logger.debug("Groq model %s failed: %s", model_name, error_msg)
                            last_error = RuntimeError(error_msg)
                    except RuntimeError:
                        raise
                    except Exception as exc:
                        logger.debug("Groq model %s exception: %s", model_name, exc)
                        last_error = exc

        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")

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
        return _parse_output(raw, perspective_name, f"groq/{actual_model}")

    async def clarify_idea(self, idea: IdeaInput) -> str:
        try:
            raw, _ = await self._chat(build_clarification_messages(idea))
            return raw.strip()
        except Exception as exc:
            logger.debug("Groq clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        """Parse freeform prompt text into structured IdeaInput using Groq LLM."""
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
            logger.debug("Groq parse_raw_prompt failed (%s) — using fallback extractor", exc)
            return await super().parse_raw_prompt(raw_text)
