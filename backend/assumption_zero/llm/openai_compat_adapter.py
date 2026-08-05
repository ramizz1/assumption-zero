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
        most_dangerous_assumption=data.get("most_dangerous_assumption", ""),
        reasoning=data.get("reasoning", ""),
    )


class OpenAICompatAdapter(LLMAdapter):
    """OpenAI Chat Completions-compatible adapter."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def model_id(self) -> str:
        return f"openai-compat/{self._settings.openai_compatible_model}"

    @property
    def is_available(self) -> bool:
        return bool(
            self._settings.openai_compatible_base_url
            and self._settings.openai_compatible_api_key
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.openai_compatible_api_key}",
            "Content-Type": "application/json",
        }

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        base = self._settings.openai_compatible_base_url.rstrip("/")
        url = f"{base}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self._settings.openai_compatible_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        }
        async with httpx.AsyncClient(
            timeout=self._settings.request_timeout,
            headers=self._headers(),
        ) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

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
            logger.error("OpenAI-compat API error for %s: %s", perspective_name.value, exc)
            raise

        try:
            return _parse_output(raw, perspective_name, self.model_id)
        except Exception as exc:
            raise ValueError(f"OpenAI-compat returned unparseable output: {exc}") from exc

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
            logger.warning("OpenAI-compat clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"
