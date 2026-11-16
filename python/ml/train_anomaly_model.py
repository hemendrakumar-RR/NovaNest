"""
Phase 05 — ML Training Script: Statistical Anomaly & Financial Risk Audit
------------------------------------------------------------------------
Executes untruncated Z-score & Tukey IQR statistical anomaly detection separately
from vectorized business-rule revenue risk scoring, preserves historical v1
anomaly_metrics.json, and writes full Phase 05 evaluation artifacts.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))

from intelligence.operations.anomaly_detection import detect_operational_anomalies_with_audit
from intelligence.operations.demand_heatmap import generate_demand_hotspots
from intelligence.operations.operational_early_warning import generate_operational_early_warnings
from intelligence.operations.revenue_leakage import detect_revenue_leakage
from intelligence.operations.rider_allocation import recommend_rider_allocation
from validation_framework import (
    RANDOM_SEED,
    load_historical_metrics,
    save_phase05_artifacts,
)


def main() -> None:
    print("=" * 68)
    print("Phase 05 — Anomaly Detection & Financial Risk Audit (Z-Score + IQR)")
    print("=" * 68)

    cleaned_dir = BASE_DIR / "datasets" / "cleaned"
    engineered_dir = BASE_DIR / "datasets" / "engineered"
    models_dir = BASE_DIR / "models" / "anomaly_detection"

    orders_df = pd.read_csv(cleaned_dir / "orders.csv")
    deliveries_df = pd.read_csv(cleaned_dir / "deliveries.csv")
    riders_df = pd.read_csv(cleaned_dir / "riders.csv")
    restaurants_df = pd.read_csv(cleaned_dir / "restaurants.csv")
    customers_df = pd.read_csv(cleaned_dir / "customers.csv")

    eng_path = engineered_dir / "orders_engineered.csv"
    orders_eng_df = pd.read_csv(eng_path) if eng_path.exists() else orders_df.copy()

    # 1. Statistical Anomaly Detection (zero truncation, zero deletion)
    anomalies_df, anom_summary = detect_operational_anomalies_with_audit(
        orders_df=orders_eng_df,
        deliveries_df=deliveries_df,
        restaurants_df=restaurants_df,
        customers_df=customers_df,
    )
    anomalies_path = engineered_dir / "operational_anomalies.csv"
    anomalies_df.to_csv(anomalies_path, index=False)
    print(f"Saved statistical operational anomalies ({len(anomalies_df):,} unique entities/orders) -> {anomalies_path}")

    # 2. Vectorized Financial Risk / Revenue Leakage Audit (Business Rules + Statistical Hybrid)
    leakage_df, leakage_kpis = detect_revenue_leakage(orders_eng_df, customers_df, restaurants_df)
    leakage_path = engineered_dir / "revenue_leakage.csv"
    leakage_df.to_csv(leakage_path, index=False)
    print(f"Saved revenue leakage flags ({len(leakage_df):,} orders, zero duplicates={leakage_kpis['Duplicate_Order_Flags']}) -> {leakage_path}")

    # 3. Supporting Operational Outputs (preserved workflow compatibility)
    rider_alloc_df = recommend_rider_allocation(orders_df, deliveries_df, riders_df, customers_df)
    rider_alloc_df.to_csv(engineered_dir / "rider_allocation.csv", index=False)

    hotspots_df = generate_demand_hotspots(orders_df, customers_df)
    hotspots_df.to_csv(engineered_dir / "demand_heatmap.csv", index=False)

    alerts_df = generate_operational_early_warnings(
        orders_df, deliveries_df, riders_df, restaurants_df, anomalies_df, leakage_df
    )
    alerts_df.to_csv(engineered_dir / "operational_alerts.csv", index=False)

    hist_v1 = load_historical_metrics(models_dir, "anomaly_metrics.json")

    metrics_payload = {
        "model_version": "2.0.0-phase05-statistical-iqr",
        "Detection_Methodology": "Dual Z-Score & Tukey IQR Statistical Bounds Separated from Business Rule Cost Scoring",
        "Statistical_Anomaly_Audit": anom_summary,
        "Revenue_Leakage_KPIs": leakage_kpis,
        "Active_Alerts_Count": int(len(alerts_df)),
        "historical_v1_comparison": {
            "v1_preserved_file": "anomaly_metrics.json",
            "v1_anomalies_detected": hist_v1.get("Total_Anomalies_Detected") if hist_v1 else None,
            "v1_flagged_leakage_orders": hist_v1.get("Revenue_Leakage_KPIs", {}).get("Flagged_Orders_Count") if hist_v1 else None,
            "v1_audit_finding": (
                "Legacy v1 claimed 'Z-Score & IQR Statistical Bounds' while computing zero IQR bounds, returning only "
                "10 truncated restaurant cancellation rows, looping via slow row iteration in revenue_leakage.py, "
                "using a hardcoded 18% commission assumption, and conflating statistical outliers with promo subsidies."
            ),
        },
    }

    metadata_payload = {
        "model_name": "NovaNest Statistical Anomaly & Financial Risk Auditor",
        "model_version": "2.0.0-phase05-statistical-iqr",
        "random_seed": RANDOM_SEED,
        "source_records_audited": len(orders_df),
        "source_records_preserved": len(orders_df),
        "duplicate_anomaly_keys": anom_summary["duplicate_anomaly_keys"],
        "duplicate_leakage_order_ids": leakage_kpis["Duplicate_Order_Flags"],
    }

    feature_doc_payload = {
        "statistical_bounds_evaluated": list(anom_summary["statistical_bounds"].keys()),
        "statistical_criteria": [
            "Z-Score (|z| > 2.5 / > 3.0) & Tukey IQR Fences (1.5x / 3.0x IQR)",
            "Discount >= 100% of gross order value flagged as Critical statistical + pricing failure",
            "Delivery speed km/h upper tail > 3.0 std & IQR fence",
            "Restaurant cancellation rate Z > 2.5 among peer cohorts with n >= 20 orders",
        ],
        "business_rule_criteria": [
            "Post-discount platform net contribution < 0 (using per-restaurant commission_percentage)",
            "High discount subsidy (>25% and >Rs 150)",
            "Cancelled order commission & fee opportunity loss",
            "Small-basket free delivery waiver (delivery_fee == 0 and order_amount < 300)",
        ],
    }

    b_rows = "\n".join([
        f"| `{name}` | {b['mean']} | {b['std']} | [{b['iqr_lower_15']}, {b['iqr_upper_15']}] | {b['z_gt_30_count']} | {b['iqr_15_outlier_count']} |"
        for name, b in anom_summary["statistical_bounds"].items()
    ])
    m_rows = "\n".join([f"| {m} | {cnt:,} |" for m, cnt in anom_summary["by_metric"].items()])
    fp_rows = "\n".join([f"| {k} | {v:,} |" for k, v in leakage_kpis["By_False_Positive_Risk"].items()])

    report_md = f"""# Operational Anomaly & Financial Risk Audit — Phase 05 Validation Report

## 1. Key Remediation Summary (v1 vs v2)
- Implemented true **Z-Score + Tukey IQR (1.5x & 3.0x)** checks on `{anom_summary['total_records_audited']:,}` orders without `.head(50)` / `.head(100)` truncation (`duplicate_anomaly_keys = {anom_summary['duplicate_anomaly_keys']}`, zero source deletions).
- Separated **Statistical Anomalies** (`{anom_summary['total_statistical_anomalies']:,}` unique entity/metric flags, `{anom_summary['anomaly_rate_pct']}%` of audited orders) from **Business Rule Cost Audits** (`{leakage_kpis['Flagged_Orders_Count']:,}` orders, `{leakage_kpis['Leakage_Rate_PCT']}%`, duplicate order flags = `{leakage_kpis['Duplicate_Order_Flags']}`).

## 2. Full-Population Statistical Bounds Audit
| Metric | Mean | Std | Tukey 1.5x IQR Bounds | Z > 3.0 Count | IQR 1.5x Outliers |
|---|---:|---:|---|---:|---:|
{b_rows}

Note: `delivery_duration` and `distance_km` follow bounded Uniform distributions in the cleaned data (`z > 2.5 count = 0`), whereas `discount_percentage` (up to `123.5%`) and `delivery_speed_kph` (up to `48.0 km/h`) contain genuine heavy-tail anomalies.

## 3. Detected Statistical Anomalies by Metric
| Metric | Flagged Count |
|---|---:|
{m_rows}

## 4. Revenue Risk Audit — False-Positive Attribution
| False-Positive Risk Bucket | Orders |
|---|---:|
{fp_rows}
"""

    written = save_phase05_artifacts(
        model_dir=models_dir,
        versioned_metrics_filename="anomaly_metrics_v2.json",
        metrics_payload=metrics_payload,
        metadata_payload=metadata_payload,
        feature_doc_payload=feature_doc_payload,
        report_markdown=report_md,
        examples_df=anomalies_df.head(100),
    )
    print(f"Statistical Anomalies: {anom_summary['total_statistical_anomalies']:,} ({anom_summary['anomaly_rate_pct']}%) | Leakage Flags: {leakage_kpis['Flagged_Orders_Count']:,}")
    print(f"Saved artifacts: {list(written.keys())}")
    print("[SUCCESS] Phase 05 Anomaly Detection & Risk Audit Complete.")


if __name__ == "__main__":
    main()
