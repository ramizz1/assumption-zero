"""
Google Gemini LLM adapter using the official google-generativeai SDK.

Configure:
  AI_PROVIDER=gemini
  GEMINI_API_KEY=your-key
  GEMINI_MODEL=gemini-1.5-flash   # or gemini-1.5-pro

Get a free API key at https://aistudio.google.com/app/apikey
"""
from __future__ import annotations

import json
import logging
from typing import List

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
    """Parse Gemini JSON response with one repair attempt."""
    # Strip markdown fences if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Repair attempt: find first { and last }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            raise ValueError(f"Cannot parse Gemini response as JSON: {text[:200]}")

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


class GeminiAdapter(LLMAdapter):
    """Google Gemini via the official google-generativeai SDK."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=self._settings.gemini_api_key)
                self._client = genai.GenerativeModel(self._settings.gemini_model)
            except ImportError:
                raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")
        return self._client

    @property
    def model_id(self) -> str:
        return f"gemini/{self._settings.gemini_model}"

    @property
    def is_available(self) -> bool:
        return bool(self._settings.gemini_api_key)

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        system_prompt = PERSPECTIVE_SYSTEM_PROMPTS[perspective_name]
        user_prompt = build_analysis_prompt(perspective_name.value, idea, evidence)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        client = self._get_client()
        try:
            # Gemini SDK is sync; run in executor for async context
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.generate_content(full_prompt),
            )
            raw = response.text
        except Exception as exc:
            logger.error("Gemini API error for perspective %s: %s", perspective_name.value, exc)
            raise

        try:
            return _parse_output(raw, perspective_name, self.model_id)
        except Exception as exc:
            logger.error("Gemini output parse failed: %s\nRaw: %.300s", exc, raw)
            raise ValueError(f"Gemini returned unparseable output: {exc}") from exc

    async def clarify_idea(self, idea: IdeaInput) -> str:
        prompt = (
            f"In 2-3 sentences, describe what is actually being evaluated:\n"
            f"Name: {idea.name}\n"
            f"Description: {idea.description}\n"
            f"Problem: {idea.problem}\n"
            f"Customer: {idea.target_customer} in {idea.geography}\n"
            f"Business model: {idea.business_model or 'unspecified'}\n"
            "Be factual. Do not predict success."
        )
        try:
            client = self._get_client()
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: client.generate_content(prompt))
            return response.text.strip()
        except Exception as exc:
            logger.warning("Gemini clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"
