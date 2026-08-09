"""Regression tests for web/CLI feature parity."""
from __future__ import annotations

from datetime import datetime

import pytest
from typer.testing import CliRunner

import assumption_zero.storage as store
from assumption_zero.analysis.unit_economics import calculate_unit_economics
from assumption_zero.cli import _run_analysis_sync, app
from assumption_zero.schemas import AnalysisResult, AnalysisStage, AnalysisStatus


runner = CliRunner()


def test_cli_exposes_web_equivalent_commands_and_provider_controls():
    root_help = runner.invoke(app, ["--help"])
    assert root_help.exit_code == 0
    for command in ("demo", "simulate", "verify-provider", "list", "show", "delete", "export"):
        assert command in root_help.stdout

    analyze_help = runner.invoke(app, ["analyze", "--help"])
    assert analyze_help.exit_code == 0
    assert "--research-provider" in analyze_help.stdout
    assert "--provider" in analyze_help.stdout
    assert "--base-url" in analyze_help.stdout

    prompt_help = runner.invoke(app, ["prompt", "--help"])
    assert prompt_help.exit_code == 0
    assert "--research-provider" in prompt_help.stdout
    assert "--provider" in prompt_help.stdout


def test_unit_economics_matches_web_default_model():
    result = calculate_unit_economics(
        price=49,
        cac=147,
        variable_cost=7,
        fixed_costs=500,
        monthly_churn_pct=5,
    )
    assert result.gross_margin_per_customer == 42
    assert result.breakeven_customers == 15
    assert round(result.payback_months or 0, 1) == 3.5
    assert result.estimated_ltv == 840
    assert round(result.ltv_to_cac or 0, 1) == 5.7
    assert result.health == "Healthy"


def test_cli_analysis_is_saved_for_web_history(monkeypatch, sample_idea):
    class FakeEngine:
        async def run(self, idea, analysis_id, progress_callback, is_demo):
            await progress_callback(AnalysisStage.COLLECTING_EVIDENCE, "Collecting")
            return AnalysisResult(
                analysis_id=analysis_id,
                status=AnalysisStatus.COMPLETE,
                stage=AnalysisStage.COMPLETE,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                idea_input=idea,
                is_demo=is_demo,
            )

    monkeypatch.setattr("assumption_zero.cli._build_engine_sync", lambda **kwargs: FakeEngine())
    result = _run_analysis_sync(sample_idea)

    row = store.get_record(result.analysis_id)
    assert row is not None
    assert row["status"] == "complete"
    assert store.get_result(result.analysis_id)["idea_input"]["name"] == sample_idea.name


@pytest.mark.asyncio
async def test_history_verdict_filters_work_for_web_and_cli(sample_idea):
    from assumption_zero.schemas import Recommendation
    from assumption_zero.services.analysis_service import list_analyses

    result = AnalysisResult(
        analysis_id="filter-test-id",
        status=AnalysisStatus.COMPLETE,
        stage=AnalysisStage.COMPLETE,
        created_at=datetime.utcnow(),
        idea_input=sample_idea,
        recommendation=Recommendation.BUILD,
    )
    store.create_record("filter-test-id", sample_idea.name, sample_idea.model_dump(mode="json"))
    store.complete_record("filter-test-id", result.model_dump(mode="json"))

    assert len(await list_analyses(status_filter="build")) == 1
    assert len(await list_analyses(status_filter="avoid")) == 0
    assert len(await list_analyses(status_filter="complete")) == 1
