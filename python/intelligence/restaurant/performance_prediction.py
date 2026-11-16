"""
Phase 05 — Restaurant Intelligence: Leak-Free Monthly Order Prediction Panel
----------------------------------------------------------------------------
Replaces v1 synthetic target leakage (Total_Orders * uniform(0.9, 1.15)) with
real chronological next-month restaurant order counts built strictly from prior
historical months (< target_month).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


FORBIDDEN_RESTAURANT_LEAKAGE_COLS: List[str] = [
    "Total_Orders",
    "Total_Revenue",
    "Actual_Next_Month_Orders",
    "Predicted_Next_Month_Orders",
]

RESTAURANT_NUMERIC_FEATURES: List[str] = [
    "prev_1m_orders",
    "prev_2m_orders",
    "prev_3m_orders",
    "trailing_3m_avg_orders",
    "trailing_3m_std_orders",
    "expanding_avg_monthly_orders",
    "trailing_3m_avg_revenue",
    "trailing_3m_aov",
    "trailing_3m_cancel_rate",
    "orders_momentum_1m_vs_3m",
    "avg_rating",
    "delivery_radius_km",
    "commission_percentage",
    "opening_year",
    "month_sin",
    "month_cos",
]

RESTAURANT_CATEGORICAL_FEATURES: List[str] = [
    "city",
    "restaurant_type",
    "cuisine_type",
]


def _prepare_orders(orders_df: pd.DataFrame) -> pd.DataFrame:
    df = orders_df.copy()
    if "order_datetime" not in df.columns and "order_time" in df.columns:
        df["order_datetime"] = df["order_time"]
    df["order_datetime"] = pd.to_datetime(df["order_datetime"])
    if "final_amount" not in df.columns:
        df["final_amount"] = df["order_amount"]
    if "order_status" not in df.columns:
        df["order_status"] = "Delivered"
    return df


def extract_restaurant_features(restaurants_df: pd.DataFrame, orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract non-leaked lifetime restaurant operational summaries without synthesizing
    artificial `Predicted_Next_Month_Orders = Total_Orders * random_noise`.
    """
    o_prep = _prepare_orders(orders_df)
    r_stats = o_prep.groupby("restaurant_id").agg(
        Total_Orders=("order_id", "count"),
        Total_Revenue=("final_amount", "sum"),
        Cancellations=("order_status", lambda x: int((x == "Cancelled").sum())),
    ).reset_index()

    merged = restaurants_df.merge(r_stats, on="restaurant_id", how="left")
    merged["Total_Orders"] = merged["Total_Orders"].fillna(0).astype(int)
    merged["Total_Revenue"] = merged["Total_Revenue"].fillna(0.0).round(2)
    merged["Cancellations"] = merged["Cancellations"].fillna(0).astype(int)
    merged["AOV"] = np.where(merged["Total_Orders"] > 0, merged["Total_Revenue"] / merged["Total_Orders"], 0.0).round(2)
    merged["Cancellation_Rate"] = np.where(merged["Total_Orders"] > 0, (merged["Cancellations"] / merged["Total_Orders"]) * 100.0, 0.0).round(2)
    return merged


def build_restaurant_monthly_panel(
    restaurants_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    min_prior_months: int = 3,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[pd.Period]]:
    """
    Construct a gap-free monthly restaurant panel using ONLY complete calendar months,
    plus the next-month live scoring feature matrix anchored after the final full month.

    Returns:
      - panel_df: labeled chronological rows (target_month >= full_months[min_prior_months])
      - scoring_features_df: strictly prior features predicting the upcoming full month
      - full_months: sorted list of complete Period('M') months used
    """
    o_prep = _prepare_orders(orders_df)
    o_prep["ym"] = o_prep["order_datetime"].dt.to_period("M")

    # Exclude partial boundary months (<25 days observed at edges) so monthly counts are apples-to-apples
    month_bounds = o_prep.groupby("ym")["order_datetime"].agg(["min", "max"])
    full_months: List[pd.Period] = []
    for ym, row in month_bounds.iterrows():
        days_covered = (row["max"].normalize() - row["min"].normalize()).days + 1
        if days_covered >= 24:
            full_months.append(ym)
    full_months = sorted(full_months)

    if len(full_months) <= min_prior_months:
        full_months = sorted(month_bounds.index.tolist())
    if len(full_months) <= min_prior_months:
        raise ValueError(f"Need > {min_prior_months} months for restaurant panel; found {len(full_months)}.")

    o_full = o_prep[o_prep["ym"].isin(full_months)].copy()
    o_full["is_cancel"] = (o_full["order_status"] == "Cancelled").astype(int)

    monthly_agg = o_full.groupby(["restaurant_id", "ym"]).agg(
        month_orders=("order_id", "count"),
        month_revenue=("final_amount", "sum"),
        month_cancellations=("is_cancel", "sum"),
    ).reset_index()

    rest_ids = restaurants_df["restaurant_id"].unique()
    grid = pd.MultiIndex.from_product([rest_ids, full_months], names=["restaurant_id", "ym"]).to_frame(index=False)
    panel = grid.merge(monthly_agg, on=["restaurant_id", "ym"], how="left")
    panel["month_orders"] = panel["month_orders"].fillna(0.0)
    panel["month_revenue"] = panel["month_revenue"].fillna(0.0)
    panel["month_cancellations"] = panel["month_cancellations"].fillna(0.0)
    panel = panel.sort_values(["restaurant_id", "ym"]).reset_index(drop=True)

    # Strictly shifted historical lags per restaurant (< target_month)
    g = panel.groupby("restaurant_id", sort=False)
    p1 = g["month_orders"].shift(1)
    p2 = g["month_orders"].shift(2)
    p3 = g["month_orders"].shift(3)
    panel["prev_1m_orders"] = p1
    panel["prev_2m_orders"] = p2
    panel["prev_3m_orders"] = p3
    panel["trailing_3m_avg_orders"] = g["month_orders"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    panel["trailing_3m_std_orders"] = g["month_orders"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).std()).fillna(0.0)
    panel["expanding_avg_monthly_orders"] = g["month_orders"].transform(lambda s: s.shift(1).expanding(min_periods=1).mean())

    t3_rev_sum = g["month_revenue"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).sum())
    t3_ord_sum = g["month_orders"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).sum())
    t3_canc_sum = g["month_cancellations"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).sum())
    panel["trailing_3m_avg_revenue"] = t3_rev_sum / 3.0
    panel["trailing_3m_aov"] = np.where(t3_ord_sum > 0, t3_rev_sum / t3_ord_sum, 0.0)
    panel["trailing_3m_cancel_rate"] = np.where(t3_ord_sum > 0, (t3_canc_sum / t3_ord_sum) * 100.0, 0.0)
    panel["orders_momentum_1m_vs_3m"] = (panel["prev_1m_orders"] + 0.5) / (panel["trailing_3m_avg_orders"] + 0.5)

    panel["target_month"] = panel["ym"].astype(str)
    panel["target_month_ts"] = panel["ym"].dt.to_timestamp()
    m_num = panel["ym"].dt.month.astype(float)
    panel["month_sin"] = np.sin(2.0 * np.pi * m_num / 12.0)
    panel["month_cos"] = np.cos(2.0 * np.pi * m_num / 12.0)
    panel["Actual_Next_Month_Orders"] = panel["month_orders"]

    static_cols = [
        c for c in ["restaurant_id", "city", "restaurant_type", "cuisine_type", "opening_year", "avg_rating", "delivery_radius_km", "commission_percentage"]
        if c in restaurants_df.columns
    ]
    panel = panel.merge(restaurants_df[static_cols], on="restaurant_id", how="left")

    valid_months = [str(m) for m in full_months[min_prior_months:]]
    labeled_panel = panel[panel["target_month"].isin(valid_months)].dropna(subset=["prev_1m_orders", "prev_2m_orders", "prev_3m_orders"]).reset_index(drop=True)

    # Next-month forward scoring rows built cleanly at final_full_month + 1 using observed full months
    last_m = full_months[-1]
    next_m = last_m + 1
    next_m_num = float(next_m.month)
    latest_hist = panel[panel["ym"] <= last_m].copy()
    last_3 = full_months[-3:]

    h_all = latest_hist.groupby("restaurant_id")["month_orders"].mean().rename("expanding_avg_monthly_orders")
    h_1 = latest_hist[latest_hist["ym"] == full_months[-1]].set_index("restaurant_id")["month_orders"].rename("prev_1m_orders")
    h_2 = latest_hist[latest_hist["ym"] == full_months[-2]].set_index("restaurant_id")["month_orders"].rename("prev_2m_orders")
    h_3 = latest_hist[latest_hist["ym"] == full_months[-3]].set_index("restaurant_id")["month_orders"].rename("prev_3m_orders")
    sub3 = latest_hist[latest_hist["ym"].isin(last_3)].groupby("restaurant_id").agg(
        trailing_3m_avg_orders=("month_orders", "mean"),
        trailing_3m_std_orders=("month_orders", "std"),
        _rev=("month_revenue", "sum"),
        _ord=("month_orders", "sum"),
        _canc=("month_cancellations", "sum"),
    )

    score_df = restaurants_df[static_cols].copy().set_index("restaurant_id")
    score_df["prev_1m_orders"] = h_1
    score_df["prev_2m_orders"] = h_2
    score_df["prev_3m_orders"] = h_3
    score_df["expanding_avg_monthly_orders"] = h_all
    score_df["trailing_3m_avg_orders"] = sub3["trailing_3m_avg_orders"]
    score_df["trailing_3m_std_orders"] = sub3["trailing_3m_std_orders"].fillna(0.0)
    score_df["trailing_3m_avg_revenue"] = sub3["_rev"] / 3.0
    score_df["trailing_3m_aov"] = np.where(sub3["_ord"] > 0, sub3["_rev"] / sub3["_ord"], 0.0)
    score_df["trailing_3m_cancel_rate"] = np.where(sub3["_ord"] > 0, (sub3["_canc"] / sub3["_ord"]) * 100.0, 0.0)
    score_df = score_df.fillna(0.0).reset_index()
    score_df["orders_momentum_1m_vs_3m"] = (score_df["prev_1m_orders"] + 0.5) / (score_df["trailing_3m_avg_orders"] + 0.5)
    score_df["month_sin"] = float(np.sin(2.0 * np.pi * next_m_num / 12.0))
    score_df["month_cos"] = float(np.cos(2.0 * np.pi * next_m_num / 12.0))
    score_df["scoring_target_month"] = str(next_m)

    return labeled_panel, score_df, full_months
