"""
Tests for Markdown and JSON export functions.
"""
from __future__ import annotations

import json
from datetime import datetime

from assumption_zero.cli import _export_markdown, DISCLAIMER
from assumption_zero.schemas import (
    AnalysisResult,
    AnalysisStage,
    AnalysisStatus,
    Recommendation,
)


def _make_result(sample_idea, sample_evidence, sample_perspectives):
    from assumption_zero.analysis.scoring import calculate_opportunity_score
    from assumption_zero.analysis.confidence import calculate_evidence_confidence
    from assumption_zero.analysis.experiment_generator import generate_experiments

    score = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    conf = calculate_evidence_confidence(sample_evidence, sample_perspectives)
    exps = generate_experiments(sample_idea, sample_perspectives, sample_evidence)

    return AnalysisResult(
        analysis_id="test-id-123",
        status=AnalysisStatus.COMPLETE,
        stage=AnalysisStage.COMPLETE,
        created_at=datetime(2025, 1, 15, 10, 0),
        idea_input=sample_idea,
        interpreted_idea="Test interpretation",
        evidence=sample_evidence,
        competitors=[],
        perspectives=sample_perspectives,
        opportunity_score=score,
        evidence_confidence=conf,
        recommendation=Recommendation.TEST_FIRST,
        most_dangerous_assumption="Test assumption",
        strongest_supporting="[E001] Good evidence",
        strongest_contradicting="[E002] Counter evidence",
        missing_information=["Missing regulatory data"],
        experiments=exps,
        disagreements=[],
        models_used=["mock"],
        provider_errors=[],
        is_demo=False,
    )


def test_markdown_export_contains_disclaimer(sample_idea, sample_evidence, sample_perspectives):
    result = _make_result(sample_idea, sample_evidence, sample_perspectives)
    md = _export_markdown(result)
    assert DISCLAIMER in md


def test_markdown_export_contains_idea_name(sample_idea, sample_evidence, sample_perspectives):
    result = _make_result(sample_idea, sample_evidence, sample_perspectives)
    md = _export_markdown(result)
    assert sample_idea.name in md


def test_markdown_export_contains_score(sample_idea, sample_evidence, sample_perspectives):
    result = _make_result(sample_idea, sample_evidence, sample_perspectives)
    md = _export_markdown(result)
    assert "Opportunity Score" in md


def test_markdown_export_contains_evidence_ids(sample_idea, sample_evidence, sample_perspectives):
    result = _make_result(sample_idea, sample_evidence, sample_perspectives)
    md = _export_markdown(result)
    assert "E001" in md
    assert "E002" in md


def test_json_export_no_secrets(sample_idea, sample_evidence, sample_perspectives):
    """Exported JSON must never contain API keys."""
    result = _make_result(sample_idea, sample_evidence, sample_perspectives)
    exported = result.model_dump_json(indent=2)
    raw = json.loads(exported)
    text = json.dumps(raw)
    for secret_key in ("api_key", "secret", "password", "token"):
        # Values should not contain actual credentials
        assert "sk-" not in text
        assert "AIza" not in text


def test_markdown_export_contains_experiments(sample_idea, sample_evidence, sample_perspectives):
    result = _make_result(sample_idea, sample_evidence, sample_perspectives)
    md = _export_markdown(result)
    assert "Validation Experiments" in md
    assert "Experiment 1" in md
