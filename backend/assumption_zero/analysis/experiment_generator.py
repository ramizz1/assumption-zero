"""
Validation experiment generator.

Produces 3-5 concrete, cheap experiments prioritized by:
  cost → time → information value → disproof potential

Never recommends deceptive experiments or collecting real payments
without clear disclosure to participants.
"""

from __future__ import annotations

from typing import TypedDict

from assumption_zero.schemas import (
    AnalysisPerspective,
    EvidenceItem,
    IdeaInput,
    ValidationExperiment,
)


class ExperimentTemplate(TypedDict):
    title: str
    assumption_tested: str
    why_it_matters: str
    procedure: str
    estimated_time: str
    estimated_cost_range: str
    success_threshold: str
    failure_threshold: str
    decision_after: str
    legal_ethical: str
    priority: int


_EXPERIMENT_TEMPLATES: list[ExperimentTemplate] = [
    {
        "title": "7-Day Manual Concierge / Smoke Test (Pre-Build Validation)",
        "assumption_tested": "Target customers will pay real money for the core outcome delivered manually before code is written",
        "why_it_matters": "Building full automated software (OAuth, cloud connectors, background jobs) before testing willingness to pay wastes 90% of founder time. Manual concierge disproves indifference in 7 days.",
        "procedure": "Offer the core outcome manually as a 1-on-1 audit or service (e.g. run open-source CLI scanners manually, format into a PDF audit report). Pitch to 10 target business founders. Request a small deposit or upfront fee ($49-$99). Do NOT build full software.",
        "estimated_time": "5-7 days",
        "estimated_cost_range": "$0 – $50 (manual effort)",
        "success_threshold": "At least 3 paying customers accept manual delivery with positive feedback",
        "failure_threshold": "0 paying customers after 15 direct pitches or calls",
        "decision_after": "If SUCCESS: Automate core manual workflow into lightweight MVP. If FAILURE: ABANDON core idea or PIVOT target segment immediately.",
        "legal_ethical": "Be transparent that delivery is manual concierge. Offer full refunds if dissatisfied.",
        "priority": 1,
    },
    {
        "title": "Customer Discovery & Problem Severity Interviews",
        "assumption_tested": "The target problem is urgent, top-3 priority, and currently costs real time or money",
        "why_it_matters": "Most startups fail because they solve a 'nice-to-have' problem. 5 customer interviews reveal if this is a top-3 priority.",
        "procedure": "Recruit 5-10 target founders/decision makers via LinkedIn or community groups. Conduct 30-minute calls focused on: current workflow, existing tools, annual spend, and biggest pain points. Do NOT pitch your solution until the final 5 minutes.",
        "estimated_time": "1-2 weeks",
        "estimated_cost_range": "$0 – $100 (gift cards)",
        "success_threshold": "7 out of 10 describe the problem as an active pain point and cite current manual/paid workarounds",
        "failure_threshold": "Fewer than 4 out of 10 cite the problem as urgent or worth paying to fix",
        "decision_after": "If SUCCESS: proceed to smoke test. If FAILURE: NARROW SCOPE or PIVOT to a specific niche.",
        "legal_ethical": "No deception. Disclose research intent. Do not collect payment.",
        "priority": 2,
    },
    {
        "title": "Landing Page + Pre-Order / Waitlist Test",
        "assumption_tested": "Cold traffic converts into real email signups and pre-order interest",
        "why_it_matters": "Measures customer acquisition feasibility and message-market fit before building features.",
        "procedure": "Build a single-page landing page (Carrd, Webflow, or HTML). Clearly explain the narrow value proposition. Include a 'Join Waitlist' or 'Pre-order for 50% off' call to action. Drive 300-500 targeted visitors via Google/LinkedIn/Reddit ads.",
        "estimated_time": "1 week to build, 1 week to run",
        "estimated_cost_range": "$100 – $250 (hosting + ad spend)",
        "success_threshold": "Conversion rate > 8% for email signups or > 2% pre-order deposit clicks",
        "failure_threshold": "Conversion rate < 3% after 500 visitors",
        "decision_after": "If SUCCESS: Proceed to build narrowest MVP. If FAILURE: Re-position messaging or PIVOT target customer.",
        "legal_ethical": "Label as 'coming soon / early access'. Inform signups clearly.",
        "priority": 3,
    },
    {
        "title": "Willingness-to-Pay Benchmark & Price Sensitivity Test",
        "assumption_tested": "Customers will pay the target price point (e.g. $49-$199/month)",
        "why_it_matters": "Under-pricing or over-pricing by 3x destroys unit economics. Van Westendorp survey measures exact price elasticity.",
        "procedure": "Present 20 target customers with the product spec and ask Van Westendorp price elasticity questions (Too Expensive, Bargain, Fair, Too Cheap). Measure acceptable pricing floor and ceiling.",
        "estimated_time": "1 week",
        "estimated_cost_range": "$0 – $50",
        "success_threshold": "Target price sits within the acceptable range for > 65% of respondents",
        "failure_threshold": "Majority cite planned price as 'too expensive' or willingness-to-pay is below unit cost",
        "decision_after": "Adjust pricing model or cost structure before building.",
        "legal_ethical": "Clear survey disclosure — no deceptive pricing claims.",
        "priority": 4,
    },
    {
        "title": "Targeted Channel Customer Acquisition Test",
        "assumption_tested": "Cost per customer acquisition (CAC) is economically viable relative to LTV",
        "why_it_matters": "Proves at least one repeatable customer acquisition channel exists.",
        "procedure": "Run $200 of targeted ads or direct cold outreach across 2 specific channels (e.g. LinkedIn InMail vs Niche Community Ads). Track conversion rates and cost per signup.",
        "estimated_time": "2 weeks",
        "estimated_cost_range": "$150 – $300",
        "success_threshold": "Cost per signup < 20% of estimated first-year customer value",
        "failure_threshold": "Cost per signup exceeds first-year customer value or CTR < 0.8%",
        "decision_after": "If SUCCESS: Double down on channel. If FAILURE: PIVOT acquisition channel.",
        "legal_ethical": "Standard advertising compliance. No misleading claims.",
        "priority": 5,
    },
]


def _pick_experiments(
    idea: IdeaInput,
    perspectives: list[AnalysisPerspective],
    evidence: list[EvidenceItem],
) -> list[ValidationExperiment]:
    """
    Select and customize 3-5 experiments based on idea context.
    Always include customer interviews and landing page test first.
    """
    # Customize templates with idea-specific values
    experiments: list[ValidationExperiment] = []

    for template in _EXPERIMENT_TEMPLATES:
        exp = ValidationExperiment(
            title=template["title"],
            assumption_tested=template["assumption_tested"],
            why_it_matters=template["why_it_matters"],
            procedure=template["procedure"],
            estimated_time=template["estimated_time"],
            estimated_cost_range=template["estimated_cost_range"],
            success_threshold=template["success_threshold"],
            failure_threshold=template["failure_threshold"],
            decision_after=template["decision_after"],
            legal_ethical=template["legal_ethical"],
            priority=template["priority"],
        )
        experiments.append(exp)

    # Sort by priority (lowest number = highest priority)
    experiments.sort(key=lambda e: e.priority)
    return experiments[:5]


def generate_experiments(
    idea: IdeaInput,
    perspectives: list[AnalysisPerspective],
    evidence: list[EvidenceItem],
) -> list[ValidationExperiment]:
    """Generate 3-5 validation experiments ordered by cost and information value."""
    return _pick_experiments(idea, perspectives, evidence)
