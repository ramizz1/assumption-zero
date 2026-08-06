"""
Ollama LLM adapter — run local models via Ollama.

Allows connecting to any local Ollama instance (http://localhost:11434).
Supports models like llama3.2, llama3.3, mistral, deepseek-r1, qwen2.5, phi3, etc.
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

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2"


class OllamaAdapter(LLMAdapter):
    """
    Adapter for local Ollama instances.
    Attempts OpenAI-compatible /v1/chat/completions endpoint first, falling back to /api/chat.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def _base_url(self) -> str:
        url = (
            os.getenv("OLLAMA_BASE_URL")
            or self._settings.ollama_base_url
            or _DEFAULT_BASE_URL
        )
        return url.rstrip("/")

    def _model(self) -> str:
        return (
            os.getenv("OLLAMA_MODEL")
            or self._settings.ollama_model
            or _DEFAULT_MODEL
        )

    @property
    def model_id(self) -> str:
        return f"ollama/{self._model()}"

    @property
    def is_available(self) -> bool:
        # Local Ollama is assumed available if base_url is set
        return bool(self._base_url())

    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        base = self._base_url()
        model_name = self._model()
        timeout = max(90.0, float(self._settings.request_timeout))

        # Attempt 1: OpenAI-compatible endpoint (/v1/chat/completions) available in Ollama >= 0.1.24
        v1_url = f"{base}/v1/chat/completions"
        v1_payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.post(v1_url, json=v1_payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        if content:
                            return content
            except Exception as exc:
                logger.debug("Ollama /v1/chat/completions failed (%s) — trying /api/chat fallback...", exc)

            # Attempt 2: Native Ollama endpoint (/api/chat)
            native_url = f"{base}/api/chat"
            native_payload = {
                "model": model_name,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            try:
                resp = await client.post(native_url, json=native_payload)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", {})
                    content = msg.get("content")
                    if content:
                        return content
                resp.raise_for_status()
            except Exception as exc:
                raise RuntimeError(
                    f"Could not connect to Ollama at {base} for model {model_name}. "
                    f"Ensure Ollama is running (`ollama serve`) and model '{model_name}' is pulled (`ollama pull {model_name}`). "
                    f"Error: {exc}"
                ) from exc

        raise RuntimeError(f"Ollama returned empty response for model {model_name}")

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
            logger.debug("Ollama parse_raw_prompt failed (%s) — using fallback extractor", exc)
            return await super().parse_raw_prompt(raw_text)
