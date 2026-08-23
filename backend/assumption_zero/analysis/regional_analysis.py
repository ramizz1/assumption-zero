"""Deterministic regional demand analysis grounded only in collected evidence."""

from __future__ import annotations

import re

from assumption_zero.schemas import (
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    RegionalEvidenceSignal,
    RegionalMarketAnalysis,
    ReliabilityLevel,
)

_REGIONAL_TYPES = {
    EvidenceType.GEOGRAPHIC,
    EvidenceType.DEMAND,
    EvidenceType.COMPLAINT,
    EvidenceType.PRICING,
    EvidenceType.REGULATORY,
    EvidenceType.DISTRIBUTION,
    EvidenceType.MARKET_DIRECTION,
}

_DEMAND_PHRASES = (
    "adoption", "budget", "buyer", "buying", "customer demand", "complaint",
    "manual workflow", "pain point", "pay for", "purchase", "shortage", "spend",
    "switching", "time-consuming", "willingness to pay",
)
_IDEA_STOPWORDS = {
    "about", "after", "also", "because", "before", "business", "customer",
    "customers", "entirely", "existing", "have", "helps", "industry", "local",
    "market", "people", "product", "service", "services", "software", "solution",
    "target", "technology", "that", "their", "this", "tool", "tools", "using",
    "with", "without",
}


def _location_tokens(geography: str) -> list[str]:
    ignored = {"the", "and", "region", "market", "area", "city", "state", "province"}
    return [
        token.casefold()
        for token in re.findall(r"[^\W\d_]{2,}", geography, flags=re.UNICODE)
        if token.casefold() not in ignored
    ]


def _is_regional(item: EvidenceItem, geography: str) -> bool:
    if item.evidence_type == EvidenceType.GEOGRAPHIC:
        return True
    haystack = f"{item.title} {item.passage} {item.search_query} {item.evidence_origin}".casefold()
    tokens = _location_tokens(geography)
    return bool(tokens) and any(token in haystack for token in tokens)


def _idea_tokens(idea: IdeaInput) -> set[str]:
    text = " ".join((idea.name, idea.problem, idea.description, idea.solution or "", idea.target_customer))
    return {
        token.casefold() for token in re.findall(r"[^\W\d_]{4,}", text, flags=re.UNICODE)
        if token.casefold() not in _IDEA_STOPWORDS
    }


def is_commercial_demand_signal(item: EvidenceItem, idea: IdeaInput) -> bool:
    """Reject generic industry coverage and technically related papers as demand proof."""
    if item.evidence_type not in {EvidenceType.DEMAND, EvidenceType.COMPLAINT}:
        return False
    content = f"{item.title} {item.passage}".casefold()
    content_tokens = set(re.findall(r"[^\W\d_]{4,}", content, flags=re.UNICODE))
    idea_overlap = len(_idea_tokens(idea) & content_tokens)
    has_commercial_language = any(phrase in content for phrase in _DEMAND_PHRASES)
    return idea_overlap >= 2 and (item.evidence_type == EvidenceType.COMPLAINT or has_commercial_language)


def _signals(
    items: list[EvidenceItem], category: str, limit: int = 8
) -> list[RegionalEvidenceSignal]:
    return [
        RegionalEvidenceSignal(
            evidence_id=item.evidence_id,
            category=category,
            title=item.title,
            source_name=item.evidence_origin or item.source_name,
            relevance_score=item.relevance_score,
        )
        for item in sorted(items, key=lambda value: value.relevance_score, reverse=True)[:limit]
    ]


def generate_regional_analysis(
    idea: IdeaInput,
    evidence: list[EvidenceItem],
) -> RegionalMarketAnalysis:
    """Measure the strength and coverage of evidence specific to the requested geography."""
    regional = [
        item
        for item in evidence
        if item.evidence_type in _REGIONAL_TYPES and _is_regional(item, idea.geography)
    ]
    demand = [item for item in regional if is_commercial_demand_signal(item, idea)]
    pricing = [item for item in regional if item.evidence_type == EvidenceType.PRICING]
    regulatory = [item for item in regional if item.evidence_type == EvidenceType.REGULATORY]
    distribution = [item for item in regional if item.evidence_type == EvidenceType.DISTRIBUTION]
    sources = {item.source_name for item in regional}
    demand_sources = {item.source_name for item in demand}

    if demand:
        avg_relevance = sum(item.relevance_score for item in demand) / len(demand)
        high_reliability = sum(item.reliability == ReliabilityLevel.HIGH for item in demand)
        score = min(40.0, len(demand) * 10.0)
        score += min(20.0, len(demand_sources) * 7.0)
        score += min(15.0, high_reliability * 4.0)
        score += avg_relevance * 15.0
        score += min(10.0, len(pricing) * 5.0)
        demand_score = round(min(100.0, score), 1)
    else:
        demand_score = 0.0

    if len(demand) >= 5 and len(demand_sources) >= 3 and len(regional) >= 8:
        confidence = ConfidenceLevel.HIGH
    elif len(demand) >= 2 and len(demand_sources) >= 2:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.LOW

    if confidence == ConfidenceLevel.HIGH:
        summary = (
            f"Commercial demand evidence for {idea.geography} is well covered across {len(demand_sources)} relevant sources. "
            "This measures evidence strength, not the probability of success; confirm willingness to pay with local buyers."
        )
    elif demand:
        summary = (
            f"Some idea-relevant commercial evidence specific to {idea.geography} was found, but coverage is not strong enough for a confident demand claim. "
            "Use the cited signals as hypotheses and close the listed research gaps locally."
        )
    elif regional:
        summary = (
            f"Sources related to {idea.geography} were collected, but none met the stricter bar for idea-specific commercial demand. "
            "General market growth, technical research, and regulation are context—not proof that buyers want this offer."
        )
    else:
        summary = f"No evidence explicitly tied to {idea.geography} was collected. Global category evidence must not be treated as proof of regional demand."

    localization = [
        f"Validate pricing and purchasing power in {idea.currency or 'the local currency'}.",
        f"Test acquisition messages in {idea.market_language or 'the language used by local buyers'}.",
        f"Interview buyers in at least two sub-markets within {idea.geography} before generalizing demand.",
    ]
    if idea.regulatory_constraints:
        localization.append(f"Verify with a qualified local expert: {idea.regulatory_constraints}.")
    if idea.acquisition_channels:
        localization.append(f"Benchmark the stated channels locally: {idea.acquisition_channels}.")

    gaps: list[str] = []
    if len(demand) < 5:
        gaps.append(
            f"Collect at least five independent demand or pain signals from {idea.geography}."
        )
    if not pricing:
        gaps.append(
            f"Find local competitor prices and willingness-to-pay evidence in {idea.currency or idea.geography}."
        )
    if not regulatory:
        gaps.append(
            f"Confirm licenses, taxes, privacy, consumer-protection, and sector rules in {idea.geography}."
        )
    if not distribution:
        gaps.append(
            f"Identify locally trusted communities, partners, directories, and acquisition benchmarks in {idea.geography}."
        )
    if len(sources) < 3:
        gaps.append("Triangulate regional claims across at least three independent source types.")

    return RegionalMarketAnalysis(
        geography=idea.geography,
        demand_score=demand_score,
        confidence=confidence,
        evidence_count=len(regional),
        source_count=len(sources),
        summary=summary,
        demand_signals=_signals(demand, "demand"),
        pricing_signals=_signals(pricing, "pricing"),
        regulatory_signals=_signals(regulatory, "regulatory"),
        distribution_signals=_signals(distribution, "distribution"),
        localization_requirements=localization,
        research_gaps=gaps,
    )
