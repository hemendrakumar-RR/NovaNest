"""
Phase 7 — Operations Twin
-------------------------
Constructs the empirical Operations & Logistics Digital Twin state
without hardcoded placeholder transit times or synthetic late percentages.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


def get_operations_twin_state(
    orders_df: pd.DataFrame,
    deliveries_df: Optional[pd.DataFrame] = None,
    riders_df: Optional[pd.DataFrame] = None,
    anomalies_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    if orders_df is None or orders_df.empty:
        return {
            "Total_Orders": 0,
            "Deliveries_Recorded": 0,
            "Avg_Delivery_Time": None,
            "Avg_ETA": None,
            "Late_Deliveries": None,
            "Fulfillment_Rate": None,
            "Active_Riders": len(riders_df) if (riders_df is not None and not riders_df.empty) else None,
            "Active_Bottlenecks": len(anomalies_df) if (anomalies_df is not None and not anomalies_df.empty) else None,
            "Logistics_Risk": "Unavailable",
            "Data_Status": "unavailable",
        }

    total_orders = int(len(orders_df))
    active_riders = int(len(riders_df)) if (riders_df is not None and not riders_df.empty) else None
    bottlenecks = int(len(anomalies_df)) if anomalies_df is not None else None

    avg_delivery_time: Optional[float] = None
    late_deliveries: Optional[int] = None
    fulfillment_rate: Optional[float] = None
    deliveries_recorded = 0
    logistics_risk = "Unavailable (No Delivery Telemetry)"
    data_status = "partial"

    if deliveries_df is not None and not deliveries_df.empty and "delivery_duration" in deliveries_df.columns:
        valid_dur = deliveries_df["delivery_duration"].dropna()
        deliveries_recorded = int(len(valid_dur))
        if deliveries_recorded > 0:
            avg_delivery_time = round(float(valid_dur.mean()), 2)
            late_deliveries = int((valid_dur > 45).sum())
            fulfillment_rate = round(float((valid_dur <= 45).sum() / deliveries_recorded * 100.0), 2)
            data_status = "available"
            if fulfillment_rate < 85.0:
                logistics_risk = "High"
            elif fulfillment_rate < 92.0:
                logistics_risk = "Moderate"
            else:
                logistics_risk = "Low"

    return {
        "Total_Orders": total_orders,
        "Deliveries_Recorded": deliveries_recorded,
        "Avg_Delivery_Time": avg_delivery_time,
        "Avg_ETA": avg_delivery_time,
        "Late_Deliveries": late_deliveries,
        "Fulfillment_Rate": fulfillment_rate,
        "Active_Riders": active_riders,
        "Active_Bottlenecks": bottlenecks,
        "Logistics_Risk": logistics_risk,
        "Data_Status": data_status,
    }
