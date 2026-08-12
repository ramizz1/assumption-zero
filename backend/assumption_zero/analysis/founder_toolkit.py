"""Generate an actionable founder playbook without inventing market facts."""

from __future__ import annotations

import re

from assumption_zero.schemas import (
    FounderAction,
    FounderToolkit,
    IdeaInput,
    Recommendation,
    ValidationExperiment,
)


def _split_channels(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[,;\n]", value) if part.strip()][:4]


def _default_channels(idea: IdeaInput) -> list[str]:
    customer = idea.target_customer.lower()
    if any(
        term in customer
        for term in ("business", "company", "firm", "team", "enterprise", "agency", "clinic")
    ):
        return [
            "Founder-led outreach to 30 narrowly matched buyers",
            "One trusted niche community where the buyer already asks for help",
            "Partnerships with consultants or tools that already serve the segment",
        ]
    return [
        "Two niche communities where target users already discuss the problem",
        "Educational content built around the painful job-to-be-done",
        "A referral loop for the first ten successful users",
    ]


def generate_founder_toolkit(
    idea: IdeaInput,
    recommendation: Recommendation,
    experiments: list[ValidationExperiment],
) -> FounderToolkit:
    """Turn known user inputs and validation thresholds into a practical roadmap."""
    channels = _split_channels(idea.acquisition_channels) or _default_channels(idea)
    alternative = idea.known_competitors or "manual workarounds and existing alternatives"
    solution = idea.solution or idea.description
    stage = idea.startup_stage or "validation stage"
    timeline = idea.launch_timeline or "30 days"
    budget = idea.budget or "a tightly capped validation budget"
    goal = idea.revenue_goal or "three committed pilot customers"

    interview_metric = (
        experiments[1].success_threshold
        if len(experiments) > 1
        else "At least 7 of 10 buyers confirm an urgent problem"
    )
    smoke_metric = (
        experiments[0].success_threshold
        if experiments
        else "At least 3 buyers commit time, data, or money"
    )

    roadmap = [
        FounderAction(
            phase="Days 1-3",
            objective="Define the beachhead and recruit interviews",
            actions=[
                f"Build a list of 30 prospects matching: {idea.target_customer}",
                "Write a neutral interview script and schedule at least ten calls",
                "Record the current workflow, frequency, cost, urgency, and buying authority",
            ],
            success_metric="10 interviews booked with qualified prospects",
            stop_condition="Fewer than 5 qualified prospects can be reached after 30 targeted attempts",
            budget_hint="$0-$50",
        ),
        FounderAction(
            phase="Days 4-10",
            objective="Prove the problem before pitching the product",
            actions=[
                "Run ten problem interviews without leading with the solution",
                f"Compare the current workflow against {alternative}",
                "Rank repeated pains by frequency, severity, and existing spend",
            ],
            success_metric=interview_metric,
            stop_condition="Fewer than 4 of 10 prospects rank the problem among their top three priorities",
            budget_hint="$0-$100",
        ),
        FounderAction(
            phase="Days 11-20",
            objective="Test willingness to commit before building",
            actions=[
                f"Offer the outcome manually: {solution}",
                "Ask for a paid pilot, refundable deposit, signed letter of intent, or scheduled onboarding",
                f"Test the first channel: {channels[0]}",
            ],
            success_metric=smoke_metric,
            stop_condition="Zero meaningful commitments after 15 qualified offers",
            budget_hint="$0-$250",
        ),
        FounderAction(
            phase="Days 21-30",
            objective="Decide, scope, and launch the smallest viable pilot",
            actions=[
                "Build only the single value loop required to deliver the promised outcome",
                "Onboard pilots manually and measure activation, time-to-value, and weekly use",
                f"Set the next milestone around {goal} within {timeline}",
            ],
            success_metric=f"A repeatable pilot plan with owners, dates, and a path to {goal}",
            stop_condition="Pilot users do not complete the core value loop or refuse a second use",
            budget_hint=budget,
        ),
    ]

    recommendation_rule = {
        Recommendation.BUILD: "BUILD only the narrowest proven value loop; keep discovery running weekly.",
        Recommendation.TEST_FIRST: "TEST FIRST: do not begin full product development until the commitment threshold is met.",
        Recommendation.PIVOT: "PIVOT the segment, problem, or offer while preserving evidence that did validate.",
        Recommendation.AVOID: "AVOID further build spend unless new primary evidence overturns the current result.",
    }[recommendation]

    return FounderToolkit(
        one_sentence_pitch=(
            f"For {idea.target_customer} in {idea.geography}, {idea.name} helps solve "
            f"{idea.problem.rstrip('.')} through {solution.rstrip('.')}, unlike {alternative}."
        ),
        ideal_customer_profile=(
            f"{idea.target_customer}; initially focused on {idea.geography}"
            + (f" in {idea.industry}" if idea.industry else "")
            + f". Current company stage: {stage}."
        ),
        beachhead_market=f"Start with the narrowest reachable subset of {idea.target_customer} in {idea.geography} that already pays or uses a workaround.",
        recommended_channels=channels,
        key_metrics=[
            "Problem interview confirmation rate",
            "Qualified visitor-to-commitment conversion",
            "Activation: users who complete the core value loop",
            "Time to first value",
            "Four-week retention or repeat-use rate",
            "Customer acquisition cost versus first-year gross profit",
        ],
        roadmap=roadmap,
        interview_questions=[
            f"Tell me about the last time you experienced: {idea.problem}",
            "How do you solve this today, and what does that cost in time or money?",
            "How often does this happen, and what happens if you do nothing?",
            "Who owns the budget and what would make this urgent enough to buy?",
            f"What would make you switch away from {alternative}?",
            "What proof, security, integration, or compliance requirement would block adoption?",
        ],
        decision_rules=[
            recommendation_rule,
            "Continue when at least 7 of 10 qualified interviews confirm an urgent recurring problem.",
            "Build a pilot only after at least 3 prospects make a meaningful commitment.",
            "Change the message or channel when qualified traffic does not convert after a defined sample.",
            "Stop or pivot when two consecutive tests miss their pre-written failure thresholds.",
        ],
    )
