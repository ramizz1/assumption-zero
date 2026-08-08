"""
News research provider.

Queries live news streams for startup market news, press releases,
competitor announcements, and regulatory updates.
No API key required.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime
from typing import List
from urllib.parse import quote_plus, unquote

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

DUCKDUCKGO_NEWS_URL = "https://html.duckduckgo.com/html/"


def _stable_id(url: str) -> str:
    return "NW" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


class NewsSearchProvider(ResearchProvider):
    """Zero-config news search provider for live industry and market news."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "Live News & Media"

    @property
    def is_available(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 5,
    ) -> List[EvidenceItem]:
        # Search news for market direction, competitor, demand, regulatory, and pricing
        news_query = f"{query} news press release"
        url = f"{DUCKDUCKGO_NEWS_URL}?q={quote_plus(news_query)}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

        items: List[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        try:
            timeout = min(8.0, float(self._settings.request_timeout))
            async with httpx.AsyncClient(
                timeout=timeout,
                headers=headers,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    html = resp.text
                    matches = re.findall(
                        r'<a class="result__snippet"[^>]*href="//duckduckgo.com/l/\?uddg=([^&"]+)[^>]*">(.*?)</a>',
                        html,
                        re.DOTALL,
                    )
                    for raw_url, snippet in matches[:max_results]:
                        clean_url = unquote(raw_url)
                        clean_text = re.sub(r"<[^>]+>", "", snippet).strip()
                        if not clean_text or len(clean_text) < 20:
                            continue

                        domain_match = re.search(r"https?://(?:www\.)?([^/]+)", clean_url)
                        domain = domain_match.group(1) if domain_match else "News"

                        items.append(
                            EvidenceItem(
                                evidence_id=_stable_id(clean_url),
                                title=f"[News - {domain}] {clean_text[:70]}…",
                                url=clean_url,
                                evidence_origin=f"News - {domain}",
                                source_name=f"News ({domain})",
                                publication_date=None,
                                retrieval_date=today,
                                passage=self._truncate(clean_text, 500),
                                search_query=news_query,
                                evidence_type=EvidenceType.MARKET_DIRECTION,
                                reliability=ReliabilityLevel.MEDIUM,
                                relevance_score=0.82,
                                retrieval_timestamp=now,
                                is_demo=False,
                            )
                        )
                    logger.info("NewsSearchProvider: %d news items for %r", len(items), query)
        except Exception as exc:
            logger.debug("NewsSearchProvider failed for %r: %s", query, exc)

        return items
