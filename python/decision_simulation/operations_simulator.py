"""
Phase 6 — Operations Simulator
------------------------------
Simulates delivery operations, ETA, and rider SLA compliance grounded on
observed deliveries telemetry (with explicit assumption labels when absent).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


def simulate_operations(
    orders_df: pd.DataFrame,
    scenario_params: Dict[str, Any],
    deliveries_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Estimates operational capacity, SLA compliance, and delivery transit delays."""
    if orders_df is None or orders_df.empty:
        return _empty_ops_result()

    valid_orders = (
        orders_df[orders_df["order_status"] != "Cancelled"]
        if "order_status" in orders_df.columns
        else orders_df
    )
    base_orders = int(len(valid_orders))
    if base_orders == 0:
        return _empty_ops_result()

    eta_assumed = False
    if deliveries_df is not None and not deliveries_df.empty and "delivery_duration" in deliveries_df.columns:
        valid_dur = deliveries_df["delivery_duration"].dropna()
        if not valid_dur.empty:
            base_avg_eta = float(valid_dur.mean())
            base_sla_compliance = float((valid_dur <= 45).mean())
            eta_note = "Empirical mean delivery duration and 45-min SLA compliance from deliveries dataset"
        else:
            eta_assumed = True
            base_avg_eta = 35.0
            base_sla_compliance = 0.85
            eta_note = "Scenario assumption: 35.0 min ETA & 85% SLA (delivery durations empty)"
    else:
        eta_assumed = True
        base_avg_eta = 35.0
        base_sla_compliance = 0.85
        eta_note = "Scenario assumption: 35.0 min ETA & 85% SLA (deliveries dataset unavailable)"

    delivery_time_mult = 1.0 + (float(scenario_params.get("delivery_time_change_pct", 0.0)) / 100.0)
    capacity_mult = 1.0 + (float(scenario_params.get("rider_capacity_change_pct", 0.0)) / 100.0)
    demand_mult = 1.0 + (float(scenario_params.get("demand_change_pct", 0.0)) / 100.0)

    sim_orders = int(round(base_orders * demand_mult))
    congestion_ratio = demand_mult / capacity_mult if capacity_mult > 0 else 1.5
    sim_avg_eta = base_avg_eta * delivery_time_mult * (1.0 + (congestion_ratio - 1.0) * 0.5)

    eta_increase_ratio = sim_avg_eta / base_avg_eta if base_avg_eta > 0 else 1.0
    sla_penalty = (eta_increase_ratio - 1.0) * 0.5
    sim_sla_compliance = max(0.0, min(1.0, base_sla_compliance - sla_penalty))

    return {
        "baseline": {
            "Total_Deliveries": base_orders,
            "Avg_ETA_Mins": round(base_avg_eta, 2),
            "SLA_Compliance": round(base_sla_compliance, 4),
        },
        "simulated": {
            "Total_Deliveries": sim_orders,
            "Avg_ETA_Mins": round(sim_avg_eta, 2),
            "SLA_Compliance": round(sim_sla_compliance, 4),
        },
        "impact": {
            "ETA_Diff_Mins": round(sim_avg_eta - base_avg_eta, 2),
            "SLA_Diff_Pct": round(sim_sla_compliance - base_sla_compliance, 4),
        },
        "metadata": {
            "eta_assumption_applied": eta_assumed,
            "assumption_note": eta_note,
        },
    }


def _empty_ops_result() -> Dict[str, Any]:
    empty = {"Total_Deliveries": 0, "Avg_ETA_Mins": 0.0, "SLA_Compliance": 0.0}
    return {
        "baseline": dict(empty),
        "simulated": dict(empty),
        "impact": {"ETA_Diff_Mins": 0.0, "SLA_Diff_Pct": 0.0},
        "metadata": {"eta_assumption_applied": False, "assumption_note": "No order data"},
    }
