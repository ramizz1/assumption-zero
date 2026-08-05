"""
OpenRouter LLM adapter.

OpenRouter provides access to 200+ models via a single OpenAI-compatible API.
https://openrouter.ai

By default this adapter uses the built-in Assumption Zero Beta key.
Users can override with their own OPENROUTER_API_KEY in .env.
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

# Built-in community key for zero-config out-of-the-box usage
_BUILTIN_OPENROUTER_KEY = "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"
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Primary default model & fallback list of verified free models on OpenRouter
_DEFAULT_MODEL = "google/gemma-4-26b-a4b-it:free"
_FALLBACK_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "openai/gpt-oss-20b:free",
    "inclusionai/ling-3.0-flash:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "poolside/laguna-xs-2.1:free",
]


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
            raise ValueError(f"OpenRouter response is not valid JSON: {text[:200]}")

    rec = data.get("recommendation", "Test First")
    if rec not in _VALID_RECOMMENDATIONS:
        rec = "Test First"

    return PerspectiveOutput(
        perspective_name=perspective_name,
        model_id=model_id,
        summary=data.get("summary", "Analysis completed."),
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

    Uses built-in key and automatically tries active free models with fallback
    support if a model is unavailable.
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
                    "temperature": 0.3,
                }
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        return content
                    else:
                        error_msg = f"HTTP {resp.status_code} for {model_name}: {resp.text[:150]}"
                        logger.debug("OpenRouter model %s failed: %s", model_name, error_msg)
                        last_error = RuntimeError(error_msg)
                except Exception as exc:
                    logger.debug("OpenRouter model %s exception: %s", model_name, exc)
                    last_error = exc

        raise RuntimeError(f"All OpenRouter models failed. Last error: {last_error}")

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
