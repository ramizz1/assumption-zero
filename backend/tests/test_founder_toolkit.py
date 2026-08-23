import json
import re

from assumption_zero.analysis.experiment_generator import generate_experiments
from assumption_zero.analysis.founder_toolkit import generate_founder_toolkit
from assumption_zero.analysis.query_generator import generate_queries
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
    assert b2b_tests[0].title == "ClinicFlow: Last-event buyer interviews"
    assert marketplace_tests[0].title == "CareMatch: Supply-side commitment test"
    assert "Independent clinics" in b2b_tests[0].assumption_tested


def test_each_idea_gets_evidence_bound_unique_analytics(sample_evidence) -> None:
    clinic = _idea()
    warehouse = _idea(
        name="StockSignal",
        description="Inventory alerting for independent hardware stores",
        problem="Hardware stores discover stockouts too late",
        target_customer="Independent hardware store operators",
        geography="Canada",
        industry="Retail operations",
        solution="A daily inventory risk digest",
    )

    clinic_evidence = sample_evidence[0].model_copy(
        update={
            "title": "Independent clinic scheduling workflow survey",
            "passage": "Independent clinics report recurring scheduling workflow failures.",
            "search_query": "independent clinic scheduling United Kingdom",
        }
    )
    clinic_tests = generate_experiments(clinic, [], [clinic_evidence])
    warehouse_tests = generate_experiments(warehouse, [], sample_evidence)

    assert clinic_tests != warehouse_tests
    assert len({item.test_type for item in clinic_tests}) == 5
    assert len({item.title for item in clinic_tests}) == 5
    assert all(item.title.startswith("ClinicFlow: ") for item in clinic_tests)
    assert all("Independent clinics" in item.data_to_capture[-1] for item in clinic_tests)
    assert any(
        "[E001] Independent clinic scheduling workflow survey (GitHub)"
        in item.why_it_matters
        for item in clinic_tests
    )
    assert "StockSignal" in json.dumps(
        [item.model_dump(mode="json") for item in warehouse_tests]
    )
    assert "Canada" in json.dumps(
        [item.model_dump(mode="json") for item in warehouse_tests]
    )


def test_free_open_source_toolkit_uses_adoption_not_payment_advice(sample_evidence) -> None:
    idea = _idea(
        name="OpenClinic",
        description="A free and open-source clinic scheduling project with no payments",
        solution="A self-hosted scheduling workspace maintained by its community",
        business_model="Free and open source; no payments",
        price=None,
        revenue_goal=None,
    )

    experiments = generate_experiments(idea, [], sample_evidence)
    toolkit = generate_founder_toolkit(
        idea,
        Recommendation.TEST_FIRST,
        experiments,
        sample_evidence,
    )
    queries = generate_queries(idea)
    output = json.dumps(
        {
            "experiments": [item.model_dump(mode="json") for item in experiments],
            "toolkit": toolkit.model_dump(mode="json"),
            "queries": queries,
        }
    ).lower()

    assert [item.test_type for item in experiments] == [
        "problem_frequency",
        "adoption_friction",
        "distribution",
        "adoption_commitment",
        "community_retention",
    ]
    assert all(item.title.startswith("OpenClinic: ") for item in experiments)
    assert not any(item["type"] == "pricing" for item in queries)
    assert "independent activation rate" in output
    assert "external maintenance signal rate" in output
    assert not re.search(
        r"\b(paid|pricing|revenue|deposit|prepay|buyer|cac|ltv|refunds?)\b",
        output,
    )


def test_budget_is_capped_and_released_sequentially() -> None:
    idea = _idea()
    experiments = generate_experiments(idea, [], [])
    toolkit = generate_founder_toolkit(idea, Recommendation.TEST_FIRST, experiments)

    assert "about 15%" in toolkit.validation_budget
    assert "£" in toolkit.validation_budget
    assert len(toolkit.budget_allocation) == 5
    assert "after commitment" in toolkit.budget_allocation[-1]
