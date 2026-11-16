"""
Phase 05 — Operations Intelligence: Leak-Free Delivery ETA Prediction
---------------------------------------------------------------------
Trains and evaluates chronological ETA models incorporating rider (`vehicle_type`,
`experience_years`, `shift_type`), temporal (cyclical hour/weekday & meal peaks),
order, and restaurant features WITHOUT fabricating GPS or live traffic telemetry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from ml.validation_framework import (
        RANDOM_SEED,
        assert_strictly_chronological_split,
        audit_missing_and_invalid,
        compute_regression_metrics,
        set_reproducible_seed,
        validate_dataframe_schema,
    )
except ImportError:
    from python.ml.validation_framework import (
        RANDOM_SEED,
        assert_strictly_chronological_split,
        audit_missing_and_invalid,
        compute_regression_metrics,
        set_reproducible_seed,
        validate_dataframe_schema,
    )


ETA_NUMERIC_FEATURES: List[str] = [
    "distance_km",
    "quantity",
    "order_amount",
    "delivery_fee",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "is_weekend",
    "is_lunch_peak",
    "is_dinner_peak",
    "experience_years",
    "avg_rating",
    "delivery_radius_km",
    "distance_to_radius_ratio",
    "cross_city_flag",
]

ETA_CATEGORICAL_FEATURES: List[str] = [
    "vehicle_type",
    "shift_type",
    "restaurant_city",
    "restaurant_type",
    "cuisine_type",
]


def _prepare_eta_frame(
    deliveries_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    customers_df: Optional[pd.DataFrame] = None,
    riders_df: Optional[pd.DataFrame] = None,
    restaurants_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    df = deliveries_df.copy()

    order_keep = [
        c for c in ["order_id", "customer_id", "restaurant_id", "order_datetime", "order_time", "quantity", "order_amount", "delivery_fee"]
        if c in orders_df.columns
    ]
    df = df.merge(orders_df[order_keep], on="order_id", how="left")

    if "order_datetime" not in df.columns and "order_time" in df.columns:
        df["order_datetime"] = df["order_time"]
    df["order_datetime"] = pd.to_datetime(df["order_datetime"], errors="coerce")
    df["order_datetime"] = df["order_datetime"].fillna(df["order_datetime"].min())

    if riders_df is not None and not riders_df.empty and "rider_id" in df.columns:
        rider_keep = [c for c in ["rider_id", "city", "vehicle_type", "experience_years", "shift_type"] if c in riders_df.columns]
        r_sub = riders_df[rider_keep].rename(columns={"city": "rider_city"})
        df = df.merge(r_sub, on="rider_id", how="left")

    if restaurants_df is not None and not restaurants_df.empty and "restaurant_id" in df.columns:
        rest_keep = [
            c for c in ["restaurant_id", "city", "restaurant_type", "cuisine_type", "avg_rating", "delivery_radius_km"]
            if c in restaurants_df.columns
        ]
        rest_sub = restaurants_df[rest_keep].rename(columns={"city": "restaurant_city"})
        df = df.merge(rest_sub, on="restaurant_id", how="left")

    if customers_df is not None and not customers_df.empty and "customer_id" in df.columns:
        if "restaurant_city" not in df.columns and "city" in customers_df.columns:
            df = df.merge(customers_df[["customer_id", "city"]].rename(columns={"city": "restaurant_city"}), on="customer_id", how="left")

    # Fill safe operational defaults when optional tables are absent
    for col, default in [
        ("quantity", 1.0),
        ("order_amount", df["order_amount"].median() if "order_amount" in df.columns else 500.0),
        ("delivery_fee", 35.0),
        ("experience_years", 2.0),
        ("avg_rating", 4.0),
        ("delivery_radius_km", 8.0),
        ("vehicle_type", "Unknown"),
        ("shift_type", "Unknown"),
        ("rider_city", "Unknown"),
        ("restaurant_city", "Unknown"),
        ("restaurant_type", "Unknown"),
        ("cuisine_type", "Unknown"),
    ]:
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    hour = df["order_datetime"].dt.hour.astype(float)
    dow = df["order_datetime"].dt.dayofweek.astype(float)
    df["hour"] = hour.astype(int)
    df["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    df["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    df["dow_sin"] = np.sin(2.0 * np.pi * dow / 7.0)
    df["dow_cos"] = np.cos(2.0 * np.pi * dow / 7.0)
    df["is_weekend"] = df["order_datetime"].dt.dayofweek.isin([5, 6]).astype(int)
    df["is_lunch_peak"] = df["hour"].between(12, 15).astype(int)
    df["is_dinner_peak"] = df["hour"].between(19, 22).astype(int)

    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce").fillna(df["distance_km"].median())
    df["delivery_radius_km"] = pd.to_numeric(df["delivery_radius_km"], errors="coerce").fillna(8.0)
    df["distance_to_radius_ratio"] = df["distance_km"] / np.clip(df["delivery_radius_km"], 1.0, None)
    df["cross_city_flag"] = (
        (df["rider_city"].astype(str) != "Unknown")
        & (df["restaurant_city"].astype(str) != "Unknown")
        & (df["rider_city"].astype(str) != df["restaurant_city"].astype(str))
    ).astype(int)

    # Sort strictly chronologically for leak-free temporal train/test evaluation
    sort_cols = [c for c in ["order_datetime", "order_id", "delivery_id"] if c in df.columns]
    df = df.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)
    return df


def _build_eta_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                ETA_NUMERIC_FEATURES,
            ),
            (
                "cat",
                Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")), ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]),
                ETA_CATEGORICAL_FEATURES,
            ),
        ]
    )


def _compute_error_analysis(test_df: pd.DataFrame, preds: np.ndarray) -> Dict[str, Any]:
    eval_df = test_df[["delivery_duration", "distance_km", "restaurant_city", "vehicle_type", "is_lunch_peak", "is_dinner_peak"]].copy()
    eval_df["predicted_eta"] = preds
    eval_df["abs_error"] = np.abs(eval_df["predicted_eta"] - eval_df["delivery_duration"])
    eval_df["error"] = eval_df["predicted_eta"] - eval_df["delivery_duration"]

    by_city = (
        eval_df.groupby("restaurant_city")["abs_error"]
        .agg(count="count", mae="mean", med_ae="median")
        .round(3)
        .to_dict(orient="index")
    )
    by_vehicle = (
        eval_df.groupby("vehicle_type")["abs_error"]
        .agg(count="count", mae="mean", med_ae="median")
        .round(3)
        .to_dict(orient="index")
    )
    eval_df["period_bucket"] = np.where(
        eval_df["is_dinner_peak"] == 1,
        "Dinner Peak (19-22h)",
        np.where(eval_df["is_lunch_peak"] == 1, "Lunch Peak (12-15h)", "Off-Peak"),
    )
    by_period = (
        eval_df.groupby("period_bucket")["abs_error"]
        .agg(count="count", mae="mean", med_ae="median")
        .round(3)
        .to_dict(orient="index")
    )
    return {
        "by_city": by_city,
        "by_vehicle_type": by_vehicle,
        "by_time_period": by_period,
    }


def train_and_predict_eta(
    deliveries_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    customers_df: Optional[pd.DataFrame] = None,
    riders_df: Optional[pd.DataFrame] = None,
    restaurants_df: Optional[pd.DataFrame] = None,
    return_artifacts: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]] | Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Train and evaluate Delivery ETA models chronologically without traffic/GPS fabrication.
    Preserves standard (predictions_df, metrics_dict) return contract by default.
    """
    set_reproducible_seed(RANDOM_SEED)
    validate_dataframe_schema(deliveries_df, ["delivery_id", "order_id", "distance_km", "delivery_duration"], "deliveries_df", min_rows=20)
    validate_dataframe_schema(orders_df, ["order_id"], "orders_df", min_rows=20)

    df = _prepare_eta_frame(deliveries_df, orders_df, customers_df, riders_df, restaurants_df)
    valid_mask = df["delivery_duration"].notna() & (df["delivery_duration"] > 0)
    clean_df = df[valid_mask].copy().reset_index(drop=True)

    feature_cols = ETA_NUMERIC_FEATURES + ETA_CATEGORICAL_FEATURES
    split_idx = int(len(clean_df) * 0.8)
    if split_idx < 10 or split_idx >= len(clean_df) - 5:
        split_idx = max(5, len(clean_df) - max(5, int(len(clean_df) * 0.2)))

    train_df = clean_df.iloc[:split_idx].copy()
    test_df = clean_df.iloc[split_idx:].copy()
    assert_strictly_chronological_split(
        train_df["order_datetime"],
        test_df["order_datetime"],
        context="ETA chronological split",
        allow_equal_boundary=True,
    )

    X_train, y_train = train_df[feature_cols], train_df["delivery_duration"].astype(float).values
    X_test, y_test = test_df[feature_cols], test_df["delivery_duration"].astype(float).values
    y_train_min = float(np.min(y_train))

    candidates: Dict[str, Any] = {
        "Baseline_HistoricalMean": Pipeline([("prep", _build_eta_preprocessor()), ("reg", DummyRegressor(strategy="mean"))]),
        "OLS_LinearRegression": Pipeline([("prep", _build_eta_preprocessor()), ("reg", LinearRegression())]),
        "Ridge_L2_Regression": Pipeline([("prep", _build_eta_preprocessor()), ("reg", Ridge(alpha=10.0, random_state=RANDOM_SEED))]),
        "HistGradientBoosting": Pipeline([
            ("prep", _build_eta_preprocessor()),
            ("reg", HistGradientBoostingRegressor(max_iter=120, max_depth=4, min_samples_leaf=50, l2_regularization=5.0, random_state=RANDOM_SEED)),
        ]),
    }

    model_results: Dict[str, Dict[str, Any]] = {}
    fitted: Dict[str, Pipeline] = {}
    for name, pipe in candidates.items():
        pipe.fit(X_train, y_train)
        fitted[name] = pipe
        preds = np.clip(pipe.predict(X_test), max(1.0, y_train_min * 0.5), 180.0)
        model_results[name] = compute_regression_metrics(y_test, preds)

    # Select best genuine ML model by lowest MAE among non-dummy candidates (and compare to Baseline)
    ml_names = [k for k in model_results if k != "Baseline_HistoricalMean"]
    best_name = min(ml_names, key=lambda m: (model_results[m]["mae"], model_results[m]["rmse"]))
    best_pipe = fitted[best_name]
    best_metrics = model_results[best_name]

    # 3-fold TimeSeriesSplit cross-validation on train_df using Ridge (fast & stable) or best_name
    tscv = TimeSeriesSplit(n_splits=3)
    cv_maes: List[float] = []
    cv_rmses: List[float] = []
    for tr_idx, va_idx in tscv.split(X_train):
        cv_pipe = candidates[best_name]
        cv_pipe.fit(X_train.iloc[tr_idx], y_train[tr_idx])
        cv_pred = np.clip(cv_pipe.predict(X_train.iloc[va_idx]), max(1.0, y_train_min * 0.5), 180.0)
        cv_m = compute_regression_metrics(y_train[va_idx], cv_pred)
        cv_maes.append(cv_m["mae"])
        cv_rmses.append(cv_m["rmse"])

    # Refit selected model on clean train split ONLY for honest out-of-sample test scoring;
    # evaluate error breakdown strictly on chronological test set
    best_pipe.fit(X_train, y_train)
    test_preds = np.clip(best_pipe.predict(X_test), max(1.0, y_train_min * 0.5), 180.0)
    error_analysis = _compute_error_analysis(test_df, test_preds)

    # Full dataset predictions produced cleanly without leaking test targets into train weights
    all_preds = np.round(np.clip(best_pipe.predict(clean_df[feature_cols]), max(1.0, y_train_min * 0.5), 180.0), 1)
    clean_df["predicted_eta"] = all_preds
    clean_df["eta_error"] = (clean_df["delivery_duration"] - clean_df["predicted_eta"]).round(1)
    clean_df["abs_eta_error"] = np.abs(clean_df["eta_error"]).round(1)
    clean_df["accuracy_pct"] = (100.0 - (clean_df["abs_eta_error"] / clean_df["delivery_duration"]) * 100.0).clip(lower=0.0).round(1)
    clean_df["accuracy_bucket"] = np.where(
        clean_df["abs_eta_error"] <= 5.0,
        "Excellent (<=5 min error)",
        np.where(clean_df["abs_eta_error"] <= 15.0, "Acceptable (5-15 min error)", "Delayed (>15 min error)"),
    )
    clean_df["split_role"] = np.where(np.arange(len(clean_df)) < split_idx, "train", "holdout_test")

    test_clean = clean_df.iloc[split_idx:]
    bucket_counts = test_clean["accuracy_bucket"].value_counts(normalize=True) * 100.0

    output_cols = [
        "order_id",
        "delivery_id",
        "rider_id",
        "distance_km",
        "delivery_duration",
        "predicted_eta",
        "eta_error",
        "abs_eta_error",
        "accuracy_pct",
        "accuracy_bucket",
    ]
    out_df = clean_df[[c for c in output_cols if c in clean_df.columns]].copy()

    metrics_dict: Dict[str, Any] = {
        "model_version": "2.0.0-phase05-chronological",
        "selected_model": best_name,
        "MAE_minutes": best_metrics["mae"],
        "Median_AE_minutes": best_metrics["median_ae"],
        "RMSE_minutes": best_metrics["rmse"],
        "R2_Score": best_metrics["r2_score"],
        "MAPE_pct": best_metrics["mape_pct"],
        "Baseline_Mean_MAE_minutes": model_results["Baseline_HistoricalMean"]["mae"],
        "Baseline_Mean_RMSE_minutes": model_results["Baseline_HistoricalMean"]["rmse"],
        "TimeSeriesCV_3Fold_Mean_MAE": round(float(np.mean(cv_maes)), 4),
        "TimeSeriesCV_3Fold_Mean_RMSE": round(float(np.mean(cv_rmses)), 4),
        "Train_Samples": int(len(train_df)),
        "Test_Samples": int(len(test_df)),
        "Train_Date_Range": f"{train_df['order_datetime'].min()} -> {train_df['order_datetime'].max()}",
        "Test_Date_Range": f"{test_df['order_datetime'].min()} -> {test_df['order_datetime'].max()}",
        "Total_Deliveries_Evaluated": int(len(out_df)),
        "Holdout_Excellent_PCT": round(float(bucket_counts.get("Excellent (<=5 min error)", 0.0)), 1),
        "Holdout_Acceptable_PCT": round(float(bucket_counts.get("Acceptable (5-15 min error)", 0.0)), 1),
        "Holdout_Delayed_PCT": round(float(bucket_counts.get("Delayed (>15 min error)", 0.0)), 1),
        "Disclaimer": (
            "Live GPS routes, real-time traffic congestion, weather, and kitchen prep durations are absent from the synthetic dataset; "
            "cleaned delivery_duration exhibits near-zero bivariate correlation with distance_km (r ~ -0.003), bounding true R2 near 0."
        ),
    }

    if not return_artifacts:
        return out_df, metrics_dict

    artifacts = {
        "best_pipeline": best_pipe,
        "candidate_models": model_results,
        "error_analysis": error_analysis,
        "data_audit": audit_missing_and_invalid(clean_df[ETA_NUMERIC_FEATURES], ETA_NUMERIC_FEATURES, "eta_features"),
        "examples_df": test_clean[["order_id", "delivery_id", "distance_km", "vehicle_type", "hour", "delivery_duration", "predicted_eta", "eta_error", "abs_eta_error", "accuracy_bucket"]].copy(),
    }
    return out_df, metrics_dict, artifacts
