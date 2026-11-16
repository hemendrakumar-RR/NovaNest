"""
Phase 05 — Leak-Free Customer Churn Feature Engineering
--------------------------------------------------------
Builds chronological observation-window customer features anchored strictly
at `cutoff_date` so NO post-cutoff orders, ratings, or full-timeline `Recency`
leak into the churn label or model inputs.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


FORBIDDEN_CHURN_LEAKAGE_COLS: List[str] = [
    "Recency",
    "Is_Churned",
    "Future_Orders",
    "Total_Timeline_Recency",
    "Total_Timeline_Frequency",
]

CHURN_NUMERIC_FEATURES: List[str] = [
    "Pre_Cutoff_Recency_Days",
    "Orders_Last_30d",
    "Orders_Last_60d",
    "Orders_Last_90d",
    "Lookback_Frequency",
    "Lookback_Monetary",
    "Lookback_AOV",
    "Spend_Last_60d",
    "Recent_vs_Prior_Order_Ratio",
    "Cancellation_Rate_Pre",
    "Discount_Usage_Pct_Pre",
    "Avg_Inter_Order_Gap_Days",
    "Lookback_Active_Span_Days",
    "Avg_Rating_Given_Pre",
    "Delivered_Rate_Pre",
]

CHURN_CATEGORICAL_FEATURES: List[str] = ["persona", "city"]


def _resolve_order_timestamps(orders_df: pd.DataFrame) -> pd.DataFrame:
    df = orders_df.copy()
    if "order_datetime" not in df.columns and "order_time" in df.columns:
        df["order_datetime"] = df["order_time"]
    df["order_datetime"] = pd.to_datetime(df["order_datetime"])
    if "final_amount" not in df.columns:
        df["final_amount"] = df["order_amount"]
    if "discount_amount" not in df.columns:
        df["discount_amount"] = 0.0
    if "order_status" not in df.columns:
        df["order_status"] = "Delivered"
    return df


def build_churn_observation_cohort(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    ratings_df: Optional[pd.DataFrame] = None,
    cutoff_date: Optional[pd.Timestamp] = None,
    churn_horizon_days: int = 90,
    lookback_days: int = 180,
    include_target: bool = True,
) -> pd.DataFrame:
    """
    Build a strictly leak-free customer feature cohort observed at `cutoff_date`.

    - Features use ONLY orders with `order_datetime <= cutoff_date`.
    - Ratings are joined by `order_id` on pre-cutoff orders only (never future reviews).
    - Target `Is_Churned = 1` iff the customer places 0 orders strictly inside
      `(cutoff_date, cutoff_date + churn_horizon_days]`.
    """
    df_orders = _resolve_order_timestamps(orders_df)
    max_dt = df_orders["order_datetime"].max()

    if cutoff_date is None:
        cutoff = max_dt - pd.Timedelta(days=churn_horizon_days) if include_target else max_dt
    else:
        cutoff = pd.to_datetime(cutoff_date)

    pre_orders = df_orders[df_orders["order_datetime"] <= cutoff].copy()
    if pre_orders.empty:
        raise ValueError(f"No pre-cutoff orders found on or before {cutoff}.")

    lookback_start = cutoff - pd.Timedelta(days=lookback_days)
    lb_orders = pre_orders[pre_orders["order_datetime"] > lookback_start].copy()

    # Pre-cutoff lifetime & recency stats
    life_agg = pre_orders.groupby("customer_id").agg(
        Pre_Cutoff_Last_Order=("order_datetime", "max"),
        Pre_Cutoff_First_Order=("order_datetime", "min"),
        Total_Pre_Orders=("order_id", "count"),
        Total_Pre_Spend=("final_amount", "sum"),
    ).reset_index()

    life_agg["Pre_Cutoff_Recency_Days"] = (
        (cutoff - life_agg["Pre_Cutoff_Last_Order"]).dt.total_seconds() / 86400.0
    ).clip(lower=0.0)
    life_agg["Tenure_Days_At_Cutoff"] = (
        (cutoff - life_agg["Pre_Cutoff_First_Order"]).dt.total_seconds() / 86400.0
    ).clip(lower=1.0)
    life_agg["Lookback_Active_Span_Days"] = life_agg["Tenure_Days_At_Cutoff"].clip(upper=float(lookback_days))

    # Multi-window behavioral signals strictly <= cutoff
    pre_orders["days_before_cutoff"] = (cutoff - pre_orders["order_datetime"]).dt.total_seconds() / 86400.0
    pre_orders["is_last_30"] = (pre_orders["days_before_cutoff"] <= 30.0).astype(int)
    pre_orders["is_last_60"] = (pre_orders["days_before_cutoff"] <= 60.0).astype(int)
    pre_orders["is_last_90"] = (pre_orders["days_before_cutoff"] <= 90.0).astype(int)
    pre_orders["is_prev_60_120"] = (
        (pre_orders["days_before_cutoff"] > 60.0) & (pre_orders["days_before_cutoff"] <= 120.0)
    ).astype(int)
    pre_orders["spend_last_60"] = np.where(pre_orders["is_last_60"] == 1, pre_orders["final_amount"], 0.0)
    pre_orders["is_cancelled"] = (pre_orders["order_status"] == "Cancelled").astype(int)
    pre_orders["is_delivered"] = (pre_orders["order_status"] == "Delivered").astype(int)

    win_agg = pre_orders.groupby("customer_id").agg(
        Orders_Last_30d=("is_last_30", "sum"),
        Orders_Last_60d=("is_last_60", "sum"),
        Orders_Last_90d=("is_last_90", "sum"),
        Orders_Prev_60_120d=("is_prev_60_120", "sum"),
        Spend_Last_60d=("spend_last_60", "sum"),
        Pre_Cancellations=("is_cancelled", "sum"),
        Pre_Delivered=("is_delivered", "sum"),
        Pre_Gross_Amount=("order_amount", "sum"),
        Pre_Discount_Amount=("discount_amount", "sum"),
    ).reset_index()

    lb_agg = lb_orders.groupby("customer_id").agg(
        Lookback_Frequency=("order_id", "count"),
        Lookback_Monetary=("final_amount", "sum"),
    ).reset_index()

    feat = life_agg.merge(win_agg, on="customer_id", how="left").merge(lb_agg, on="customer_id", how="left")
    feat["Lookback_Frequency"] = feat["Lookback_Frequency"].fillna(0.0)
    feat["Lookback_Monetary"] = feat["Lookback_Monetary"].fillna(0.0)
    feat["Lookback_AOV"] = np.where(
        feat["Lookback_Frequency"] > 0,
        feat["Lookback_Monetary"] / feat["Lookback_Frequency"],
        feat["Total_Pre_Spend"] / np.maximum(feat["Total_Pre_Orders"], 1),
    )
    feat["Recent_vs_Prior_Order_Ratio"] = (feat["Orders_Last_60d"] + 0.5) / (feat["Orders_Prev_60_120d"] + 0.5)
    feat["Cancellation_Rate_Pre"] = (feat["Pre_Cancellations"] / np.maximum(feat["Total_Pre_Orders"], 1)) * 100.0
    feat["Delivered_Rate_Pre"] = (feat["Pre_Delivered"] / np.maximum(feat["Total_Pre_Orders"], 1)) * 100.0
    feat["Discount_Usage_Pct_Pre"] = (
        feat["Pre_Discount_Amount"] / np.maximum(feat["Pre_Gross_Amount"], 1.0)
    ) * 100.0
    feat["Avg_Inter_Order_Gap_Days"] = np.where(
        feat["Total_Pre_Orders"] > 1,
        (
            (feat["Pre_Cutoff_Last_Order"] - feat["Pre_Cutoff_First_Order"]).dt.total_seconds() / 86400.0
        ) / (feat["Total_Pre_Orders"] - 1),
        float(lookback_days),
    )

    # Pre-cutoff ratings only (joined by pre-cutoff order_id so zero future review leakage)
    default_rating = 4.0
    if ratings_df is not None and not ratings_df.empty:
        pre_order_ids = set(pre_orders["order_id"].unique())
        r_pre = ratings_df.copy()
        if "order_id" in r_pre.columns:
            r_pre = r_pre[r_pre["order_id"].isin(pre_order_ids)]
        rating_cols = [c for c in ["delivery_rating", "restaurant_rating"] if c in r_pre.columns]
        if rating_cols and not r_pre.empty:
            r_pre["_mean_rating"] = r_pre[rating_cols].mean(axis=1)
            if "customer_id" in r_pre.columns:
                r_agg = r_pre.groupby("customer_id")["_mean_rating"].mean().reset_index(name="Avg_Rating_Given_Pre")
            else:
                r_pre_m = r_pre.merge(pre_orders[["order_id", "customer_id"]], on="order_id", how="inner")
                r_agg = r_pre_m.groupby("customer_id")["_mean_rating"].mean().reset_index(name="Avg_Rating_Given_Pre")
            feat = feat.merge(r_agg, on="customer_id", how="left")
            default_rating = float(r_agg["Avg_Rating_Given_Pre"].median()) if not r_agg.empty else 4.0

    if "Avg_Rating_Given_Pre" not in feat.columns:
        feat["Avg_Rating_Given_Pre"] = default_rating
    else:
        feat["Avg_Rating_Given_Pre"] = feat["Avg_Rating_Given_Pre"].fillna(default_rating)

    # Merge safe static customer attributes
    cust_cols = ["customer_id"] + [c for c in ["persona", "city"] if c in customers_df.columns]
    merged = customers_df[cust_cols].merge(feat, on="customer_id", how="inner")
    if "persona" not in merged.columns:
        merged["persona"] = "Unknown"
    if "city" not in merged.columns:
        merged["city"] = "Unknown"

    merged["Observation_Cutoff"] = cutoff

    if include_target:
        horizon_end = cutoff + pd.Timedelta(days=churn_horizon_days)
        if horizon_end > max_dt + pd.Timedelta(seconds=1):
            raise ValueError(
                f"Cannot evaluate {churn_horizon_days}-day churn label: horizon_end={horizon_end} exceeds max_dt={max_dt}."
            )
        post_orders = df_orders[(df_orders["order_datetime"] > cutoff) & (df_orders["order_datetime"] <= horizon_end)]
        post_counts = post_orders.groupby("customer_id")["order_id"].count().rename("Future_Orders").reset_index()
        merged = merged.merge(post_counts, on="customer_id", how="left")
        merged["Future_Orders"] = merged["Future_Orders"].fillna(0).astype(int)
        merged["Is_Churned"] = (merged["Future_Orders"] == 0).astype(int)

    return merged


def extract_churn_features(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    ratings_df: Optional[pd.DataFrame] = None,
    cutoff_date: Optional[pd.Timestamp] = None,
    churn_horizon_days: int = 90,
) -> pd.DataFrame:
    """
    Backward-compatible entry point returning the leak-free labeled observation cohort.
    Never defines `Is_Churned` from full-timeline `Recency > 90`.
    """
    return build_churn_observation_cohort(
        orders_df=orders_df,
        customers_df=customers_df,
        ratings_df=ratings_df,
        cutoff_date=cutoff_date,
        churn_horizon_days=churn_horizon_days,
        lookback_days=180,
        include_target=True,
    )
