"""Generate idea-specific demand tests with explicit evidence and spending gates."""
from __future__ import annotations

import re
from typing import List

from assumption_zero.schemas import AnalysisPerspective, EvidenceItem, EvidenceType, IdeaInput, ValidationExperiment


def _profile(idea: IdeaInput) -> str:
    text = " ".join(value or "" for value in (
        idea.description, idea.problem, idea.target_customer, idea.industry,
        idea.business_model, idea.solution,
    )).casefold()
    if any(term in text for term in ("marketplace", "buyers and sellers", "two-sided", "vendors and customers", "matchmaking")):
        return "marketplace"
    if any(term in text for term in ("restaurant", "cafe", "shop", "retail", "food", "delivery", "local service", "venue", "salon")):
        return "local"
    if any(term in text for term in ("business", "company", "firm", "team", "enterprise", "agency", "clinic", "practice", "b2b")):
        return "b2b"
    return "consumer"


def _is_regulated(idea: IdeaInput) -> bool:
    text = f"{idea.industry or ''} {idea.regulatory_constraints or ''} {idea.description}".casefold()
    return bool(idea.regulatory_constraints) or any(
        term in text for term in ("health", "medical", "legal", "finance", "bank", "insurance", "child", "privacy", "patient")
    )


def _price(idea: IdeaInput) -> str:
    return idea.price or "the proposed price"


def _solution(idea: IdeaInput) -> str:
    return (idea.solution or idea.description).rstrip(".")


def _channel(idea: IdeaInput, profile: str) -> str:
    if idea.acquisition_channels:
        return re.split(r"[,;\n]", idea.acquisition_channels)[0].strip()
    if profile == "b2b":
        return "founder-led email or LinkedIn outreach"
    if profile == "local":
        return "a local community, partner, or in-person intercept"
    if profile == "marketplace":
        return "the niche community where each side already transacts"
    return "the smallest relevant online community"


def budget_guidance(idea: IdeaInput) -> tuple[list[str], str, list[str]]:
    """Cap the complete sequence at roughly 15% of a parseable founder budget."""
    raw = f"{idea.currency or ''} {idea.budget or ''}".strip()
    match = re.search(r"(?<!\d)(\d[\d,.]*)(?!\d)", idea.budget or "")
    total = float(match.group(1).replace(",", "")) if match else None
    marker = next((value for token, value in (
        ("$", "$"), ("usd", "$"), ("£", "£"), ("gbp", "£"),
        ("€", "€"), ("eur", "€"), ("azn", "AZN "),
    ) if token in raw.casefold()), None)
    if total and marker:
        percentages = (0.01, 0.02, 0.02, 0.04, 0.06)

        def money(value: float) -> str:
            rounded = max(10, int(round(value / 10.0) * 10))
            return f"{marker}{rounded:,}"

        costs = [f"{marker}0–{money(total * share)}" for share in percentages]
        cap = money(total * sum(percentages))
        summary = f"Sequential validation cap: {cap} (about 15% of {idea.budget}). Keep the remainder untouched until a test passes."
        allocations = [
            f"Problem evidence: up to {costs[0].split('–')[-1]}",
            f"Behavior/workflow proof: up to {costs[1].split('–')[-1]}",
            f"Reach or transaction test: up to {costs[2].split('–')[-1]}",
            f"Commitment/value test: up to {costs[3].split('–')[-1]}",
            f"Pilot/retention test: up to {costs[4].split('–')[-1]}, released only after commitment",
        ]
        return costs, summary, allocations

    costs = ["$0–$30", "$0–$75", "$0–$100", "$0–$200", "$0–$400 after commitment"]
    return costs, (
        "No reliable numeric budget was supplied. Start free, authorize one test at a time, "
        "and do not exceed $300 before a buyer makes a meaningful commitment."
    ), [
        "Problem research: $0–$30",
        "Behavior/workflow proof: $0–$75",
        "Reach test: $0–$100",
        "Commitment test: $0–$200",
        "Pilot/retention: up to $400, released only after commitment",
    ]


def _evidence_counts(evidence: List[EvidenceItem]) -> dict[EvidenceType, int]:
    return {kind: sum(item.evidence_type == kind for item in evidence) for kind in EvidenceType}


def _make(*, title: str, test_type: str, assumption: str, why: str, procedure: str,
          time: str, cost: str, target: str, metric: str, capture: list[str],
          success: str, failure: str, decision: str, budget_rationale: str,
          priority: int, legal: str = "Be transparent that this is validation research; collect only necessary data and honor opt-outs and refunds.") -> ValidationExperiment:
    return ValidationExperiment(
        title=title, test_type=test_type, assumption_tested=assumption,
        why_it_matters=why, procedure=procedure, estimated_time=time,
        estimated_cost_range=cost, target_sample=target, primary_metric=metric,
        data_to_capture=capture, success_threshold=success,
        failure_threshold=failure, decision_after=decision,
        budget_rationale=budget_rationale, legal_ethical=legal, priority=priority,
    )


def _b2b_tests(idea: IdeaInput, costs: list[str], counts: dict[EvidenceType, int], risky_claim: str) -> list[ValidationExperiment]:
    customer, problem, solution = idea.target_customer, idea.problem.rstrip("."), _solution(idea)
    channel, price = _channel(idea, "b2b"), _price(idea)
    return [
        _make(
            title="Last-event buyer interviews", test_type="problem_frequency",
            assumption=f"{customer} experience ‘{problem}’ often enough to act now.",
            why=f"Web research found {counts[EvidenceType.DEMAND] + counts[EvidenceType.COMPLAINT]} demand or complaint signals, but only recent first-hand examples establish urgency.",
            procedure=f"Interview 10 qualified people from {customer}. Ask for the last occurrence, trigger, frequency, consequence, current fix, and who approved any spend. Do not describe {idea.name} until the end.",
            time="3–5 days", cost=costs[0], target="10 qualified users; include at least 5 budget owners",
            metric="Recent-problem confirmation rate",
            capture=["Date of last occurrence", "Frequency and measurable consequence", "User, champion, and budget owner", "Current workaround"],
            success="At least 7/10 give a recent specific example; at least 5 call it a top-three problem.",
            failure="Fewer than 4/10 experienced it in the last 90 days, or consequences are consistently minor.",
            decision="Pass → audit current spend. Fail → change the customer/problem pair before testing a solution.",
            budget_rationale="Use direct outreach first; incentives are optional and must not buy positive answers.", priority=1,
        ),
        _make(
            title="Current-workflow and spend audit", test_type="existing_behavior",
            assumption=f"The buyer already spends money, staff time, or accepted risk to handle {problem}.",
            why=f"Existing behavior is stronger demand evidence than stated interest. Research found {counts[EvidenceType.PRICING]} pricing and {counts[EvidenceType.MANUAL_WORKFLOW]} workflow signals to verify directly.",
            procedure=f"Ask 6 interviewees to screen-share or describe the real workflow and provide a redacted invoice, spreadsheet, calendar, ticket, or time estimate. Compare it with {idea.known_competitors or 'their current alternative'}.",
            time="2–4 days", cost=costs[1], target="6 workflow owners from the interview sample",
            metric="Verified current-cost rate",
            capture=["Steps and people involved", "Monthly spend and staff hours", "Failure/rework cost", "Switching constraints"],
            success="At least 4/6 verify a recurring cost and the median cost is materially above the proposed price.",
            failure="Fewer than 2/6 can show a real workaround, budget line, or measurable cost.",
            decision="Pass → test whether the segment is reachable. Fail → target a costlier workflow or reduce the offer.",
            budget_rationale="Pay only for research access or redaction effort; no software build is needed.", priority=2,
        ),
        _make(
            title=f"Reachability test via {channel}", test_type="distribution",
            assumption=f"Qualified {customer} can be reached predictably without an uneconomic acquisition cost.",
            why="Demand is not commercially useful if the budget owner cannot be reached. This measures access before ad spend or product work.",
            procedure=f"Build a hand-checked list of 40 matching prospects in {idea.geography}. Send one problem-led message through {channel}, one follow-up, and offer a 15-minute workflow review. Track delivered, replies, qualified replies, and booked calls separately.",
            time="5 business days", cost=costs[2], target="40 hand-qualified prospects",
            metric="Qualified positive-reply rate",
            capture=["Delivery and reply rate", "Qualified positive replies", "Calls booked", "Reason for rejection"],
            success="At least 6 qualified positive replies and 4 booked conversations from 40 prospects.",
            failure="Fewer than 2 qualified replies after 40 prospects and one follow-up.",
            decision="Pass → make a commitment offer through this channel. Fail → change channel or tighten the segment; do not buy more traffic yet.",
            budget_rationale="Use manual prospecting; a bad list cannot be rescued with more volume.", priority=3,
            legal="Use relevant, personalized outreach; honor opt-outs and applicable anti-spam/privacy rules in the target geography.",
        ),
        _make(
            title=f"{price} commitment offer", test_type="willingness_to_pay", assumption=risky_claim,
            why="A signed pilot, refundable deposit, or scheduled onboarding is stronger evidence than a survey answer or waitlist signup.",
            procedure=f"Show a one-page offer for this outcome: {solution}. Quote {price}, a start date, scope, and cancellation terms. Make the same offer to 12 qualified budget owners and ask for the strongest legally appropriate commitment.",
            time="5–7 days", cost=costs[3], target="12 qualified budget owners who confirmed the problem",
            metric="Meaningful commitment rate",
            capture=["Offer accepted or declined", "Exact objection", "Approved price and approval path", "Time-to-decision"],
            success="At least 3/12 sign a pilot/LOI, place a refundable deposit, or schedule onboarding with a decision date.",
            failure="0/12 commit, or more than 8 reject for the same price/value reason.",
            decision="Pass → deliver a manual pilot. Fail → revise one of segment, outcome, proof, or price and rerun once.",
            budget_rationale="No paid acquisition or product build until a commitment is obtained.", priority=4,
            legal="State what exists today, what will be manual, delivery dates, cancellation terms, and refund deposits promptly when requested.",
        ),
        _make(
            title="Paid concierge pilot and renewal test", test_type="delivered_value_and_retention",
            assumption=f"Delivering {solution} creates repeat value strong enough for customers to pay again.",
            why="Acquisition proves initial demand; repeated use or renewal proves the outcome is valuable after the pitch.",
            procedure="Deliver the promised outcome manually to the first 3 committed customers. Define activation before starting, measure time-to-value and usage weekly, then ask each customer to renew, expand, or refer at the end.",
            time="2–4 weeks", cost=costs[4], target="3 committed pilot customers",
            metric="Activation plus renewal/expansion rate",
            capture=["Time to first value", "Weekly core action", "Outcome before/after", "Renewal, expansion, or referral"],
            success="All 3 activate; at least 2/3 renew, expand, or make a qualified referral without a new incentive.",
            failure="Fewer than 2 activate, or 0/3 want continued use after delivery.",
            decision="Pass → automate only the repeated bottleneck. Fail → diagnose delivery versus value; do not scale acquisition.",
            budget_rationale="Release this budget only after the commitment test passes; spend on delivery, not polish.", priority=5,
        ),
    ]


def _consumer_tests(idea: IdeaInput, costs: list[str], counts: dict[EvidenceType, int], risky_claim: str, local: bool = False) -> list[ValidationExperiment]:
    customer, problem, solution = idea.target_customer, idea.problem.rstrip("."), _solution(idea)
    channel, price = _channel(idea, "local" if local else "consumer"), _price(idea)
    venue = "in the target neighborhood" if local else "inside one existing niche community"
    return [
        _make(
            title="Seven-day problem diary", test_type="problem_frequency",
            assumption=f"{customer} repeatedly encounter ‘{problem}’ in real life, not just when asked.",
            why=f"The web scan found {counts[EvidenceType.DEMAND] + counts[EvidenceType.COMPLAINT]} category signals; a diary measures observed frequency for this exact audience.",
            procedure=f"Recruit 12 matching people {venue}. For 7 days, have them log every occurrence with time, context, current action, and consequence. Interview them only after the diary closes.",
            time="7 days", cost=costs[0], target="12 target users; aim for at least 9 complete diaries",
            metric="Observed weekly problem frequency",
            capture=["Occurrence timestamp", "Context and trigger", "Current action", "Time, money, or frustration cost"],
            success="At least 8/12 log 2+ occurrences and at least 6 already take action to solve it.",
            failure="Fewer than 4/12 log a second occurrence during the week.",
            decision="Pass → test message and access. Fail → narrow to the context where occurrences cluster.",
            budget_rationale="Use a small completion incentive only; do not pay per reported problem.", priority=1,
        ),
        _make(
            title=f"Message and reach test via {channel}", test_type="distribution",
            assumption=f"A concrete description of the problem attracts qualified {customer} through a reachable channel.",
            why="This separates weak messaging or distribution from weak product demand before any build.",
            procedure=f"Publish two problem-led messages through {channel}, each with the same ‘show me how it works’ action. Reach 100 qualified views organically or with tightly capped spend; tag source and message variant.",
            time="3–5 days", cost=costs[1], target="100 qualified views across two message variants",
            metric="Qualified action rate",
            capture=["Qualified views", "CTA actions by message", "Audience match", "Questions and objections"],
            success="At least 10 qualified actions from 100 views and one message clearly outperforms the other.",
            failure="Fewer than 3 actions after 100 qualified views.",
            decision="Pass → test price/commitment with responders. Fail → change message or channel once before changing the idea.",
            budget_rationale="Cap reach spend until one message earns an organic response.", priority=2,
        ),
        _make(
            title=f"Real-choice price test at {price}", test_type="willingness_to_pay", assumption=risky_claim,
            why="A choice with a consequence is more reliable than asking whether someone ‘would pay.’",
            procedure=f"Show 20 qualified responders the same offer for {solution} at {price}. Ask them to choose: reserve with a refundable deposit, schedule onboarding, join free updates, or decline. Do not mix outcomes when calculating conversion.",
            time="3–5 days", cost=costs[2], target="20 qualified people who took the prior action",
            metric="Deposit or scheduled-onboarding rate",
            capture=["Choice made", "Price objection", "Expected outcome", "Refund/cancellation request"],
            success="At least 4/20 choose a deposit or scheduled onboarding; at least 10/20 choose more than free updates.",
            failure="0/20 make a consequential choice or the median acceptable price is below delivery cost.",
            decision="Pass → deliver manually. Fail → revise price, packaging, or target context; do not treat free signups as demand.",
            budget_rationale="Spend only on reaching already-qualified users; a larger survey will not fix a weak commitment rate.", priority=3,
            legal="Make availability, refund terms, delivery timing, and the current product stage unmistakably clear.",
        ),
        _make(
            title="Manual value-delivery test", test_type="delivered_value",
            assumption=f"{solution} causes a measurable improvement for the target user.",
            why="This tests the promised outcome without confusing it with interface quality or feature count.",
            procedure="Deliver the outcome manually to 8 committed users. Record a baseline, define one observable completion event, and measure the same outcome immediately after use. Do not add features mid-test.",
            time="7–10 days", cost=costs[3], target="8 committed users",
            metric="Activation and measured outcome improvement",
            capture=["Baseline", "Activation event", "Time to value", "Outcome change and support needed"],
            success="At least 6/8 activate and at least 5 show the predefined outcome improvement.",
            failure="Fewer than 4/8 activate or improvement cannot be observed.",
            decision="Pass → test repeat behavior. Fail → fix the value proposition or delivery path before software.",
            budget_rationale="Buy only what is needed to deliver the outcome manually; avoid design and automation spend.", priority=4,
        ),
        _make(
            title="Unprompted repeat-use test", test_type="retention",
            assumption=f"Users return to {idea.name} when the problem recurs without founder reminders.",
            why="Initial curiosity creates false positives. Repeat behavior distinguishes durable demand from one-time novelty.",
            procedure="Give 8 pilot users access for 14 days. After onboarding, send no usage reminders for the core action. Measure return on a new problem occurrence, then ask active users to renew, refer, or prepay.",
            time="14 days", cost=costs[4], target="8 activated pilot users",
            metric="Unprompted repeat-use plus renewal rate",
            capture=["Second core action", "Days between uses", "Reason for non-return", "Renewal, referral, or prepay"],
            success="At least 5/8 repeat the core action unprompted and at least 3 make a renewal/referral/prepay commitment.",
            failure="Fewer than 3/8 return when the problem recurs.",
            decision="Pass → build the smallest repeatable product loop. Fail → stop acquisition and investigate why value did not persist.",
            budget_rationale="Release only after manual value delivery passes; preserve the rest for the proven retention bottleneck.", priority=5,
        ),
    ]


def _marketplace_tests(idea: IdeaInput, costs: list[str], counts: dict[EvidenceType, int], risky_claim: str) -> list[ValidationExperiment]:
    solution = _solution(idea)
    tests = _consumer_tests(idea, costs, counts, risky_claim)
    tests[0] = _make(
        title="Supply-side commitment test", test_type="supply_liquidity",
        assumption="A narrowly defined supplier group will list real availability before buyer demand is guaranteed.",
        why="A marketplace cannot test buyer demand with empty or hypothetical supply.",
        procedure=f"Recruit 15 matching suppliers in {idea.geography}. Ask each for an actual listing, price, availability window, and response SLA for the manual version of {solution}.",
        time="5–7 days", cost=costs[0], target="15 qualified suppliers", metric="Live, usable supply commitments",
        capture=["Listing completed", "Price and availability", "Response SLA", "Reason for refusal"],
        success="At least 8/15 provide complete, usable inventory or availability.",
        failure="Fewer than 4/15 provide real availability after two contacts.",
        decision="Pass → recruit demand against this exact inventory. Fail → improve supplier value or change supply niche.",
        budget_rationale="Recruit manually; do not build seller tooling before suppliers commit inventory.", priority=1,
    )
    tests[1] = _make(
        title="Buyer request test against real supply", test_type="buyer_demand",
        assumption="Qualified buyers submit specific requests when shown available supply.",
        why="Traffic or waitlists do not prove marketplace demand; a request with timing, budget, and constraints does.",
        procedure="Show committed inventory to 40 matching buyers through one existing channel. Ask for a dated request with requirements and budget, not an email signup.",
        time="5–7 days", cost=costs[1], target="40 qualified buyers", metric="Qualified request rate",
        capture=["Request requirements", "Budget and timing", "Inventory viewed", "Reason no option fit"],
        success="At least 8/40 submit a qualified request and at least 5 match available supply.",
        failure="Fewer than 3 qualified requests or no requests match live supply.",
        decision="Pass → manually match and close. Fail → change buyer niche, inventory, or message.",
        budget_rationale="Pay for targeted reach only after supply exists; never optimize generic clicks.", priority=2,
    )
    tests[2] = _make(
        title="Manual match-and-close test", test_type="marketplace_transaction", assumption=risky_claim,
        why="Only completed matches expose trust, timing, pricing, and operational friction on both sides.",
        procedure="Concierge-match the first 10 qualified requests. Handle discovery, trust checks, scheduling, and confirmation manually; record every failed match reason.",
        time="7–14 days", cost=costs[2], target="10 buyer requests with committed suppliers", metric="Completed-match rate and time to match",
        capture=["Matches attempted/completed", "Time to match", "Failure reason", "Support minutes per transaction"],
        success="At least 5/10 requests complete and median time-to-match meets the buyer's deadline.",
        failure="Fewer than 2/10 complete or manual support cost exceeds plausible revenue.",
        decision="Pass → test the fee. Fail → fix liquidity constraints before building marketplace software.",
        budget_rationale="Spend on completing real matches, not marketplace features.", priority=3,
    )
    tests[3] = _make(
        title="Transaction-fee acceptance test", test_type="willingness_to_pay",
        assumption=f"One side will pay {idea.price or 'the proposed fee'} for a completed match.",
        why="Gross transaction value is not revenue; the payer and fee must be explicit.",
        procedure="Before the next 8 manual matches, disclose the exact fee and who pays it. Ask for acceptance before doing matching work, then track completion and objections.",
        time="7–14 days", cost=costs[3], target="8 otherwise-qualified transactions", metric="Fee acceptance and paid completion rate",
        capture=["Fee accepted", "Transaction completed", "Take rate", "Fee objection by side"],
        success="At least 5/8 accept the fee and at least 4 transactions complete.",
        failure="Fewer than 2/8 accept, or accepted fees do not cover manual variable cost.",
        decision="Pass → test repeat liquidity. Fail → change payer, pricing model, or value provided.",
        budget_rationale="Do not subsidize both sides; measure the true cost of each completed match.", priority=4,
        legal="Disclose fees, refund/cancellation terms, and any role in the transaction before matching begins.",
    )
    tests[4] = _make(
        title="Repeat liquidity cohort", test_type="retention_and_liquidity",
        assumption="The same narrow market produces repeat requests and responsive supply without founder chasing.",
        why="A marketplace is viable only when liquidity improves and at least one side returns.",
        procedure="Run the same micro-market for 21 days. Track new/repeat requests, supplier response, fill rate, time-to-match, and repeat transactions without expanding geography or category.",
        time="21 days", cost=costs[4], target="One fixed micro-market; at least 10 total requests", metric="Fill rate, time-to-match, and repeat rate",
        capture=["Weekly requests", "Fill rate", "Supplier response time", "Repeat buyer or supplier activity"],
        success="At least 60% fill rate, improving time-to-match, and 3 repeat participants.",
        failure="Fill rate stays below 30% or no participant returns.",
        decision="Pass → automate the highest-friction matching step. Fail → keep the market narrower or stop.",
        budget_rationale="Release only after paid transactions; preserve budget until repeat liquidity appears.", priority=5,
    )
    return tests


def generate_experiments(idea: IdeaInput, perspectives: List[AnalysisPerspective], evidence: List[EvidenceItem]) -> List[ValidationExperiment]:
    """Return five sequential tests that answer different demand questions."""
    profile = _profile(idea)
    costs, _, _ = budget_guidance(idea)
    counts = _evidence_counts(evidence)
    risky_claim = idea.key_assumptions or next(
        (perspective.most_dangerous_assumption for perspective in perspectives if perspective.most_dangerous_assumption),
        f"{idea.target_customer} will make a real commitment for {_solution(idea)} at {_price(idea)}.",
    )
    if profile == "marketplace":
        tests = _marketplace_tests(idea, costs, counts, risky_claim)
    elif profile == "b2b":
        tests = _b2b_tests(idea, costs, counts, risky_claim)
    else:
        tests = _consumer_tests(idea, costs, counts, risky_claim, local=profile == "local")
    if _is_regulated(idea):
        tests[1].procedure += " Before proceeding, ask one qualified domain/compliance expert to identify any rule that would prevent this workflow or evidence collection."
        tests[1].data_to_capture.append("Blocking compliance or consent requirement")
        tests[1].legal_ethical = "Use redacted artifacts and appropriate consent. Verify sector-specific requirements with a qualified local professional."
    return tests
