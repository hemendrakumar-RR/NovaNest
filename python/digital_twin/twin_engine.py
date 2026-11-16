"""
Phase 7 — Digital Twin Engine
-----------------------------
Orchestrates creation of the unified empirical analytical Digital Twin State.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import pandas as pd

from digital_twin.customer_twin import get_customer_twin_state
from digital_twin.financial_twin import get_financial_twin_state
from digital_twin.operations_twin import get_operations_twin_state
from digital_twin.restaurant_twin import get_restaurant_twin_state
from digital_twin.twin_alerts import generate_twin_alerts
from digital_twin.twin_state import TwinState
from digital_twin.validation import validate_twin_inputs


def build_digital_twin_state(data: Dict[str, Any]) -> TwinState:
    """Builds the current analytical digital twin state from verified platform datasets."""
    if not validate_twin_inputs(data):
        return TwinState(timestamp=datetime.now().isoformat())

    orders_df = data.get("orders")
    customers_df = data.get("customers")
    restaurants_df = data.get("restaurants")
    orders_eng_df = data.get("orders_engineered")
    leakage_df = data.get("revenue_leakage")
    churn_df = data.get("customer_churn_predictions")
    ratings_df = data.get("ratings_reviews")
    deliveries_df = data.get("deliveries")
    riders_df = data.get("riders")
    anomalies_df = data.get("operational_anomalies")

    fin_state = get_financial_twin_state(orders_df, orders_eng_df, leakage_df)
    cust_state = get_customer_twin_state(customers_df, orders_df, churn_df)
    rest_state = get_restaurant_twin_state(restaurants_df, orders_df, ratings_df)
    ops_state = get_operations_twin_state(orders_df, deliveries_df, riders_df, anomalies_df)

    alerts = generate_twin_alerts(fin_state, ops_state, cust_state, rest_state)

    # Calculate Business Health Score (0-100) cleanly with null-safe checks
    health_score = 100
    if (fin_state.get("Profit_Margin") or 0.0) < 0.10:
        health_score -= 15

    late_deliv = ops_state.get("Late_Deliveries")
    denom = ops_metrics_denom = ops_state.get("Deliveries_Recorded") or ops_state.get("Total_Orders") or 0
    if late_deliv is not None and ops_metrics_denom > 0 and late_deliv > (ops_metrics_denom * 0.10):
        health_score -= 15

    gross_rev = fin_state.get("Gross_Revenue") or 0.0
    leakage_est = fin_state.get("Revenue_Leakage_Est") or 0.0
    if gross_rev > 0 and leakage_est > (gross_rev * 0.10):
        health_score -= 10

    fin_state["Business_Health_Score"] = max(0, int(health_score))

    return TwinState(
        timestamp=datetime.now().isoformat(),
        financial_state=fin_state,
        customer_state=cust_state,
        restaurant_state=rest_state,
        operations_state=ops_state,
        alerts=alerts,
    )
