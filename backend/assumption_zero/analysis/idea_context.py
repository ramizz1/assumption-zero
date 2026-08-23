"""Shared idea-shape signals used to keep analysis commercially appropriate."""

from __future__ import annotations

from assumption_zero.schemas import IdeaInput

_NONCOMMERCIAL_MARKERS = (
    "free and open source",
    "free open source",
    "open-source",
    "open source",
    "no payments",
    "no payment",
    "non-commercial",
    "noncommercial",
    "not for profit",
    "nonprofit",
    "public good",
    "community maintained",
)
_COMMERCIAL_MARKERS = (
    "subscription",
    "saas",
    "transaction fee",
    "commission",
    "license fee",
    "paid plan",
    "freemium",
    "per seat",
    "monthly fee",
)


def is_noncommercial(idea: IdeaInput) -> bool:
    """Return true only when the submitter explicitly describes a free/noncommercial model."""
    fields = (
        idea.description,
        idea.solution,
        idea.business_model,
        idea.price,
        idea.revenue_goal,
        idea.additional_context,
    )
    text = " ".join(value or "" for value in fields).casefold()
    explicit_no_payment = any(
        marker in text
        for marker in ("no payments", "no payment", "non-commercial", "noncommercial")
    )
    if explicit_no_payment:
        return True
    if any(marker in text for marker in _COMMERCIAL_MARKERS) or idea.price or idea.revenue_goal:
        return False
    return any(marker in text for marker in _NONCOMMERCIAL_MARKERS)


def model_label(idea: IdeaInput) -> str:
    return "free/open-source" if is_noncommercial(idea) else "commercial"
