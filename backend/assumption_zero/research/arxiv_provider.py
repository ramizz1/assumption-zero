"""
Arxiv research provider.

Queries the public Arxiv API (export.arxiv.org) for real-world scientific,
technical, algorithmic, and market research papers.
No API key required.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime
from urllib.parse import quote_plus

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

ARXIV_API = "http://export.arxiv.org/api/query"


def _stable_id(url: str) -> str:
    return "AX" + hashlib.sha1(url.encode()).hexdigest()[:8].upper()


class ArxivProvider(ResearchProvider):
    """Search Arxiv for scientific papers, algorithms, and technical research."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "Arxiv Research"

    @property
    def is_available(self) -> bool:
        return True

    async def search(
        self,
        query: str,
        query_type: str,
        idea: IdeaInput,
        max_results: int = 5,
    ) -> list[EvidenceItem]:
        # Only search Arxiv for relevant query types
        if query_type not in {
            "competitor",
            "oss_alternative",
            "market_direction",
            "general",
            "manual_workflow",
        }:
            return []

        clean_q = quote_plus(query)
        url = f"{ARXIV_API}?search_query=all:{clean_q}&start=0&max_results={max_results}"

        items: list[EvidenceItem] = []
        now = datetime.utcnow()
        today = date.today()

        try:
            async with httpx.AsyncClient(
                timeout=min(6.0, float(self._settings.request_timeout)),
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    xml = resp.text
                    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
                    for entry in entries:
                        title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                        summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                        id_m = re.search(r"<id>(.*?)</id>", entry)

                        if title_m and id_m:
                            title = title_m.group(1).replace("\n", " ").strip()
                            paper_url = id_m.group(1).strip()
                            summary = (
                                summary_m.group(1).replace("\n", " ").strip() if summary_m else ""
                            )

                            title_lower = title.lower()
                            summary_lower = summary.lower()

                            # Hard filter: skip known irrelevant academic domains
                            IRRELEVANT_KEYWORDS = {
                                "covid",
                                "virus",
                                "quark",
                                "polarisation",
                                "semimartingale",
                                "fluid antenna",
                                "clinical",
                                "medical",
                                "physics",
                                "chemistry",
                                "genomic",
                                "protein",
                                "earthquake",
                                "seismic",
                                "stellar",
                            }
                            if any(
                                ik in title_lower or ik in summary_lower
                                for ik in IRRELEVANT_KEYWORDS
                            ):
                                continue

                            # Dynamic relevance: require at least one word from the search query
                            query_words = set(re.sub(r"[^\w\s]", "", query.lower()).split()) - {
                                "the",
                                "a",
                                "an",
                                "for",
                                "and",
                                "or",
                                "in",
                                "of",
                                "to",
                                "is",
                                "with",
                                "on",
                                "at",
                                "by",
                                "from",
                                "this",
                                "that",
                                "how",
                                "why",
                            }
                            # Also accept general startup/tech relevance terms
                            ALWAYS_RELEVANT = {
                                "startup",
                                "market",
                                "saas",
                                "software",
                                "platform",
                                "revenue",
                                "pricing",
                                "user",
                                "customer",
                                "product",
                                "business",
                                "ai",
                                "machine learning",
                                "deep learning",
                                "algorithm",
                                "security",
                                "cybersecurity",
                                "cloud",
                                "api",
                                "mobile",
                                "web",
                                "app",
                                "data",
                                "privacy",
                                "compliance",
                                "automation",
                                "analytics",
                            }
                            combined_relevant = query_words | ALWAYS_RELEVANT
                            if not any(
                                rk in title_lower or rk in summary_lower for rk in combined_relevant
                            ):
                                continue

                            items.append(
                                EvidenceItem(
                                    evidence_id=_stable_id(paper_url),
                                    title=f"[Arxiv Paper] {title[:75]}",
                                    url=paper_url,
                                    evidence_origin="ArXiv",
                                    source_name="Arxiv Research",
                                    publication_date=None,
                                    retrieval_date=today,
                                    passage=self._truncate(f"Abstract: {summary}", 500),
                                    search_query=query,
                                    evidence_type=EvidenceType.DEMAND,
                                    reliability=ReliabilityLevel.HIGH,
                                    relevance_score=0.75,
                                    retrieval_timestamp=now,
                                    is_demo=False,
                                )
                            )
                    logger.info("ArxivProvider: %d papers for %r", len(items), query)
        except Exception as exc:
            logger.debug("ArxivProvider failed for %r: %s", query, exc)

        return items
