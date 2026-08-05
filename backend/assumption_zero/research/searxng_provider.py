"""
SearXNG research provider.

Uses a self-hosted or public SearXNG instance for general web search.
Configure SEARXNG_BASE_URL in your .env.

Terms: SearXNG itself is AGPL-licensed and designed for privacy-respecting
search aggregation.  Deployers must respect the terms of the underlying
search engines SearXNG queries on their behalf.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

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

# Map our internal query types to SearXNG categories
_CATEGORY_MAP: Dict[str, str] = {
    "competitor": "general",
    "oss_alternative": "general",
    "complaint": "general",
    "demand": "general",
    "pricing": "general",
    "regulatory": "general",
    "distribution": "general",
    "failed_product": "general",
    "failure_reason": "general",
    "market_direction": "general",
    "geographic": "general",
    "manual_workflow": "general",
    "general": "general",
}

_EVIDENCE_TYPE_MAP: Dict[str, EvidenceType] = {
    "competitor": EvidenceType.COMPETITOR,
    "oss_alternative": EvidenceType.OSS_ALTERNATIVE,
    "complaint": EvidenceType.COMPLAINT,
    "demand": EvidenceType.DEMAND,
    "pricing": EvidenceType.PRICING,
    "regulatory": EvidenceType.REGULATORY,
    "distribution": EvidenceType.DISTRIBUTION,
    "failed_product": EvidenceType.FAILED_PRODUCT,
    "failure_reason": EvidenceType.FAILURE_REASON,
    "market_direction": EvidenceType.MARKET_DIRECTION,
    "geographic": EvidenceType.GEOGRAPHIC,
    "manual_workflow": EvidenceType.MANUAL_WORKFLOW,
    "general": EvidenceType.GENERAL,
}


def _stable_id(url: str, prefix: str = "SX") -> str:
    """Generate a stable short hash ID from a URL."""
    return prefix + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _reliability_from_domain(url: str) -> ReliabilityLevel:
    high = ["reuters.com", "bbc.com", "nytimes.com", "wsj.com", "techcrunch.com",
            "bloomberg.com", "ft.com", "statista.com", "gartner.com", "forrester.com"]
    low = ["reddit.com", "quora.com", "yahoo.com", "medium.com"]
    domain = url.split("/")[2] if "//" in url else url
    if any(h in domain for h in high):
        return ReliabilityLevel.HIGH
    if any(l in domain for l in low):
        return ReliabilityLevel.LOW
    return ReliabilityLevel.MEDIUM


class SearXNGProvider(ResearchProvider):
    """Search via a SearXNG instance (SEARXNG_BASE_URL must be configured)."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._base_url = (self._settings.searxng_base_url or "").rstrip("/")

    @property
    def name(self) -> str:
        return "SearXNG"

    @property
    def is_available(self) -> bool:
        return bool(self._base_url)

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> List[EvidenceItem]:
        if not self.is_available:
            return []

        params = {
            "q": query,
            "format": "json",
            "categories": _CATEGORY_MAP.get(query_type, "general"),
            "language": "en",
        }
        url = f"{self._base_url}/search?{urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                data: Dict[str, Any] = resp.json()
        except Exception as exc:
            logger.warning("SearXNG search failed for %r: %s", query, exc)
            return []

        items: List[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()
        ev_type = _EVIDENCE_TYPE_MAP.get(query_type, EvidenceType.GENERAL)

        for result in data.get("results", [])[:max_results]:
            result_url = result.get("url", "")
            if not result_url:
                continue
            passage = self._truncate(
                result.get("content") or result.get("title") or "", 500
            )
            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(result_url),
                    title=result.get("title", "Untitled"),
                    url=result_url,
                    source_name=f"SearXNG / {result.get('engine', 'web')}",
                    publication_date=None,
                    retrieval_date=today,
                    passage=passage,
                    search_query=query,
                    evidence_type=ev_type,
                    reliability=_reliability_from_domain(result_url),
                    relevance_score=min(1.0, result.get("score", 0.5)),
                    retrieval_timestamp=now,
                    is_demo=False,
                )
            )

        logger.info("SearXNG: %d results for %r", len(items), query)
        return items
