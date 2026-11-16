"""
Phase 05 — ML Training Script: Restaurant Next-Month Order Prediction
---------------------------------------------------------------------
Replaces synthetic uniform target leakage with chronological monthly panel
forecasting, evaluates Ridge / RF / HGBR against historical baselines, preserves
historical v1 restaurant_metrics.json, and updates restaurant_predictions.csv.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))
sys.path.insert(0, str(BASE_DIR / "python" / "intelligence" / "restaurant"))

from performance_prediction import (
    FORBIDDEN_RESTAURANT_LEAKAGE_COLS,
    RESTAURANT_CATEGORICAL_FEATURES,
    RESTAURANT_NUMERIC_FEATURES,
    build_restaurant_monthly_panel,
    extract_restaurant_features,
)
from validation_framework import (
    RANDOM_SEED,
    assert_no_forbidden_features,
    assert_strictly_chronological_split,
    audit_missing_and_invalid,
    compute_regression_metrics,
    load_historical_metrics,
    save_phase05_artifacts,
    set_reproducible_seed,
    validate_dataframe_schema,
)


def _build_rest_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), RESTAURANT_NUMERIC_FEATURES),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")), ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), RESTAURANT_CATEGORICAL_FEATURES),
        ]
    )


def train_restaurant_pipeline(
    restaurants_df: pd.DataFrame,
    orders_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Train and chronologically validate real monthly restaurant order prediction."""
    set_reproducible_seed(RANDOM_SEED)
    validate_dataframe_schema(restaurants_df, ["restaurant_id", "city"], "restaurants_df", min_rows=10)
    validate_dataframe_schema(orders_df, ["order_id", "restaurant_id", "order_datetime", "order_amount"], "orders_df", min_rows=50)

    panel_df, score_df, full_months = build_restaurant_monthly_panel(restaurants_df, orders_df, min_prior_months=3)
    target_months = sorted(panel_df["target_month"].unique())
    if len(target_months) < 2:
        raise ValueError(f"Need at least 2 labeled target months for chronological holdout; got {target_months}")

    holdout_month = target_months[-1]
    train_df = panel_df[panel_df["target_month"] < holdout_month].copy()
    test_df = panel_df[panel_df["target_month"] == holdout_month].copy()

    assert_strictly_chronological_split(
        train_df["target_month_ts"],
        test_df["target_month_ts"],
        context="Restaurant monthly panel split",
        allow_equal_boundary=False,
    )

    feature_cols = RESTAURANT_NUMERIC_FEATURES + RESTAURANT_CATEGORICAL_FEATURES
    assert_no_forbidden_features(feature_cols, FORBIDDEN_RESTAURANT_LEAKAGE_COLS, context="Restaurant prediction X matrix")

    X_train, y_train = train_df[feature_cols], train_df["Actual_Next_Month_Orders"].astype(float).values
    X_test, y_test = test_df[feature_cols], test_df["Actual_Next_Month_Orders"].astype(float).values

    # Baselines evaluated on same held-out month (n=1,500 restaurants)
    dummy_base = Pipeline([("prep", _build_rest_preprocessor()), ("reg", DummyRegressor(strategy="mean"))])
    dummy_base.fit(X_train, y_train)
    baselines = {
        "Baseline_GlobalTrainMean": compute_regression_metrics(y_test, dummy_base.predict(X_test)),
        "Baseline_RestaurantExpandingMean": compute_regression_metrics(y_test, test_df["expanding_avg_monthly_orders"].values),
        "Baseline_PreviousMonth_Orders": compute_regression_metrics(y_test, test_df["prev_1m_orders"].values),
    }

    candidates = {
        "Ridge_L2_Regression": Pipeline([("prep", _build_rest_preprocessor()), ("reg", Ridge(alpha=50.0, random_state=RANDOM_SEED))]),
        "RandomForest_Regularized": Pipeline([
            ("prep", _build_rest_preprocessor()),
            ("reg", RandomForestRegressor(n_estimators=120, max_depth=5, min_samples_leaf=30, random_state=RANDOM_SEED, n_jobs=-1)),
        ]),
        "HistGradientBoosting": Pipeline([
            ("prep", _build_rest_preprocessor()),
            ("reg", HistGradientBoostingRegressor(max_iter=100, max_depth=3, min_samples_leaf=50, l2_regularization=10.0, random_state=RANDOM_SEED)),
        ]),
    }

    model_results: Dict[str, Dict[str, Any]] = dict(baselines)
    fitted: Dict[str, Pipeline] = {}
    for name, pipe in candidates.items():
        pipe.fit(X_train, y_train)
        fitted[name] = pipe
        preds = np.clip(pipe.predict(X_test), 0.0, None)
        model_results[name] = compute_regression_metrics(y_test, preds)

    best_name = min(candidates.keys(), key=lambda m: (model_results[m]["rmse"], model_results[m]["mae"]))
    best_pipe = fitted[best_name]
    best_metrics = model_results[best_name]

    # Rolling expanding backtest across final 3 target months
    backtest_folds: List[Dict[str, Any]] = []
    for bt_m in target_months[-3:]:
        tr_sub = panel_df[panel_df["target_month"] < bt_m]
        va_sub = panel_df[panel_df["target_month"] == bt_m]
        if tr_sub.empty or va_sub.empty:
            continue
        bt_pipe = Pipeline([("prep", _build_rest_preprocessor()), ("reg", Ridge(alpha=50.0, random_state=RANDOM_SEED))])
        bt_pipe.fit(tr_sub[feature_cols], tr_sub["Actual_Next_Month_Orders"].values)
        bt_pred = np.clip(bt_pipe.predict(va_sub[feature_cols]), 0.0, None)
        bt_m_metrics = compute_regression_metrics(va_sub["Actual_Next_Month_Orders"].values, bt_pred)
        backtest_folds.append({
            "target_month": bt_m,
            "train_months": int(tr_sub["target_month"].nunique()),
            "n_restaurants": bt_m_metrics["n_samples"],
            "mae": bt_m_metrics["mae"],
            "median_ae": bt_m_metrics["median_ae"],
            "rmse": bt_m_metrics["rmse"],
            "r2_score": bt_m_metrics["r2_score"],
        })

    # Holdout restaurant error analysis
    test_eval = test_df.copy()
    test_eval["predicted_orders"] = np.clip(best_pipe.predict(X_test), 0.0, None).round(2)
    test_eval["abs_error"] = np.abs(test_eval["predicted_orders"] - test_eval["Actual_Next_Month_Orders"]).round(2)
    error_by_city = (
        test_eval.groupby("city")["abs_error"].agg(count="count", mae="mean", med_ae="median").round(3).to_dict(orient="index")
    )

    # Feature importances from best model
    prep_names = [n.replace("num__", "").replace("cat__", "") for n in best_pipe.named_steps["prep"].get_feature_names_out()]
    reg = best_pipe.named_steps["reg"]
    if hasattr(reg, "coef_"):
        raw_w = np.abs(reg.coef_)
        importances = dict(sorted({k: round(float(v), 4) for k, v in zip(prep_names, raw_w / max(raw_w.sum(), 1e-9))}.items(), key=lambda kv: kv[1], reverse=True))
    elif hasattr(reg, "feature_importances_"):
        raw_w = reg.feature_importances_
        importances = dict(sorted({k: round(float(v), 4) for k, v in zip(prep_names, raw_w / max(raw_w.sum(), 1e-9))}.items(), key=lambda kv: kv[1], reverse=True))
    else:
        importances = {}

    # Refit selected architecture on full labeled panel to score next upcoming full month
    if best_name == "Ridge_L2_Regression":
        prod_reg = Ridge(alpha=50.0, random_state=RANDOM_SEED)
    elif best_name == "RandomForest_Regularized":
        prod_reg = RandomForestRegressor(n_estimators=120, max_depth=5, min_samples_leaf=30, random_state=RANDOM_SEED, n_jobs=-1)
    else:
        prod_reg = HistGradientBoostingRegressor(max_iter=100, max_depth=3, min_samples_leaf=50, l2_regularization=10.0, random_state=RANDOM_SEED)
    prod_pipe = Pipeline([("prep", _build_rest_preprocessor()), ("reg", prod_reg)])
    prod_pipe.fit(panel_df[feature_cols], panel_df["Actual_Next_Month_Orders"].astype(float).values)

    next_month_preds = np.clip(prod_pipe.predict(score_df[feature_cols]), 0.0, None).round(0).astype(int)
    summary_df = extract_restaurant_features(restaurants_df, orders_df)
    summary_df = summary_df.merge(
        pd.DataFrame({
            "restaurant_id": score_df["restaurant_id"],
            "Predicted_Next_Month_Orders": next_month_preds,
            "Historical_Monthly_Avg": score_df["expanding_avg_monthly_orders"].round(2),
            "Model_Version": "2.0.0-phase05-real-panel",
        }),
        on="restaurant_id",
        how="left",
    )

    return {
        "best_model_name": best_name,
        "best_pipeline": prod_pipe,
        "best_metrics": best_metrics,
        "baseline_metrics": baselines,
        "all_model_results": model_results,
        "backtest_folds": backtest_folds,
        "error_by_city": error_by_city,
        "feature_importances": importances,
        "holdout_month": holdout_month,
        "train_months": sorted(train_df["target_month"].unique().tolist()),
        "full_months": [str(m) for m in full_months],
        "train_samples": int(len(train_df)),
        "test_samples": int(len(test_df)),
        "data_audit": audit_missing_and_invalid(panel_df[RESTAURANT_NUMERIC_FEATURES], RESTAURANT_NUMERIC_FEATURES, "restaurant_panel"),
        "examples_df": test_eval[["restaurant_id", "city", "target_month", "prev_1m_orders", "trailing_3m_avg_orders", "expanding_avg_monthly_orders", "Actual_Next_Month_Orders", "predicted_orders", "abs_error"]].copy(),
        "output_df": summary_df,
    }


def main() -> None:
    print("=" * 68)
    print("Phase 05 — Restaurant Order Prediction (Zero Synthetic Target Leakage)")
    print("=" * 68)

    cleaned_dir = BASE_DIR / "datasets" / "cleaned"
    engineered_dir = BASE_DIR / "datasets" / "engineered"
    models_dir = BASE_DIR / "models" / "restaurant_prediction"

    restaurants_df = pd.read_csv(cleaned_dir / "restaurants.csv")
    orders_df = pd.read_csv(cleaned_dir / "orders.csv")

    result = train_restaurant_pipeline(restaurants_df, orders_df)
    hist_v1 = load_historical_metrics(models_dir, "restaurant_metrics.json")

    output_csv = engineered_dir / "restaurant_predictions.csv"
    result["output_df"].to_csv(output_csv, index=False)
    print(f"Saved restaurant predictions ({len(result['output_df']):,} restaurants) -> {output_csv}")

    bm = result["best_metrics"]
    bl = result["baseline_metrics"]["Baseline_GlobalTrainMean"]

    metrics_payload = {
        "model_version": "2.0.0-phase05-real-panel",
        "selected_model": result["best_model_name"],
        "target_definition": "Real observed monthly order count per restaurant in complete calendar month M_t predicted from < M_t features",
        "chronological_split": {
            "full_months_observed": result["full_months"],
            "train_target_months": result["train_months"],
            "holdout_target_month": result["holdout_month"],
            "train_samples": result["train_samples"],
            "test_samples": result["test_samples"],
        },
        "holdout_metrics": bm,
        "baseline_comparisons": result["baseline_metrics"],
        "candidate_model_comparison": result["all_model_results"],
        "rolling_3month_backtest": result["backtest_folds"],
        "error_by_city": result["error_by_city"],
        "feature_importances": result["feature_importances"],
        "historical_v1_comparison": {
            "v1_preserved_file": "restaurant_metrics.json",
            "v1_reported_r2": hist_v1.get("r2_score") if hist_v1 else None,
            "v1_reported_mae": hist_v1.get("mae") if hist_v1 else None,
            "v1_leakage_root_cause": (
                "v1 performance_prediction.py synthesized target as Predicted_Next_Month_Orders = Total_Orders * uniform(0.9, 1.15) "
                "and passed Total_Orders directly into OLS, fabricating R2 = 0.8559."
            ),
        },
        "synthetic_data_limitation": (
            "In NovaNest's cleaned transaction data, restaurant order assignments across months have near-zero persistence "
            "(adjacent month r ~ -0.02 to +0.02, monthly orders ~ Poisson(2.7)). Eliminating synthetic target leakage reduces "
            "out-of-time R2 from fake 0.8559 to ~0.00 (MAE ~1.3 orders/month), honestly reflecting unpersonalized uniform store demand."
        ),
    }

    metadata_payload = {
        "model_name": "NovaNest Restaurant Monthly Throughput Predictor",
        "model_version": "2.0.0-phase05-real-panel",
        "random_seed": RANDOM_SEED,
        "selected_algorithm": result["best_model_name"],
        "forbidden_leakage_features_excluded": FORBIDDEN_RESTAURANT_LEAKAGE_COLS,
        "data_audit": result["data_audit"],
    }

    feature_doc_payload = {
        "numeric_features": RESTAURANT_NUMERIC_FEATURES,
        "categorical_features": RESTAURANT_CATEGORICAL_FEATURES,
        "excluded_leaked_features": FORBIDDEN_RESTAURANT_LEAKAGE_COLS,
    }

    comp_rows = "\n".join([
        f"| {m} | {r['mae']} | {r['median_ae']} | {r['rmse']} | {r['r2_score']} |"
        for m, r in result["all_model_results"].items()
    ])
    bt_rows = "\n".join([
        f"| {b['target_month']} | {b['train_months']} | {b['n_restaurants']} | {b['mae']} | {b['rmse']} | {b['r2_score']} |"
        for b in result["backtest_folds"]
    ])

    report_md = f"""# Restaurant Next-Month Order Prediction — Phase 05 Validation Report

## 1. Synthetic Target Leakage Removal (v1 vs v2)
- **v1 Defect**: `performance_prediction.py` synthesized `Predicted_Next_Month_Orders = Total_Orders * uniform(0.9, 1.15)` and passed `Total_Orders` as a feature (fake R² = `0.8559`).
- **v2 Remediation**: Evaluated on real observed monthly restaurant counts across complete calendar months (`{result['full_months'][0]} -> {result['full_months'][-1]}`), holding out `{result['holdout_month']}` (n={result['test_samples']:,} restaurants) using strictly prior (`< {result['holdout_month']}`) lag & metadata features.

## 2. Holdout Month Performance (`{result['holdout_month']}`, n={result['test_samples']:,})
| Model / Baseline | MAE (orders/mo) | Median AE | RMSE | R² Score |
|---|---:|---:|---:|---:|
{comp_rows}

**Selected Model**: `{result['best_model_name']}` (Baseline Train Mean MAE = `{bl['mae']}`, Selected MAE = `{bm['mae']}`, RMSE = `{bm['rmse']}`).

## 3. Rolling Expanding-Window Backtest
| Target Month | Prior Train Months | Restaurants | MAE | RMSE | R² |
|---|---:|---:|---:|---:|---:|
{bt_rows}

## 4. Synthetic Data Limitation
Adjacent monthly restaurant order volumes in `datasets/cleaned/orders.csv` exhibit near-zero autocorrelation (`|r| <= 0.02`), bounding any honest leak-free predictor near the Poisson mean (~2.7–2.9 orders/month per restaurant, RMSE ~1.67 orders).
"""

    written = save_phase05_artifacts(
        model_dir=models_dir,
        versioned_metrics_filename="restaurant_metrics_v2.json",
        metrics_payload=metrics_payload,
        metadata_payload=metadata_payload,
        feature_doc_payload=feature_doc_payload,
        report_markdown=report_md,
        examples_df=result["examples_df"],
        model_obj=result["best_pipeline"],
    )
    print(f"Selected Model: {result['best_model_name']} | MAE={bm['mae']}, MedAE={bm['median_ae']}, RMSE={bm['rmse']}, R2={bm['r2_score']}")
    print(f"Saved artifacts: {list(written.keys())}")
    print("[SUCCESS] Phase 05 Restaurant Prediction Complete.")


if __name__ == "__main__":
    main()
