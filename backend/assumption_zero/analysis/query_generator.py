"""
Research query generator.

Produces clean, concise queries across categories for a given idea.
Each query is formatted to be search-engine-friendly (short phrases, no paragraph dumps).
"""
from __future__ import annotations

import re
from typing import Dict, List

from assumption_zero.schemas import IdeaInput

IGNORE_COMPETITOR_WORDS = {"idk", "none", "no", "n/a", "unknown", "nothing", "no idea", "dont know", "don't know", "na"}

QUERY_TYPES = [
    "competitor",
    "oss_alternative",
    "complaint",
    "demand",
    "pricing",
    "manual_workflow",
    "market_direction",
    "geographic",
    "regulatory",
    "failed_product",
    "failure_reason",
    "distribution",
    "general",
]


def _clean_phrase(text: str, max_words: int = 5) -> str:
    """Extract up to `max_words` clean words from text for search queries."""
    if not text:
        return ""
    # Strip parentheticals and punctuation
    cleaned = re.sub(r"\(.*?\)", "", text)
    cleaned = re.sub(r"[^\w\s-]", " ", cleaned)
    words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
    return " ".join(words[:max_words])


def generate_queries(idea: IdeaInput) -> List[Dict[str, str]]:
    """
    Generate targeted research queries for an idea.

    Returns a list of dicts with keys: 'query' and 'type'.
    """
    name = idea.name
    problem = _clean_phrase(idea.problem, max_words=5) or name
    customer = _clean_phrase(idea.target_customer, max_words=4) or "customers"
    geography = idea.geography or "global"
    model = idea.business_model or ""
    known_comps = idea.known_competitors or ""

    queries: List[Dict[str, str]] = []

    # ── Direct competitors ────────────────────────────────────────
    queries.append({"query": f"best apps for {problem}", "type": "competitor"})
    queries.append({"query": f"top alternatives to {name}", "type": "competitor"})

    valid_comps = [
        c.strip() for c in known_comps.split(",")
        if c.strip() and c.strip().lower() not in IGNORE_COMPETITOR_WORDS
    ]

    if valid_comps:
        for comp in valid_comps[:4]:
            queries.append({"query": f"{comp} software features pricing", "type": "competitor"})
            queries.append({"query": f"{comp} alternatives reviews", "type": "pricing"})
    else:
        queries.append({"query": f"top tools for {problem}", "type": "competitor"})
        queries.append({"query": f"apps like {name} {problem}", "type": "competitor"})

    # ── Open-source alternatives ──────────────────────────────────
    queries.append({"query": f"open source {name} github", "type": "oss_alternative"})
    queries.append({"query": f"open source {problem} tool", "type": "oss_alternative"})

    # ── Customer complaints ───────────────────────────────────────
    queries.append({"query": f"{customer} complaints {problem}", "type": "complaint"})
    queries.append({"query": f"{problem} frustration app store reviews", "type": "complaint"})

    # ── Demand indicators ─────────────────────────────────────────
    queries.append({"query": f"demand for {problem} {geography}", "type": "demand"})
    queries.append({"query": f"{customer} looking for {problem} app", "type": "demand"})

    # ── Pricing evidence ──────────────────────────────────────────
    queries.append({"query": f"{problem} subscription pricing comparison", "type": "pricing"})
    if model:
        queries.append({"query": f"{model} pricing {customer}", "type": "pricing"})

    # ── Existing manual workflows ─────────────────────────────────
    queries.append({"query": f"{customer} solve {problem} manually", "type": "manual_workflow"})

    # ── Market direction ──────────────────────────────────────────
    queries.append({"query": f"{problem} market trends", "type": "market_direction"})

    # ── Geographic relevance ──────────────────────────────────────
    queries.append({"query": f"{problem} market {geography}", "type": "geographic"})

    # ── Regulatory concerns ───────────────────────────────────────
    queries.append({"query": f"{problem} regulations data privacy {geography}", "type": "regulatory"})

    # ── Failed products ───────────────────────────────────────────
    queries.append({"query": f"failed {problem} startups", "type": "failed_product"})

    # ── Common failure reasons ────────────────────────────────────
    queries.append({"query": f"why {customer} don't pay for {problem}", "type": "failure_reason"})

    # ── Distribution channels ─────────────────────────────────────
    queries.append({"query": f"customer acquisition for {problem} app", "type": "distribution"})

    return queries
