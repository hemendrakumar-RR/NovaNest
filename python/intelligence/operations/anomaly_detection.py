"""
Phase 05 — Operations Intelligence: Statistical Operational Anomaly Detection
-----------------------------------------------------------------------------
Implements true dual Z-Score and Tukey IQR statistical anomaly detection across
orders, delivery speeds/durations, discounts, and restaurant cohorts WITHOUT
silent `.head(50)` / `.head(100)` truncation, duplicate entity keys, or
deletion of source records.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from ml.validation_framework import validate_dataframe_schema
except ImportError:
    from python.ml.validation_framework import validate_dataframe_schema


def compute_statistical_bounds(series: pd.Series, metric_name: str, z_threshold: float = 3.0) -> Dict[str, Any]:
    """Compute Z-Score and Tukey IQR (1.5x & 3.0x) fences on a finite numeric series."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {
            "metric": metric_name,
            "n_samples": 0,
            "mean": 0.0,
            "std": 0.0,
            "q1": 0.0,
            "median": 0.0,
            "q3": 0.0,
            "iqr": 0.0,
            "iqr_lower_15": 0.0,
            "iqr_upper_15": 0.0,
            "iqr_upper_30": 0.0,
            "z_gt_25_count": 0,
            "z_gt_30_count": 0,
            "iqr_15_outlier_count": 0,
            "iqr_30_extreme_count": 0,
        }

    mean_v = float(s.mean())
    std_v = float(s.std(ddof=1)) if len(s) > 1 else 0.0
    q1 = float(s.quantile(0.25))
    med = float(s.quantile(0.50))
    q3 = float(s.quantile(0.75))
    iqr = max(q3 - q1, 0.0)

    low_15 = q1 - 1.5 * iqr
    high_15 = q3 + 1.5 * iqr
    high_30 = q3 + 3.0 * iqr

    z_scores = np.abs((s - mean_v) / std_v) if std_v > 1e-12 else pd.Series(0.0, index=s.index)
    return {
        "metric": metric_name,
        "n_samples": int(len(s)),
        "mean": round(mean_v, 4),
        "std": round(std_v, 4),
        "q1": round(q1, 4),
        "median": round(med, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "iqr_lower_15": round(low_15, 4),
        "iqr_upper_15": round(high_15, 4),
        "iqr_upper_30": round(high_30, 4),
        "z_gt_25_count": int((z_scores > 2.5).sum()),
        "z_gt_30_count": int((z_scores > z_threshold).sum()),
        "iqr_15_outlier_count": int(((s < low_15) | (s > high_15)).sum()),
        "iqr_30_extreme_count": int(((s < (q1 - 3.0 * iqr)) | (s > high_30)).sum()),
    }


def _enrich_orders_for_audit(orders_df: pd.DataFrame, deliveries_df: pd.DataFrame) -> pd.DataFrame:
    df = orders_df.copy()
    if deliveries_df is not None and not deliveries_df.empty and "order_id" in deliveries_df.columns:
        d_cols = [c for c in ["order_id", "delivery_id", "distance_km", "delivery_duration"] if c in deliveries_df.columns]
        # Avoid duplicate column collisions if orders_df already includes engineered columns
        d_sub = deliveries_df[d_cols].drop_duplicates(subset=["order_id"])
        for col in ["delivery_id", "distance_km", "delivery_duration"]:
            if col in d_sub.columns and col in df.columns:
                df = df.drop(columns=[col])
        df = df.merge(d_sub, on="order_id", how="left")

    df["order_amount"] = pd.to_numeric(df.get("order_amount", 0.0), errors="coerce").fillna(0.0)
    df["discount_amount"] = pd.to_numeric(df.get("discount_amount", 0.0), errors="coerce").fillna(0.0)
    df["delivery_fee"] = pd.to_numeric(df.get("delivery_fee", 0.0), errors="coerce").fillna(0.0)

    df["discount_pct_calc"] = np.where(
        df["order_amount"] > 0,
        (df["discount_amount"] / df["order_amount"]) * 100.0,
        0.0,
    )
    if "delivery_duration" in df.columns and "distance_km" in df.columns:
        dur_h = pd.to_numeric(df["delivery_duration"], errors="coerce") / 60.0
        dist = pd.to_numeric(df["distance_km"], errors="coerce")
        df["delivery_speed_kph_calc"] = np.where(dur_h > 0, dist / dur_h, np.nan)
    else:
        df["delivery_speed_kph_calc"] = np.nan

    return df


def _severity_from_z(z_val: float, severe_override: bool = False) -> str:
    if severe_override or abs(z_val) >= 4.0:
        return "Critical"
    if abs(z_val) >= 3.5:
        return "High"
    if abs(z_val) >= 2.5:
        return "Medium"
    return "Low"


def detect_operational_anomalies_with_audit(
    orders_df: pd.DataFrame,
    deliveries_df: pd.DataFrame,
    restaurants_df: Optional[pd.DataFrame] = None,
    customers_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect true statistical anomalies (Z-Score + Tukey IQR) across orders,
    deliveries, and restaurant cohorts, returning deduplicated anomaly rows and
    full untruncated population summary counts.
    """
    validate_dataframe_schema(orders_df, ["order_id", "order_amount"], "orders_df", min_rows=1)
    enriched = _enrich_orders_for_audit(orders_df, deliveries_df)
    total_orders = len(enriched)

    # Full population statistical bounds across key numeric dimensions
    bounds_audit: Dict[str, Dict[str, Any]] = {
        "delivery_duration": compute_statistical_bounds(enriched.get("delivery_duration", pd.Series(dtype=float)), "delivery_duration"),
        "distance_km": compute_statistical_bounds(enriched.get("distance_km", pd.Series(dtype=float)), "distance_km"),
        "discount_percentage": compute_statistical_bounds(enriched["discount_pct_calc"], "discount_percentage"),
        "delivery_speed_kph": compute_statistical_bounds(enriched["delivery_speed_kph_calc"], "delivery_speed_kph"),
        "order_amount": compute_statistical_bounds(enriched["order_amount"], "order_amount"),
    }

    records: List[Dict[str, Any]] = []

    # 1. Delivery Duration Z-score / IQR anomalies (true statistical extremes only)
    if "delivery_duration" in enriched.columns and enriched["delivery_duration"].notna().sum() >= 5:
        b = bounds_audit["delivery_duration"]
        if b["std"] > 1e-12:
            z_dur = (enriched["delivery_duration"] - b["mean"]) / b["std"]
            mask_dur = (np.abs(z_dur) > 2.5) | (enriched["delivery_duration"] > b["iqr_upper_15"])
            for idx in enriched.index[mask_dur]:
                val = float(enriched.at[idx, "delivery_duration"])
                zv = float(z_dur.at[idx])
                records.append({
                    "Entity_Type": "Order Delivery",
                    "Entity_ID": str(enriched.at[idx, "order_id"]),
                    "Metric": "Delivery Duration (min)",
                    "Actual_Value": f"{val:.1f} min",
                    "Expected_Value": f"{b['mean']:.1f} min",
                    "Deviation_Pct": f"{((val - b['mean']) / max(b['mean'], 1e-6) * 100):+.1f}%",
                    "Severity": _severity_from_z(zv),
                    "Explanation": f"Statistical transit duration outlier (z={zv:+.2f}, IQR upper={b['iqr_upper_15']:.1f} min).",
                    "Detection_Method": "Z-Score (>2.5) & Tukey IQR (1.5x)",
                    "Anomaly_Category": "Statistical Anomaly",
                    "Z_Score": round(zv, 3),
                    "IQR_Fence_Breached": bool(val > b["iqr_upper_15"]),
                    "False_Positive_Risk": "Moderate - Weather/traffic spikes uncaptured in dataset",
                    "Record_Preserved": True,
                })

    # 2. Delivery Speed Extreme Statistical & Physical Plausibility Outliers (Z > 3.0 & IQR)
    sp = enriched["delivery_speed_kph_calc"]
    if sp.notna().sum() >= 5:
        bs = bounds_audit["delivery_speed_kph"]
        if bs["std"] > 1e-12:
            z_sp = (sp - bs["mean"]) / bs["std"]
            mask_sp = (z_sp > 3.0) & (sp > bs["iqr_upper_15"])
            for idx in enriched.index[mask_sp.fillna(False)]:
                val = float(sp.at[idx])
                zv = float(z_sp.at[idx])
                records.append({
                    "Entity_Type": "Order Delivery",
                    "Entity_ID": str(enriched.at[idx, "order_id"]),
                    "Metric": "Delivery Speed (km/h)",
                    "Actual_Value": f"{val:.1f} km/h",
                    "Expected_Value": f"{bs['mean']:.1f} km/h",
                    "Deviation_Pct": f"{((val - bs['mean']) / max(bs['mean'], 1e-6) * 100):+.1f}%",
                    "Severity": _severity_from_z(zv, severe_override=(val >= 42.0)),
                    "Explanation": (
                        f"Upper-tail transit velocity outlier (z={zv:+.2f} vs IQR fence {bs['iqr_upper_15']:.1f} km/h); "
                        f"implies {enriched.at[idx, 'distance_km']:.1f} km in {enriched.at[idx, 'delivery_duration']:.0f} min."
                    ),
                    "Detection_Method": "Z-Score (>3.0) & Tukey IQR (1.5x)",
                    "Anomaly_Category": "Statistical Anomaly",
                    "Z_Score": round(zv, 3),
                    "IQR_Fence_Breached": True,
                    "False_Positive_Risk": "Moderate - Short straight-line GPS radius or synthetic uniform pairing",
                    "Record_Preserved": True,
                })

    # 3. Order Discount Statistical Extremes (Z > 3.0 & IQR 3.0x Extreme Fence, including >=100% discounts)
    bd = bounds_audit["discount_percentage"]
    if bd["std"] > 1e-12:
        dp = enriched["discount_pct_calc"]
        z_disc = (dp - bd["mean"]) / bd["std"]
        mask_disc = ((z_disc > 3.0) & (dp > bd["iqr_upper_30"])) | (dp >= 100.0)
        for idx in enriched.index[mask_disc.fillna(False)]:
            val = float(dp.at[idx])
            zv = float(z_disc.at[idx])
            records.append({
                "Entity_Type": "Order Pricing",
                "Entity_ID": str(enriched.at[idx, "order_id"]),
                "Metric": "Discount Percentage (%)",
                "Actual_Value": f"{val:.1f}%",
                "Expected_Value": f"{bd['mean']:.1f}%",
                "Deviation_Pct": f"{(val - bd['mean']):+.1f} pp",
                "Severity": _severity_from_z(zv, severe_override=(val >= 100.0)),
                "Explanation": (
                    f"Extreme discount outlier (z={zv:+.2f}, Tukey 3x-IQR fence={bd['iqr_upper_30']:.1f}%); "
                    + ("discount meets or exceeds gross order amount." if val >= 100.0 else "far exceeds typical promotional band.")
                ),
                "Detection_Method": "Z-Score (>3.0) & Extreme Tukey IQR (3.0x)",
                "Anomaly_Category": "Statistical Anomaly",
                "Z_Score": round(zv, 3),
                "IQR_Fence_Breached": bool(val > bd["iqr_upper_30"]),
                "False_Positive_Risk": "Low - Extreme tail beyond planned coupon slabs" if val >= 80.0 else "Moderate - Could be flash promo stacking",
                "Record_Preserved": True,
            })

    # 4. Restaurant Cohort Statistical Cancellation Outliers (Z > 2.5, n >= 20 orders)
    if "restaurant_id" in enriched.columns and "order_status" in enriched.columns:
        rest_agg = enriched.groupby("restaurant_id").agg(
            total_orders=("order_id", "count"),
            cancelled=("order_status", lambda x: int((x == "Cancelled").sum())),
        ).reset_index()
        eligible = rest_agg[rest_agg["total_orders"] >= 20].copy()
        if len(eligible) >= 5:
            eligible["cancel_rate_pct"] = (eligible["cancelled"] / eligible["total_orders"]) * 100.0
            br = compute_statistical_bounds(eligible["cancel_rate_pct"], "restaurant_cancellation_rate_pct")
            bounds_audit["restaurant_cancellation_rate_pct"] = br
            if br["std"] > 1e-12:
                eligible["z_cancel"] = (eligible["cancel_rate_pct"] - br["mean"]) / br["std"]
                if restaurants_df is not None and not restaurants_df.empty and "restaurant_name" in restaurants_df.columns:
                    eligible = eligible.merge(restaurants_df[["restaurant_id", "restaurant_name"]], on="restaurant_id", how="left")
                outliers = eligible[(eligible["z_cancel"] > 2.5) | (eligible["cancel_rate_pct"] > br["iqr_upper_15"])]
                for _, row in outliers.iterrows():
                    rname = row.get("restaurant_name", row["restaurant_id"])
                    entity_label = f"{rname} ({row['restaurant_id']})" if rname != row["restaurant_id"] else str(row["restaurant_id"])
                    zv = float(row["z_cancel"])
                    rate = float(row["cancel_rate_pct"])
                    records.append({
                        "Entity_Type": "Restaurant",
                        "Entity_ID": entity_label,
                        "Metric": "Cancellation Rate (%)",
                        "Actual_Value": f"{rate:.1f}%",
                        "Expected_Value": f"{br['mean']:.1f}%",
                        "Deviation_Pct": f"{((rate - br['mean']) / max(br['mean'], 1e-6) * 100):+.1f}%",
                        "Severity": _severity_from_z(zv),
                        "Explanation": f"Restaurant cancellation rate {rate:.1f}% ({int(row['cancelled'])}/{int(row['total_orders'])}) exceeds peer baseline {br['mean']:.1f}% (z={zv:+.2f}).",
                        "Detection_Method": "Peer Z-Score (>2.5) & Tukey IQR (1.5x)",
                        "Anomaly_Category": "Statistical Anomaly",
                        "Z_Score": round(zv, 3),
                        "IQR_Fence_Breached": bool(rate > br["iqr_upper_15"]),
                        "False_Positive_Risk": "Low - Minimum sample threshold n>=20 enforced" if row["total_orders"] >= 30 else "Moderate - Borderline volume (20-29 orders)",
                        "Record_Preserved": True,
                    })

    # 5. Order Value Upper-Tail Statistical Outliers (IQR 1.5x & Z > 2.5 check if extreme)
    bo = bounds_audit["order_amount"]
    if bo["std"] > 1e-12 and bo["iqr_15_outlier_count"] > 0:
        z_ord = (enriched["order_amount"] - bo["mean"]) / bo["std"]
        mask_ord = enriched["order_amount"] > bo["iqr_upper_15"]
        for idx in enriched.index[mask_ord.fillna(False)]:
            val = float(enriched.at[idx, "order_amount"])
            zv = float(z_ord.at[idx])
            records.append({
                "Entity_Type": "Order Value",
                "Entity_ID": str(enriched.at[idx, "order_id"]),
                "Metric": "Gross Order Amount (INR)",
                "Actual_Value": f"₹{val:,.2f}",
                "Expected_Value": f"₹{bo['mean']:,.2f}",
                "Deviation_Pct": f"{((val - bo['mean']) / max(bo['mean'], 1e-6) * 100):+.1f}%",
                "Severity": "Medium" if zv < 3.0 else "High",
                "Explanation": f"High-value basket exceeds Tukey upper fence ₹{bo['iqr_upper_15']:,.2f} (z={zv:+.2f}).",
                "Detection_Method": "Tukey IQR (1.5x) & Z-Score",
                "Anomaly_Category": "Statistical Anomaly",
                "Z_Score": round(zv, 3),
                "IQR_Fence_Breached": True,
                "False_Positive_Risk": "High - Likely legitimate group/party order; retain for VIP audit",
                "Record_Preserved": True,
            })

    cols = [
        "Entity_Type",
        "Entity_ID",
        "Metric",
        "Actual_Value",
        "Expected_Value",
        "Deviation_Pct",
        "Severity",
        "Explanation",
        "Detection_Method",
        "Anomaly_Category",
        "Z_Score",
        "IQR_Fence_Breached",
        "False_Positive_Risk",
        "Record_Preserved",
    ]
    anomalies_df = pd.DataFrame(records, columns=cols)

    # Deduplicate cleanly so zero duplicate anomaly keys exist
    if not anomalies_df.empty:
        anomalies_df = anomalies_df.drop_duplicates(subset=["Entity_Type", "Entity_ID", "Metric"], keep="first")
        sev_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        anomalies_df["_rank"] = anomalies_df["Severity"].map(sev_rank).fillna(9)
        anomalies_df = anomalies_df.sort_values(["_rank", "Z_Score"], ascending=[True, False]).drop(columns=["_rank"]).reset_index(drop=True)

    summary = {
        "total_records_audited": int(total_orders),
        "total_statistical_anomalies": int(len(anomalies_df)),
        "anomaly_rate_pct": round(float(len(anomalies_df) / max(total_orders, 1) * 100.0), 3),
        "duplicate_anomaly_keys": int(anomalies_df.duplicated(subset=["Entity_Type", "Entity_ID", "Metric"]).sum()) if not anomalies_df.empty else 0,
        "by_severity": anomalies_df["Severity"].value_counts().to_dict() if not anomalies_df.empty else {},
        "by_metric": anomalies_df["Metric"].value_counts().to_dict() if not anomalies_df.empty else {},
        "statistical_bounds": bounds_audit,
        "truncated": False,
        "original_records_deleted": 0,
    }
    return anomalies_df, summary


def detect_operational_anomalies(
    orders_df: pd.DataFrame,
    deliveries_df: pd.DataFrame,
    restaurants_df: Optional[pd.DataFrame] = None,
    customers_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Backward-compatible wrapper returning deduplicated full statistical anomalies DataFrame."""
    anomalies_df, _ = detect_operational_anomalies_with_audit(
        orders_df=orders_df,
        deliveries_df=deliveries_df,
        restaurants_df=restaurants_df,
        customers_df=customers_df,
    )
    return anomalies_df
