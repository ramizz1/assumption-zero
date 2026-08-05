"""
Groq LLM adapter — ultra-fast Llama 3.3 inference.

Groq provides 200,000 tokens/day on its free tier.
https://console.groq.com/keys
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List

import httpx

from assumption_zero.config import get_settings
from assumption_zero.llm.base import (
    PERSPECTIVE_SYSTEM_PROMPTS,
    LLMAdapter,
    PerspectiveOutput,
    build_analysis_prompt,
)
from assumption_zero.llm.openrouter_adapter import _parse_output, _repair_and_parse_json
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName

logger = logging.getLogger(__name__)

_GROQ_BASE = "https://api.groq.com/openai/v1"
_DEFAULT_MODEL = "openai/gpt-oss-120b"
_FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]


class GroqAdapter(LLMAdapter):
    """
    Groq adapter for ultra-fast Llama 3.3 inference.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def _api_key(self) -> str:
        key = (
            os.getenv("GROQ_API_KEY")
            or self._settings.groq_api_key
            or ""
        )
        return key.strip()

    def _model(self) -> str:
        return self._settings.groq_model or _DEFAULT_MODEL

    @property
    def model_id(self) -> str:
        return f"groq/{self._model()}"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key())

    def _headers(self) -> Dict[str, str]:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError(
                "Groq API key is missing. Please set GROQ_API_KEY in your .env file or get a free key at https://console.groq.com/keys"
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        url = f"{_GROQ_BASE}/chat/completions"
        primary = self._model()
        models_to_try = [primary] + [m for m in _FALLBACK_MODELS if m != primary]

        last_error = None
        timeout = max(30.0, float(self._settings.request_timeout))

        async with httpx.AsyncClient(
            timeout=timeout,
            headers=self._headers(),
        ) as client:
            for model_name in models_to_try:
                payload: Dict[str, Any] = {
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
                                return content
                        if "error" in data:
                            err_msg = data["error"].get("message", str(data["error"]))
                            logger.debug("Groq model %s error payload: %s", model_name, err_msg)
                            last_error = RuntimeError(f"Groq model {model_name} error: {err_msg}")
                            continue
                    elif resp.status_code == 401:
                        raise RuntimeError(
                            "Groq API key is invalid or unauthorized (HTTP 401). "
                            "Please check your GROQ_API_KEY at https://console.groq.com/keys"
                        )
                    elif resp.status_code in (402, 429):
                        logger.debug("Groq model %s rate limited (HTTP %s) — trying fallback model...", model_name, resp.status_code)
                        last_error = RuntimeError(
                            f"Groq API quota or rate limit exceeded on {model_name} (HTTP {resp.status_code}). "
                            "Please check your limit at https://console.groq.com"
                        )
                        continue
                    else:
                        error_msg = f"HTTP {resp.status_code} for {model_name}: {resp.text[:150]}"
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
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        messages = [
            {"role": "system", "content": PERSPECTIVE_SYSTEM_PROMPTS[perspective_name]},
            {"role": "user", "content": build_analysis_prompt(perspective_name.value, idea, evidence)},
        ]
        raw = await self._chat(messages)
        return _parse_output(raw, perspective_name, self.model_id)

    async def clarify_idea(self, idea: IdeaInput) -> str:
        prompt = (
            f"In 2-3 sentences describe what this startup idea is evaluating. Be concise and factual.\n"
            f"Name: {idea.name}\nDescription: {idea.description}\n"
            f"Problem: {idea.problem}\nCustomer: {idea.target_customer} in {idea.geography}"
        )
        try:
            raw = await self._chat([{"role": "user", "content": prompt}])
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
            "You are a startup analyst. Convert the user's raw idea text into a JSON object matching this schema EXACTLY:\n"
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
            raw_response = await self._chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this startup idea:\n{raw_text}"},
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
