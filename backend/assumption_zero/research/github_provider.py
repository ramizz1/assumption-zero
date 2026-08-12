"""
GitHub research provider.

Finds open-source competitors, alternatives, and related projects.
Uses the public GitHub Search API:
  https://docs.github.com/en/rest/search/search

Rate limits:
  - Unauthenticated: 10 requests/minute
  - With GITHUB_TOKEN: 30 requests/minute

Set GITHUB_TOKEN in .env for a higher limit.
Terms: GitHub's Terms of Service allow automated search API use.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime
from typing import Any

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

GITHUB_API = "https://api.github.com/search/repositories"


def _stable_id(url: str) -> str:
    return "GH" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


class GitHubProvider(ResearchProvider):
    """Search GitHub for open-source alternatives and related projects."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "GitHub"

    @property
    def is_available(self) -> bool:
        # GitHub public API works without a token
        return True

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self._settings.github_token:
            h["Authorization"] = f"Bearer {self._settings.github_token}"
        return h

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 10,
    ) -> list[EvidenceItem]:
        # Only search GitHub for competitor / oss_alternative queries
        if query_type not in ("competitor", "oss_alternative", "general"):
            return []

        params: dict[str, str | int] = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(max_results, 30),
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.request_timeout,
                headers=self._headers(),
            ) as client:
                resp = await client.get(GITHUB_API, params=params)
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()
        except Exception as exc:
            logger.debug("GitHub search skipped or rate limited for %r: %s", query, exc)
            return []

        items: list[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        for repo in data.get("items", [])[:max_results]:
            repo_url = repo.get("html_url", "")
            if not repo_url:
                continue
            stars = repo.get("stargazers_count", 0)
            desc = repo.get("description") or "No description provided"
            passage = (
                f"{desc.strip()} — ⭐ {stars:,} stars. "
                f"Language: {repo.get('language') or 'Unknown'}. "
                f"Last updated: {(repo.get('updated_at') or '')[:10]}."
            )
            # Relevance: use star count as a proxy (capped at 1.0)
            relevance = min(1.0, stars / 10000) if stars else 0.3

            items.append(
                EvidenceItem(
                    evidence_id=_stable_id(repo_url),
                    title=f"[GitHub] {repo.get('full_name', repo.get('name', 'unknown'))}",
                    url=repo_url,
                    evidence_origin=f"GitHub - {repo.get('full_name', 'Unknown')}",
                    source_name="GitHub",
                    publication_date=None,
                    retrieval_date=today,
                    passage=self._truncate(passage, 500),
                    search_query=query,
                    evidence_type=EvidenceType.OSS_ALTERNATIVE,
                    reliability=ReliabilityLevel.HIGH,  # GitHub data is first-party
                    relevance_score=relevance,
                    retrieval_timestamp=now,
                    is_demo=False,
                )
            )

        logger.info("GitHub: %d repos for %r", len(items), query)
        return items
