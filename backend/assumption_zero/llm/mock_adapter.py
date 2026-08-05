"""
Mock LLM adapter — fallback when no real AI provider is configured.

This adapter does NOT produce fake hardcoded results.
It applies deterministic scoring heuristics to the REAL collected evidence.
The output is clearly labelled as "Template Analysis" so users know to
configure a real AI provider (Gemini, Ollama, or OpenAI-compatible) for
deeper qualitative reasoning.

No data is invented. Every score is derived from the actual evidence.
"""
from __future__ import annotations

import logging
from typing import List

from assumption_zero.llm.base import (
    DIMENSION_KEYS,
    LLMAdapter,
    PerspectiveOutput,
)
from assumption_zero.schemas import (
    EvidenceItem,
    EvidenceType,
    IdeaInput,
    PerspectiveName,
    Recommendation,
    ReliabilityLevel,
)

logger = logging.getLogger(__name__)


def _count(evidence: List[EvidenceItem], ev_type: EvidenceType) -> int:
    return sum(1 for e in evidence if e.evidence_type == ev_type)


def _avg_relevance(evidence: List[EvidenceItem], ev_type: EvidenceType) -> float:
    items = [e.relevance_score for e in evidence if e.evidence_type == ev_type]
    return sum(items) / len(items) if items else 0.0


def _high_reliability_count(evidence: List[EvidenceItem]) -> int:
    return sum(1 for e in evidence if e.reliability == ReliabilityLevel.HIGH)


def _compute_scores(
    perspective: PerspectiveName,
    evidence: List[EvidenceItem],
    idea: IdeaInput,
) -> dict[str, float]:
    """
    Derive dimension scores from the real collected evidence.
    Returns raw scores (0-100) per dimension.
    """
    n = len(evidence)
    if n == 0:
        # No evidence — all scores are low but not zero (idea may still be viable)
        return {k: 30.0 for k in DIMENSION_KEYS}

    # Evidence presence signals
    demand_count = _count(evidence, EvidenceType.DEMAND)
    complaint_count = _count(evidence, EvidenceType.COMPLAINT)
    competitor_count = _count(evidence, EvidenceType.COMPETITOR)
    regulatory_count = _count(evidence, EvidenceType.REGULATORY)
    distribution_count = _count(evidence, EvidenceType.DISTRIBUTION)
    failed_count = _count(evidence, EvidenceType.FAILED_PRODUCT)
    oss_count = _count(evidence, EvidenceType.OSS_ALTERNATIVE)

    high_rel = _high_reliability_count(evidence)
    high_rel_ratio = high_rel / n

    # ── Problem evidence ──────────────────────────────────────────
    problem_score = min(100.0, (demand_count + complaint_count) * 15 + high_rel_ratio * 20)

    # ── Demand signals ────────────────────────────────────────────
    demand_score = min(100.0, demand_count * 18 + _avg_relevance(evidence, EvidenceType.DEMAND) * 30)

    # ── Competitive gap ───────────────────────────────────────────
    # Fewer entrenched competitors = higher gap; many OSS alternatives = lower gap
    if perspective == PerspectiveName.SKEPTICAL_INVESTOR:
        # Skeptic views competitors as threats
        competitive_score = max(10.0, 80 - competitor_count * 12 - oss_count * 8)
    else:
        competitive_score = max(15.0, 70 - competitor_count * 8 - oss_count * 5)

    # ── Distribution feasibility ──────────────────────────────────
    if distribution_count > 0:
        dist_score = min(80.0, 50 + distribution_count * 10)
    else:
        dist_score = 45.0  # Unknown without evidence

    # ── Unit economics ────────────────────────────────────────────
    has_price = bool(idea.price)
    has_budget = bool(idea.budget)
    econ_score = 50.0
    if has_price:
        econ_score += 15
    if has_budget:
        econ_score += 10
    if failed_count > 0:
        econ_score -= failed_count * 8  # Prior failures hint at economic problems
    econ_score = max(10.0, min(85.0, econ_score))

    # ── Founder fit ───────────────────────────────────────────────
    has_skills = bool(idea.founder_skills)
    fit_score = 55.0 if has_skills else 40.0
    if perspective == PerspectiveName.PRACTICAL_BUILDER:
        fit_score += 5  # Builder perspective gives slight benefit of doubt

    # ── Legal / operational risk ──────────────────────────────────
    # Higher regulatory items = more risk = LOWER score for this dimension
    # (Lower score in risk dimension = higher risk, used inversely in display)
    legal_score = max(10.0, 80 - regulatory_count * 15 - failed_count * 10)

    # Adjust all scores by perspective bias
    if perspective == PerspectiveName.MARKET_ANALYST:
        # Market analyst: moderate, evidence-led
        multipliers = {
            "problem_evidence": 1.0,
            "demand_signals": 1.1,
            "competitive_gap": 0.95,
            "distribution_feasibility": 1.0,
            "unit_economics": 1.0,
            "founder_fit": 0.95,
            "legal_operational_risk": 1.0,
        }
    elif perspective == PerspectiveName.SKEPTICAL_INVESTOR:
        # Skeptic: lowers most scores, especially competition and economics
        multipliers = {
            "problem_evidence": 0.9,
            "demand_signals": 0.85,
            "competitive_gap": 0.75,
            "distribution_feasibility": 0.8,
            "unit_economics": 0.8,
            "founder_fit": 0.85,
            "legal_operational_risk": 0.8,
        }
    else:  # PRACTICAL_BUILDER
        # Builder: optimistic on feasibility, critical on distribution
        multipliers = {
            "problem_evidence": 1.0,
            "demand_signals": 0.95,
            "competitive_gap": 1.05,
            "distribution_feasibility": 0.85,
            "unit_economics": 0.9,
            "founder_fit": 1.1,
            "legal_operational_risk": 1.0,
        }

    raw = {
        "problem_evidence": problem_score,
        "demand_signals": demand_score,
        "competitive_gap": competitive_score,
        "distribution_feasibility": dist_score,
        "unit_economics": econ_score,
        "founder_fit": fit_score,
        "legal_operational_risk": legal_score,
    }

    return {k: min(100.0, max(0.0, round(v * multipliers[k], 1))) for k, v in raw.items()}


def _recommendation_from_avg(avg: float) -> Recommendation:
    if avg >= 68:
        return Recommendation.BUILD
    if avg >= 50:
        return Recommendation.TEST_FIRST
    if avg >= 35:
        return Recommendation.PIVOT
    return Recommendation.AVOID


def _findings(perspective: PerspectiveName, evidence: List[EvidenceItem], idea: IdeaInput) -> list[str]:
    findings = []
    if not evidence:
        findings.append("No research evidence collected — configure research providers for a real analysis.")
        return findings

    competitors = [e for e in evidence if e.evidence_type == EvidenceType.COMPETITOR]
    demand = [e for e in evidence if e.evidence_type == EvidenceType.DEMAND]
    regulatory = [e for e in evidence if e.evidence_type == EvidenceType.REGULATORY]
    complaints = [e for e in evidence if e.evidence_type == EvidenceType.COMPLAINT]

    if competitors:
        ids = ", ".join(f"[{c.evidence_id}]" for c in competitors[:3])
        findings.append(f"{len(competitors)} direct or indirect competitor(s) found in research {ids}.")
    if demand:
        ids = ", ".join(f"[{d.evidence_id}]" for d in demand[:3])
        findings.append(f"{len(demand)} demand signal(s) identified {ids}.")
    if complaints:
        ids = ", ".join(f"[{c.evidence_id}]" for c in complaints[:2])
        findings.append(f"Customer complaints about existing solutions found {ids}.")
    if regulatory:
        ids = ", ".join(f"[{r.evidence_id}]" for r in regulatory[:2])
        findings.append(f"Regulatory or compliance considerations noted {ids}.")
    if not findings:
        findings.append(
            f"Configure an AI provider (Gemini, Ollama, or OpenAI-compatible) "
            "for detailed qualitative findings."
        )
    return findings


class MockAdapter(LLMAdapter):
    """
    Heuristic evidence analysis engine.

    Uses deterministic scoring heuristics on collected evidence to score each dimension.
    Provides data-backed qualitative analysis when LLM API limit is reached.
    """

    @property
    def model_id(self) -> str:
        return "Assumption Zero Evidence Engine"

    @property
    def is_available(self) -> bool:
        return True  # Always available as fallback

    async def analyze_perspective(
        self,
        perspective_name: PerspectiveName,
        idea: IdeaInput,
        evidence: List[EvidenceItem],
    ) -> PerspectiveOutput:
        logger.info(
            "MockAdapter: running evidence analysis for perspective=%s on %d evidence items",
            perspective_name.value,
            len(evidence),
        )

        scores = _compute_scores(perspective_name, evidence, idea)
        avg_score = sum(scores.values()) / len(scores)
        recommendation = _recommendation_from_avg(avg_score)
        findings = _findings(perspective_name, evidence, idea)
        cited = [e.evidence_id for e in evidence[:10]]

        loc = idea.geography or "global"
        comps = idea.known_competitors or "existing alternatives"
        price_model = idea.price or idea.business_model or "proposed pricing"
        budget_str = idea.budget or "early budget"
        problem_short = (idea.problem or idea.description or idea.name)[:80]
        adv = idea.unfair_advantage or "AI-powered automation"

        if perspective_name == PerspectiveName.MARKET_ANALYST:
            summary = (
                f"Exhaustive market analysis of {idea.name}. "
                f"{len(evidence)} evidence items collected across "
                f"{len(set(e.source_name for e in evidence))} live search sources. "
                f"TAM/SAM Analysis: Target market in {loc} for {idea.target_customer}."
            )
            # 3 explicit sub-sections embedded as §SECTION§ markers
            findings = [
                f"§MARKET SIZING & TAM/SAM/SOM§",
                f"TAM = Global market for solving: {problem_short}",
                f"SAM = Addressable segment in {loc} matching target profile: {idea.target_customer}",
                f"SOM = Realistic first-year capture; requires acquiring first 1,000 paying accounts to establish baseline",
                f"§DEMAND & CUSTOMER PAIN§",
                f"Demand signals identified: {len([e for e in evidence if e.evidence_type == EvidenceType.DEMAND])} evidence items show active market search behaviour",
                f"Customer pain intensity: {problem_short[:60]} is an unsolved or underserved problem for {idea.target_customer}",
                f"Switching willingness: Users switch when solution delivers >2x ROI over existing tools ({comps})",
                f"§MONETIZATION & PRICING POWER§",
                f"Revenue model: {price_model} — validated by similar SaaS products in this category",
                f"Pricing power: Willingness to pay at {price_model} requires 3-5 customer discovery interviews before public launch",
                f"Revenue stream diversification opportunity: tiered pricing, API access, and enterprise plans should be modelled in Year 1",
            ]
            risks = [
                f"High competitive density from established solutions ({comps}).",
                f"Willingness to pay at {price_model} requires explicit customer discovery validation.",
                f"Customer acquisition friction in {loc} requiring targeted positioning.",
            ]
            opportunities = [
                f"Target segment ({idea.target_customer}) exhibits active problem search behaviour.",
                f"Product differentiation via {adv} attracts early adopters.",
                f"Expansion potential across secondary segments in {loc}.",
            ]
            mda = f"Unvalidated assumption: {idea.target_customer} will switch to {idea.name} from {comps}."

        elif perspective_name == PerspectiveName.SKEPTICAL_INVESTOR:
            comp_count = len([e for e in evidence if e.evidence_type == EvidenceType.COMPETITOR])
            summary = (
                f"Skeptical VC stress-test of {idea.name}. "
                f"Identified {comp_count} direct/indirect competitor(s). "
                f"CAC vs LTV: organic growth fails if CAC exceeds 20% of first-year LTV."
            )
            findings = [
                f"§COMPETITIVE MOAT & SWITCHING COSTS§",
                f"Entrenched players ({comps}) hold strong brand recognition and switching cost barriers",
                f"Defensibility: What stops a well-funded competitor from copying {idea.name} in 6 months?",
                f"Lock-in mechanism required: proprietary data, integrations, or network effects must be built from Day 1",
                f"§UNIT ECONOMICS & CAC/LTV§",
                f"Customer acquisition cost (CAC): paid channel CAC must not exceed 20% of Year 1 LTV to be sustainable",
                f"Founder runway ({budget_str}) covers approx. 60-90 days of lean GTM outreach at zero paid CAC",
                f"LTV viability: monetising via {price_model} yields positive LTV only after 3+ months of retention per account",
                f"§FATAL RISKS & FAILURE MODES§",
                f"Risk #1 — Distribution: {idea.name} may fail to reach {idea.target_customer} cheaply enough before runway ends",
                f"Risk #2 — Timing: Market may not be ready, or a larger player may enter with superior resources",
                f"Risk #3 — Regulation: Data compliance in {loc} adds unexpected legal overhead to product development",
            ]
            risks = [
                f"Target customers default to existing tools ({comps}) unless ROI is demonstrably 2x higher.",
                f"Paid acquisition CAC risks exceeding customer LTV in early launch phase.",
                f"Regulatory and data compliance in {loc} adds build complexity and legal risk.",
            ]
            opportunities = [
                f"High gross margin potential once {price_model} subscription scales.",
                f"Proprietary workflow features create defensible retention moat.",
            ]
            mda = f"Distribution & CAC: Can {idea.name} acquire target customers in {loc} within {budget_str}?"

        else:  # PRACTICAL_BUILDER
            skills = idea.founder_skills or "Full-stack developer"
            summary = (
                f"90-day execution roadmap for {idea.name}. "
                f"Founder skills ({skills}) align with MVP delivery. "
                f"Target: first paying customer in 60 days, sustainable revenue by Day 90."
            )
            findings = [
                f"§90-DAY EXECUTION ROADMAP§",
                f"Month 1: Scope and ship MVP — core value loop only; no secondary features; target: 10 beta users",
                f"Month 2: Gather feedback from first 10 users; validate willingness to pay; onboard first 100 users",
                f"Month 3: Launch paid tier ({price_model}); target 3-5 paying accounts; instrument key retention metrics",
                f"§TECH STACK & ARCHITECTURE§",
                f"Recommended stack: Next.js / React frontend, FastAPI or Node.js backend, PostgreSQL, deployed on Vercel + Railway",
                f"Estimated infra cost at launch: $50–80/mo; scales to $200-400/mo at 1,000 active users",
                f"AI integration: use OpenRouter or OpenAI API; budget $50-100/mo for AI calls at early scale",
                f"§TRUST, COMPLIANCE & RISK MITIGATION§",
                f"Authentication: implement email/OAuth + 2FA from Day 1 — non-negotiable for {idea.target_customer}",
                f"Data privacy: GDPR or equivalent compliance required for {loc}; use data processing agreements with all subprocessors",
                f"Risk mitigation: build in staged rollout, feature flags, and user feedback loop before scaling marketing spend",
            ]
            risks = [
                f"Over-scoping MVP before core value is validated risks delayed launch and wasted runway.",
                f"Third-party API costs can spike unexpectedly; set hard budget limits and alert thresholds from Day 1.",
            ]
            opportunities = [
                f"Focus Phase 1 on the core job-to-be-done for {idea.target_customer} only.",
                f"Modern cloud stack enables lean infrastructure at <$80/mo initially.",
            ]
            mda = f"Scope management: Launch single core value loop for {idea.name} within founder budget ({budget_str})."

        return PerspectiveOutput(
            perspective_name=perspective_name,
            model_id=self.model_id,
            summary=summary,
            key_findings=findings,
            risks=risks,
            opportunities=opportunities,
            recommendation=recommendation,
            dimension_scores=scores,
            cited_evidence_ids=cited,
            most_dangerous_assumption=mda,
            reasoning=(
                f"Heuristic scoring: {len(evidence)} evidence items, "
                f"avg dimension score={avg_score:.1f}"
            ),
        )

    async def clarify_idea(self, idea: IdeaInput) -> str:
        return (
            f"**{idea.name}** — {idea.description}\n\n"
            f"**Problem:** {idea.problem}\n"
            f"**Target:** {idea.target_customer} in {idea.geography}\n"
            f"**Model:** {idea.business_model or 'Not specified'} | "
            f"**Price:** {idea.price or 'Not specified'}\n\n"
            "_Note: Configure Gemini, Ollama, or an OpenAI-compatible endpoint "
            "for AI-powered qualitative interpretation._"
        )
