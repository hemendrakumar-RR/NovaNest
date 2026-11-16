"""
Phase 6 — Customer Impact Simulator
-----------------------------------
Simulates scenario impact on customer retention and active base, grounding baseline
churn in actual churn predictions when available and explicitly labeling assumptions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


def simulate_customer_impact(
    customers_df: pd.DataFrame,
    scenario_params: Dict[str, Any],
    churn_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Estimates changes to customer retention and active base."""
    if customers_df is None or customers_df.empty:
        return _empty_customer_result()

    base_customers = int(len(customers_df))

    churn_assumed = False
    if churn_df is not None and not churn_df.empty:
        risk_col = (
            "Churn_Risk"
            if "Churn_Risk" in churn_df.columns
            else ("churn_risk_level" if "churn_risk_level" in churn_df.columns else None)
        )
        if risk_col:
            base_churned = int(
                churn_df[risk_col].astype(str).str.lower().isin(["high risk", "high", "critical"]).sum()
            )
            base_churn_rate = base_churned / base_customers if base_customers > 0 else 0.0
            churn_note = "Empirical high-risk cohort count from churn predictions"
        else:
            churn_assumed = True
            base_churn_rate = 0.15
            base_churned = int(base_customers * base_churn_rate)
            churn_note = "Scenario assumption: 15.0% baseline monthly churn (risk column missing)"
    else:
        churn_assumed = True
        base_churn_rate = 0.15
        base_churned = int(base_customers * base_churn_rate)
        churn_note = "Scenario assumption: 15.0% baseline monthly churn (churn dataset unavailable)"

    base_retained = max(0, base_customers - base_churned)

    retention_mult = 1.0 + (float(scenario_params.get("retention_change_pct", 0.0)) / 100.0)
    churn_reduction = float(scenario_params.get("churn_reduction_pct", 0.0)) / 100.0
    acq_mult = 1.0 + (float(scenario_params.get("customer_acquisition_pct", 0.0)) / 100.0)

    sim_churn_rate = base_churn_rate * max(0.0, (1.0 - churn_reduction))
    if retention_mult > 0:
        sim_churn_rate = sim_churn_rate / retention_mult

    sim_churned = int(round(base_customers * sim_churn_rate))
    sim_retained = max(0, base_customers - sim_churned)

    # Acquisition pipeline modeled as explicit scenario parameter (20% of customer base)
    base_acquired = int(base_customers * 0.20)
    sim_acquired = int(round(base_acquired * acq_mult))

    sim_total_active = sim_retained + sim_acquired
    base_total_active = base_retained + base_acquired

    return {
        "baseline": {
            "Total_Customers": base_customers,
            "Churn_Rate": round(base_churn_rate, 4),
            "Churned_Customers": base_churned,
            "Retained_Customers": base_retained,
            "New_Acquisitions": base_acquired,
            "Ending_Active_Base": base_total_active,
        },
        "simulated": {
            "Total_Customers": base_customers,
            "Churn_Rate": round(sim_churn_rate, 4),
            "Churned_Customers": sim_churned,
            "Retained_Customers": sim_retained,
            "New_Acquisitions": sim_acquired,
            "Ending_Active_Base": sim_total_active,
        },
        "impact": {
            "Active_Base_Diff": sim_total_active - base_total_active,
            "Churn_Reduction": base_churned - sim_churned,
        },
        "metadata": {
            "churn_assumption_applied": churn_assumed,
            "churn_note": churn_note,
            "acquisition_assumption_note": "Scenario assumption: 20.0% baseline new-acquisition pipeline",
        },
    }


def _empty_customer_result() -> Dict[str, Any]:
    empty = {
        "Total_Customers": 0,
        "Churn_Rate": 0.0,
        "Churned_Customers": 0,
        "Retained_Customers": 0,
        "New_Acquisitions": 0,
        "Ending_Active_Base": 0,
    }
    return {
        "baseline": dict(empty),
        "simulated": dict(empty),
        "impact": {"Active_Base_Diff": 0, "Churn_Reduction": 0},
        "metadata": {"churn_assumption_applied": False, "churn_note": "No customer data"},
    }
