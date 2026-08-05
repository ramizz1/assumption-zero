"""
Demo provider removed — no fixture data.

The "demo" command runs the sample idea (examples/sample-idea.json) through
the REAL research and AI pipeline. Configure .env with your preferred providers.

This file is intentionally a no-op shim so existing imports don't break.
"""
from assumption_zero.research.base import ResearchProvider
from assumption_zero.schemas import EvidenceItem, IdeaInput
from typing import List


class DemoProvider(ResearchProvider):
    """
    Stub provider — not a data source.

    The demo mode in Assumption Zero simply runs examples/sample-idea.json
    through the live research pipeline (SearXNG, GitHub, HackerNews, Wikipedia,
    Reddit, etc.).  There is no hardcoded or fake evidence.

    This class exists only so that 'demo' can be listed in provider names
    without breaking imports.  is_available always returns False so the engine
    never routes queries here.
    """

    @property
    def name(self) -> str:
        return "Demo"

    @property
    def is_available(self) -> bool:
        # Never used as a real provider — real providers collect evidence
        return False

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> List[EvidenceItem]:
        return []
