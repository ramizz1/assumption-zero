"""
Ollama adapter for local models.

Configure:
  AI_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.2

Install Ollama: https://ollama.ai
Pull a model: ollama pull llama3.2
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
            raise ValueError(f"Ollama response is not valid JSON: {text[:200]}")

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


class OllamaAdapter(LLMAdapter):
    """Local model inference via Ollama API."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def model_id(self) -> str:
        return f"ollama/{self._settings.ollama_model}"

    @property
    def is_available(self) -> bool:
        return bool(self._settings.ollama_base_url)

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        url = f"{self._settings.ollama_base_url.rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": self._settings.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

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
            logger.error("Ollama API error for %s: %s", perspective_name.value, exc)
            raise

        try:
            return _parse_output(raw, perspective_name, self.model_id)
        except Exception as exc:
            logger.error("Ollama output parse failed: %s\nRaw: %.300s", exc, raw)
            raise ValueError(f"Ollama returned unparseable output: {exc}") from exc

    async def clarify_idea(self, idea: IdeaInput) -> str:
        prompt = (
            f"Describe in 2-3 sentences what this startup idea is evaluating. Be factual.\n"
            f"Name: {idea.name}\nDescription: {idea.description}\n"
            f"Problem: {idea.problem}\nCustomer: {idea.target_customer}"
        )
        try:
            raw = await self._chat([{"role": "user", "content": prompt}])
            return raw.strip()
        except Exception as exc:
            logger.warning("Ollama clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"
