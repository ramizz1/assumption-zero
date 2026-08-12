"""
Tests for the scoring engine.

Critical: weights must sum to exactly 100.
Scoring must be deterministic pure Python.
"""

from __future__ import annotations

import pytest

from assumption_zero.analysis.scoring import (
    DIMENSION_WEIGHTS,
    calculate_opportunity_score,
)


def test_weights_sum_to_100():
    """Score weights must sum exactly to 100 — architectural invariant."""
    assert sum(DIMENSION_WEIGHTS.values()) == 100, (
        f"Weights sum to {sum(DIMENSION_WEIGHTS.values())}, expected 100"
    )


def test_all_seven_dimensions_present():
    expected = {
        "problem_evidence",
        "demand_signals",
        "competitive_gap",
        "distribution_feasibility",
        "unit_economics",
        "founder_fit",
        "legal_operational_risk",
    }
    assert set(DIMENSION_WEIGHTS.keys()) == expected


def test_score_calculation_deterministic(sample_idea, sample_evidence, sample_perspectives):
    """Same input must produce identical output every run."""
    result1 = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    result2 = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    assert result1.total == result2.total


def test_score_is_within_bounds(sample_idea, sample_evidence, sample_perspectives):
    result = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    assert 0 <= result.total <= 100, f"Score {result.total} is out of bounds"


def test_score_has_correct_dimension_count(sample_idea, sample_evidence, sample_perspectives):
    result = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    assert len(result.dimensions) == 7


def test_weighted_scores_sum_to_total(sample_idea, sample_evidence, sample_perspectives):
    """The sum of weighted_score values must equal the total."""
    result = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    computed_total = sum(d.weighted_score for d in result.dimensions)
    assert abs(computed_total - result.total) < 0.1, (
        f"Dimension weighted sum {computed_total} != total {result.total}"
    )


def test_score_no_perspectives(sample_idea, sample_evidence):
    """With no perspectives, score defaults to neutral (all 50.0 raw → 50.0 total)."""
    result = calculate_opportunity_score([], sample_evidence, sample_idea)
    # All raw = 50.0, weighted = 50% of weight per dim, total = 50.0
    assert result.total == pytest.approx(50.0, abs=1.0)


def test_score_all_high(sample_idea, sample_evidence, sample_perspectives):
    """High scores in all dimensions should produce a high total."""
    for p in sample_perspectives:
        for k in p.dimension_scores:
            p.dimension_scores[k] = 90.0
    result = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    assert result.total >= 80.0


def test_score_all_low(sample_idea, sample_evidence, sample_perspectives):
    """Low scores in all dimensions should produce a low total."""
    for p in sample_perspectives:
        for k in p.dimension_scores:
            p.dimension_scores[k] = 10.0
    result = calculate_opportunity_score(sample_perspectives, sample_evidence, sample_idea)
    assert result.total <= 20.0
