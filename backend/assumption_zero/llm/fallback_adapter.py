"""
Fallback Chain Adapter — Smart multi-key LLM failover.

Automatically sequences the adapters supplied by the analysis service and fails over safely.
If a provider hits rate limits (429), quota limits (402), timeouts, or network failures,
it automatically fails over to the next configured provider seamlessly.
"""

from __future__ import annotations

import logging

from assumption_zero.llm.base import LLMAdapter, PerspectiveName, PerspectiveOutput
from assumption_zero.schemas import EvidenceItem, IdeaInput

logger = logging.getLogger(__name__)


class FallbackChainAdapter(LLMAdapter):
    """
    Orchestrates a priority chain of LLM adapters.
    Tries adapters in sequence and fails over on rate limits (429), quota limits (402),
    network timeouts, or server errors.
    """

    def __init__(self, adapters: list[LLMAdapter]):
        # Filter down to adapters that report is_available == True
        self.adapters = [a for a in adapters if a.is_available]
        if not self.adapters:
            # Fallback to mock adapter if no key adapters are available
            from assumption_zero.llm.mock_adapter import MockAdapter

            self.adapters = [MockAdapter()]

    @property
    def model_id(self) -> str:
        names = [a.model_id for a in self.adapters]
        return f"fallback-chain({', '.join(names)})"

    @property
    def is_available(self) -> bool:
        return any(a.is_available for a in self.adapters)

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: list[EvidenceItem],
    ) -> PerspectiveOutput:
        last_error = None
        for adapter in self.adapters:
            try:
                logger.info(
                    "Executing perspective '%s' via adapter: %s", perspective_name, adapter.model_id
                )
                return await adapter.analyze_perspective(perspective_name, idea, evidence)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Adapter %s failed for perspective '%s': %s. Failing over to next provider in chain...",
                    adapter.model_id,
                    perspective_name,
                    exc,
                )
                continue

        # If all adapters failed, raise clean user-shielded message
        if last_error:
            err_text = str(last_error)
            if "429" in err_text or "rate limit" in err_text.lower():
                raise RuntimeError(
                    "API Key Rate Limit Reached for selected providers. "
                    "Please check your API key quota or switch to another provider."
                )
            if "402" in err_text or "quota" in err_text.lower() or "credit" in err_text.lower():
                raise RuntimeError(
                    "API Key Quota Exceeded for selected providers. "
                    "Please check your account balance or switch provider."
                )
            raise RuntimeError(
                "All configured AI providers were unreachable or returned an error. "
                "Please verify your API keys and internet connection."
            )
        raise RuntimeError("No available LLM provider could complete the request.")

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        last_error = None
        for adapter in self.adapters:
            try:
                logger.info("Parsing prompt via adapter: %s", adapter.model_id)
                return await adapter.parse_raw_prompt(raw_text)
            except ValueError:
                # Do not suppress input validation errors (gibberish rejection)
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Adapter %s failed prompt parsing: %s. Failing over...",
                    adapter.model_id,
                    exc,
                )
                continue

        if last_error:
            err_text = str(last_error)
            if "429" in err_text or "rate limit" in err_text.lower():
                raise RuntimeError("API Key Rate Limit Reached for AI provider.")
            if "402" in err_text or "quota" in err_text.lower():
                raise RuntimeError("API Key Quota Exceeded for AI provider.")
            raise RuntimeError("Selected AI providers were unreachable.")
        raise RuntimeError("Failed to parse prompt across all available AI providers.")

    async def clarify_idea(self, idea: IdeaInput) -> str:
        for adapter in self.adapters:
            try:
                return await adapter.clarify_idea(idea)
            except Exception:
                continue
        return f"Analyzing idea: {idea.name} — {idea.description}"
