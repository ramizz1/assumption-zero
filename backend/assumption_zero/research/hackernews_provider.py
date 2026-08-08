"""
Hacker News research provider (via Algolia HN Search API).

Finds product launches (Show HN), demand discussions (Ask HN),
competitor mentions, and customer complaints.

API: https://hn.algolia.com/api
Terms: Public, documented API — no key required.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from typing import Any, Dict, List

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

HN_API = "https://hn.algolia.com/api/v1/search"


def _stable_id(url: str) -> str:
    return "HN" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _ev_type_for_hn(title: str, query_type: str) -> EvidenceType:
    t = title.lower()
    if "show hn" in t:
        return EvidenceType.COMPETITOR
    if "ask hn" in t:
        return EvidenceType.DEMAND
    if query_type == "complaint":
        return EvidenceType.COMPLAINT
    return EvidenceType.GENERAL


class HackerNewsProvider(ResearchProvider):
    """Search Hacker News via the Algolia HN Search API."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "Hacker News"

    @property
    def is_available(self) -> bool:
        return True  # Public API, no key required

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> List[EvidenceItem]:
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": min(max_results, 20),
        }

        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout) as client:
                resp = await client.get(HN_API, params=params)
                resp.raise_for_status()
                data: Dict[str, Any] = resp.json()
        except Exception as exc:
            logger.warning("HN search failed for %r: %s", query, exc)
            return []

        items: List[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        for hit in data.get("hits", [])[:max_results]:
            story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            title = hit.get("title") or "Untitled HN Story"
            points = hit.get("points") or 0
            num_comments = hit.get("num_comments") or 0

            # Build a meaningful passage from available fields
            passage = (
                f"HN story: '{title}'. "
                f"Points: {points}, Comments: {num_comments}. "
            )
            if hit.get("_highlightResult", {}).get("title", {}).get("value"):
                passage += f"Excerpt: {hit['_highlightResult']['title']['value']}"

            # Published timestamp
            created_at = hit.get("created_at")
            pub_date: date | None = None
            if created_at:
                try:
                    pub_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
                except ValueError:
                    pub_date = None

            relevance = min(1.0, (points or 0) / 500)

            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(story_url),
                    title=f"[HN] {title}",
                    url=story_url,
                    evidence_origin="Hacker News",
                    source_name="Hacker News",
                    publication_date=pub_date,
                    retrieval_date=today,
                    passage=self._truncate(passage, 500),
                    search_query=query,
                    evidence_type=_ev_type_for_hn(title, query_type),
                    reliability=ReliabilityLevel.LOW,
                    relevance_score=max(0.1, relevance),
                    retrieval_timestamp=now,
                    is_demo=False,
                )
            )

        logger.info("HackerNews: %d stories for %r", len(items), query)
        return items
