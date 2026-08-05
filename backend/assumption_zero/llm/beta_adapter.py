"""
Assumption Zero Beta AI — the built-in AI provider.

Routes to OpenRouter's free open-weight models using a built-in key.
No user configuration required — works out of the box.
"""
from __future__ import annotations

from typing import List

from assumption_zero.llm.openrouter_adapter import OpenRouterAdapter, PerspectiveOutput
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName


class BetaAdapter(OpenRouterAdapter):
    """
    Assumption Zero Beta AI.

    The default built-in AI provider. No API key required from the user.
    Powered by open-weight models via OpenRouter (openrouter.ai).
    """

    @property
    def model_id(self) -> str:
        return f"az-beta/{self._model()}"

    @property
    def is_available(self) -> bool:
        return True  # Always available — built-in key

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        return await super().analyze_perspective(perspective_name, idea, evidence)

    async def clarify_idea(self, idea: IdeaInput) -> str:
        return await super().clarify_idea(idea)
