"""
Wikipedia research provider.

Uses the Wikipedia REST API to find factual context: market definitions,
regulatory background, technology overviews.

API: https://en.wikipedia.org/api/rest_v1/
Terms: Wikipedia content is freely available under CC BY-SA.
No API key required. Documented API.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from typing import Any, Dict, List
from urllib.parse import quote

import httpx

from assumption_zero.config import get_settings
from assumption_zero.research.base import ResearchProvider
from assumption_zero.schemas import (
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    ReliabilityLevel,
)

logger = logging.getLogger(__name__)

WIKI_SEARCH_API = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"


def _stable_id(url: str) -> str:
    return "WK" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _ev_type_for_wiki(query_type: str) -> EvidenceType:
    mapping: Dict[str, EvidenceType] = {
        "regulatory": EvidenceType.REGULATORY,
        "market_direction": EvidenceType.MARKET_DIRECTION,
        "competitor": EvidenceType.COMPETITOR,
        "failed_product": EvidenceType.FAILED_PRODUCT,
    }
    return mapping.get(query_type, EvidenceType.GENERAL)


class WikipediaProvider(ResearchProvider):
    """Fetch Wikipedia article summaries for market and technology context."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "Wikipedia"

    @property
    def is_available(self) -> bool:
        return True  # No key required

    async def _search_titles(self, query: str, limit: int) -> List[str]:
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "namespace": 0,
            "format": "json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.request_timeout,
                headers={"User-Agent": "AssumptionZero/0.1 (research tool)"},
            ) as client:
                resp = await client.get(WIKI_SEARCH_API, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data[1] if isinstance(data, list) and len(data) > 1 else []
        except Exception as exc:
            logger.warning("Wikipedia search failed for %r: %s", query, exc)
            return []

    async def _get_summary(self, title: str) -> Dict[str, Any]:
        encoded = quote(title.replace(" ", "_"))
        url = f"{WIKI_SUMMARY_API}{encoded}"
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.request_timeout,
                headers={"User-Agent": "AssumptionZero/0.1 (research tool)"},
            ) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as exc:
            logger.debug("Wikipedia summary failed for %r: %s", title, exc)
        return {}

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 5,
    ) -> List[EvidenceItem]:
        # Wikipedia is most useful for regulatory/market/general context
        if query_type not in (
            "regulatory", "market_direction", "competitor", "general",
            "failed_product", "oss_alternative",
        ):
            return []

        titles = await self._search_titles(query, max_results)
        if not titles:
            return []

        items: List[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        for title in titles[:max_results]:
            summary = await self._get_summary(title)
            if not summary:
                continue

            page_url = summary.get("content_urls", {}).get("desktop", {}).get("page", "")
            if not page_url:
                page_url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"

            extract = summary.get("extract", "")
            if not extract:
                continue

            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(page_url),
                    title=f"[Wikipedia] {summary.get('title', title)}",
                    url=page_url,
                    source_name="Wikipedia",
                    publication_date=None,
                    retrieval_date=today,
                    passage=self._truncate(extract, 500),
                    search_query=query,
                    evidence_type=_ev_type_for_wiki(query_type),
                    reliability=ReliabilityLevel.MEDIUM,
                    relevance_score=0.6,
                    retrieval_timestamp=now,
                    is_demo=False,
                )
            )

        logger.info("Wikipedia: %d articles for %r", len(items), query)
        return items
