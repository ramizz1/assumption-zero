"""
Reddit research provider.

Uses Reddit's public JSON API to find demand signals, complaints, and
competitor discussions in relevant communities.

API: https://www.reddit.com/search.json (public, no auth for basic search)
Terms: Reddit's public JSON API is documented and allows read-only access
without a user account for non-commercial search.  Heavy scraping without
authentication violates Reddit's Terms; we use the documented JSON endpoint
with appropriate rate limits and User-Agent.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from typing import Any, Dict, List
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

REDDIT_SEARCH = "https://www.reddit.com/search.json"

# Query types where Reddit is genuinely useful
_USEFUL_TYPES = {
    "complaint", "demand", "competitor", "manual_workflow",
    "failure_reason", "general", "pricing",
}


def _stable_id(url: str) -> str:
    return "RD" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _ev_type(query_type: str, title: str) -> EvidenceType:
    mapping: Dict[str, EvidenceType] = {
        "complaint": EvidenceType.COMPLAINT,
        "demand": EvidenceType.DEMAND,
        "competitor": EvidenceType.COMPETITOR,
        "pricing": EvidenceType.PRICING,
        "failure_reason": EvidenceType.FAILURE_REASON,
        "manual_workflow": EvidenceType.MANUAL_WORKFLOW,
    }
    return mapping.get(query_type, EvidenceType.GENERAL)


class RedditProvider(ResearchProvider):
    """Search Reddit for community discussions, complaints, and demand signals."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "Reddit"

    @property
    def is_available(self) -> bool:
        return True  # Public JSON API

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> List[EvidenceItem]:
        if query_type not in _USEFUL_TYPES:
            return []

        params = {
            "q": query,
            "sort": "relevance",
            "t": "year",
            "limit": min(max_results, 25),
            "type": "link",
        }

        headers = {
            # Reddit requires a non-empty User-Agent identifying the app
            "User-Agent": "AssumptionZero/0.1 (open-source research tool; contact: admin@example.com)",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.request_timeout,
                headers=headers,
                follow_redirects=True,
            ) as client:
                url = f"{REDDIT_SEARCH}?{urlencode(params)}"
                resp = await client.get(url)
                resp.raise_for_status()
                data: Dict[str, Any] = resp.json()
        except Exception as exc:
            logger.warning("Reddit search failed for %r: %s", query, exc)
            return []

        items: List[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        posts = data.get("data", {}).get("children", [])
        for child in posts[:max_results]:
            post = child.get("data", {})
            post_url = post.get("url", "")
            if not post_url or post_url.startswith("/"):
                post_url = "https://reddit.com" + post.get("permalink", "")

            title = post.get("title") or "Untitled"
            selftext = post.get("selftext", "")
            subreddit = post.get("subreddit", "")
            score = post.get("score", 0)
            num_comments = post.get("num_comments", 0)

            passage = f"r/{subreddit}: {title}"
            if selftext:
                passage += f" — {selftext[:300]}"
            passage += f" (↑{score}, {num_comments} comments)"

            created_utc = post.get("created_utc")
            pub_date: date | None = None
            if created_utc:
                try:
                    pub_date = datetime.utcfromtimestamp(float(created_utc)).date()
                except (ValueError, OSError):
                    pub_date = None

            relevance = min(1.0, max(0.1, score / 1000))

            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(post_url),
                    title=f"[Reddit r/{subreddit}] {title}",
                    url=post_url,
                    source_name="Reddit",
                    publication_date=pub_date,
                    retrieval_date=today,
                    passage=self._truncate(passage, 500),
                    search_query=query,
                    evidence_type=_ev_type(query_type, title),
                    reliability=ReliabilityLevel.LOW,
                    relevance_score=relevance,
                    retrieval_timestamp=now,
                    is_demo=False,
                )
            )

        logger.info("Reddit: %d posts for %r", len(items), query)
        return items
