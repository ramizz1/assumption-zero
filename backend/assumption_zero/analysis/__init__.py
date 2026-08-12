"""Analysis engine package."""

from assumption_zero.analysis.citation_validator import validate_citations
from assumption_zero.analysis.competitor_merger import merge_competitors
from assumption_zero.analysis.confidence import calculate_evidence_confidence
from assumption_zero.analysis.disagreement import detect_disagreements
from assumption_zero.analysis.engine import AnalysisEngine
from assumption_zero.analysis.experiment_generator import generate_experiments
from assumption_zero.analysis.query_generator import generate_queries
from assumption_zero.analysis.scoring import DIMENSION_WEIGHTS, calculate_opportunity_score

__all__ = [
    "DIMENSION_WEIGHTS",
    "AnalysisEngine",
    "calculate_evidence_confidence",
    "calculate_opportunity_score",
    "detect_disagreements",
    "generate_experiments",
    "generate_queries",
    "merge_competitors",
    "validate_citations",
]
