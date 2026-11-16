"""
Phase 6 — Restaurant Simulator
------------------------------
Simulates restaurant revenue, volume, and partner take-rate metrics on non-cancelled orders.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


def simulate_restaurant_impact(
    restaurants_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    scenario_params: Dict[str, Any],
    orders_engineered_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    if restaurants_df is None or restaurants_df.empty or orders_df is None or orders_df.empty:
        return _empty_rest_result()

    base_restaurants = int(len(restaurants_df))
    valid_orders = (
        orders_df[orders_df["order_status"] != "Cancelled"]
        if "order_status" in orders_df.columns
        else orders_df
    )
    base_gross_revenue = float(valid_orders["order_amount"].sum()) if "order_amount" in valid_orders.columns else 0.0

    commission_assumed = False
    if (
        orders_engineered_df is not None
        and not orders_engineered_df.empty
        and "commission_revenue" in orders_engineered_df.columns
        and base_gross_revenue > 0
    ):
        eng_deliv = (
            orders_engineered_df[orders_engineered_df["order_status"] == "Delivered"]
            if "order_status" in orders_engineered_df.columns
            else orders_engineered_df
        )
        base_commission = float(eng_deliv["commission_revenue"].sum())
        base_commission_rate = base_commission / base_gross_revenue
    elif "commission_percentage" in restaurants_df.columns and not restaurants_df["commission_percentage"].dropna().empty:
        base_commission_rate = float(restaurants_df["commission_percentage"].dropna().mean()) / 100.0
        base_commission = base_gross_revenue * base_commission_rate
    else:
        commission_assumed = True
        base_commission_rate = 0.20
        base_commission = base_gross_revenue * base_commission_rate

    base_restaurant_revenue = base_gross_revenue - base_commission

    aov_mult = 1.0 + (float(scenario_params.get("aov_change_pct", 0.0)) / 100.0)
    demand_mult = 1.0 + (float(scenario_params.get("demand_change_pct", 0.0)) / 100.0)
    comm_mult = 1.0 + (float(scenario_params.get("commission_change_pct", 0.0)) / 100.0)

    sim_gross_revenue = base_gross_revenue * demand_mult * aov_mult
    sim_commission_rate = base_commission_rate * comm_mult
    sim_commission = sim_gross_revenue * sim_commission_rate
    sim_restaurant_revenue = sim_gross_revenue - sim_commission

    return {
        "baseline": {
            "Active_Restaurants": base_restaurants,
            "Total_Restaurant_Revenue": round(base_restaurant_revenue, 2),
            "Avg_Platform_Commission": round(base_commission_rate, 4),
        },
        "simulated": {
            "Active_Restaurants": base_restaurants,
            "Total_Restaurant_Revenue": round(sim_restaurant_revenue, 2),
            "Avg_Platform_Commission": round(sim_commission_rate, 4),
        },
        "impact": {
            "Revenue_Diff": round(sim_restaurant_revenue - base_restaurant_revenue, 2),
            "Commission_Rate_Diff": round(sim_commission_rate - base_commission_rate, 4),
        },
        "metadata": {
            "commission_assumption_applied": commission_assumed,
        },
    }


def _empty_rest_result() -> Dict[str, Any]:
    empty = {"Active_Restaurants": 0, "Total_Restaurant_Revenue": 0.0, "Avg_Platform_Commission": 0.0}
    return {
        "baseline": dict(empty),
        "simulated": dict(empty),
        "impact": {"Revenue_Diff": 0.0, "Commission_Rate_Diff": 0.0},
        "metadata": {"commission_assumption_applied": False},
    }
