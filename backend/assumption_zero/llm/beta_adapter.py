"""
Assumption Zero Beta AI.

This provider previously offered a built-in free key, but this is removed
for the open-source version to prevent credential abuse.
It now acts as an alias to OpenRouterAdapter and requires user configuration.
"""

from __future__ import annotations

from assumption_zero.llm.openrouter_adapter import OpenRouterAdapter, PerspectiveOutput
from assumption_zero.schemas import EvidenceItem, IdeaInput, PerspectiveName


class BetaAdapter(OpenRouterAdapter):
    """
    Assumption Zero Beta AI.

    Requires a user-configured OPENROUTER_API_KEY.
    """

    @property
    def model_id(self) -> str:
        return f"az-beta/{self._model()}"

    @property
    def is_available(self) -> bool:
        return super().is_available

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: list[EvidenceItem],
    ) -> PerspectiveOutput:
        return await super().analyze_perspective(perspective_name, idea, evidence)

    async def clarify_idea(self, idea: IdeaInput) -> str:
        return await super().clarify_idea(idea)
