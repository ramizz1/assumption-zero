"""Abstract base class for all research providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from assumption_zero.schemas import EvidenceItem, IdeaInput


class ResearchProvider(ABC):
    """
    Each provider collects evidence for a given query and query type.

    Providers must:
    - Return normalized EvidenceItem objects
    - Fail gracefully (return empty list + log error, never raise unless fatal)
    - Never invent URLs or sources
    - Respect timeouts and rate limits
    - Document any terms-of-service constraints
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name, used in evidence source_name."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is configured and reachable."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> List[EvidenceItem]:
        """
        Run a single search query and return a list of evidence items.

        Args:
            query:       The search string.
            query_type:  Category (e.g. "competitor", "complaint").
            idea:        The original idea — for context / relevance scoring.
            max_results: Upper bound on returned items.

        Returns:
            List of EvidenceItem (may be empty on failure).
        """
        ...

    def _truncate(self, text: str, max_len: int = 500) -> str:
        """Truncate a passage to a safe length."""
        if len(text) <= max_len:
            return text
        return text[:max_len].rsplit(" ", 1)[0] + " …"
