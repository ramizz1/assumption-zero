from assumption_zero.analysis.experiment_generator import generate_experiments
from assumption_zero.analysis.founder_toolkit import generate_founder_toolkit
from assumption_zero.schemas import IdeaInput, Recommendation


def _idea(**overrides) -> IdeaInput:
    values = {
        "name": "ClinicFlow",
        "description": "A scheduling and intake workflow for small clinics",
        "problem": "Small clinics lose staff time coordinating intake and appointment changes manually",
        "target_customer": "Independent clinics with 2-10 practitioners",
        "geography": "United Kingdom",
        "industry": "Healthcare operations",
        "startup_stage": "Idea validation",
        "solution": "A shared automated intake and scheduling workspace",
        "budget": "GBP 2,000 validation budget",
        "launch_timeline": "30 days",
        "revenue_goal": "5 paid pilots",
        "known_competitors": "spreadsheets and phone calls",
    }
    values.update(overrides)
    return IdeaInput(**values)


def test_founder_toolkit_contains_measurable_roadmap() -> None:
    idea = _idea()
    experiments = generate_experiments(idea, [], [])

    toolkit = generate_founder_toolkit(idea, Recommendation.TEST_FIRST, experiments)

    assert len(toolkit.roadmap) == 4
    assert toolkit.roadmap[0].phase == "Days 1-3"
    assert all(action.success_metric and action.stop_condition for action in toolkit.roadmap)
    assert "TEST FIRST" in toolkit.decision_rules[0]
    assert idea.target_customer in toolkit.one_sentence_pitch
    assert len(toolkit.interview_questions) >= 5


def test_founder_toolkit_uses_declared_acquisition_channels() -> None:
    idea = _idea(acquisition_channels="Trade association; founder newsletter, referral partners")

    toolkit = generate_founder_toolkit(idea, Recommendation.BUILD, [])

    assert toolkit.recommended_channels == [
        "Trade association",
        "founder newsletter",
        "referral partners",
    ]
    assert toolkit.roadmap[1].actions[-1] == "Test the first channel: Trade association"


def test_experiments_are_distinct_and_specific_to_business_shape() -> None:
    b2b = _idea()
    marketplace = _idea(
        name="CareMatch",
        description="A two-sided marketplace matching clinics with temporary practitioners",
        business_model="Marketplace transaction fee",
    )

    b2b_tests = generate_experiments(b2b, [], [])
    marketplace_tests = generate_experiments(marketplace, [], [])

    assert len({experiment.test_type for experiment in b2b_tests}) == 5
    assert len({experiment.test_type for experiment in marketplace_tests}) == 5
    assert b2b_tests[0].title == "Last-event buyer interviews"
    assert marketplace_tests[0].title == "Supply-side commitment test"
    assert "Independent clinics" in b2b_tests[0].assumption_tested


def test_budget_is_capped_and_released_sequentially() -> None:
    idea = _idea()
    experiments = generate_experiments(idea, [], [])
    toolkit = generate_founder_toolkit(idea, Recommendation.TEST_FIRST, experiments)

    assert "about 15%" in toolkit.validation_budget
    assert "£" in toolkit.validation_budget
    assert len(toolkit.budget_allocation) == 5
    assert "after commitment" in toolkit.budget_allocation[-1]
