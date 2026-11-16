"""
NovaNest Phase 05 — Shared ML Validation, Leakage Guard & Artifact Framework
----------------------------------------------------------------------------
Provides reusable utilities for:
- Deterministic seeding (RANDOM_SEED = 42)
- DataFrame schema & missing/invalid value auditing
- Chronological split & target/feature leakage assertions
- Unified classification & regression evaluation metrics (incl. Median AE)
- Historical v1 artifact preservation and versioned v2 model artifact storage
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    median_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)

RANDOM_SEED = 42


def set_reproducible_seed(seed: int = RANDOM_SEED) -> None:
    """Enforce deterministic RNG across Python and NumPy."""
    random.seed(seed)
    np.random.seed(seed)


def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: Sequence[str],
    df_name: str = "DataFrame",
    min_rows: int = 1,
) -> None:
    """Validate non-empty DataFrame and presence of required columns."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError(f"{df_name} must be a valid pandas DataFrame.")
    if len(df) < min_rows:
        raise ValueError(f"{df_name} has {len(df)} rows, fewer than required minimum {min_rows}.")
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{df_name} missing required columns: {missing}")


def audit_missing_and_invalid(
    df: pd.DataFrame,
    numeric_columns: Optional[Sequence[str]] = None,
    name: str = "dataset",
) -> Dict[str, Any]:
    """Audit missing values, infinities, duplicates, and zero-variance columns."""
    audit: Dict[str, Any] = {
        "dataset": name,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "null_counts": {},
        "inf_counts": {},
        "zero_variance_columns": [],
    }
    for col in df.columns:
        nulls = int(df[col].isna().sum())
        if nulls > 0:
            audit["null_counts"][col] = nulls

    check_cols = list(numeric_columns) if numeric_columns is not None else df.select_dtypes(include=[np.number]).columns.tolist()
    for col in check_cols:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        infs = int(np.isinf(series.fillna(0.0)).sum())
        if infs > 0:
            audit["inf_counts"][col] = infs
        if series.nunique(dropna=True) <= 1:
            audit["zero_variance_columns"].append(col)

    return audit


def assert_strictly_chronological_split(
    train_timestamps: Iterable[Any],
    test_timestamps: Iterable[Any],
    context: str = "temporal split",
    allow_equal_boundary: bool = True,
) -> Tuple[str, str]:
    """Ensure training observations strictly precede or match cutoff of test observations."""
    tr = pd.to_datetime(pd.Series(list(train_timestamps)))
    te = pd.to_datetime(pd.Series(list(test_timestamps)))
    if tr.empty or te.empty:
        raise ValueError(f"[{context}] Empty train or test timestamp sequence.")
    tr_max = tr.max()
    te_min = te.min()
    violated = (tr_max > te_min) if allow_equal_boundary else (tr_max >= te_min)
    if violated:
        raise AssertionError(
            f"Temporal leakage detected in {context}: max(train)={tr_max} violates boundary vs min(test)={te_min}."
        )
    return str(tr_max), str(te_min)


def assert_no_forbidden_features(
    feature_cols: Sequence[str],
    forbidden_cols: Sequence[str],
    context: str = "feature matrix",
) -> None:
    """Prevent leaked or target-derived columns from entering model feature sets."""
    feature_set = set(feature_cols)
    leaked = sorted(feature_set.intersection(set(forbidden_cols)))
    if leaked:
        raise AssertionError(f"Leakage guard triggered in {context}: forbidden features present: {leaked}")


def compute_classification_metrics(
    y_true: Sequence[int] | np.ndarray,
    y_pred: Sequence[int] | np.ndarray,
    y_prob: Sequence[float] | np.ndarray,
) -> Dict[str, Any]:
    """Compute standardized binary classification evaluation metrics."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)
    ypr = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)

    tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
    unique_classes = len(np.unique(yt))

    roc_auc = float(roc_auc_score(yt, ypr)) if unique_classes > 1 else None
    pr_auc = float(average_precision_score(yt, ypr)) if unique_classes > 1 else None
    brier = float(brier_score_loss(yt, ypr)) if len(yt) > 0 else None

    return {
        "n_samples": int(len(yt)),
        "positive_count": int(yt.sum()),
        "positive_rate_pct": round(float(yt.mean() * 100.0), 2) if len(yt) > 0 else 0.0,
        "accuracy": round(float(accuracy_score(yt, yp)), 4),
        "precision": round(float(precision_score(yt, yp, zero_division=0)), 4),
        "recall": round(float(recall_score(yt, yp, zero_division=0)), 4),
        "f1_score": round(float(f1_score(yt, yp, zero_division=0)), 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
        "brier_score": round(brier, 4) if brier is not None else None,
        "confusion_matrix": {
            "TP": int(tp),
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
        },
    }


def compute_regression_metrics(
    y_true: Sequence[float] | np.ndarray,
    y_pred: Sequence[float] | np.ndarray,
    epsilon: float = 1e-6,
) -> Dict[str, Any]:
    """Compute standardized regression metrics including Median Absolute Error."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    mask = np.isfinite(yt) & np.isfinite(yp)
    yt = yt[mask]
    yp = yp[mask]
    if len(yt) == 0:
        raise ValueError("Cannot compute regression metrics on zero finite samples.")

    errors = yp - yt
    abs_errors = np.abs(errors)
    nonzero = np.abs(yt) > epsilon
    mape = float(np.mean(abs_errors[nonzero] / np.abs(yt[nonzero])) * 100.0) if np.any(nonzero) else None

    return {
        "n_samples": int(len(yt)),
        "mae": round(float(mean_absolute_error(yt, yp)), 4),
        "median_ae": round(float(median_absolute_error(yt, yp)), 4),
        "rmse": round(float(root_mean_squared_error(yt, yp)), 4),
        "r2_score": round(float(r2_score(yt, yp)), 4) if np.var(yt) > 1e-12 else 0.0,
        "mape_pct": round(mape, 2) if mape is not None else None,
        "mean_bias_error": round(float(np.mean(errors)), 4),
        "max_abs_error": round(float(np.max(abs_errors)), 4),
        "target_mean": round(float(np.mean(yt)), 4),
        "target_std": round(float(np.std(yt)), 4),
    }


def load_historical_metrics(model_dir: Path, legacy_filename: str) -> Optional[Dict[str, Any]]:
    """Read legacy v1 metrics JSON if present without modifying it."""
    path = Path(model_dir) / legacy_filename
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_phase05_artifacts(
    model_dir: Path,
    versioned_metrics_filename: str,
    metrics_payload: Dict[str, Any],
    metadata_payload: Dict[str, Any],
    feature_doc_payload: Dict[str, Any],
    report_markdown: str,
    examples_df: Optional[pd.DataFrame] = None,
    model_obj: Optional[Any] = None,
) -> Dict[str, str]:
    """
    Save updated Phase 05 artifacts into `models/<model>/` without overwriting
    historical v1 `*_metrics.json` reports.
    """
    out_dir = Path(model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    metrics_with_ts = {"generated_at_utc": generated_at, **metrics_payload}
    metadata_with_ts = {"generated_at_utc": generated_at, **metadata_payload}
    feat_with_ts = {"generated_at_utc": generated_at, **feature_doc_payload}

    written: Dict[str, str] = {}

    metrics_path = out_dir / versioned_metrics_filename
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_with_ts, f, indent=4)
    written["metrics_v2"] = str(metrics_path)

    meta_path = out_dir / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_with_ts, f, indent=4)
    written["metadata"] = str(meta_path)

    feat_path = out_dir / "feature_documentation.json"
    with open(feat_path, "w", encoding="utf-8") as f:
        json.dump(feat_with_ts, f, indent=4)
    written["feature_documentation"] = str(feat_path)

    report_path = out_dir / "validation_report.md"
    report_path.write_text(report_markdown, encoding="utf-8")
    written["validation_report"] = str(report_path)

    if examples_df is not None and not examples_df.empty:
        ex_path = out_dir / "prediction_examples.csv"
        examples_df.head(100).to_csv(ex_path, index=False)
        written["prediction_examples"] = str(ex_path)

    if model_obj is not None:
        art_path = out_dir / "model_artifact.joblib"
        joblib.dump(model_obj, art_path)
        written["model_artifact"] = str(art_path)

    return written

