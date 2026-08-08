"""
OpenCode LLM adapter — connect to OpenCode AI API.

https://opencode.ai
"""
from __future__ import annotations

import os
import json
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

_DEFAULT_BASE_URL = "https://opencode.ai/api/v1"
_DEFAULT_MODEL = "opencode/claude-3.5-sonnet"


class OpencodeAdapter(LLMAdapter):
    """
    Adapter for OpenCode AI API endpoint.
    """

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None, **kwargs) -> None:
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
        return url.rstrip("/")

    def _model(self) -> str:
        return (
            self._model_override
            or os.getenv("OPENCODE_MODEL")
            or getattr(self._settings, "opencode_model", None)
            or _DEFAULT_MODEL
        )

    @property
    def model_id(self) -> str:
        return f"opencode/{self._model()}"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key())

    def _headers(self) -> Dict[str, str]:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError(
                "OpenCode API key is missing. Set OPENCODE_API_KEY in your .env file or environment."
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        base = self._base_url()
        url = f"{base}/chat/completions"
        model_name = self._model()
        timeout = max(60.0, float(self._settings.request_timeout))

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=timeout, headers=self._headers()) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        if content:
                            return content
                elif resp.status_code == 401:
                    raise RuntimeError(
                        "OpenCode API key is invalid or unauthorized (HTTP 401). "
                        "Please check your OPENCODE_API_KEY setting."
                    )
                else:
                    resp.raise_for_status()
            except RuntimeError:
                raise
            except Exception as exc:
                logger.error("OpenCode API error for %s: %s", model_name, exc)
                raise RuntimeError(f"OpenCode API request failed: {exc}") from exc

        raise RuntimeError("OpenCode API returned empty content")

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
            logger.debug("OpenCode parse_raw_prompt failed (%s) — using fallback extractor", exc)
            return await super().parse_raw_prompt(raw_text)
