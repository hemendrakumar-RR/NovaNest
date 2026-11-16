"""
Phase 7 — Customer Twin
-----------------------
Constructs the empirical Customer Digital Twin state from verified customer,
order, CLV, and churn datasets with explicit unavailability states.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd

try:
    from intelligence.customer.clv import calculate_customer_clv
except ImportError:
    from python.intelligence.customer.clv import calculate_customer_clv


def get_customer_twin_state(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    churn_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    if customers_df is None or customers_df.empty:
        return {
            "Total_Customers": 0,
            "Active_Customers": 0,
            "At_Risk_Customers": None,
            "High_Churn_Risk_Customers": None,
            "Total_CLV_Capital": None,
            "Retention_Rate": None,
            "Avg_Engagement_Score": None,
            "Data_Status": "unavailable",
        }

    total_cust = int(len(customers_df))
    has_orders = orders_df is not None and not orders_df.empty
    if has_orders:
        valid_orders = (
            orders_df[orders_df["order_status"] != "Cancelled"]
            if "order_status" in orders_df.columns
            else orders_df
        )
        active = int(valid_orders["customer_id"].nunique()) if "customer_id" in valid_orders.columns else 0
        order_freq = round(len(valid_orders) / total_cust, 2) if total_cust > 0 else 0.0
        delivered = (
            orders_df[orders_df["order_status"] == "Delivered"]
            if "order_status" in orders_df.columns
            else valid_orders
        )
        aov_col = "final_amount" if "final_amount" in delivered.columns else "order_amount"
        aov = round(float(delivered[aov_col].mean()), 2) if (not delivered.empty and aov_col in delivered.columns) else 0.0
    else:
        active = 0
        order_freq = 0.0
        aov = 0.0

    # Churn risk counts (never fabricated when churn_df is missing)
    at_risk_customers: Optional[int] = None
    retention_rate: Optional[float] = None
    if churn_df is not None and not churn_df.empty:
        risk_col = (
            "Churn_Risk"
            if "Churn_Risk" in churn_df.columns
            else ("churn_risk_level" if "churn_risk_level" in churn_df.columns else None)
        )
        if risk_col:
            at_risk_customers = int(
                churn_df[risk_col].astype(str).str.lower().isin(["high risk", "high", "critical"]).sum()
            )
            if total_cust > 0:
                retention_rate = round(max(0.0, (total_cust - at_risk_customers) / total_cust), 4)

    # Empirical 12M CLV Capital when temporal order fields exist
    total_clv_capital: Optional[float] = None
    if has_orders and ("order_datetime" in orders_df.columns or "order_time" in orders_df.columns):
        try:
            prep_orders = orders_df.copy()
            if "order_datetime" not in prep_orders.columns and "order_time" in prep_orders.columns:
                prep_orders["order_datetime"] = prep_orders["order_time"]
            if "final_amount" not in prep_orders.columns and "order_amount" in prep_orders.columns:
                prep_orders["final_amount"] = prep_orders["order_amount"]
            clv_df = calculate_customer_clv(prep_orders, customers_df)
            if not clv_df.empty and "Estimated_CLV" in clv_df.columns:
                total_clv_capital = round(float(clv_df["Estimated_CLV"].sum()), 2)
        except Exception:
            total_clv_capital = None

    engagement_score = round((active / total_cust) * 100.0, 1) if total_cust > 0 else None

    return {
        "Total_Customers": total_cust,
        "Active_Customers": active,
        "Order_Frequency": order_freq,
        "AOV": aov,
        "At_Risk_Customers": at_risk_customers,
        "High_Churn_Risk_Customers": at_risk_customers,
        "Total_CLV_Capital": total_clv_capital,
        "Retention_Rate": retention_rate,
        "Avg_Engagement_Score": engagement_score,
        "Data_Status": "available",
    }
