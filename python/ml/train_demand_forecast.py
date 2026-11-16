"""
Phase 05 — ML Training Script: Demand Forecast Model
---------------------------------------------------
Trains regularized daily city demand forecasting models on contiguous calendar
grids, evaluates baselines + expanding-window backtests, saves Phase 05 artifacts
without overwriting historical v1 demand_metrics.json, and updates demand_forecasts.csv.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))

from intelligence.operations.demand_forecasting import (
    DEMAND_CATEGORICAL_FEATURES,
    DEMAND_NUMERIC_FEATURES,
    prepare_demand_time_series,
    train_and_forecast_demand,
)
from validation_framework import (
    RANDOM_SEED,
    load_historical_metrics,
    save_phase05_artifacts,
)


def main() -> None:
    print("=" * 68)
    print("Phase 05 — City Demand Forecasting (Regularized + Backtested)")
    print("=" * 68)

    cleaned_dir = BASE_DIR / "datasets" / "cleaned"
    engineered_dir = BASE_DIR / "datasets" / "engineered"
    models_dir = BASE_DIR / "models" / "demand_forecast"

    orders_df = pd.read_csv(cleaned_dir / "orders.csv")
    customers_df = pd.read_csv(cleaned_dir / "customers.csv") if (cleaned_dir / "customers.csv").exists() else None
    restaurants_df = pd.read_csv(cleaned_dir / "restaurants.csv") if (cleaned_dir / "restaurants.csv").exists() else None

    daily_demand_df = prepare_demand_time_series(orders_df, customers_df, restaurants_df)
    forecast_df, metrics, artifacts = train_and_forecast_demand(
        daily_demand_df, forecast_horizon_days=14, return_artifacts=True
    )

    output_csv = engineered_dir / "demand_forecasts.csv"
    forecast_df.to_csv(output_csv, index=False)
    print(f"Saved demand forecasts ({len(forecast_df):,} rows across {forecast_df['city'].nunique()} cities) -> {output_csv}")

    hist_v1 = load_historical_metrics(models_dir, "demand_metrics.json")

    metrics_payload = {
        **metrics,
        "candidate_model_comparison": artifacts["candidate_models"],
        "historical_v1_comparison": {
            "v1_preserved_file": "demand_metrics.json",
            "v1_reported_mae": hist_v1.get("MAE") if hist_v1 else None,
            "v1_reported_rmse": hist_v1.get("RMSE") if hist_v1 else None,
            "v1_reported_r2": hist_v1.get("R2_Score") if hist_v1 else None,
            "v1_audit_finding": (
                "Legacy v1 claimed 'OLS Ridge' while using unregularized pinv OLS, omitted rolling_std_7 despite computing it, "
                "lacked calendar reindexing & baseline comparisons, and reported only pooled cross-city R2 without within-city breakdown."
            ),
        },
    }

    metadata_payload = {
        "model_name": "NovaNest City Demand Forecaster",
        "model_version": "2.0.0-phase05-regularized",
        "random_seed": RANDOM_SEED,
        "selected_algorithm": metrics["Model_Type"],
        "forecast_horizon_days": 14,
        "data_audit": artifacts["data_audit"],
    }

    feature_doc_payload = {
        "numeric_features": DEMAND_NUMERIC_FEATURES,
        "categorical_features": DEMAND_CATEGORICAL_FEATURES,
        "fixes_applied": [
            "Contiguous daily calendar reindexing with 0-fill prior to lag shifting",
            "Included rolling_std_7, lag_14, lag_28, rolling_14, rolling_28, and cyclical weekday/month sin/cos",
            "Replaced unregularized np.linalg.pinv OLS with L2 Ridge (alpha=25.0) & HGBR comparisons",
        ],
    }

    comp_rows = "\n".join([
        f"| {m} | {r['mae']} | {r['median_ae']} | {r['rmse']} | {r['r2_score']} | {r['mape_pct']}% |"
        for m, r in artifacts["candidate_models"].items()
    ])
    city_rows = "\n".join([
        f"| {c} | {v['mean_actual']} | {v['mae']} | {v['rmse']} | {v['r2_score_within_city']} | {v['seasonal_naive_lag7_mae']} |"
        for c, v in metrics["Per_City_Metrics"].items()
    ])
    bt_rows = "\n".join([
        f"| Fold {b['fold']} | {b['window']} | {b['ridge_mae']} | {b['ridge_rmse']} | {b['seasonal_naive_lag7_mae']} |"
        for b in metrics["Backtest_3Fold_Expanding"]
    ])

    report_md = f"""# City Demand Forecasting — Phase 05 Validation Report

## 1. Chronological Holdout Comparison (All 5 Cities Pooled, n={metrics['Validation_Samples']})
| Model / Baseline | MAE | Median AE | RMSE | Pooled R² | MAPE |
|---|---:|---:|---:|---:|---:|
{comp_rows}

## 2. Per-City Within-City Diagnostics ({metrics['Model_Type']})
| City | Mean Daily Orders | MAE | RMSE | Within-City R² | Seasonal Naive (Lag 7) MAE |
|---|---:|---:|---:|---:|---:|
{city_rows}

## 3. Expanding-Window 3-Fold Backtesting
| Fold | Window | Ridge MAE | Ridge RMSE | Seasonal Naive MAE |
|---|---|---:|---:|---:|
{bt_rows}

## 4. Analytical Interpretation
- {metrics['Pooled_vs_City_Note']}
"""

    written = save_phase05_artifacts(
        model_dir=models_dir,
        versioned_metrics_filename="demand_metrics_v2.json",
        metrics_payload=metrics_payload,
        metadata_payload=metadata_payload,
        feature_doc_payload=feature_doc_payload,
        report_markdown=report_md,
        examples_df=artifacts["examples_df"],
        model_obj=artifacts["best_pipeline"],
    )
    print(f"Selected Model: {metrics['Model_Type']} | MAE={metrics['MAE']}, MedAE={metrics['Median_AE']}, RMSE={metrics['RMSE']}, Pooled R2={metrics['R2_Score']}")
    print(f"Saved artifacts: {list(written.keys())}")
    print("[SUCCESS] Phase 05 Demand Forecast Training Complete.")


if __name__ == "__main__":
    main()
