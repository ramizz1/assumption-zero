"""
OpenRouter LLM adapter.

OpenRouter provides access to 200+ models via a single OpenAI-compatible API.
https://openrouter.ai

By default this adapter uses the built-in Assumption Zero Beta key.
Users can override with their own OPENROUTER_API_KEY in .env.

Configure (optional — works out of the box):
  AI_PROVIDER=openrouter
  OPENROUTER_API_KEY=sk-or-v1-...        # optional override
  OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
"""
from __future__ import annotations

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
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName, Recommendation

logger = logging.getLogger(__name__)

_VALID_RECOMMENDATIONS = {r.value for r in Recommendation}

# Default built-in key — allows zero-config usage
_BUILTIN_OPENROUTER_KEY = "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"
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


def _parse_output(raw: str, perspective_name: PerspectiveName, model_id: str) -> PerspectiveOutput:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            raise ValueError(f"OpenRouter response is not JSON: {text[:200]}")

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
        most_dangerous_assumption=data.get("most_dangerous_assumption", ""),
        reasoning=data.get("reasoning", ""),
    )


class OpenRouterAdapter(LLMAdapter):
    """
    OpenRouter adapter.

    Uses a built-in community key by default so the app works without any
    configuration. Users can set OPENROUTER_API_KEY to use their own key.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def _api_key(self) -> str:
        return self._settings.openrouter_api_key or _BUILTIN_OPENROUTER_KEY

    def _model(self) -> str:
        return self._settings.openrouter_model or _DEFAULT_MODEL

    @property
    def model_id(self) -> str:
        return f"openrouter/{self._model()}"

    @property
    def is_available(self) -> bool:
        # Always available — built-in key is always present
        return True

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://assumption-zero.dev",
            "X-Title": "Assumption Zero",
        }

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        url = f"{_OPENROUTER_BASE}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self._model(),
            "messages": messages,
            "temperature": 0.3,
        }
        async with httpx.AsyncClient(
            timeout=self._settings.request_timeout,
            headers=self._headers(),
        ) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content

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
        try:
            raw = await self._chat(messages)
        except Exception as exc:
            logger.error("OpenRouter API error for %s: %s", perspective_name.value, exc)
            raise

        try:
            return _parse_output(raw, perspective_name, self.model_id)
        except Exception as exc:
            raise ValueError(f"OpenRouter returned unparseable output: {exc}") from exc

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
            logger.warning("OpenRouter clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"
