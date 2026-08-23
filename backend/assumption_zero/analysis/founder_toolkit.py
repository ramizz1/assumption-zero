"""Generate an actionable founder playbook without inventing market facts."""

from __future__ import annotations

import re

from assumption_zero.analysis.experiment_generator import budget_guidance
from assumption_zero.analysis.idea_context import is_noncommercial
from assumption_zero.analysis.regional_analysis import is_commercial_demand_signal
from assumption_zero.schemas import (
    EvidenceItem,
    EvidenceType,
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


def _default_channels(idea: IdeaInput, *, noncommercial: bool) -> list[str]:
    customer = idea.target_customer.lower()
    if any(
        term in customer
        for term in ("business", "company", "firm", "team", "enterprise", "agency", "clinic")
    ):
        if noncommercial:
            return [
                "Maintainer-led outreach to 30 narrowly matched users",
                "One trusted technical community where users already ask for help",
                "Integrations or documentation shared through tools serving the segment",
            ]
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
    evidence: list[EvidenceItem] | None = None,
) -> FounderToolkit:
    """Turn known user inputs and validation thresholds into a practical roadmap."""
    noncommercial = is_noncommercial(idea)
    channels = _split_channels(idea.acquisition_channels) or _default_channels(
        idea, noncommercial=noncommercial
    )
    alternative = idea.known_competitors or "manual workarounds and existing alternatives"
    solution = idea.solution or idea.description
    stage = idea.startup_stage or "validation stage"
    timeline = idea.launch_timeline or "30 days"
    goal = (
        "five independently activated users and two external maintenance signals"
        if noncommercial
        else idea.revenue_goal or "three committed pilot customers"
    )
    evidence = evidence or []
    _, validation_budget, budget_allocation = budget_guidance(idea)
    pain_count = sum(is_commercial_demand_signal(item, idea) for item in evidence)
    pricing_count = sum(item.evidence_type == EvidenceType.PRICING for item in evidence)
    workflow_count = sum(item.evidence_type == EvidenceType.MANUAL_WORKFLOW for item in evidence)
    source_count = len({item.source_name for item in evidence})

    reach_metric = experiments[2].success_threshold if len(experiments) > 2 else "At least four qualified conversations"
    commitment_metric = experiments[3].success_threshold if len(experiments) > 3 else "At least three meaningful commitments"
    retention_metric = experiments[4].success_threshold if len(experiments) > 4 else (
        "At least five users repeat and two contribute a useful maintenance signal"
        if noncommercial
        else "At least two customers repeat or renew"
    )

    roadmap = [
        FounderAction(
            phase="Days 1-3",
            objective=f"Define the {idea.name} beachhead and recruit qualified interviews",
            actions=[
                f"Build a list of 30 prospects matching: {idea.target_customer}",
                "Write a neutral interview script and schedule at least ten calls",
                (
                    "Record workflow frequency, consequence, current tool, and installation authority"
                    if noncommercial
                    else "Record the current workflow, frequency, cost, urgency, and buying authority"
                ),
            ],
            success_metric="10 interviews booked with qualified prospects",
            stop_condition="Fewer than 5 qualified prospects can be reached after 30 targeted attempts",
            budget_hint=experiments[0].estimated_cost_range if experiments else "$0-$50",
        ),
        FounderAction(
            phase="Days 4-10",
            objective=f"Verify behavior and reach {idea.target_customer}",
            actions=[
                f"Compare the current workflow against {alternative}",
                (
                    "Verify setup effort, maintenance burden, permissions, and switching constraints with real artifacts"
                    if noncommercial
                    else "Verify current spend, time, and switching constraints with real artifacts"
                ),
                f"Test the first channel: {channels[0]}",
            ],
            success_metric=reach_metric,
            stop_condition=experiments[2].failure_threshold if len(experiments) > 2 else "The segment cannot be reached after a bounded test",
            budget_hint=experiments[1].estimated_cost_range if len(experiments) > 1 else "$0-$100",
        ),
        FounderAction(
            phase="Days 11-20",
            objective=(
                "Test installation and contribution commitment before expanding scope"
                if noncommercial
                else "Test willingness to commit before building"
            ),
            actions=[
                f"Offer the outcome manually: {solution}",
                (
                    "Ask for a dated install, real-workflow integration, reproducible issue, example, or contribution"
                    if noncommercial
                    else "Ask for a paid pilot, refundable deposit, signed letter of intent, or scheduled onboarding"
                ),
                (
                    "Use the same scope, license, setup path, and core value event for every qualified user"
                    if noncommercial
                    else "Use the exact same scope and price for every qualified prospect"
                ),
            ],
            success_metric=commitment_metric,
            stop_condition=experiments[3].failure_threshold if len(experiments) > 3 else "Zero meaningful commitments after 15 qualified offers",
            budget_hint=experiments[3].estimated_cost_range if len(experiments) > 3 else "$0-$250",
        ),
        FounderAction(
            phase="Days 21-30",
            objective=(
                "Decide, scope, and support the smallest maintainable release"
                if noncommercial
                else "Decide, scope, and launch the smallest viable pilot"
            ),
            actions=[
                "Build only the single value loop required to deliver the promised outcome",
                (
                    "Observe independent installation, activation, repeat use, upgrades, and outside maintenance signals"
                    if noncommercial
                    else "Onboard pilots manually and measure activation, time-to-value, and weekly use"
                ),
                f"Set the next milestone around {goal} within {timeline}",
            ],
            success_metric=retention_metric,
            stop_condition=experiments[4].failure_threshold if len(experiments) > 4 else "Pilot users do not repeat the core value loop",
            budget_hint=experiments[4].estimated_cost_range if len(experiments) > 4 else "Release only after commitment",
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
        beachhead_market=(
            f"Start with the narrowest reachable subset of {idea.target_customer} in {idea.geography} "
            "that already uses a workaround and can independently install or integrate a solution."
            if noncommercial
            else f"Start with the narrowest reachable subset of {idea.target_customer} in {idea.geography} that already pays or uses a workaround."
        ),
        recommended_channels=channels,
        key_metrics=list(dict.fromkeys(
            [experiment.primary_metric for experiment in experiments if experiment.primary_metric]
            + (["Independent activation rate", "External maintenance signal rate"] if noncommercial else ["Time to first value", "Customer acquisition cost versus first-year gross profit"])
        )),
        demand_snapshot=(
            [
                f"Secondary research: {pain_count} idea-relevant adoption/pain signals across {source_count} collected sources.",
                f"Workflow evidence: {workflow_count} current-workflow signals collected for direct verification.",
                "Direct user evidence: interviews must verify recent events, current workarounds, and installation authority.",
                "Adoption evidence: unproven until qualified users independently install and reach first value.",
                "Community evidence: unproven until users repeat, integrate, report useful issues, refer, or contribute.",
            ]
            if noncommercial
            else [
                f"Secondary research: {pain_count} demand/complaint signals across {source_count} collected sources.",
                f"Commercial evidence: {pricing_count} pricing signals and {workflow_count} current-workflow signals.",
                "Direct buyer evidence: not collected by web analysis; interviews must verify recent events and existing behavior.",
                "Commitment evidence: not proven until a qualified buyer signs, deposits, schedules onboarding, or pays.",
                "Retention evidence: not proven until pilot users repeat, renew, expand, or refer without prompting.",
            ]
        ),
        validation_budget=validation_budget,
        budget_allocation=budget_allocation,
        budget_release_rules=(
            [
                "Run tests in order and stop when a failure threshold is reached.",
                "Do not buy broad traffic; measure qualified setup starts and activations.",
                "Do not expand the feature backlog before users independently activate.",
                "Release maintenance effort only after repeat use or an external maintenance signal appears.",
            ]
            if noncommercial
            else [
                "Run tests in order and stop spending when a failure threshold is reached.",
                "Do not buy broad traffic before a manual channel reaches qualified people.",
                "Do not fund product development from the validation reserve before commitment passes.",
                "Release pilot money only for delivering the promised outcome; postpone polish and automation.",
            ]
        ),
        roadmap=roadmap,
        interview_questions=(
            [
                f"Tell me about the last time you experienced: {idea.problem}",
                f"How do you solve this today, including any repository or manual workflow related to {alternative}?",
                "How often does this happen, and what breaks if you do nothing?",
                "Who can approve installation, permissions, integration, and ongoing maintenance?",
                f"What would make you install and keep using {idea.name} instead of {alternative}?",
                "What documentation, license, security, compatibility, or governance issue would block adoption?",
            ]
            if noncommercial
            else [
                f"Tell me about the last time you experienced: {idea.problem}",
                "How do you solve this today, and what does that cost in time or money?",
                "How often does this happen, and what happens if you do nothing?",
                "Who owns the budget and what would make this urgent enough to buy?",
                f"What would make you switch away from {alternative}?",
                "What proof, security, integration, or compliance requirement would block adoption?",
            ]
        ),
        decision_rules=(
            [
                recommendation_rule,
                "Continue when at least 7 of 10 qualified interviews confirm an urgent recurring problem.",
                "Expand scope only after at least 4 qualified users commit to a dated adoption action and 2 complete it.",
                "Change the message or channel when qualified visits do not produce setup starts.",
                "Stop or narrow when two consecutive cohorts miss activation or repeat-use thresholds.",
            ]
            if noncommercial
            else [
                recommendation_rule,
                "Continue when at least 7 of 10 qualified interviews confirm an urgent recurring problem.",
                "Build a pilot only after at least 3 prospects make a meaningful commitment.",
                "Change the message or channel when qualified traffic does not convert after a defined sample.",
                "Stop or pivot when two consecutive tests miss their pre-written failure thresholds.",
            ]
        ),
    )
