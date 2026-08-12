"""
Citation validator.

Checks that every evidence ID cited by an AI perspective actually exists
in the collected evidence set. Invalid citations are flagged and stored
on the perspective — they do NOT cause analysis failure.
"""

from __future__ import annotations

from assumption_zero.schemas import AnalysisPerspective, EvidenceItem


def validate_citations(
    perspectives: list[AnalysisPerspective],
    evidence: list[EvidenceItem],
) -> list[AnalysisPerspective]:
    """
    For each perspective, move any cited evidence IDs that do not exist
    in the evidence set into the invalid_citations list.

    Returns the same list of perspectives with invalid_citations populated.
    Mutates in place and also returns for chaining.
    """
    valid_ids = {e.evidence_id for e in evidence}

    for perspective in perspectives:
        valid: list[str] = []
        invalid: list[str] = []

        for eid in perspective.cited_evidence_ids:
            if eid in valid_ids:
                valid.append(eid)
            else:
                invalid.append(eid)

        perspective.cited_evidence_ids = valid
        perspective.invalid_citations = invalid

    return perspectives
