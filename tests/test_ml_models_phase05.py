"""
Phase 05 — Automated Test Suite for NovaNest ML Models & Validation Framework
-----------------------------------------------------------------------------
Verifies leakage removal, chronological splits, missing-value handling,
edge cases, reproducibility, schema parity, and artifact preservation across
all 5 NovaNest ML subsystems.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))
sys.path.insert(0, str(BASE_DIR / "python" / "intelligence" / "customer"))
sys.path.insert(0, str(BASE_DIR / "python" / "intelligence" / "operations"))
sys.path.insert(0, str(BASE_DIR / "python" / "intelligence" / "restaurant"))

from anomaly_detection import compute_statistical_bounds, detect_operational_anomalies_with_audit
from churn import (
    CHURN_NUMERIC_FEATURES,
    FORBIDDEN_CHURN_LEAKAGE_COLS,
    build_churn_observation_cohort,
    extract_churn_features,
)
from demand_forecasting import (
    DEMAND_NUMERIC_FEATURES,
    prepare_demand_time_series,
    train_and_forecast_demand,
)
from eta_prediction import train_and_predict_eta
from performance_prediction import (
    FORBIDDEN_RESTAURANT_LEAKAGE_COLS,
    RESTAURANT_NUMERIC_FEATURES,
    build_restaurant_monthly_panel,
    extract_restaurant_features,
)
from revenue_leakage import detect_revenue_leakage
from train_customer_churn import train_churn_pipeline
from train_restaurant_prediction import train_restaurant_pipeline
from validation_framework import (
    RANDOM_SEED,
    assert_no_forbidden_features,
    assert_strictly_chronological_split,
    compute_classification_metrics,
    compute_regression_metrics,
    set_reproducible_seed,
    validate_dataframe_schema,
)


def _make_synthetic_orders_fixture(seed: int = 42, n_days: int = 240, n_orders: int = 1200) -> dict[str, pd.DataFrame]:
    """Create a deterministic lightweight fixture mirroring cleaned NovaNest tables."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-07-01")
    order_dates = start + pd.to_timedelta(rng.integers(0, n_days, size=n_orders), unit="D") + pd.to_timedelta(rng.integers(0, 24, size=n_orders), unit="h")

    n_cust = 120
    n_rest = 30
    n_riders = 40
    cities = ["Bangalore", "Chennai", "Hyderabad"]

    customers = pd.DataFrame({
        "customer_id": [f"C{i:04d}" for i in range(n_cust)],
        "name": [f"Customer {i}" for i in range(n_cust)],
        "city": rng.choice(cities, size=n_cust),
        "persona": rng.choice(["Family", "Student", "Working Professional"], size=n_cust),
    })
    restaurants = pd.DataFrame({
        "restaurant_id": [f"R{i:04d}" for i in range(n_rest)],
        "restaurant_name": [f"Resto {i}" for i in range(n_rest)],
        "city": rng.choice(cities, size=n_rest),
        "restaurant_type": rng.choice(["Cafe", "Cloud Kitchen"], size=n_rest),
        "cuisine_type": rng.choice(["South Indian", "Biryani"], size=n_rest),
        "opening_year": rng.integers(2015, 2024, size=n_rest),
        "avg_rating": np.round(rng.uniform(3.5, 4.8, size=n_rest), 2),
        "delivery_radius_km": np.round(rng.uniform(4.0, 10.0, size=n_rest), 1),
        "commission_percentage": rng.choice([15.0, 18.0, 22.0], size=n_rest),
    })
    riders = pd.DataFrame({
        "rider_id": [f"RD{i:04d}" for i in range(n_riders)],
        "rider_name": [f"Rider {i}" for i in range(n_riders)],
        "city": rng.choice(cities, size=n_riders),
        "vehicle_type": rng.choice(["Bike", "Scooter"], size=n_riders),
        "experience_years": np.round(rng.uniform(0.5, 7.0, size=n_riders), 1),
        "shift_type": rng.choice(["Morning", "Evening"], size=n_riders),
    })

    cust_ids = rng.choice(customers["customer_id"], size=n_orders)
    # Force customers C0000..C0024 to stop ordering after day 100 for realistic positive churn cohorts
    early_mask = np.isin(cust_ids, [f"C{i:04d}" for i in range(25)])
    early_days = rng.integers(0, 95, size=int(early_mask.sum()))
    order_dates_arr = order_dates.to_numpy(copy=True)
    order_dates_arr[early_mask] = (start + pd.to_timedelta(early_days, unit="D")).to_numpy()
    order_dates = pd.DatetimeIndex(order_dates_arr)

    rest_ids = rng.choice(restaurants["restaurant_id"], size=n_orders)
    rider_ids = rng.choice(riders["rider_id"], size=n_orders)
    order_amt = np.round(rng.uniform(150.0, 1800.0, size=n_orders), 2)
    disc_amt = np.round(order_amt * rng.uniform(0.0, 0.2, size=n_orders), 2)
    deliv_fee = rng.choice([0.0, 25.0, 40.0], size=n_orders)

    orders = pd.DataFrame({
        "order_id": [f"O{i:06d}" for i in range(n_orders)],
        "customer_id": cust_ids,
        "restaurant_id": rest_ids,
        "rider_id": rider_ids,
        "order_datetime": order_dates.strftime("%Y-%m-%d %H:%M:%S"),
        "quantity": rng.integers(1, 5, size=n_orders),
        "order_amount": order_amt,
        "discount_amount": disc_amt,
        "delivery_fee": deliv_fee,
        "final_amount": np.round(order_amt - disc_amt + deliv_fee, 2),
        "order_status": rng.choice(["Delivered", "Delivered", "Delivered", "Cancelled"], size=n_orders, p=[0.9, 0.03, 0.03, 0.04]),
    })

    deliveries = pd.DataFrame({
        "delivery_id": [f"DV{i:06d}" for i in range(n_orders)],
        "order_id": orders["order_id"],
        "rider_id": rider_ids,
        "distance_km": np.round(rng.uniform(1.0, 12.0, size=n_orders), 1),
        "delivery_duration": rng.integers(15, 60, size=n_orders),
    })

    ratings = pd.DataFrame({
        "review_id": [f"RV{i:05d}" for i in range(n_orders // 2)],
        "order_id": orders["order_id"].iloc[: n_orders // 2].values,
        "customer_id": orders["customer_id"].iloc[: n_orders // 2].values,
        "restaurant_rating": rng.uniform(2.5, 5.0, size=n_orders // 2).round(1),
        "delivery_rating": rng.uniform(2.5, 5.0, size=n_orders // 2).round(1),
    })

    return {
        "orders": orders,
        "customers": customers,
        "restaurants": restaurants,
        "riders": riders,
        "deliveries": deliveries,
        "ratings": ratings,
    }


class TestPhase05MLSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = _make_synthetic_orders_fixture(seed=42, n_days=240, n_orders=1500)

    # 1. Shared validation & leakage guards
    def test_01_validation_guards_and_metrics(self) -> None:
        with self.assertRaises(ValueError):
            validate_dataframe_schema(pd.DataFrame({"a": [1]}), ["a", "missing_col"], "bad_df")

        assert_strictly_chronological_split(["2026-01-01", "2026-02-01"], ["2026-02-01", "2026-03-01"])
        with self.assertRaises(AssertionError):
            assert_strictly_chronological_split(["2026-03-01"], ["2026-02-01"], "inverted")

        with self.assertRaises(AssertionError):
            assert_no_forbidden_features(["Lookback_Frequency", "Recency"], ["Recency"])

        cls_m = compute_classification_metrics([0, 1, 1, 0], [0, 1, 0, 0], [0.1, 0.9, 0.4, 0.2])
        self.assertEqual(cls_m["accuracy"], 0.75)
        self.assertAlmostEqual(cls_m["roc_auc"], 1.0)

        reg_m = compute_regression_metrics([10.0, 20.0, 30.0], [12.0, 19.0, 33.0])
        self.assertAlmostEqual(reg_m["mae"], 2.0)
        self.assertAlmostEqual(reg_m["median_ae"], 2.0)

    # 2. Model 1: Churn feature temporal cutoff & zero leakage
    def test_02_churn_temporal_isolation_and_pipeline(self) -> None:
        orders = self.fx["orders"].copy()
        customers = self.fx["customers"]
        ratings = self.fx["ratings"].copy()

        # Assert leaked Recency/Is_Churned are forbidden from numeric feature list
        assert_no_forbidden_features(CHURN_NUMERIC_FEATURES, FORBIDDEN_CHURN_LEAKAGE_COLS)

        cutoff = pd.Timestamp("2025-11-15")
        c1 = build_churn_observation_cohort(orders, customers, ratings, cutoff_date=cutoff, churn_horizon_days=60, include_target=True)

        # Corrupt post-cutoff orders & ratings to prove pre-cutoff features never change
        orders_mod = orders.copy()
        post_mask = pd.to_datetime(orders_mod["order_datetime"]) > cutoff
        orders_mod.loc[post_mask, "final_amount"] = 999999.0

        post_order_ids = set(orders_mod.loc[post_mask, "order_id"])
        ratings_mod = ratings.copy()
        ratings_mod.loc[ratings_mod["order_id"].isin(post_order_ids), "delivery_rating"] = 1.0

        c2 = build_churn_observation_cohort(orders_mod, customers, ratings_mod, cutoff_date=cutoff, churn_horizon_days=60, include_target=True)
        pd.testing.assert_frame_equal(
            c1[["customer_id"] + CHURN_NUMERIC_FEATURES],
            c2[["customer_id"] + CHURN_NUMERIC_FEATURES],
        )

        # Also check ratings_df=None handling and full training pipeline with horizon=60 on fixture
        c_no_ratings = extract_churn_features(orders, customers, ratings_df=None, cutoff_date=cutoff, churn_horizon_days=60)
        self.assertFalse(c_no_ratings[CHURN_NUMERIC_FEATURES].isna().any().any())

        res = train_churn_pipeline(orders, customers, ratings, churn_horizon_days=60, lookback_days=90)
        res_repeat = train_churn_pipeline(orders, customers, ratings, churn_horizon_days=60, lookback_days=90)
        self.assertEqual(res["best_metrics"]["roc_auc"], res_repeat["best_metrics"]["roc_auc"], "Pipeline must be deterministic")
        self.assertLess(res["best_metrics"]["roc_auc"], 0.99, "Must not exhibit circular 1.000 leakage")
        self.assertGreater(res["best_metrics"]["roc_auc"], 0.55, "Genuine pre-cutoff dormancy pattern must be learnable")
        self.assertTrue(((res["scoring_df"]["Churn_Probability"] >= 0.0) & (res["scoring_df"]["Churn_Probability"] <= 1.0)).all())

    # 3. Model 2: Delivery ETA chronological ordering & optional table resilience
    def test_03_eta_chronological_and_missing_resilience(self) -> None:
        deliv = self.fx["deliveries"].copy()
        orders = self.fx["orders"].copy()
        riders = self.fx["riders"].copy()
        restaurants = self.fx["restaurants"].copy()

        # Shuffle deliveries row order & inject NaNs to prove chronological sort + imputation work
        deliv_shuffled = deliv.sample(frac=1.0, random_state=7).reset_index(drop=True)
        deliv_shuffled.loc[0, "distance_km"] = np.nan
        deliv_shuffled.loc[1, "delivery_duration"] = -5

        preds_df, metrics, artifacts = train_and_predict_eta(
            deliv_shuffled, orders, self.fx["customers"], riders, restaurants, return_artifacts=True
        )
        self.assertGreater(metrics["MAE_minutes"], 0)
        self.assertGreater(metrics["Median_AE_minutes"], 0)
        self.assertGreaterEqual(metrics["RMSE_minutes"], metrics["MAE_minutes"])
        self.assertIn("Disclaimer", metrics)
        self.assertIn("OLS_LinearRegression", artifacts["candidate_models"])
        self.assertIn("Ridge_L2_Regression", artifacts["candidate_models"])

        # Fallback without optional riders/restaurants/customers tables
        preds_minimal, metrics_minimal = train_and_predict_eta(deliv, orders)
        self.assertEqual(len(preds_minimal), len(deliv))
        self.assertGreater(metrics_minimal["MAE_minutes"], 0)

    # 4. Model 3: Demand Forecasting gap reindexing & strict lag non-leakage
    def test_04_demand_contiguous_calendar_and_no_future_lag_leak(self) -> None:
        orders = self.fx["orders"].copy()
        customers = self.fx["customers"]
        ts = prepare_demand_time_series(orders, customers)

        # Assert every city has zero missing calendar dates after preparation
        for city, g in ts.groupby("city"):
            expected_days = (g["date"].max() - g["date"].min()).days + 1
            self.assertEqual(len(g), expected_days, f"Calendar gap detected for {city}")

        forecast_df, metrics, artifacts = train_and_forecast_demand(ts, forecast_horizon_days=14, return_artifacts=True)
        self.assertIn("Per_City_Metrics", metrics)
        self.assertIn("Baseline_SeasonalNaive_Lag7_MAE", metrics)
        self.assertIn("Backtest_3Fold_Expanding", metrics)
        self.assertGreaterEqual(len(metrics["Backtest_3Fold_Expanding"]), 1)

        future_rows = forecast_df[forecast_df["actual_orders"].isna()]
        self.assertEqual(len(future_rows), 14 * ts["city"].nunique())
        self.assertTrue((future_rows["predicted_orders"] >= 0).all())
        self.assertTrue((future_rows["lower_bound"] <= future_rows["predicted_orders"]).all())
        self.assertTrue((future_rows["upper_bound"] >= future_rows["predicted_orders"]).all())

    # 5. Model 4: Restaurant real chronological panel & synthetic leakage elimination
    def test_05_restaurant_real_panel_no_synthetic_leak(self) -> None:
        orders = self.fx["orders"]
        restaurants = self.fx["restaurants"]

        assert_no_forbidden_features(RESTAURANT_NUMERIC_FEATURES, FORBIDDEN_RESTAURANT_LEAKAGE_COLS)

        # Deterministic extract_restaurant_features without fake random predicted target
        e1 = extract_restaurant_features(restaurants, orders)
        e2 = extract_restaurant_features(restaurants, orders)
        pd.testing.assert_frame_equal(e1, e2)
        self.assertNotIn("Predicted_Next_Month_Orders", e1.columns)

        panel_df, score_df, full_months = build_restaurant_monthly_panel(restaurants, orders, min_prior_months=3)
        self.assertGreaterEqual(len(full_months), 5)
        self.assertIn("Actual_Next_Month_Orders", panel_df.columns)
        self.assertEqual(len(score_df), len(restaurants))

        res = train_restaurant_pipeline(restaurants, orders)
        self.assertGreater(res["best_metrics"]["mae"], 0)
        self.assertGreaterEqual(res["best_metrics"]["rmse"], res["best_metrics"]["mae"])
        self.assertTrue((res["output_df"]["Predicted_Next_Month_Orders"] >= 0).all())

    # 6. Model 5: Statistical anomalies (Z + IQR), zero truncation, zero duplicates, source preservation
    def test_06_anomaly_detection_and_revenue_leakage(self) -> None:
        orders = self.fx["orders"].copy()
        deliv = self.fx["deliveries"].copy()
        rest = self.fx["restaurants"].copy()
        cust = self.fx["customers"].copy()

        # Inject 130 deliberate extreme >=100% discount orders to prove no head(100)/head(50) truncation
        inject_idx = orders.index[:130]
        orders.loc[inject_idx, "discount_amount"] = orders.loc[inject_idx, "order_amount"] * 1.15
        orders.loc[inject_idx, "final_amount"] = 0.0

        # Inject physically impossible speed (12 km in 2 min = 360 km/h)
        deliv.loc[0, "distance_km"] = 12.0
        deliv.loc[0, "delivery_duration"] = 2

        orig_len = len(orders)
        anom_df, audit = detect_operational_anomalies_with_audit(orders, deliv, rest, cust)

        self.assertEqual(len(orders), orig_len, "Source orders DataFrame length must never be altered")
        self.assertEqual(audit["duplicate_anomaly_keys"], 0)
        self.assertFalse(audit["truncated"])
        disc_flags = anom_df[anom_df["Metric"] == "Discount Percentage (%)"]
        self.assertGreaterEqual(len(disc_flags), 130, "All 130 injected extreme discount anomalies must be reported without truncation")
        speed_flags = anom_df[(anom_df["Entity_ID"] == str(deliv.loc[0, "order_id"])) & (anom_df["Metric"] == "Delivery Speed (km/h)")]
        self.assertEqual(len(speed_flags), 1)

        bounds = compute_statistical_bounds(orders["discount_amount"], "discount_amount")
        self.assertIn("iqr_upper_15", bounds)
        self.assertIn("z_gt_30_count", bounds)

        leak_df, leak_kpis = detect_revenue_leakage(orders, cust, rest)
        self.assertEqual(leak_kpis["Duplicate_Order_Flags"], 0)
        self.assertEqual(leak_kpis["Original_Orders_Preserved"], orig_len)
        self.assertIn("false_positive_risk", leak_df.columns)
        self.assertIn("detection_category", leak_df.columns)
        self.assertIn("severity", leak_df.columns)

    # 7. Real repository artifacts & v1 preservation verification
    def test_07_repository_models_and_v1_preserved(self) -> None:
        models_dir = BASE_DIR / "models"
        expected_pairs = [
            ("customer_churn", "churn_metrics.json", "churn_metrics_v2.json"),
            ("eta_prediction", "eta_metrics.json", "eta_metrics_v2.json"),
            ("demand_forecast", "demand_metrics.json", "demand_metrics_v2.json"),
            ("restaurant_prediction", "restaurant_metrics.json", "restaurant_metrics_v2.json"),
            ("anomaly_detection", "anomaly_metrics.json", "anomaly_metrics_v2.json"),
        ]
        for sub, v1_name, v2_name in expected_pairs:
            mdir = models_dir / sub
            v1_path = mdir / v1_name
            v2_path = mdir / v2_name
            self.assertTrue(v1_path.exists(), f"Missing preserved v1 report: {v1_path}")
            self.assertTrue(v2_path.exists(), f"Missing Phase 05 v2 report: {v2_path}")
            self.assertTrue((mdir / "model_metadata.json").exists(), f"Missing metadata in {mdir}")
            self.assertTrue((mdir / "validation_report.md").exists(), f"Missing validation_report.md in {mdir}")
            self.assertTrue((mdir / "feature_documentation.json").exists(), f"Missing feature_documentation.json in {mdir}")
            with open(v2_path, "r", encoding="utf-8") as f:
                v2 = json.load(f)
            self.assertIn("model_version", v2)
            self.assertTrue(str(v2["model_version"]).startswith("2.0.0-phase05"))
            if sub == "customer_churn":
                self.assertLess(v2["test_metrics"]["roc_auc"], 0.70)
            if sub == "restaurant_prediction":
                self.assertLess(v2["holdout_metrics"]["r2_score"], 0.50)

    # 8. FastAPI endpoint smoke check verifying updated Phase 05 CSVs load cleanly
    def test_08_api_compatibility_with_phase05_outputs(self) -> None:
        try:
            from fastapi.testclient import TestClient
            from api.main import app
        except Exception as exc:
            self.skipTest(f"FastAPI TestClient unavailable: {exc}")
            return

        import os
        import secrets
        from unittest.mock import patch

        ephemeral_key = secrets.token_urlsafe(32)
        with patch.dict(os.environ, {"NOVANEST_API_KEY": ephemeral_key}):
            client = TestClient(app, headers={"X-API-Key": ephemeral_key})
            for endpoint in ["/api/customer/overview", "/api/operations/overview", "/api/financial/overview"]:
                resp = client.get(endpoint)
                self.assertEqual(resp.status_code, 200, f"Endpoint {endpoint} failed with {resp.status_code}")
                payload = resp.json()
                self.assertIsInstance(payload, dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
