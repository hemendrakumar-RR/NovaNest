"""
Phase 7 — Restaurant Twin
-------------------------
Constructs the empirical Restaurant Network Digital Twin state.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd

try:
    from intelligence.restaurant.health_score import calculate_restaurant_health_score
    from intelligence.restaurant.risk_detection import detect_restaurant_risks
except ImportError:
    from python.intelligence.restaurant.health_score import calculate_restaurant_health_score
    from python.intelligence.restaurant.risk_detection import detect_restaurant_risks


def get_restaurant_twin_state(
    restaurants_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    ratings_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    if restaurants_df is None or restaurants_df.empty:
        return {
            "Total_Restaurants": 0,
            "Total_Merchants": 0,
            "Active_Restaurants": 0,
            "Critical_Risk_Partners": None,
            "Healthy_Restaurants": None,
            "High_Cancellation_Partners": None,
            "Avg_Merchant_Health": None,
            "Avg_Rating": None,
            "Network_Cancellation_Rate": None,
            "Data_Status": "unavailable",
        }

    total_rest = int(len(restaurants_df))
    active_rest = int(orders_df["restaurant_id"].nunique()) if (orders_df is not None and not orders_df.empty and "restaurant_id" in orders_df.columns) else 0

    rating_col = "avg_rating" if "avg_rating" in restaurants_df.columns else ("rating" if "rating" in restaurants_df.columns else None)
    avg_rating = round(float(restaurants_df[rating_col].dropna().mean()), 2) if rating_col and not restaurants_df[rating_col].dropna().empty else None

    cancel_rate: Optional[float] = None
    if orders_df is not None and not orders_df.empty and "order_status" in orders_df.columns:
        cancel_rate = round(float((orders_df["order_status"] == "Cancelled").sum() / len(orders_df) * 100.0), 2)

    critical_count: Optional[int] = None
    healthy_count: Optional[int] = None
    high_cancel_partners: Optional[int] = None
    avg_merchant_health: Optional[float] = None

    if orders_df is not None and not orders_df.empty and {"order_status", "order_amount"}.issubset(orders_df.columns):
        try:
            prep_orders = orders_df.copy()
            if "final_amount" not in prep_orders.columns:
                prep_orders["final_amount"] = prep_orders["order_amount"]
            if "order_datetime" not in prep_orders.columns and "order_time" in prep_orders.columns:
                prep_orders["order_datetime"] = prep_orders["order_time"]
            health_df = calculate_restaurant_health_score(
                restaurants_df,
                prep_orders,
                ratings_df if ratings_df is not None else pd.DataFrame(),
            )
            risk_df = detect_restaurant_risks(health_df)
            if not health_df.empty and "Health_Score" in health_df.columns:
                avg_merchant_health = round(float(health_df["Health_Score"].mean()), 1)
            if not risk_df.empty and "Risk_Category" in risk_df.columns:
                critical_count = int((risk_df["Risk_Category"] == "Critical").sum())
                healthy_count = int((risk_df["Risk_Category"] == "Healthy").sum())
            if not risk_df.empty and "Cancellation_Rate" in risk_df.columns:
                high_cancel_partners = int((risk_df["Cancellation_Rate"] > 5.0).sum())
        except Exception:
            pass

    return {
        "Total_Restaurants": total_rest,
        "Total_Merchants": total_rest,
        "Active_Restaurants": active_rest,
        "Critical_Risk_Partners": critical_count,
        "Healthy_Restaurants": healthy_count,
        "High_Cancellation_Partners": high_cancel_partners,
        "Avg_Merchant_Health": avg_merchant_health,
        "Avg_Rating": avg_rating,
        "Network_Cancellation_Rate": cancel_rate,
        "Data_Status": "available",
    }
