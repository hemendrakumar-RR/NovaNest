"""
NovaNest Financial Impact Engine (Phase 08)
-------------------------------------------
Calculates standardized, mathematically verifiable financial impacts, ROI ratios,
and payback durations for all prescriptive recommendations.

Strict Rule: Separates estimated forward projections from realized historical actuals.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from python.decision.prescriptive_contracts import (
    FinancialImpactBreakdown,
    RealizedOutcomeRecord,
    utc_now_iso,
)


def calculate_financial_impact(
    gross_benefit: float,
    implementation_cost: float,
    measurement_period: str = "30 days",
    success_metric: str = "Net contribution margin improvement",
    is_estimated: bool = True,
) -> FinancialImpactBreakdown:
    """
    Computes rigorous financial impact breakdown with ROI and payback period.
    """
    g_ben = round(float(gross_benefit), 2)
    cost = round(float(implementation_cost), 2)
    net_imp = round(g_ben - cost, 2)

    # ROI multiple: net_impact / cost (if cost > 0)
    roi = round(net_imp / cost, 2) if cost > 0 else (1.0 if net_imp > 0 else 0.0)

    # Payback period (days) assuming linear realization over measurement period
    days_map = {"14 days": 14, "30 days": 30, "45 days": 45, "60 days": 60, "90 days": 90}
    tot_days = days_map.get(measurement_period, 30)
    if g_ben > 0 and cost > 0:
        daily_benefit = g_ben / tot_days
        payback_days = min(tot_days * 2, max(1, int(round(cost / daily_benefit))))
    elif cost == 0:
        payback_days = 0
    else:
        payback_days = tot_days

    return FinancialImpactBreakdown(
        gross_benefit=g_ben,
        implementation_cost=cost,
        net_financial_impact=net_imp,
        roi_multiple=roi,
        payback_period_days=payback_days,
        measurement_period=measurement_period,
        success_metric=success_metric,
        is_estimated=is_estimated,
    )


def audit_realized_financial_outcome(
    projected: FinancialImpactBreakdown,
    realized_gross_benefit: float,
    actual_cost: float,
    measured_by: str = "Human Operator",
    audit_notes: str = "Post-implementation outcome measurement",
) -> RealizedOutcomeRecord:
    """
    Audits actual business performance post-implementation and calculates variance against projections.
    """
    r_ben = round(float(realized_gross_benefit), 2)
    a_cost = round(float(actual_cost), 2)
    r_net = round(r_ben - a_cost, 2)

    # Benefit variance %: (realized - projected) / projected
    proj_ben = projected.gross_benefit
    if proj_ben > 0:
        var_pct = round(((r_ben - proj_ben) / proj_ben * 100.0), 2)
    else:
        var_pct = 0.0

    return RealizedOutcomeRecord(
        measured_at=utc_now_iso(),
        realized_gross_benefit=r_ben,
        actual_cost=a_cost,
        realized_net_impact=r_net,
        benefit_variance_pct=var_pct,
        measured_by=measured_by,
        notes=audit_notes,
    )
