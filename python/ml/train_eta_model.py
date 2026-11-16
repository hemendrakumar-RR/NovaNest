"""
Phase 05 — ML Training Script: Delivery ETA Prediction
-----------------------------------------------------
Trains and evaluates chronological ETA models with full rider/order/restaurant
features, saves versioned Phase 05 artifacts to models/eta_prediction/ without
overwriting historical v1 eta_metrics.json, and updates eta_predictions.csv.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))

from intelligence.operations.eta_prediction import (
    ETA_CATEGORICAL_FEATURES,
    ETA_NUMERIC_FEATURES,
    train_and_predict_eta,
)
from validation_framework import (
    RANDOM_SEED,
    load_historical_metrics,
    save_phase05_artifacts,
)


def main() -> None:
    print("=" * 68)
    print("Phase 05 — Delivery ETA Prediction (Chronological Validation)")
    print("=" * 68)

    cleaned_dir = BASE_DIR / "datasets" / "cleaned"
    engineered_dir = BASE_DIR / "datasets" / "engineered"
    models_dir = BASE_DIR / "models" / "eta_prediction"

    deliveries_df = pd.read_csv(cleaned_dir / "deliveries.csv")
    orders_df = pd.read_csv(cleaned_dir / "orders.csv")
    customers_df = pd.read_csv(cleaned_dir / "customers.csv") if (cleaned_dir / "customers.csv").exists() else None
    riders_df = pd.read_csv(cleaned_dir / "riders.csv") if (cleaned_dir / "riders.csv").exists() else None
    restaurants_df = pd.read_csv(cleaned_dir / "restaurants.csv") if (cleaned_dir / "restaurants.csv").exists() else None

    eta_df, metrics, artifacts = train_and_predict_eta(
        deliveries_df=deliveries_df,
        orders_df=orders_df,
        customers_df=customers_df,
        riders_df=riders_df,
        restaurants_df=restaurants_df,
        return_artifacts=True,
    )

    output_csv = engineered_dir / "eta_predictions.csv"
    eta_df.to_csv(output_csv, index=False)
    print(f"Saved ETA predictions ({len(eta_df):,} deliveries) -> {output_csv}")

    hist_v1 = load_historical_metrics(models_dir, "eta_metrics.json")

    metrics_payload = {
        **metrics,
        "candidate_model_comparison": artifacts["candidate_models"],
        "residual_error_analysis": artifacts["error_analysis"],
        "historical_v1_comparison": {
            "v1_preserved_file": "eta_metrics.json",
            "v1_reported_mae_minutes": hist_v1.get("MAE_minutes") if hist_v1 else None,
            "v1_reported_rmse_minutes": hist_v1.get("RMSE_minutes") if hist_v1 else None,
            "v1_reported_r2": hist_v1.get("R2_Score") if hist_v1 else None,
            "v1_audit_finding": (
                "Legacy eta_metrics.json (50,000 rows) came from an earlier synthetic snapshot where distance_km "
                "correlated linearly with delivery_duration (r=0.61). In the certified Phase 2 cleaned dataset (49,971 rows), "
                "distance_km and delivery_duration have r=-0.0029 and unmeasured live traffic/GPS/kitchen-prep drivers dominate variance."
            ),
        },
    }

    metadata_payload = {
        "model_name": "NovaNest Delivery ETA Predictor",
        "model_version": "2.0.0-phase05-chronological",
        "random_seed": RANDOM_SEED,
        "selected_algorithm": metrics["selected_model"],
        "split_strategy": "Strict chronological 80/20 order_datetime holdout + 3-fold TimeSeriesSplit CV",
        "data_audit": artifacts["data_audit"],
    }

    feature_doc_payload = {
        "numeric_features": ETA_NUMERIC_FEATURES,
        "categorical_features": ETA_CATEGORICAL_FEATURES,
        "newly_added_features": [
            "vehicle_type",
            "shift_type",
            "hour_sin / hour_cos",
            "dow_sin / dow_cos",
            "is_lunch_peak / is_dinner_peak",
            "quantity",
            "order_amount",
            "delivery_fee",
            "restaurant_type / cuisine_type / avg_rating / delivery_radius_km",
            "distance_to_radius_ratio",
            "cross_city_flag",
        ],
        "prohibited_fabricated_features": "Zero fabricated GPS coordinates, live road speeds, or synthetic traffic multipliers.",
    }

    comp_rows = "\n".join([
        f"| {m} | {r['mae']} | {r['median_ae']} | {r['rmse']} | {r['r2_score']} | {r['mape_pct']}% |"
        for m, r in artifacts["candidate_models"].items()
    ])
    city_rows = "\n".join([
        f"| {c} | {v['count']} | {v['mae']} | {v['med_ae']} |"
        for c, v in artifacts["error_analysis"]["by_city"].items()
    ])
    veh_rows = "\n".join([
        f"| {vt} | {v['count']} | {v['mae']} | {v['med_ae']} |"
        for vt, v in artifacts["error_analysis"]["by_vehicle_type"].items()
    ])

    report_md = f"""# Delivery ETA Prediction — Phase 05 Validation Report

## 1. Chronological Validation Setup
- **Split**: Strict time-ordered 80/20 split (`Train = {metrics['Train_Samples']:,}`, `Test = {metrics['Test_Samples']:,}`).
- **3-Fold TimeSeriesSplit CV**: Mean MAE = `{metrics['TimeSeriesCV_3Fold_Mean_MAE']} min`, Mean RMSE = `{metrics['TimeSeriesCV_3Fold_Mean_RMSE']} min`.

## 2. Model Comparison (Held-Out Chronological Test Set)
| Model | MAE (min) | Median AE (min) | RMSE (min) | R² Score | MAPE |
|---|---:|---:|---:|---:|---:|
{comp_rows}

**Selected Model**: `{metrics['selected_model']}` (Holdout SLA: <=5m `{metrics['Holdout_Excellent_PCT']}%`, 5-15m `{metrics['Holdout_Acceptable_PCT']}%`, >15m `{metrics['Holdout_Delayed_PCT']}%`).

## 3. Residual Error Breakdown
### By City
| City | Test Deliveries | MAE (min) | Median AE (min) |
|---|---:|---:|---:|
{city_rows}

### By Rider Vehicle Type
| Vehicle Type | Test Deliveries | MAE (min) | Median AE (min) |
|---|---:|---:|---:|
{veh_rows}

## 4. Known Data & Domain Limitations
- {metrics['Disclaimer']}
"""

    written = save_phase05_artifacts(
        model_dir=models_dir,
        versioned_metrics_filename="eta_metrics_v2.json",
        metrics_payload=metrics_payload,
        metadata_payload=metadata_payload,
        feature_doc_payload=feature_doc_payload,
        report_markdown=report_md,
        examples_df=artifacts["examples_df"],
        model_obj=artifacts["best_pipeline"],
    )
    print(f"Selected Model: {metrics['selected_model']} | Holdout MAE={metrics['MAE_minutes']}m, MedAE={metrics['Median_AE_minutes']}m, RMSE={metrics['RMSE_minutes']}m, R2={metrics['R2_Score']}")
    print(f"Saved artifacts: {list(written.keys())}")
    print("[SUCCESS] Phase 05 ETA Prediction Training Complete.")


if __name__ == "__main__":
    main()
