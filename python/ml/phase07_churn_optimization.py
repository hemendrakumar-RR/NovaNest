"""
NovaNest Phase 07 — Advanced Customer Churn Optimization
--------------------------------------------------------
Implements leakage-free customer churn modeling with:
- Heuristic, Logistic Regression, Random Forest, HistGradientBoosting, LightGBM, and XGBoost benchmarks
- Probability calibration (Brier score evaluation)
- Native TreeSHAP feature attributions and local instance explainability
- Actionable retention segmentation (High-Value At-Risk, Discount-Sensitive, etc.)
- Model Registry v3 integration with automated rollback & dataset lineage tracking
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import xgboost as xgb

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))
sys.path.insert(0, str(BASE_DIR / "python" / "intelligence" / "customer"))

from python.intelligence.customer.churn import (
    CHURN_CATEGORICAL_FEATURES,
    CHURN_NUMERIC_FEATURES,
    FORBIDDEN_CHURN_LEAKAGE_COLS,
    build_churn_observation_cohort,
)
from python.ml.explainability import (
    compute_global_feature_importance,
    compute_treeshap_contributions,
    explain_local_prediction,
)
from python.ml.model_registry import model_registry
from python.ml.validation_framework import (
    RANDOM_SEED,
    assert_no_forbidden_features,
    assert_strictly_chronological_split,
    audit_missing_and_invalid,
    compute_classification_metrics,
    set_reproducible_seed,
    validate_dataframe_schema,
)


def build_preprocessor() -> ColumnTransformer:
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, CHURN_NUMERIC_FEATURES),
            ("cat", cat_pipe, CHURN_CATEGORICAL_FEATURES),
        ]
    )


def extract_actionable_retention_segments(
    scored_df: pd.DataFrame,
    prob_col: str = "churn_probability",
) -> Dict[str, Any]:
    """Segment customers by value and churn risk to prescribe specific retention interventions."""
    df = scored_df.copy()
    if prob_col not in df.columns:
        return {}

    high_risk = df[df[prob_col] >= 0.60]
    high_value_threshold = df["Lookback_Monetary"].quantile(0.80) if "Lookback_Monetary" in df.columns else 1000.0

    high_value_at_risk = high_risk[high_risk["Lookback_Monetary"] >= high_value_threshold]
    discount_sensitive_at_risk = high_risk[high_risk.get("Discount_Usage_Pct_Pre", 0.0) >= 30.0]
    loyal_advocates = df[(df[prob_col] < 0.25) & (df["Lookback_Monetary"] >= high_value_threshold)]

    return {
        "total_active_cohort": int(len(df)),
        "high_risk_count": int(len(high_risk)),
        "high_risk_pct": round(float(len(high_risk) / len(df) * 100.0), 2) if len(df) > 0 else 0.0,
        "segments": {
            "high_value_at_risk": {
                "count": int(len(high_value_at_risk)),
                "avg_spend": round(float(high_value_at_risk["Lookback_Monetary"].mean()), 2) if not high_value_at_risk.empty else 0.0,
                "recommended_action": "Dedicated account manager outreach, personalized VIP reactivation credit (₹300+).",
            },
            "discount_sensitive_at_risk": {
                "count": int(len(discount_sensitive_at_risk)),
                "avg_discount_pct": round(float(discount_sensitive_at_risk.get("Discount_Usage_Pct_Pre", pd.Series([0])).mean()), 2),
                "recommended_action": "Dynamic limited-time flash discount (15-20% off next 2 orders).",
            },
            "loyal_advocates": {
                "count": int(len(loyal_advocates)),
                "avg_spend": round(float(loyal_advocates["Lookback_Monetary"].mean()), 2) if not loyal_advocates.empty else 0.0,
                "recommended_action": "Early access to new restaurant launches, loyalty milestone perks.",
            },
        },
    }


def train_and_benchmark_churn_models(
    datasets_dir: Path = BASE_DIR / "datasets" / "cleaned",
) -> Dict[str, Any]:
    """Execute complete Phase 07 Customer Churn benchmark, explainability, and registration."""
    set_reproducible_seed(RANDOM_SEED)

    orders_path = datasets_dir / "orders.csv"
    customers_path = datasets_dir / "customers.csv"
    ratings_path = datasets_dir / "ratings_reviews.csv"

    orders_df = pd.read_csv(orders_path)
    customers_df = pd.read_csv(customers_path)
    ratings_df = pd.read_csv(ratings_path) if ratings_path.is_file() else None

    # Date handling
    if "order_datetime" not in orders_df.columns and "order_time" in orders_df.columns:
        orders_df["order_datetime"] = orders_df["order_time"]
    orders_df["order_datetime"] = pd.to_datetime(orders_df["order_datetime"])
    max_dt = orders_df["order_datetime"].max()

    # Chronological cohorts: 90-day churn horizon, 180-day lookback
    test_cutoff = max_dt - pd.Timedelta(days=90)
    train_cutoff = test_cutoff - pd.Timedelta(days=90)

    train_df = build_churn_observation_cohort(
        orders_df, customers_df, ratings_df,
        cutoff_date=train_cutoff, churn_horizon_days=90, lookback_days=180, include_target=True
    )
    test_df = build_churn_observation_cohort(
        orders_df, customers_df, ratings_df,
        cutoff_date=test_cutoff, churn_horizon_days=90, lookback_days=180, include_target=True
    )

    feature_cols = CHURN_NUMERIC_FEATURES + CHURN_CATEGORICAL_FEATURES
    assert_no_forbidden_features(feature_cols, FORBIDDEN_CHURN_LEAKAGE_COLS, "Phase 07 Churn Features")

    X_train = train_df[feature_cols]
    y_train = train_df["Is_Churned"].values
    X_test = test_df[feature_cols]
    y_test = test_df["Is_Churned"].values

    # Preprocessor
    preprocessor = build_preprocessor()
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    feature_names_out = (
        CHURN_NUMERIC_FEATURES +
        list(preprocessor.named_transformers_["cat"].named_steps["ohe"].get_feature_names_out(CHURN_CATEGORICAL_FEATURES))
    )

    # 1. Baseline Heuristic
    heuristic_pred = (test_df["Pre_Cutoff_Recency_Days"].fillna(999.0) > 90.0).astype(int).values
    heuristic_prob = np.clip(test_df["Pre_Cutoff_Recency_Days"].fillna(999.0).values / 180.0, 0.0, 1.0)
    heuristic_metrics = compute_classification_metrics(y_test, heuristic_pred, heuristic_prob)

    # Model candidates
    candidates: Dict[str, Any] = {
        "LogisticRegression_L2": LogisticRegression(C=1.0, max_iter=500, random_state=RANDOM_SEED),
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=RANDOM_SEED, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=100, max_depth=5, random_state=RANDOM_SEED),
        "LightGBM": lgb.LGBMClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=RANDOM_SEED, verbose=-1),
        "XGBoost": xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=RANDOM_SEED, eval_metric="logloss"),
    }

    benchmark_results: Dict[str, Any] = {
        "Heuristic_Recency_Baseline": heuristic_metrics,
    }
    fitted_models: Dict[str, Any] = {}

    best_name = "LightGBM"
    best_roc_auc = -1.0
    best_calibrated_clf = None

    for name, raw_clf in candidates.items():
        # Wrap in probability calibration with 3-fold cross validation
        calibrated = CalibratedClassifierCV(estimator=raw_clf, method="sigmoid", cv=3)
        calibrated.fit(X_train_trans, y_train)

        y_pred = calibrated.predict(X_test_trans)
        y_prob = calibrated.predict_proba(X_test_trans)[:, 1]
        metrics = compute_classification_metrics(y_test, y_pred, y_prob)
        benchmark_results[name] = metrics
        fitted_models[name] = (raw_clf, calibrated)

        auc_score = metrics.get("roc_auc") or 0.0
        if auc_score > best_roc_auc:
            best_roc_auc = auc_score
            best_name = name
            best_calibrated_clf = calibrated

    # If LightGBM or XGBoost was competitive, ensure tree booster is available for native TreeSHAP
    selected_raw, selected_calibrated = fitted_models[best_name]

    # Global feature importance
    global_importance = compute_global_feature_importance(
        selected_raw,
        X_test_trans,
        y_test,
        feature_names=feature_names_out,
        method="shap" if best_name in ("LightGBM", "XGBoost") else "auto",
        top_k=15,
    )

    # Scored live test cohort & retention segmentation
    test_df_scored = test_df.copy()
    test_df_scored["churn_probability"] = selected_calibrated.predict_proba(X_test_trans)[:, 1]
    test_df_scored["predicted_churn"] = selected_calibrated.predict(X_test_trans)
    retention_insights = extract_actionable_retention_segments(test_df_scored, "churn_probability")

    # Local explanations for top at-risk customer
    top_risk_cust = test_df_scored.sort_values(by="churn_probability", ascending=False).iloc[0]
    top_risk_idx = test_df_scored.index.get_loc(top_risk_cust.name)
    sample_x = X_test_trans[top_risk_idx]

    local_explanation = explain_local_prediction(
        selected_raw,
        sample_x,
        feature_names=feature_names_out,
        predicted_value=float(top_risk_cust["churn_probability"]),
        framework="lightgbm" if best_name == "LightGBM" else "xgboost",
    )

    # Save artifact pipeline containing preprocessor + calibrated classifier + raw booster
    full_artifact = {
        "preprocessor": preprocessor,
        "calibrated_classifier": selected_calibrated,
        "raw_model": selected_raw,
        "feature_names_in": feature_cols,
        "feature_names_out": feature_names_out,
        "best_algorithm": best_name,
    }

    # Register in Model Registry
    dataset_paths = {
        "orders.csv": orders_path,
        "customers.csv": customers_path,
        "ratings_reviews.csv": ratings_path,
    }

    reg_metadata = model_registry.register_model(
        model_name="customer_churn",
        version="v3",
        algorithm=f"{best_name}_Calibrated",
        model_type="classification",
        artifact=full_artifact,
        evaluation_metrics={
            "benchmark_comparison": benchmark_results,
            "best_model_metrics": benchmark_results[best_name],
            "brier_score": benchmark_results[best_name].get("brier_score"),
            "roc_auc": benchmark_results[best_name].get("roc_auc"),
            "pr_auc": benchmark_results[best_name].get("pr_auc"),
            "f1_score": benchmark_results[best_name].get("f1_score"),
        },
        features=feature_cols,
        hyperparameters={"best_algorithm": best_name, "calibration": "sigmoid"},
        dataset_paths=dataset_paths,
        set_active=True,
        notes="Phase 07 leak-free customer churn optimization with native TreeSHAP and retention segmentation.",
    )

    # Write prediction examples and metrics v3 file
    churn_dir = BASE_DIR / "models" / "customer_churn"
    with open(churn_dir / "churn_metrics_v3.json", "w", encoding="utf-8") as f:
        json.dump({
            "model": "Customer Churn Optimization",
            "version": "v3",
            "benchmarks": benchmark_results,
            "best_model": best_name,
            "global_feature_importance": global_importance,
            "retention_segments": retention_insights,
            "local_explanation_sample": local_explanation,
            "confidence_tier": reg_metadata["confidence_tier"],
            "confidence_caveat": reg_metadata["confidence_caveat"],
        }, f, indent=2)

    sample_predictions = test_df_scored[["customer_id", "Pre_Cutoff_Recency_Days", "Lookback_Monetary", "Is_Churned", "churn_probability", "predicted_churn"]].head(20)
    sample_predictions.to_csv(churn_dir / "prediction_examples_v3.csv", index=False)

    return {
        "best_model": best_name,
        "benchmark_results": benchmark_results,
        "retention_insights": retention_insights,
        "global_importance": global_importance,
        "confidence_tier": reg_metadata["confidence_tier"],
    }


if __name__ == "__main__":
    print("Running Phase 07 Customer Churn Optimization...")
    res = train_and_benchmark_churn_models()
    print("Optimization Completed!")
    print(f"Best Model: {res['best_model']}")
    print(f"Metrics: {json.dumps(res['benchmark_results'], indent=2)}")
