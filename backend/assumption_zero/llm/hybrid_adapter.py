"""
Hybrid Dual-Engine LLM Adapter.

Intelligently balances workloads between Groq and OpenRouter:
- Distributes perspectives across providers (e.g. Groq for Market Analyst & Practical Builder, OpenRouter for Skeptical Investor).
- Automatically fails over if one provider hits rate limits (HTTP 429) or token quotas.
- Gives founders maximum resilience, accuracy, and double the daily token limit.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from assumption_zero.llm.base import LLMAdapter, PerspectiveOutput
from assumption_zero.llm.groq_adapter import GroqAdapter
from assumption_zero.llm.openrouter_adapter import OpenRouterAdapter
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName

logger = logging.getLogger(__name__)


class HybridLLMAdapter(LLMAdapter):
    """
    Dual-engine adapter that load balances and fails over between Groq and OpenRouter.
    """

    def __init__(
        self,
        groq_adapter: Optional[GroqAdapter] = None,
        openrouter_adapter: Optional[OpenRouterAdapter] = None,
    ) -> None:
        self.groq = groq_adapter or GroqAdapter()
        self.openrouter = openrouter_adapter or OpenRouterAdapter()

    @property
    def model_id(self) -> str:
        return f"hybrid({self.groq.model_id} + {self.openrouter.model_id})"

    @property
    def is_available(self) -> bool:
        return self.groq.is_available or self.openrouter.is_available

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        """
        Distribute perspective runs intelligently.
        - Skeptical Investor -> OpenRouter (different perspective model weights)
        - Market Analyst & Practical Builder -> Groq (ultra-fast inference)
        Falls back to the other provider if rate limited or unavailable.
        """
        groq_ok = self.groq.is_available
        openrouter_ok = self.openrouter.is_available

        if not groq_ok and not openrouter_ok:
            raise RuntimeError(
                "No active AI providers available. Please set GROQ_API_KEY (console.groq.com/keys) "
                "or OPENROUTER_API_KEY (openrouter.ai/keys)."
            )

        # Assign primary and fallback based on perspective + availability
        if perspective_name == PerspectiveName.SKEPTICAL_INVESTOR and openrouter_ok:
            primary_adapter: LLMAdapter = self.openrouter
            fallback_adapter: LLMAdapter = self.groq if groq_ok else self.openrouter
        elif groq_ok:
            primary_adapter = self.groq
            fallback_adapter = self.openrouter if openrouter_ok else self.groq
        else:
            primary_adapter = self.openrouter
            fallback_adapter = self.openrouter  # only one available

        try:
            logger.info("Running perspective %s on primary provider %s", perspective_name.value, primary_adapter.model_id)
            return await primary_adapter.analyze_perspective(perspective_name, idea, evidence)
        except Exception as primary_exc:
            if fallback_adapter is primary_adapter:
                # No real fallback available
                raise
            logger.warning(
                "Primary provider %s failed for %s (%s). Attempting automatic failover to %s...",
                primary_adapter.model_id,
                perspective_name.value,
                primary_exc,
                fallback_adapter.model_id,
            )
            if fallback_adapter.is_available:
                try:
                    return await fallback_adapter.analyze_perspective(perspective_name, idea, evidence)
                except Exception as fallback_exc:
                    raise RuntimeError(
                        f"Both AI providers failed for {perspective_name.value}.\n"
                        f"  Primary ({primary_adapter.model_id}): {primary_exc}\n"
                        f"  Fallback ({fallback_adapter.model_id}): {fallback_exc}\n"
                        f"Tip: If you reached daily limits, connect a free API key at https://console.groq.com/keys or https://openrouter.ai/keys"
                    ) from fallback_exc
            raise primary_exc

    async def clarify_idea(self, idea: IdeaInput) -> str:
        if self.groq.is_available:
            try:
                return await self.groq.clarify_idea(idea)
            except Exception:
                pass
        if self.openrouter.is_available:
            try:
                return await self.openrouter.clarify_idea(idea)
            except Exception:
                pass
        return await super().clarify_idea(idea)

    async def parse_raw_prompt(self, raw_text: str) -> IdeaInput:
        if self.groq.is_available:
            try:
                return await self.groq.parse_raw_prompt(raw_text)
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Groq prompt parsing failed (%s) — failing over to OpenRouter", exc)

        if self.openrouter.is_available:
            try:
                return await self.openrouter.parse_raw_prompt(raw_text)
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("OpenRouter prompt parsing failed (%s)", exc)

        return await super().parse_raw_prompt(raw_text)
