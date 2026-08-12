"""
Reddit research provider.

Uses Reddit search with DuckDuckGo fallback for community discussions,
complaints, and demand signals.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import quote_plus, urlencode

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
DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/"

_USEFUL_TYPES = {
    "complaint",
    "demand",
    "competitor",
    "manual_workflow",
    "failure_reason",
    "general",
    "pricing",
}


def _stable_id(url: str) -> str:
    return "RD" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


def _ev_type(query_type: str) -> EvidenceType:
    mapping: dict[str, EvidenceType] = {
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
        return True

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> list[EvidenceItem]:
        if query_type not in _USEFUL_TYPES:
            return []

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html",
        }

        # Try native Reddit search first
        params = {
            "q": query,
            "sort": "relevance",
            "t": "year",
            "limit": min(max_results, 15),
            "type": "link",
        }

        items: list[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        try:
            async with httpx.AsyncClient(
                timeout=min(5.0, float(self._settings.request_timeout)),
                headers=headers,
                follow_redirects=True,
            ) as client:
                url = f"{REDDIT_SEARCH}?{urlencode(params)}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data: dict[str, Any] = resp.json()
                    posts = data.get("data", {}).get("children", [])
                    for child in posts[:max_results]:
                        post = child.get("data", {})
                        post_url = post.get("url", "")
                        if not post_url or post_url.startswith("/"):
                            post_url = "https://reddit.com" + post.get("permalink", "")
                        title = post.get("title") or "Untitled"
                        selftext = post.get("selftext", "")
                        subreddit = post.get("subreddit", "discussion")
                        post.get("score", 0)

                        passage = f"r/{subreddit}: {title}"
                        if selftext:
                            passage += f" — {selftext[:250]}"

                        items.append(
                            EvidenceItem(
                                evidence_id=_stable_id(post_url),
                                title=f"[Reddit r/{subreddit}] {title}",
                                url=post_url,
                                evidence_origin=f"Reddit - r/{subreddit}",
                                source_name="Reddit",
                                publication_date=None,
                                retrieval_date=today,
                                passage=self._truncate(passage, 500),
                                search_query=query,
                                evidence_type=_ev_type(query_type),
                                reliability=ReliabilityLevel.LOW,
                                relevance_score=0.7,
                                retrieval_timestamp=now,
                                is_demo=False,
                            )
                        )
                    if items:
                        logger.info(
                            "Reddit native search returned %d items for %r", len(items), query
                        )
                        return items
        except Exception as exc:
            logger.debug("Reddit native search failed silently: %s", exc)

        # Fallback to DuckDuckGo search for Reddit threads
        try:
            ddg_url = f"{DUCKDUCKGO_HTML}?q=site:reddit.com+{quote_plus(query)}"
            async with httpx.AsyncClient(
                timeout=5.0,
                headers=headers,
                follow_redirects=True,
            ) as client:
                resp = await client.get(ddg_url)
                if resp.status_code == 200:
                    # Match links in DuckDuckGo HTML
                    matches = re.findall(
                        r'<a class="result__url" href="([^"]+)">.*?<a class="result__snippet[^">]*">(.*?)</a>',
                        resp.text,
                        re.DOTALL,
                    )
                    for link, snippet in matches[:max_results]:
                        clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                        if "reddit.com" in link:
                            items.append(
                                EvidenceItem(
                                    evidence_id=_stable_id(link),
                                    title=f"[Reddit via Web] {clean_snippet[:60]}",
                                    url=link,
                                    evidence_origin="Reddit Search",
                                    source_name="Reddit",
                                    publication_date=None,
                                    retrieval_date=today,
                                    passage=self._truncate(clean_snippet, 400),
                                    search_query=query,
                                    evidence_type=_ev_type(query_type),
                                    reliability=ReliabilityLevel.LOW,
                                    relevance_score=0.6,
                                    retrieval_timestamp=now,
                                    is_demo=False,
                                )
                            )
        except Exception as exc:
            logger.debug("Reddit DuckDuckGo fallback failed: %s", exc)

        return items
