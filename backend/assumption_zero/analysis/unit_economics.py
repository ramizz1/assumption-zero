"""Transparent unit-economics calculations shared by CLI reporting tools."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class UnitEconomicsResult:
    monthly_price: float
    cac: float
    variable_cost: float
    fixed_costs: float
    monthly_churn_pct: float
    gross_margin_per_customer: float
    monthly_contribution: float
    breakeven_customers: int | None
    payback_months: float | None
    estimated_ltv: float | None
    ltv_to_cac: float | None
    health: str


def extract_price(value: str | None, fallback: float = 20.0) -> float:
    """Extract the first numeric price, matching the web simulator behavior."""
    if not value:
        return fallback
    match = re.search(r"[\d,]+(?:\.\d+)?", value)
    return float(match.group(0).replace(",", "")) if match else fallback


def calculate_unit_economics(
    price: float,
    cac: float,
    variable_cost: float,
    fixed_costs: float,
    monthly_churn_pct: float,
) -> UnitEconomicsResult:
    """Calculate the same directional subscription model shown in the web UI."""
    values = (price, cac, variable_cost, fixed_costs, monthly_churn_pct)
    if any(value < 0 for value in values) or monthly_churn_pct > 100:
        raise ValueError(
            "Economics inputs must be non-negative and churn must be between 0 and 100."
        )

    gross_margin = price - variable_cost
    churn_rate = monthly_churn_pct / 100
    replacement_acquisition = churn_rate * cac
    monthly_contribution = gross_margin - replacement_acquisition
    breakeven = math.ceil(fixed_costs / monthly_contribution) if monthly_contribution > 0 else None
    payback = cac / gross_margin if gross_margin > 0 else None
    ltv = gross_margin / churn_rate if churn_rate > 0 and gross_margin > 0 else None
    ratio = ltv / cac if ltv is not None and cac > 0 else None
    health = (
        "Incomplete"
        if ratio is None
        else "Healthy"
        if ratio >= 3
        else "Needs work"
        if ratio >= 1
        else "Unsustainable"
    )

    return UnitEconomicsResult(
        monthly_price=price,
        cac=cac,
        variable_cost=variable_cost,
        fixed_costs=fixed_costs,
        monthly_churn_pct=monthly_churn_pct,
        gross_margin_per_customer=gross_margin,
        monthly_contribution=monthly_contribution,
        breakeven_customers=breakeven,
        payback_months=payback,
        estimated_ltv=ltv,
        ltv_to_cac=ratio,
        health=health,
    )
