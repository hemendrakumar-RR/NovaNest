"""
Customer 360 Analytics Engine
"""

from __future__ import annotations

import pandas as pd


def build_customer_360_profile(
    customer_id: str,
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    rfm_df: pd.DataFrame,
    clv_df: pd.DataFrame,
    churn_df: pd.DataFrame,
) -> dict:
    """Builds a complete 360-degree profile for a given customer."""
    cust_base = customers_df[customers_df["customer_id"] == customer_id]
    if cust_base.empty:
        return {}
    cust_info = cust_base.iloc[0].to_dict()

    cust_orders = orders_df[orders_df["customer_id"] == customer_id]
    valid_orders = (
        cust_orders[cust_orders["order_status"] != "Cancelled"]
        if (not cust_orders.empty and "order_status" in cust_orders.columns)
        else cust_orders
    )
    total_orders = int(len(cust_orders))
    valid_order_count = int(len(valid_orders))
    spend_col = "final_amount" if "final_amount" in valid_orders.columns else "order_amount"
    total_spent = float(valid_orders[spend_col].sum()) if (valid_order_count > 0 and spend_col in valid_orders.columns) else 0.0
    aov = (total_spent / valid_order_count) if valid_order_count > 0 else 0.0

    cust_rfm = rfm_df[rfm_df["customer_id"] == customer_id] if (rfm_df is not None and not rfm_df.empty) else pd.DataFrame()
    rfm_segment = cust_rfm.iloc[0]["RFM_Segment"] if not cust_rfm.empty and "RFM_Segment" in cust_rfm.columns else "Unavailable"
    recency_days = (
        int(cust_rfm.iloc[0]["Recency"])
        if not cust_rfm.empty and "Recency" in cust_rfm.columns and pd.notna(cust_rfm.iloc[0]["Recency"])
        else None
    )

    cust_clv = clv_df[clv_df["customer_id"] == customer_id] if (clv_df is not None and not clv_df.empty) else pd.DataFrame()
    est_clv = float(cust_clv.iloc[0]["Estimated_CLV"]) if not cust_clv.empty and "Estimated_CLV" in cust_clv.columns else total_spent
    clv_segment = cust_clv.iloc[0]["CLV_Segment"] if not cust_clv.empty and "CLV_Segment" in cust_clv.columns else "Unavailable"

    cust_churn = churn_df[churn_df["customer_id"] == customer_id] if (churn_df is not None and not churn_df.empty) else pd.DataFrame()
    if not cust_churn.empty:
        raw_prob = cust_churn.iloc[0].get("Churn_Probability")
        churn_prob = float(raw_prob) if pd.notna(raw_prob) else None
        raw_risk = cust_churn.iloc[0].get("Churn_Risk")
        churn_risk = str(raw_risk) if pd.notna(raw_risk) and str(raw_risk).strip() else "Unavailable"
    else:
        churn_prob = None
        churn_risk = "Unavailable"

    if churn_risk == "High Risk" and est_clv >= 10000:
        recommendation = "High-Value At-Risk Customer: Trigger VIP Retention Offer (25% off + Free Delivery)."
    elif churn_risk == "High Risk":
        recommendation = "At-Risk Customer: Send re-engagement push notification with discount coupon."
    elif rfm_segment in ["Champions", "Loyal Customers"]:
        recommendation = "Loyal Advocate: Invite to NovaNest Premium Subscription Loyalty Club."
    elif churn_risk == "Unavailable":
        recommendation = "Standard Engagement: Predictive churn score unavailable; monitor repeat order cadence."
    else:
        recommendation = "Standard Engagement: Recommend top-rated restaurants in customer's city."

    time_col = "order_datetime" if "order_datetime" in cust_orders.columns else ("order_time" if "order_time" in cust_orders.columns else None)

    return {
        "identity": cust_info,
        "metrics": {
            "Total_Orders": total_orders,
            "Non_Cancelled_Orders": valid_order_count,
            "Total_Spent": round(total_spent, 2),
            "AOV": round(aov, 2),
            "Recency_Days": recency_days,
            "First_Order": cust_orders[time_col].min() if (total_orders > 0 and time_col) else "N/A",
            "Last_Order": cust_orders[time_col].max() if (total_orders > 0 and time_col) else "N/A",
        },
        "intelligence": {
            "RFM_Segment": rfm_segment,
            "Estimated_CLV": round(est_clv, 2),
            "CLV_Segment": clv_segment,
            "Churn_Probability": churn_prob,
            "Churn_Risk": churn_risk,
        },
        "recommendation": recommendation,
    }
