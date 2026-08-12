"""Zero-configuration web research through a public RSS search endpoint."""

from __future__ import annotations

import hashlib
import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from urllib.parse import urlparse

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

BING_RSS = "https://www.bing.com/search"


def _stable_id(url: str) -> str:
    return "WS" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _ev_type(query_type: str) -> EvidenceType:
    mapping: dict[str, EvidenceType] = {
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
    """Collect public web results from Bing's RSS representation."""

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
    ) -> list[EvidenceItem]:
        del idea  # The generated query already carries the idea and region context.
        headers = {
            "User-Agent": "Assumption-Zero/0.1 (+https://github.com/ramizz1/assumption-zero)",
            "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8",
        }
        params = {"format": "rss", "q": query}
        items: list[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        try:
            timeout = min(10.0, float(self._settings.request_timeout))
            async with httpx.AsyncClient(
                timeout=timeout,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(BING_RSS, params=params)
                response.raise_for_status()

            root = ET.fromstring(response.content)
            for result in root.findall("./channel/item")[:max_results]:
                clean_url = (result.findtext("link") or "").strip()
                title = html.unescape((result.findtext("title") or "").strip())
                raw_description = result.findtext("description") or ""
                clean_text = html.unescape(re.sub(r"<[^>]+>", " ", raw_description))
                clean_text = re.sub(r"\s+", " ", clean_text).strip()
                if not clean_url.startswith(("http://", "https://")) or len(clean_text) < 15:
                    continue

                domain = (urlparse(clean_url).hostname or "web").removeprefix("www.")
                items.append(
                    EvidenceItem(
                        evidence_id=_stable_id(clean_url),
                        title=title or f"Result from {domain}",
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
        except (httpx.HTTPError, ET.ParseError, ValueError) as exc:
            logger.warning("WebSearchProvider failed for %r: %s", query, exc)

        return items
