"""
OpenRouter LLM adapter.

OpenRouter provides access to 200+ models via a single OpenAI-compatible API.
https://openrouter.ai

This adapter requires an OPENROUTER_API_KEY supplied in configuration or at runtime.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

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

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Primary default model & fallback list of verified free models on OpenRouter
_DEFAULT_MODEL = "openrouter/free"
_FALLBACK_MODELS = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "inclusionai/ling-3.0-flash:free",
    "poolside/laguna-s-2.1:free",
]


def _repair_and_parse_json(text: str) -> dict:
    """Robustly parse JSON, repairing common LLM output syntax flaws."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part_str = part.strip()
            if part_str.startswith("json"):
                part_str = part_str[4:].strip()
            if part_str.startswith("{") and part_str.endswith("}"):
                text = part_str
                break

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    # Attempt 1: Standard JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: Fix trailing commas and missing commas between properties
    cleaned = re.sub(r",\s*([\}\]])", r"\1", text)
    cleaned = re.sub(r'("|\d|true|false)\s*\n\s*(")', r"\1,\n\2", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 3: Sanitize newlines inside quoted strings
    buf: list[str] = []
    in_string = False
    escaped = False
    for char in cleaned:
        if char == '"' and not escaped:
            in_string = not in_string
            buf.append(char)
        elif char == "\n" and in_string:
            buf.append("\\n")
        elif char == "\r" and in_string:
            buf.append("")
        else:
            buf.append(char)
        escaped = char == "\\" and not escaped

    sanitized = "".join(buf)
    try:
        return json.loads(sanitized)
    except json.JSONDecodeError:
        pass

    # Attempt 4: Fallback regex extraction of essential fields
    result: dict = {}

    summary_match = re.search(r'"summary"\s*:\s*"(.*?)"', text, re.DOTALL)
    result["summary"] = (
        summary_match.group(1).replace("\n", " ").strip() if summary_match else text[:300]
    )

    rec_match = re.search(r'"recommendation"\s*:\s*"(.*?)"', text)
    result["recommendation"] = rec_match.group(1).strip() if rec_match else "Test First"

    assumption_match = re.search(r'"most_dangerous_assumption"\s*:\s*"(.*?)"', text, re.DOTALL)
    if assumption_match:
        result["most_dangerous_assumption"] = assumption_match.group(1).strip()

    # Extract lists of strings for findings/risks/opportunities
    findings: list[str] = []
    findings_block = re.search(r'"key_findings"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if findings_block:
        findings = re.findall(r'"([^"]{5,300})"', findings_block.group(1))
    result["key_findings"] = findings

    risks: list[str] = []
    risks_block = re.search(r'"risks"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if risks_block:
        risks = re.findall(r'"([^"]{5,300})"', risks_block.group(1))
    result["risks"] = risks

    opps: list[str] = []
    opps_block = re.search(r'"opportunities"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if opps_block:
        opps = re.findall(r'"([^"]{5,300})"', opps_block.group(1))
    result["opportunities"] = opps

    # Extract dimension scores
    dim_scores: dict = {}
    dim_block = re.search(r'"dimension_scores"\s*:\s*\{(.*?)\}', text, re.DOTALL)
    if dim_block:
        for key, val in re.findall(r'"(\w+)"\s*:\s*(\d+(?:\.\d+)?)', dim_block.group(1)):
            dim_scores[key] = float(val)
    result["dimension_scores"] = dim_scores

    return result


def _parse_output(raw: str, perspective_name: PerspectiveName, model_id: str) -> PerspectiveOutput:
    data = _repair_and_parse_json(raw)

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
        competitors=data.get("competitors", []),
        most_dangerous_assumption=data.get("most_dangerous_assumption", ""),
        reasoning=data.get("reasoning", ""),
    )


class OpenRouterAdapter(LLMAdapter):
    """
    OpenRouter adapter.

    Uses the configured key and automatically tries active free models with
    fallback support if a model is unavailable.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None, **kwargs) -> None:
        self._settings = get_settings()
        self._api_key_override = api_key
        self._model_override = model

    def _api_key(self) -> str:
        import os

        key = (
            self._api_key_override
            or os.getenv("OPENROUTER_API_KEY")
            or self._settings.openrouter_api_key
            or ""
        )
        return key.strip()

    def _model(self) -> str:
        return self._model_override or self._settings.openrouter_model or _DEFAULT_MODEL

    @property
    def model_id(self) -> str:
        return f"openrouter/{self._model()}"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key())

    def _headers(self) -> dict[str, str]:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError(
                "OpenRouter API key is missing. Please set OPENROUTER_API_KEY in your .env file or environment."
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://assumption-zero.dev",
            "X-Title": "Assumption Zero",
        }

    async def _chat(self, messages: list[dict[str, str]]) -> str:
        url = f"{_OPENROUTER_BASE}/chat/completions"
        primary = self._model()
        models_to_try = [primary] + [m for m in _FALLBACK_MODELS if m != primary]

        last_error: Exception | None = None
        timeout = max(30.0, float(self._settings.request_timeout))

        async with httpx.AsyncClient(
            timeout=timeout,
            headers=self._headers(),
        ) as client:
            for model_name in models_to_try:
                payload: dict[str, Any] = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.3,
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
                            logger.debug(
                                "OpenRouter model %s error payload: %s", model_name, err_msg
                            )
                            last_error = RuntimeError(
                                f"OpenRouter model {model_name} error: {err_msg}"
                            )
                            continue
                    elif resp.status_code == 401:
                        raise RuntimeError(
                            "OpenRouter API key is invalid or unauthorized (HTTP 401). "
                            "Please check your OPENROUTER_API_KEY at https://openrouter.ai/keys"
                        )
                    elif resp.status_code in (402, 429):
                        raise RuntimeError(
                            f"OpenRouter API quota or rate limit exceeded (HTTP {resp.status_code}). "
                            "You are out of credits or rate limited. Please check your credit balance at https://openrouter.ai/credits"
                        )
                    else:
                        error_msg = f"HTTP {resp.status_code} for {model_name}: {resp.text[:150]}"
                        logger.debug("OpenRouter model %s failed: %s", model_name, error_msg)
                        last_error = RuntimeError(error_msg)
                except RuntimeError:
                    raise
                except Exception as exc:
                    logger.debug("OpenRouter model %s exception: %s", model_name, exc)
                    last_error = exc

        raise RuntimeError(f"All OpenRouter models failed. Last error: {last_error}")

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
            logger.debug("OpenRouter clarify_idea failed: %s", exc)
            return f"{idea.name}: {idea.description}"

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        """Parse freeform prompt text into structured IdeaInput using OpenRouter LLM."""
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
            raw_response = await self._chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this startup idea:\n{raw_text}"},
                ]
            )
            parsed_data = _repair_and_parse_json(raw_response)
            parsed_data["name"] = parsed_data.get("name") or "New Idea"
            parsed_data["description"] = parsed_data.get("description") or raw_text[:200]
            parsed_data["problem"] = parsed_data.get("problem") or raw_text[:300]
            parsed_data["target_customer"] = parsed_data.get("target_customer") or "Target users"
            parsed_data["geography"] = parsed_data.get("geography") or "global"
            parsed_data["additional_context"] = raw_text

            return IdeaInput(**parsed_data)
        except Exception as exc:
            logger.debug("OpenRouter parse_raw_prompt failed (%s) — using fallback extractor", exc)
            return await super().parse_raw_prompt(raw_text)
