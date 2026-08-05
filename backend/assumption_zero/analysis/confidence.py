"""
Evidence Confidence calculator.

Calculated independently of the Opportunity Score using:
  - Number of relevant sources
  - Source diversity (provider variety)
  - Source reliability ratings
  - Source recency
  - Agreement vs contradiction between sources
  - Percentage of cited claims with valid evidence IDs

A high Opportunity Score backed by weak evidence shows LOW confidence.
"""
from __future__ import annotations

from datetime import date
from typing import List

from assumption_zero.schemas import (
    AnalysisPerspective,
    ConfidenceLevel,
    EvidenceItem,
    ReliabilityLevel,
)


def calculate_evidence_confidence(
    evidence: List[EvidenceItem],
    perspectives: List[AnalysisPerspective],
) -> ConfidenceLevel:
    """
    Return Low / Medium / High evidence confidence.

    Score breakdown (total 100):
      source_count          0-25   (more evidence = more confidence)
      source_diversity      0-20   (unique providers count)
      reliability_quality   0-25   (ratio of high-reliability items)
      recency               0-15   (fraction of items from last 2 years)
      citation_validity     0-15   (fraction of AI citations that are valid)
    """
    if not evidence:
        return ConfidenceLevel.LOW

    valid_ids = {e.evidence_id for e in evidence}
    n = len(evidence)

    # ── Source count (0-25) ───────────────────────────────────────
    source_count_score = min(25.0, n * 2.5)

    # ── Source diversity (0-20) ───────────────────────────────────
    unique_providers = len({e.source_name for e in evidence})
    diversity_score = min(20.0, unique_providers * 5.0)

    # ── Reliability quality (0-25) ────────────────────────────────
    high = sum(1 for e in evidence if e.reliability == ReliabilityLevel.HIGH)
    medium = sum(1 for e in evidence if e.reliability == ReliabilityLevel.MEDIUM)
    reliability_score = min(25.0, (high * 3.0 + medium * 1.5))

    # ── Recency (0-15): items published within last 2 years ───────
    today = date.today()
    recent = sum(
        1 for e in evidence
        if e.publication_date and (today - e.publication_date).days <= 730
    )
    recency_score = min(15.0, (recent / n) * 15.0) if n else 0

    # ── Citation validity (0-15) ──────────────────────────────────
    all_cited: List[str] = []
    all_invalid: List[str] = []
    for p in perspectives:
        all_cited.extend(p.cited_evidence_ids)
        all_invalid.extend(p.invalid_citations)

    if all_cited:
        valid_fraction = max(0.0, (len(all_cited) - len(all_invalid)) / len(all_cited))
        citation_score = valid_fraction * 15.0
    else:
        citation_score = 5.0  # No citations at all = partial score

    total = (
        source_count_score
        + diversity_score
        + reliability_score
        + recency_score
        + citation_score
    )

    if total >= 65:
        return ConfidenceLevel.HIGH
    if total >= 35:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
