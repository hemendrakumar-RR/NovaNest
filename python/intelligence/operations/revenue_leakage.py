"""
Phase 05 — Operations Intelligence: Vectorized Financial Risk & Revenue Leakage
--------------------------------------------------------------------------------
Evaluates 100% vectorized order-level business rule checks alongside statistical
margin/discount outlier flags, separating Business Rules from Statistical
Anomalies, attaching False-Positive Risk assessments, and preserving all source records.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd


def detect_revenue_leakage(
    orders_eng_df: pd.DataFrame,
    customers_df: Optional[pd.DataFrame] = None,
    restaurants_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Audit ALL orders using vectorized unit-economics rules + statistical bounds.
    Never modifies or deletes source records; clearly documents false-positive risk.
    """
    if orders_eng_df is None or orders_eng_df.empty:
        return pd.DataFrame(), {"Total_Potential_Leakage": 0.0, "Flagged_Orders_Count": 0, "Total_Orders_Audited": 0}

    df = orders_eng_df.copy()
    total_orders = len(df)

    # Ensure unique order audit rows if duplicates accidentally passed
    if "order_id" in df.columns:
        df = df.drop_duplicates(subset=["order_id"], keep="first").reset_index(drop=True)

    df["order_amount"] = pd.to_numeric(df.get("order_amount", 0.0), errors="coerce").fillna(0.0)
    df["discount_amount"] = pd.to_numeric(df.get("discount_amount", 0.0), errors="coerce").fillna(0.0)
    df["delivery_fee"] = pd.to_numeric(df.get("delivery_fee", 0.0), errors="coerce").fillna(0.0)
    df["final_amount"] = pd.to_numeric(df.get("final_amount", df["order_amount"] - df["discount_amount"] + df["delivery_fee"]), errors="coerce").fillna(0.0)
    df["order_status"] = df.get("order_status", "Delivered").fillna("Delivered").astype(str)

    # Join restaurant commission_percentage & names cleanly if missing
    if restaurants_df is not None and not restaurants_df.empty and "restaurant_id" in df.columns:
        r_cols = ["restaurant_id"] + [c for c in ["restaurant_name", "commission_percentage"] if c in restaurants_df.columns and c not in df.columns]
        if len(r_cols) > 1:
            df = df.merge(restaurants_df[r_cols].drop_duplicates("restaurant_id"), on="restaurant_id", how="left")
    if customers_df is not None and not customers_df.empty and "customer_id" in df.columns:
        if "customer_name" not in df.columns and "name" in customers_df.columns:
            df = df.merge(customers_df[["customer_id", "name"]].rename(columns={"name": "customer_name"}), on="customer_id", how="left")

    comm_pct = pd.to_numeric(df.get("commission_percentage", 18.0), errors="coerce").fillna(18.0)
    if "commission_revenue" in df.columns:
        df["_commission_rev"] = pd.to_numeric(df["commission_revenue"], errors="coerce").fillna(df["order_amount"] * comm_pct / 100.0)
    else:
        df["_commission_rev"] = df["order_amount"] * comm_pct / 100.0

    # Platform net contribution assuming platform absorbs discount_amount (conservative worst-case audit)
    delivery_cost_est = 30.0
    net_after_discount = df["_commission_rev"] + df["delivery_fee"] - delivery_cost_est - df["discount_amount"]
    df["estimated_profit_net_subsidy"] = net_after_discount.round(2)
    if "estimated_profit" not in df.columns:
        df["estimated_profit"] = df["estimated_profit_net_subsidy"]

    disc_pct = np.where(df["order_amount"] > 0, (df["discount_amount"] / df["order_amount"]) * 100.0, 0.0)
    disc_mean = float(np.mean(disc_pct))
    disc_std = float(np.std(disc_pct, ddof=1)) if len(disc_pct) > 1 else 0.0
    disc_q1, disc_q3 = float(np.quantile(disc_pct, 0.25)), float(np.quantile(disc_pct, 0.75))
    disc_iqr_upper = disc_q3 + 1.5 * max(disc_q3 - disc_q1, 0.0)
    disc_z = (disc_pct - disc_mean) / disc_std if disc_std > 1e-12 else np.zeros(len(df))

    # Separate Business Rule Conditions vs Statistical Outlier Conditions
    cond_neg_margin = net_after_discount < 0.0
    cond_promo_subsidy = (disc_pct > 25.0) & (df["discount_amount"] > 150.0)
    cond_extreme_disc_stat = (disc_z > 3.0) | (disc_pct >= 100.0) | (disc_pct > disc_iqr_upper * 1.5)
    cond_cancelled = df["order_status"] == "Cancelled"
    cond_free_deliv_small = (df["delivery_fee"] == 0.0) & (df["order_amount"] < 300.0)

    # Leakage impact accumulation (non-overlapping components)
    leak_margin = np.where(cond_neg_margin, np.abs(net_after_discount), 0.0)
    leak_promo = np.where(cond_promo_subsidy & ~cond_neg_margin, np.maximum(0.0, df["discount_amount"] - 150.0), 0.0)
    # Cancelled order opportunity loss = lost commission + lost delivery fee
    leak_cancel = np.where(cond_cancelled, np.maximum(0.0, df["_commission_rev"] + df["delivery_fee"]), 0.0)
    leak_deliv = np.where(cond_free_deliv_small & ~cond_cancelled, 35.0, 0.0)

    total_leak_vec = (leak_margin + leak_promo + leak_cancel + leak_deliv).round(2)
    any_flagged = cond_neg_margin | cond_promo_subsidy | cond_cancelled | cond_free_deliv_small | cond_extreme_disc_stat

    # Vectorized labels & severity
    is_business_rule = cond_neg_margin | cond_promo_subsidy | cond_cancelled | cond_free_deliv_small
    detection_category = np.where(
        is_business_rule & cond_extreme_disc_stat,
        "Hybrid (Business Rule + Statistical Anomaly)",
        np.where(cond_extreme_disc_stat, "Statistical Anomaly", "Business Rule"),
    )

    severity = np.where(
        (disc_pct >= 100.0) | cond_neg_margin & cond_cancelled | (total_leak_vec > 300.0),
        "Critical",
        np.where(cond_neg_margin | cond_cancelled, "High", np.where(cond_promo_subsidy | cond_extreme_disc_stat, "Medium", "Low")),
    )
    risk_level = np.where(
        severity == "Critical",
        "Critical Leakage",
        np.where(severity == "High", "High Leakage", "Watch"),
    )

    # False-positive risk attribution (explicit auditability)
    false_positive_risk = np.where(
        (disc_pct >= 100.0),
        "Low - Discount meets/exceeds gross order value",
        np.where(
            cond_cancelled & ~cond_neg_margin,
            "Low - Verified cancelled order lost commission",
            np.where(
                cond_neg_margin & ~cond_promo_subsidy,
                "Moderate - Negative only if discount is 100% platform-funded",
                "High - Likely intentional marketing promo or free-delivery waiver",
            ),
        ),
    )

    # Compose readable leakage_reason cleanly
    r1 = np.where(cond_neg_margin, "Net Contribution < 0 (Post-Discount)", "")
    r2 = np.where(cond_promo_subsidy, "High Discount Subsidy (>25% & >Rs150)", "")
    r3 = np.where(cond_extreme_disc_stat, "Statistical Discount Outlier (Z>3.0)", "")
    r4 = np.where(cond_cancelled, "Cancelled Order Lost Commission", "")
    r5 = np.where(cond_free_deliv_small, "Small-Basket Free Delivery (<Rs300)", "")

    reasons_series = pd.Series("", index=df.index)
    for part in [r1, r2, r3, r4, r5]:
        reasons_series = np.where(
            part != "",
            np.where(reasons_series != "", reasons_series + " | " + part, part),
            reasons_series,
        )

    flagged = df.loc[any_flagged].copy()
    flagged["leakage_reason"] = pd.Series(reasons_series, index=df.index).loc[any_flagged]
    flagged["potential_leakage_amount"] = pd.Series(total_leak_vec, index=df.index).loc[any_flagged]
    flagged["leakage_amount"] = flagged["potential_leakage_amount"]  # API compatibility alias
    flagged["leakage_type"] = np.where(
        pd.Series(cond_cancelled, index=df.index).loc[any_flagged],
        "Cancelled Commission Loss",
        np.where(
            pd.Series(cond_neg_margin, index=df.index).loc[any_flagged],
            "Post-Discount Margin Deficit",
            "Promotional & Delivery Subsidies",
        ),
    )
    flagged["risk_level"] = pd.Series(risk_level, index=df.index).loc[any_flagged]
    flagged["severity"] = pd.Series(severity, index=df.index).loc[any_flagged]
    flagged["detection_category"] = pd.Series(detection_category, index=df.index).loc[any_flagged]
    flagged["false_positive_risk"] = pd.Series(false_positive_risk, index=df.index).loc[any_flagged]
    flagged["anomaly_z_score"] = np.round(pd.Series(disc_z, index=df.index).loc[any_flagged], 3)
    flagged["record_preserved"] = True

    output_cols = [
        "order_id",
        "customer_id",
        "restaurant_id",
        "order_amount",
        "discount_amount",
        "delivery_fee",
        "final_amount",
        "estimated_profit",
        "estimated_profit_net_subsidy",
        "leakage_reason",
        "leakage_type",
        "potential_leakage_amount",
        "leakage_amount",
        "risk_level",
        "severity",
        "detection_category",
        "false_positive_risk",
        "anomaly_z_score",
        "record_preserved",
    ]
    for extra in ["restaurant_name", "customer_name"]:
        if extra in flagged.columns:
            output_cols.append(extra)

    flagged = flagged[[c for c in output_cols if c in flagged.columns]].sort_values(
        "potential_leakage_amount", ascending=False
    ).reset_index(drop=True)

    kpis: Dict[str, Any] = {
        "Total_Potential_Leakage": round(float(flagged["potential_leakage_amount"].sum()), 2) if not flagged.empty else 0.0,
        "Flagged_Orders_Count": int(len(flagged)),
        "Total_Orders_Audited": int(total_orders),
        "Leakage_Rate_PCT": round(float(len(flagged) / max(total_orders, 1) * 100.0), 2),
        "Duplicate_Order_Flags": int(flagged["order_id"].duplicated().sum()) if not flagged.empty and "order_id" in flagged.columns else 0,
        "Critical_Risk_Count": int((flagged["severity"] == "Critical").sum()) if not flagged.empty else 0,
        "High_Risk_Count": int((flagged["severity"] == "High").sum()) if not flagged.empty else 0,
        "Medium_Risk_Count": int((flagged["severity"] == "Medium").sum()) if not flagged.empty else 0,
        "Low_Risk_Count": int((flagged["severity"] == "Low").sum()) if not flagged.empty else 0,
        "By_Detection_Category": flagged["detection_category"].value_counts().to_dict() if not flagged.empty else {},
        "By_False_Positive_Risk": flagged["false_positive_risk"].value_counts().to_dict() if not flagged.empty else {},
        "Original_Orders_Preserved": int(total_orders),
        "Disclaimer": (
            "Distinguishes Statistical Anomalies (Z-score/IQR extremes) from Business Rule cost checks; "
            "high false-positive promo subsidies require merchant vs platform funding attribution."
        ),
    }

    return flagged, kpis
