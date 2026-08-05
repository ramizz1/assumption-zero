"""
Validation experiment generator.

Produces 3-5 concrete, cheap experiments prioritized by:
  cost → time → information value → disproof potential

Never recommends deceptive experiments or collecting real payments
without clear disclosure to participants.
"""
from __future__ import annotations

from typing import List

from assumption_zero.schemas import (
    AnalysisPerspective,
    EvidenceItem,
    IdeaInput,
    Recommendation,
    ValidationExperiment,
)

_EXPERIMENT_TEMPLATES = [
    {
        "title": "Customer Discovery Interviews",
        "assumption_tested": "The problem is real and painful enough to motivate purchasing",
        "why_it_matters": "Most startups fail because they build for a problem that is not painful enough to drive action. 5 conversations can disprove this cheaply.",
        "procedure": "Recruit 5-10 people matching the target customer profile via LinkedIn, Reddit, or community groups. Run 30-minute calls focused on: current workflow, biggest frustrations, what they have tried, and what they would pay to fix it. Do NOT pitch the product.",
        "estimated_time": "2-3 weeks",
        "estimated_cost_range": "$0 – $200 (incentives)",
        "success_threshold": "7 out of 10 express the specific problem unprompted and say they actively looked for a solution",
        "failure_threshold": "Fewer than 4 out of 10 describe the problem as a real pain point",
        "decision_after": "If success: proceed to landing page test. If failure: pivot problem statement or target customer.",
        "legal_ethical": "No deception. Be transparent that you are researching a potential product. Do not collect payment.",
        "priority": 1,
    },
    {
        "title": "Landing Page + Waitlist Test",
        "assumption_tested": "Target customers are interested enough to sign up with their real email",
        "why_it_matters": "Email sign-ups are weak but cheap signals of real interest. They disprove complete indifference.",
        "procedure": "Build a single-page website (Carrd, Webflow, or static HTML). Describe the product clearly. Add an email capture form ('Join waitlist'). Run $100-200 of targeted advertising on Google or Reddit to the audience. Track conversion rate.",
        "estimated_time": "1 week to build, 2 weeks to run",
        "estimated_cost_range": "$100 – $300 (hosting + ads)",
        "success_threshold": "Conversion rate above 8% (visitors who sign up)",
        "failure_threshold": "Conversion rate below 3% after 500 visitors",
        "decision_after": "If success: run pricing test or concierge. If failure: revise positioning or change target audience.",
        "legal_ethical": "Do not imply the product exists if it does not. Label as 'coming soon'. Inform signups they are on a waitlist for a product in development.",
        "priority": 2,
    },
    {
        "title": "Manual Concierge Service",
        "assumption_tested": "Customers will pay money for the outcome this product delivers",
        "why_it_matters": "Paying real money is a far stronger signal than an email sign-up. A concierge delivers the outcome manually before building automation.",
        "procedure": "Offer the core outcome as a service done manually. Charge a real price. Deliver it personally. You will learn which part of the experience customers care about most and whether they will actually pay.",
        "estimated_time": "2-4 weeks",
        "estimated_cost_range": "$0 – $100 (your time, no build cost)",
        "success_threshold": "3+ paying customers with zero refund requests",
        "failure_threshold": "0 paying customers after 20 outreach attempts, or 50%+ refund rate",
        "decision_after": "If success: identify what to automate first. If failure: pricing or value proposition is wrong.",
        "legal_ethical": "Charge real money only for real service delivery. Do not collect payment for software that does not yet exist without a clear refund policy.",
        "priority": 2,
    },
    {
        "title": "Pricing Survey",
        "assumption_tested": "Customers will pay the expected price point",
        "why_it_matters": "Price sensitivity is the most commonly under-tested assumption. Founder pricing intuition is often wrong by 2-5×.",
        "procedure": "Show the product description and ask: 'At what price would this be too expensive? Too cheap? A bargain? A fair price?' Use Van Westendorp Price Sensitivity Meter. Run with 20-30 target customers via email, LinkedIn message, or community posts.",
        "estimated_time": "1-2 weeks",
        "estimated_cost_range": "$0 – $100 (survey tool)",
        "success_threshold": "Acceptable price range overlaps with planned pricing; majority cite planned price as 'fair'",
        "failure_threshold": "Majority cite your planned price as 'too expensive', or 'too cheap' range exceeds your cost floor",
        "decision_after": "Adjust pricing model or cost structure based on results.",
        "legal_ethical": "No deception. This is a survey — be clear you are not selling yet.",
        "priority": 3,
    },
    {
        "title": "Small Advertising Experiment",
        "assumption_tested": "There is a cost-effective channel to reach target customers at scale",
        "why_it_matters": "Organic growth assumptions fail. Proving at least one paid channel works before building prevents distribution failure.",
        "procedure": "Run $200-300 of targeted ads to the landing page. Test two different audiences or messages. Measure click-through rate, conversion to sign-up, and cost per sign-up. Document all targeting parameters.",
        "estimated_time": "2 weeks",
        "estimated_cost_range": "$200 – $400",
        "success_threshold": "Cost per sign-up below 20% of expected first-year customer value",
        "failure_threshold": "No ad variant achieves above 1% CTR or cost per sign-up exceeds first-year value",
        "decision_after": "If success: scale the winning channel. If failure: find a different acquisition channel before building.",
        "legal_ethical": "Standard advertising ethics apply. Do not use misleading ad copy.",
        "priority": 4,
    },
]


def _pick_experiments(
    idea: IdeaInput,
    perspectives: List[AnalysisPerspective],
    evidence: List[EvidenceItem],
) -> List[ValidationExperiment]:
    """
    Select and customize 3-5 experiments based on idea context.
    Always include customer interviews and landing page test first.
    """
    # Customize templates with idea-specific values
    experiments: List[ValidationExperiment] = []

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
    perspectives: List[AnalysisPerspective],
    evidence: List[EvidenceItem],
) -> List[ValidationExperiment]:
    """Generate 3-5 validation experiments ordered by cost and information value."""
    return _pick_experiments(idea, perspectives, evidence)
