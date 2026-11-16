"""
Phase 6 — Financial Simulator
-----------------------------
Simulates financial impact of decision scenarios on revenue, profit, and margins,
grounded on non-cancelled/delivered baseline orders and empirical take rates.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


def simulate_financials(
    orders_df: pd.DataFrame,
    scenario_params: Dict[str, Any],
    orders_engineered_df: Optional[pd.DataFrame] = None,
    restaurants_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Simulates financial metrics based on certified non-cancelled/delivered orders."""
    if orders_df is None or orders_df.empty:
        return _empty_financial_result()

    has_status = "order_status" in orders_df.columns
    if has_status:
        non_cancelled = orders_df[orders_df["order_status"] != "Cancelled"]
        delivered = orders_df[orders_df["order_status"] == "Delivered"]
    else:
        non_cancelled = orders_df
        delivered = orders_df

    base_orders = int(len(delivered) if not delivered.empty else len(non_cancelled))
    if base_orders == 0:
        return _empty_financial_result()

    base_gross_revenue = float(non_cancelled["order_amount"].sum()) if "order_amount" in non_cancelled.columns else 0.0
    base_discount = float(delivered["discount_amount"].sum()) if "discount_amount" in delivered.columns else 0.0
    base_delivery_fee = float(delivered["delivery_fee"].sum()) if "delivery_fee" in delivered.columns else 0.0

    # Derive empirical commission take rate when engineered or merchant data exists
    commission_assumed = False
    assumption_note = "Empirical commission rate derived from delivered orders"
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
        base_commission_revenue = float(eng_deliv["commission_revenue"].sum())
        base_commission_rate = base_commission_revenue / base_gross_revenue
    elif restaurants_df is not None and not restaurants_df.empty and "commission_percentage" in restaurants_df.columns:
        base_commission_rate = float(restaurants_df["commission_percentage"].dropna().mean()) / 100.0
        base_commission_revenue = base_gross_revenue * base_commission_rate
    else:
        commission_assumed = True
        base_commission_rate = 0.20
        base_commission_revenue = base_gross_revenue * base_commission_rate
        assumption_note = "Scenario fallback: assumed 20.0% baseline commission rate (orders_engineered unavailable)"

    base_platform_revenue = base_commission_revenue + base_delivery_fee - base_discount
    base_aov = base_gross_revenue / base_orders if base_orders > 0 else 0.0
    base_margin = (base_platform_revenue / base_gross_revenue) if base_gross_revenue > 0 else 0.0

    # Apply scenario multipliers
    aov_mult = 1.0 + (float(scenario_params.get("aov_change_pct", 0.0)) / 100.0)
    demand_mult = 1.0 + (float(scenario_params.get("demand_change_pct", 0.0)) / 100.0)
    discount_mult = 1.0 + (float(scenario_params.get("discount_change_pct", 0.0)) / 100.0)
    fee_mult = 1.0 + (float(scenario_params.get("delivery_fee_change_pct", 0.0)) / 100.0)
    comm_mult = 1.0 + (float(scenario_params.get("commission_change_pct", 0.0)) / 100.0)

    sim_orders = int(round(base_orders * demand_mult))
    sim_aov = base_aov * aov_mult
    sim_gross_revenue = sim_orders * sim_aov

    avg_discount = (base_discount / base_orders) * discount_mult if base_orders > 0 else 0.0
    avg_fee = (base_delivery_fee / base_orders) * fee_mult if base_orders > 0 else 0.0

    sim_discount = sim_orders * avg_discount
    sim_delivery_fee = sim_orders * avg_fee

    sim_commission_rate = base_commission_rate * comm_mult
    sim_commission_revenue = sim_gross_revenue * sim_commission_rate

    sim_platform_revenue = sim_commission_revenue + sim_delivery_fee - sim_discount
    sim_margin = (sim_platform_revenue / sim_gross_revenue) if sim_gross_revenue > 0 else 0.0

    return {
        "baseline": {
            "Orders": base_orders,
            "AOV": round(base_aov, 2),
            "Gross_Revenue": round(base_gross_revenue, 2),
            "Discount_Cost": round(base_discount, 2),
            "Delivery_Fee_Revenue": round(base_delivery_fee, 2),
            "Commission_Rate": round(base_commission_rate, 4),
            "Platform_Revenue": round(base_platform_revenue, 2),
            "Profit_Margin": round(base_margin, 6),
        },
        "simulated": {
            "Orders": sim_orders,
            "AOV": round(sim_aov, 2),
            "Gross_Revenue": round(sim_gross_revenue, 2),
            "Discount_Cost": round(sim_discount, 2),
            "Delivery_Fee_Revenue": round(sim_delivery_fee, 2),
            "Commission_Rate": round(sim_commission_rate, 4),
            "Platform_Revenue": round(sim_platform_revenue, 2),
            "Profit_Margin": round(sim_margin, 6),
        },
        "impact": {
            "Orders_Diff": sim_orders - base_orders,
            "Gross_Revenue_Diff": round(sim_gross_revenue - base_gross_revenue, 2),
            "Platform_Revenue_Diff": round(sim_platform_revenue - base_platform_revenue, 2),
            "Margin_Diff": round(sim_margin - base_margin, 6),
        },
        "metadata": {
            "commission_assumption_applied": commission_assumed,
            "assumption_note": assumption_note,
            "cancelled_orders_excluded": has_status,
        },
    }


def _empty_financial_result() -> Dict[str, Any]:
    empty_block = {
        "Orders": 0,
        "AOV": 0.0,
        "Gross_Revenue": 0.0,
        "Discount_Cost": 0.0,
        "Delivery_Fee_Revenue": 0.0,
        "Commission_Rate": 0.0,
        "Platform_Revenue": 0.0,
        "Profit_Margin": 0.0,
    }
    return {
        "baseline": dict(empty_block),
        "simulated": dict(empty_block),
        "impact": {
            "Orders_Diff": 0,
            "Gross_Revenue_Diff": 0.0,
            "Platform_Revenue_Diff": 0.0,
            "Margin_Diff": 0.0,
        },
        "metadata": {
            "commission_assumption_applied": False,
            "assumption_note": "No order data available",
            "cancelled_orders_excluded": True,
        },
    }
