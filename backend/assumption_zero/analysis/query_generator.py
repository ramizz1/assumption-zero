"""
Research query generator.

Produces focused queries across 13 categories for a given idea.
Each query is tagged with its type so providers can route efficiently.
"""
from __future__ import annotations

from typing import Dict, List

from assumption_zero.schemas import IdeaInput

# Types of queries we generate — maps to EvidenceType categories
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


def generate_queries(idea: IdeaInput) -> List[Dict[str, str]]:
    """
    Generate targeted research queries for an idea.

    Returns a list of dicts with keys: 'query' and 'type'.
    """
    name = idea.name
    problem = idea.problem[:120]   # Truncate for query use
    customer = idea.target_customer[:80]
    geography = idea.geography
    model = idea.business_model or ""
    known_comps = idea.known_competitors or ""

    queries: List[Dict[str, str]] = []

    # ── Direct competitors ────────────────────────────────────────
    queries.append({"query": f"{name} competitors alternatives", "type": "competitor"})
    queries.append({"query": f"best software for {problem}", "type": "competitor"})
    if known_comps:
        for comp in known_comps.split(",")[:3]:
            comp = comp.strip()
            if comp:
                queries.append({"query": f"{comp} pricing features reviews", "type": "competitor"})

    # ── Open-source alternatives ──────────────────────────────────
    queries.append({"query": f"open source {name} github", "type": "oss_alternative"})
    queries.append({"query": f"open source {problem} tool", "type": "oss_alternative"})

    # ── Customer complaints ───────────────────────────────────────
    queries.append({"query": f"{customer} complaints problems {problem}", "type": "complaint"})
    queries.append({"query": f"alternatives to {name} reddit", "type": "complaint"})

    # ── Demand indicators ─────────────────────────────────────────
    queries.append({"query": f"demand for {problem} solution {geography}", "type": "demand"})
    queries.append({"query": f"{customer} need help {problem}", "type": "demand"})
    queries.append({"query": f"how many {customer} use {problem} tools", "type": "demand"})

    # ── Pricing evidence ──────────────────────────────────────────
    queries.append({"query": f"{problem} software pricing comparison 2024", "type": "pricing"})
    if model:
        queries.append({"query": f"{model} pricing model {customer}", "type": "pricing"})

    # ── Existing manual workflows ─────────────────────────────────
    queries.append({"query": f"how {customer} currently solve {problem} manually", "type": "manual_workflow"})
    queries.append({"query": f"{customer} workflow without software {problem}", "type": "manual_workflow"})

    # ── Market direction ──────────────────────────────────────────
    queries.append({"query": f"{problem} market trends 2024 2025", "type": "market_direction"})
    queries.append({"query": f"{name} industry growth forecast", "type": "market_direction"})

    # ── Geographic relevance ──────────────────────────────────────
    queries.append({"query": f"{problem} market {geography}", "type": "geographic"})
    queries.append({"query": f"{customer} {geography} market size", "type": "geographic"})

    # ── Regulatory concerns ───────────────────────────────────────
    queries.append({"query": f"{problem} regulations compliance {geography}", "type": "regulatory"})
    queries.append({"query": f"{customer} data privacy legal requirements", "type": "regulatory"})

    # ── Failed products ───────────────────────────────────────────
    queries.append({"query": f"failed {problem} startups {geography}", "type": "failed_product"})
    queries.append({"query": f"why {name} similar companies failed", "type": "failed_product"})

    # ── Common failure reasons ────────────────────────────────────
    queries.append({"query": f"startup failure reasons {problem} market", "type": "failure_reason"})
    queries.append({"query": f"why {customer} don't buy {problem} software", "type": "failure_reason"})

    # ── Distribution channels ─────────────────────────────────────
    queries.append({"query": f"how to sell {problem} software to {customer}", "type": "distribution"})
    queries.append({"query": f"marketing channels {customer} software {geography}", "type": "distribution"})

    return queries
