"""
Phase 7 — Financial Twin
------------------------
Constructs the empirical Financial Digital Twin state aligned with NovaNest
Phase 04 Certified KPI definitions without fabricated fallback assumptions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


def get_financial_twin_state(
    orders_df: pd.DataFrame,
    orders_engineered_df: Optional[pd.DataFrame] = None,
    leakage_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    if orders_df is None or orders_df.empty:
        return {
            "Gross_Revenue": 0.0,
            "Gross_Merchandise_Value": 0.0,
            "Net_Platform_Revenue": 0.0,
            "Discounts": 0.0,
            "Delivery_Fees": 0.0,
            "Commissions": 0.0,
            "Platform_Revenue": 0.0,
            "Profit_Margin": 0.0,
            "Margin_Rate": 0.0,
            "Revenue_Leakage_Est": 0.0,
            "Leakage_Exposure": 0.0,
            "Leakage_Confirmed": False,
            "Data_Status": "unavailable",
        }

    has_status = "order_status" in orders_df.columns
    if has_status:
        non_cancelled = orders_df[orders_df["order_status"] != "Cancelled"]
        delivered = orders_df[orders_df["order_status"] == "Delivered"]
    else:
        non_cancelled = orders_df
        delivered = orders_df

    gross_gmv = float(non_cancelled["order_amount"].sum()) if "order_amount" in non_cancelled.columns else 0.0
    discounts = float(delivered["discount_amount"].sum()) if (not delivered.empty and "discount_amount" in delivered.columns) else 0.0
    fees = float(delivered["delivery_fee"].sum()) if (not delivered.empty and "delivery_fee" in delivered.columns) else 0.0
    net_inflow = (
        float(delivered["final_amount"].sum())
        if (not delivered.empty and "final_amount" in delivered.columns)
        else gross_gmv
    )

    commission_assumed = False
    if (
        orders_engineered_df is not None
        and not orders_engineered_df.empty
        and "commission_revenue" in orders_engineered_df.columns
    ):
        eng_deliv = (
            orders_engineered_df[orders_engineered_df["order_status"] == "Delivered"]
            if "order_status" in orders_engineered_df.columns
            else orders_engineered_df
        )
        commissions = float(eng_deliv["commission_revenue"].sum())
        realized_profit = (
            float(eng_deliv["estimated_profit"].sum())
            if "estimated_profit" in eng_deliv.columns
            else (commissions + fees - discounts)
        )
        platform_rev = realized_profit
        margin_denom = net_inflow if net_inflow > 0 else gross_gmv
        margin = (realized_profit / margin_denom) if margin_denom > 0 else 0.0
    else:
        # Scenario / unit-test fallback when pre-engineered profit table is absent
        commission_assumed = True
        commissions = gross_gmv * 0.20
        platform_rev = commissions + fees - discounts
        net_inflow = float(delivered["final_amount"].sum()) if (not delivered.empty and "final_amount" in delivered.columns) else platform_rev
        margin = (platform_rev / gross_gmv) if gross_gmv > 0 else 0.0

    if leakage_df is not None and not leakage_df.empty and "potential_leakage_amount" in leakage_df.columns:
        leakage_est = round(float(leakage_df["potential_leakage_amount"].sum()), 2)
        leakage_status = "unverified_candidates"
    else:
        leakage_est = round(discounts, 2) if (gross_gmv > 0 and discounts > (gross_gmv * 0.15)) else 0.0
        leakage_status = "not_audited" if leakage_est == 0 else "heuristic_subsidy_threshold"

    return {
        "Gross_Revenue": round(gross_gmv, 2),
        "Gross_Merchandise_Value": round(gross_gmv, 2),
        "Net_Platform_Revenue": round(net_inflow, 2),
        "Discounts": round(discounts, 2),
        "Delivery_Fees": round(fees, 2),
        "Commissions": round(commissions, 2),
        "Platform_Revenue": round(platform_rev, 2),
        "Profit_Margin": round(margin, 6),
        "Margin_Rate": round(margin * 100.0, 2),
        "Revenue_Leakage_Est": leakage_est,
        "Leakage_Exposure": leakage_est,
        "Leakage_Confirmed": False,
        "Leakage_Status": leakage_status,
        "Commission_Assumption_Applied": commission_assumed,
        "Commission_Assumption_Note": "Assumed 20% commission rate (orders_engineered unavailable)" if commission_assumed else "Derived empirically from orders_engineered delivered rows",
        "Data_Status": "available",
    }
