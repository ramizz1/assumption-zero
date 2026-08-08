"""
Web Search research provider.

Uses DuckDuckGo Web Search API / HTML scraper for zero-config live web research.
No API key required. Works globally across all geographies and niches.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime
from typing import Dict, List
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

DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/"


def _stable_id(url: str) -> str:
    return "WS" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _ev_type(query_type: str) -> EvidenceType:
    mapping: Dict[str, EvidenceType] = {
        "competitor": EvidenceType.COMPETITOR,
        "pricing": EvidenceType.PRICING,
        "complaint": EvidenceType.COMPLAINT,
        "demand": EvidenceType.DEMAND,
        "regulatory": EvidenceType.REGULATORY,
        "market_direction": EvidenceType.DEMAND,
        "geographic": EvidenceType.DEMAND,
        "failure_reason": EvidenceType.FAILURE_REASON,
        "failed_product": EvidenceType.FAILURE_REASON,
        "manual_workflow": EvidenceType.MANUAL_WORKFLOW,
    }
    return mapping.get(query_type, EvidenceType.GENERAL)


class WebSearchProvider(ResearchProvider):
    """Zero-config web search provider querying live search engines."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "Web Search"

    @property
    def is_available(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> List[EvidenceItem]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        url = f"{DUCKDUCKGO_HTML}?q={quote_plus(query)}"
        items: List[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        try:
            timeout = min(10.0, float(self._settings.request_timeout))
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
                        if not clean_text or len(clean_text) < 15:
                            continue

                        # Extract domain for clean title
                        domain_match = re.search(r"https?://(?:www\.)?([^/]+)", clean_url)
                        domain = domain_match.group(1) if domain_match else "Web"

                        title = f"[{domain}] {clean_text[:70]}…"

                        items.append(
                            EvidenceItem(
                                evidence_id=_stable_id(clean_url),
                                title=title,
                                url=clean_url,
                                evidence_origin=f"Web Search - {domain}",
                                source_name=f"Web ({domain})",
                                publication_date=None,
                                retrieval_date=today,
                                passage=self._truncate(clean_text, 500),
                                search_query=query,
                                evidence_type=_ev_type(query_type),
                                reliability=ReliabilityLevel.MEDIUM,
                                relevance_score=0.8,
                                retrieval_timestamp=now,
                                is_demo=False,
                            )
                        )
                    logger.info("WebSearchProvider: %d results for %r", len(items), query)
        except Exception as exc:
            logger.debug("WebSearchProvider failed for %r: %s", query, exc)

        return items
