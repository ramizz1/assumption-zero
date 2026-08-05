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
    # Use specific problem domain + name, never hardcode "app marketplace"
    queries.append({"query": f"{name} competitors {problem[:30]}", "type": "competitor"})
    queries.append({"query": f"best tools for {problem}", "type": "competitor"})
    queries.append({"query": f"top alternatives to {name}", "type": "competitor"})

    valid_comps = [
        c.strip() for c in known_comps.split(",")
        if c.strip() and c.strip().lower() not in IGNORE_COMPETITOR_WORDS
    ]

    if valid_comps:
        for comp in valid_comps[:4]:
            queries.append({"query": f"{comp} software features pricing", "type": "competitor"})
            queries.append({"query": f"{comp} vs {name} comparison", "type": "pricing"})
    else:
        queries.append({"query": f"top {problem[:40]} software 2024", "type": "competitor"})
        queries.append({"query": f"SaaS tools for {problem[:40]}", "type": "competitor"})

    # ── Open-source alternatives ──────────────────────────────────
    queries.append({"query": f"open source {problem[:40]} github", "type": "oss_alternative"})
    queries.append({"query": f"self hosted {problem[:30]} tool", "type": "oss_alternative"})

    # ── Customer complaints & pain ────────────────────────────────
    queries.append({"query": f"{customer[:30]} pain points {problem[:30]}", "type": "complaint"})
    queries.append({"query": f"problems with {problem[:40]} tools reddit", "type": "complaint"})

    # ── Demand indicators ─────────────────────────────────────────
    queries.append({"query": f"market demand {problem[:40]} {geography}", "type": "demand"})
    queries.append({"query": f"{customer[:30]} need {problem[:30]}", "type": "demand"})

    # ── Pricing evidence ──────────────────────────────────────────
    queries.append({"query": f"{problem[:40]} SaaS pricing tiers", "type": "pricing"})
    if model:
        queries.append({"query": f"{model} pricing {customer[:30]}", "type": "pricing"})

    # ── Existing manual workflows ─────────────────────────────────
    queries.append({"query": f"how {customer[:30]} manually does {problem[:30]}", "type": "manual_workflow"})

    # ── Market direction ──────────────────────────────────────────
    queries.append({"query": f"{problem[:40]} industry trends 2024", "type": "market_direction"})

    # ── Geographic relevance ──────────────────────────────────────
    if geography and geography != "global":
        queries.append({"query": f"{problem[:40]} market {geography}", "type": "geographic"})

    # ── Regulatory concerns ───────────────────────────────────────
    queries.append({"query": f"{problem[:30]} data privacy compliance regulations", "type": "regulatory"})

    # ── Failed products ───────────────────────────────────────────
    queries.append({"query": f"failed {problem[:30]} startup reasons", "type": "failed_product"})

    # ── Common failure reasons ────────────────────────────────────
    queries.append({"query": f"why startups fail in {problem[:30]} space", "type": "failure_reason"})

    # ── Distribution channels ─────────────────────────────────────
    queries.append({"query": f"how to acquire {customer[:30]} customers {problem[:25]}", "type": "distribution"})

    return queries
