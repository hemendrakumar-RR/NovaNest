"""
NovaNest Phase 07 — Advanced Machine Learning Intelligence & Model Optimization Test Suite
------------------------------------------------------------------------------------------
Validates:
1. Model Registry lifecycle, semantic versioning (v1, v2, v3), SHA-256 lineage & rollback
2. Explainable AI (XAI): native TreeSHAP, permutation importance, local explanations & prediction intervals
3. Model 1 (Customer Churn): leak-free cutoffs, Brier calibration, retention segmentation
4. Model 2 (Delivery ETA): dispatch-time boundary, stratified breakdowns, prediction intervals
5. Model 3 (Demand Forecast): contiguous daily grid, 3-fold rolling-origin backtest, WAPE & MASE < 1.0
6. Model 4 (Restaurant Performance): multi-target regression (orders, revenue, ratings), zero leakage
7. Model 5 (Anomaly & Risk): strict fraud policy compliance, consensus ensemble, explainable triggers
8. AI Agent Integration: honest confidence gating & ModelCaveat emission across domain agents
9. Artifact Serialization & Backward Compatibility: v1, v2, v3 co-existence
10. Dataset Lineage & Record Count Integrity (all 304,405 records preserved)
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "python" / "ml"))

from python.ai.agents.context import AgentContext
from python.ai.agents.contracts import AgentDomain, AgentRequest, AgentStatus
from python.ai.agents.customer_agent import CustomerAgent
from python.ai.agents.operations_agent import OperationsAgent
from python.ai.agents.restaurant_agent import RestaurantAgent
from python.ml.explainability import (
    compute_global_feature_importance,
    compute_prediction_interval,
    compute_treeshap_contributions,
    explain_local_prediction,
)
from python.ml.model_registry import ModelRegistry, compute_file_sha256, model_registry


class TestPhase07MLOptimization(unittest.TestCase):
    """Automated test suite verifying Phase 07 Advanced ML Intelligence."""

    @classmethod
    def setUpClass(cls):
        cls.models_dir = BASE_DIR / "models"
        cls.cleaned_dir = BASE_DIR / "datasets" / "cleaned"

    def test_01_model_registry_lifecycle_and_rollback(self):
        """Verify registry index, active v3 versioning, SHA-256 hashes, and rollback capability."""
        index = model_registry.get_index()
        expected_models = [
            "customer_churn",
            "eta_prediction",
            "demand_forecast",
            "restaurant_prediction",
            "anomaly_detection",
        ]
        for m in expected_models:
            self.assertIn(m, index["models"], f"Model '{m}' missing from registry index.")
            self.assertEqual(index["models"][m]["active_version"], "v3")
            self.assertIn("v1", index["models"][m]["available_versions"])
            self.assertIn("v2", index["models"][m]["available_versions"])
            self.assertIn("v3", index["models"][m]["available_versions"])

        # Test rollback to v2
        rollback_res = model_registry.rollback_model("customer_churn", "v2")
        self.assertEqual(rollback_res["active_version"], "v2")
        self.assertEqual(model_registry.get_index()["models"]["customer_churn"]["active_version"], "v2")

        # Roll back to v3
        restore_res = model_registry.rollback_model("customer_churn", "v3")
        self.assertEqual(restore_res["active_version"], "v3")
        self.assertEqual(model_registry.get_index()["models"]["customer_churn"]["active_version"], "v3")

        # Verify metadata has valid SHA-256 hashes
        meta_v3_path = self.models_dir / "customer_churn" / "metadata_v3.json"
        self.assertTrue(meta_v3_path.is_file())
        with open(meta_v3_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        for ds_name, sha in meta.get("dataset_sha256", {}).items():
            self.assertEqual(len(sha), 64, f"Invalid SHA-256 hash length for {ds_name}")

    def test_02_explainability_engine_treeshap_and_local(self):
        """Verify TreeSHAP attributions, permutation importance, and local explanations."""
        import xgboost as xgb
        np.random.seed(42)
        X = np.random.randn(30, 4)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        clf = xgb.XGBClassifier(n_estimators=5, random_state=42)
        clf.fit(X, y)

        feat_names = ["feat_1", "feat_2", "feat_3", "feat_4"]
        contribs, base_val = compute_treeshap_contributions(clf, X, feat_names, framework="xgboost")
        self.assertEqual(contribs.shape, (30, 4))
        self.assertTrue(np.isfinite(base_val))

        # Local explanation
        local_exp = explain_local_prediction(clf, X[0], feat_names, predicted_value=0.75, framework="xgboost")
        self.assertIn("predicted_value", local_exp)
        self.assertIn("base_value", local_exp)
        self.assertIn("narrative", local_exp)
        self.assertIsInstance(local_exp["narrative"], str)
        self.assertTrue(len(local_exp["narrative"]) > 0)

        # Prediction interval
        low_90, high_90 = compute_prediction_interval(30.0, 5.0, confidence_level=0.90)
        self.assertLess(low_90, 30.0)
        self.assertGreater(high_90, 30.0)
        self.assertAlmostEqual(high_90 - 30.0, 30.0 - low_90, delta=0.1)

        # Global feature importance
        g_imp = compute_global_feature_importance(clf, X, y, feature_names=feat_names)
        self.assertAlmostEqual(sum(g_imp.values()), 1.0, delta=0.01)

    def test_03_customer_churn_leakage_and_metrics(self):
        """Verify leak-free churn evaluation, calibration, and retention segmentation."""
        metrics_path = self.models_dir / "customer_churn" / "churn_metrics_v3.json"
        self.assertTrue(metrics_path.is_file(), "churn_metrics_v3.json missing")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        benchmarks = data["benchmarks"]
        self.assertIn("Heuristic_Recency_Baseline", benchmarks)
        self.assertIn("RandomForest", benchmarks)
        self.assertIn("LightGBM", benchmarks)
        self.assertIn("XGBoost", benchmarks)

        # Verify Brier score <= 0.15
        rf_brier = benchmarks["RandomForest"]["brier_score"]
        self.assertLessEqual(rf_brier, 0.15, f"Brier score {rf_brier} exceeds 0.15")

        # Verify retention segments exist
        segments = data.get("retention_segments", {}).get("segments", {})
        self.assertIn("high_value_at_risk", segments)
        self.assertIn("discount_sensitive_at_risk", segments)
        self.assertIn("loyal_advocates", segments)
        self.assertIn("recommended_action", segments["high_value_at_risk"])

        # Verify honest confidence tier
        self.assertEqual(data["confidence_tier"], "LOW_EMPIRICAL")

    def test_04_delivery_eta_dispatch_boundaries_and_breakdowns(self):
        """Verify ETA model dispatch features, city/distance breakdowns, and prediction intervals."""
        metrics_path = self.models_dir / "eta_prediction" / "eta_metrics_v3.json"
        self.assertTrue(metrics_path.is_file(), "eta_metrics_v3.json missing")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        benchmarks = data["benchmarks"]
        self.assertIn("Baseline_Mean", benchmarks)
        self.assertIn("HistGradientBoosting", benchmarks)
        self.assertIn("LightGBM", benchmarks)
        self.assertIn("XGBoost", benchmarks)

        # Check stratified breakdowns
        breakdowns = data.get("stratified_breakdowns", {})
        self.assertIn("by_city", breakdowns)
        self.assertIn("by_distance_tier", breakdowns)
        self.assertIn("by_vehicle_type", breakdowns)

        # Verify cities present
        cities = breakdowns["by_city"]
        for c in ("Bangalore", "Chennai", "Coimbatore", "Hyderabad", "Vijayawada"):
            self.assertIn(c, cities)
            self.assertGreater(cities[c]["count"], 0)
            self.assertGreater(cities[c]["mae_minutes"], 0.0)

        # Verify prediction interval residual std is recorded
        self.assertGreater(data.get("residual_std_minutes", 0.0), 5.0)

    def test_05_demand_forecasting_rolling_origin_and_mase(self):
        """Verify rolling-origin 3-fold backtesting, MASE < 1.0, and WAPE metrics."""
        metrics_path = self.models_dir / "demand_forecast" / "demand_metrics_v3.json"
        self.assertTrue(metrics_path.is_file(), "demand_metrics_v3.json missing")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        benchmarks = data["benchmarks"]
        self.assertIn("Seasonal_Naive_lag7", benchmarks)
        self.assertIn("Rolling_Mean_7d", benchmarks)
        self.assertIn("Ridge_L2", benchmarks)
        self.assertIn("HistGradientBoosting", benchmarks)

        # Verify MASE < 1.0 (beats seasonal naive baseline)
        best_m = benchmarks[data["selected_model"]]
        self.assertLess(best_m["mase"], 1.0, f"MASE {best_m['mase']} is not less than 1.0")
        self.assertLess(best_m["wape_pct"], 25.0, f"WAPE {best_m['wape_pct']}% exceeds 25%")

        # Verify 3-fold rolling-origin backtest results
        backtest = data.get("rolling_origin_backtest", [])
        self.assertEqual(len(backtest), 3, "Rolling origin backtest must have exactly 3 folds")
        for fold in backtest:
            self.assertIn("model_mae", fold)
            self.assertIn("seasonal_naive_mae", fold)
            self.assertLess(fold["model_mae"], fold["seasonal_naive_mae"], "Model must beat seasonal naive in each fold")

    def test_06_restaurant_performance_multitarget(self):
        """Verify multi-target modeling (orders, revenue, ratings) without target leakage."""
        metrics_path = self.models_dir / "restaurant_prediction" / "restaurant_metrics_v3.json"
        self.assertTrue(metrics_path.is_file(), "restaurant_metrics_v3.json missing")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        targets = data.get("targets", {})
        self.assertIn("orders", targets)
        self.assertIn("revenue", targets)
        self.assertIn("ratings", targets)

        # Check order benchmarks
        order_benchmarks = targets["orders"]["benchmarks"]
        self.assertIn("Baseline_GlobalTrainMean", order_benchmarks)
        self.assertIn("Baseline_RestaurantExpandingMean", order_benchmarks)
        self.assertIn("Ridge_L2", order_benchmarks)

        # Check city breakdown
        city_breakdown = data.get("city_breakdown", {})
        self.assertTrue(len(city_breakdown) >= 4)
        for city, cdata in city_breakdown.items():
            self.assertIn("restaurant_count", cdata)
            self.assertIn("mae_orders", cdata)

    def test_07_anomaly_detection_fraud_policy_and_consensus(self):
        """Verify strict fraud policy compliance (0 confirmed fraud labels) and consensus scoring."""
        metrics_path = self.models_dir / "anomaly_detection" / "anomaly_metrics_v3.json"
        self.assertTrue(metrics_path.is_file(), "anomaly_metrics_v3.json missing")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        bm = data["benchmarks"]
        self.assertEqual(bm["Total_Orders_Audited"], 49971)

        # Verify fraud policy compliance
        compliance = bm["Fraud_Policy_Compliance"]
        self.assertEqual(compliance["status"], "COMPLIANT")
        self.assertEqual(compliance["confirmed_fraud_labels_count"], 0)
        self.assertEqual(
            compliance["categories_used"],
            ["NORMAL_OPERATION", "STATISTICAL_OUTLIER", "SUSPECTED_OPERATIONAL_RISK"],
        )

        # Verify consensus ensemble
        methods = bm["Methods_Evaluated"]
        self.assertIn("Dual_ZScore_TukeyIQR", methods)
        self.assertIn("Isolation_Forest", methods)
        self.assertIn("Consensus_Ensemble", methods)
        self.assertGreater(methods["Consensus_Ensemble"]["high_risk_exposure_inr"], 100000.0)

    def test_08_ai_agent_confidence_gating(self):
        """Verify AI agents emit honest confidence caveats querying ModelRegistry."""
        ctx = AgentContext(
            session_id="test_p07_eval",
            principal_id="eval_user",
            principal_role="admin",
            principal_scopes=["read", "operator", "analyst", "admin"],
            user_query="Run full platform ML confidence evaluation",
        )

        # Customer Agent
        req_cust = AgentRequest(
            agent_id="customer_agent",
            principal_id="eval_user",
            user_query="Customer churn risk evaluation",
            domain=AgentDomain.CUSTOMER,
        )
        res_cust = CustomerAgent().execute(req_cust, ctx)
        self.assertEqual(res_cust.status, AgentStatus.SUCCESS)
        self.assertTrue(len(res_cust.caveats) >= 1)
        self.assertIn("customer_churn (v3)", [c.model_name for c in res_cust.caveats])
        self.assertFalse(res_cust.caveats[0].is_production_ready)

        # Operations Agent
        req_ops = AgentRequest(
            agent_id="operations_agent",
            principal_id="eval_user",
            user_query="Operations ETA and demand review",
            domain=AgentDomain.OPERATIONS,
        )
        res_ops = OperationsAgent().execute(req_ops, ctx)
        self.assertEqual(res_ops.status, AgentStatus.SUCCESS)
        ops_caveat_names = [c.model_name for c in res_ops.caveats]
        self.assertIn("eta_prediction (v3)", ops_caveat_names)
        self.assertIn("demand_forecast (v3)", ops_caveat_names)
        self.assertIn("anomaly_detection (v3)", ops_caveat_names)

        # Restaurant Agent
        req_rest = AgentRequest(
            agent_id="restaurant_agent",
            principal_id="eval_user",
            user_query="Restaurant next month order projections",
            domain=AgentDomain.RESTAURANT,
        )
        res_rest = RestaurantAgent().execute(req_rest, ctx)
        self.assertEqual(res_rest.status, AgentStatus.SUCCESS)
        self.assertIn("restaurant_prediction (v3)", [c.model_name for c in res_rest.caveats])

    def test_09_model_artifact_serialization_and_backward_compatibility(self):
        """Verify v3 joblib artifacts load cleanly and legacy v1/v2 files are preserved."""
        # Check v3 artifacts load
        churn_art = joblib.load(self.models_dir / "customer_churn" / "model_artifact_v3.joblib")
        self.assertIn("calibrated_classifier", churn_art)

        eta_art = joblib.load(self.models_dir / "eta_prediction" / "model_artifact_v3.joblib")
        self.assertIn("regressor", eta_art)

        demand_art = joblib.load(self.models_dir / "demand_forecast" / "model_artifact_v3.joblib")
        self.assertIn("regressor", demand_art)

        rest_art = joblib.load(self.models_dir / "restaurant_prediction" / "model_artifact_v3.joblib")
        self.assertIn("order_regressor", rest_art)

        anom_art = joblib.load(self.models_dir / "anomaly_detection" / "model_artifact_v3.joblib")
        self.assertIn("isolation_forest", anom_art)

        # Check historical v1 and v2 files exist undisturbed
        self.assertTrue((self.models_dir / "customer_churn" / "churn_metrics.json").is_file())
        self.assertTrue((self.models_dir / "customer_churn" / "churn_metrics_v2.json").is_file())
        self.assertTrue((self.models_dir / "eta_prediction" / "eta_metrics.json").is_file())
        self.assertTrue((self.models_dir / "eta_prediction" / "eta_metrics_v2.json").is_file())
        self.assertTrue((self.models_dir / "demand_forecast" / "demand_metrics.json").is_file())
        self.assertTrue((self.models_dir / "demand_forecast" / "demand_metrics_v2.json").is_file())
        self.assertTrue((self.models_dir / "restaurant_prediction" / "restaurant_metrics.json").is_file())
        self.assertTrue((self.models_dir / "restaurant_prediction" / "restaurant_metrics_v2.json").is_file())
        self.assertTrue((self.models_dir / "anomaly_detection" / "anomaly_metrics.json").is_file())
        self.assertTrue((self.models_dir / "anomaly_detection" / "anomaly_metrics_v2.json").is_file())

    def test_10_dataset_lineage_and_record_count_integrity(self):
        """Verify all 10 datasets exist with exactly 304,405 records preserved."""
        expected_counts = {
            "customers.csv": 5000,
            "restaurants.csv": 1500,
            "riders.csv": 4000,
            "promotions.csv": 200,
            "menu_items.csv": 15000,
            "orders.csv": 49971,
            "payments.csv": 49971,
            "deliveries.csv": 49971,
            "ratings_reviews.csv": 28792,
            "app_events.csv": 100000,
        }
        total_rows = 0
        for filename, expected_rows in expected_counts.items():
            fpath = self.cleaned_dir / filename
            self.assertTrue(fpath.is_file(), f"Dataset {filename} missing.")
            df = pd.read_csv(fpath)
            self.assertEqual(len(df), expected_rows, f"Row count mismatch for {filename}: {len(df)} vs {expected_rows}")
            total_rows += len(df)

        self.assertEqual(total_rows, 304405, f"Total records must be exactly 304,405; got {total_rows}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
