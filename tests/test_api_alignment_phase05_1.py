"""
Phase 05.1 — API Data Contract & Business Logic Alignment Test Suite
====================================================================
Verifies FastAPI REST endpoints and loader against actual Phase 04 certified KPIs,
Phase 05 CSV outputs, honest unavailability / model readiness reporting, empty/missing CSV
resilience, and negative HTTP validation.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import api.main as api_main
from api.loader import _safe_read_csv, load_data


class TestPhase051ApiAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._ephemeral_key = secrets.token_urlsafe(32)
        cls._prev_api_key = os.environ.get("NOVANEST_API_KEY")
        os.environ["NOVANEST_API_KEY"] = cls._ephemeral_key
        load_data(force_reload=True)
        cls.client = TestClient(api_main.app, headers={"X-API-Key": cls._ephemeral_key})
        cls.orders = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "orders.csv")
        cls.orders_eng = pd.read_csv(PROJECT_ROOT / "datasets" / "engineered" / "orders_engineered.csv")
        cls.customers = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "customers.csv")
        cls.riders = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "riders.csv")
        cls.churn = pd.read_csv(PROJECT_ROOT / "datasets" / "engineered" / "customer_churn_predictions.csv")
        cls.forecasts = pd.read_csv(PROJECT_ROOT / "datasets" / "engineered" / "demand_forecasts.csv")
        cls.heatmap = pd.read_csv(PROJECT_ROOT / "datasets" / "engineered" / "demand_heatmap.csv")
        cls.anomalies = pd.read_csv(PROJECT_ROOT / "datasets" / "engineered" / "operational_anomalies.csv")
        cls.leakage = pd.read_csv(PROJECT_ROOT / "datasets" / "engineered" / "revenue_leakage.csv")
        cls.promotions = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "promotions.csv")
        cls.kpi_defs = json.loads(
            (PROJECT_ROOT / "datasets" / "analytics" / "kpi_definitions.json").read_text(encoding="utf-8")
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._prev_api_key is None:
            os.environ.pop("NOVANEST_API_KEY", None)
        else:
            os.environ["NOVANEST_API_KEY"] = cls._prev_api_key

    def test_01_overview_certified_kpis_parity(self) -> None:
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        kpis = payload["kpis"]

        non_cancelled = self.orders[self.orders["order_status"] != "Cancelled"]
        delivered = self.orders[self.orders["order_status"] == "Delivered"]
        eng_deliv = self.orders_eng[self.orders_eng["order_status"] == "Delivered"]

        expected_gmv = round(float(non_cancelled["order_amount"].sum()), 2)
        expected_net_rev = round(float(delivered["final_amount"].sum()), 2)
        expected_net_aov = round(expected_net_rev / len(delivered), 2)
        expected_profit = round(float(eng_deliv["estimated_profit"].sum()), 2)
        expected_margin = round((expected_profit / expected_net_rev) * 100.0, 2)

        self.assertEqual(kpis["total_gmv"], expected_gmv)
        self.assertEqual(kpis["net_platform_revenue"], expected_net_rev)
        self.assertEqual(kpis["avg_order_value"], expected_net_aov)
        self.assertEqual(kpis["realized_operating_profit"], expected_profit)
        self.assertEqual(kpis["contribution_margin_pct"], expected_margin)
        self.assertEqual(kpis["total_orders"], len(self.orders))
        self.assertEqual(kpis["delivered_orders"], len(delivered))

        # Verify city breakdown sums reconcile cleanly to non-cancelled GMV
        city_sum = round(sum(item["revenue"] for item in payload["city_breakdown"]), 2)
        self.assertAlmostEqual(city_sum, expected_gmv, delta=1.0)

        # Verify city filter
        resp_city = self.client.get("/api/overview?city=Chennai")
        self.assertEqual(resp_city.status_code, 200)
        city_kpis = resp_city.json()["kpis"]
        self.assertGreater(city_kpis["total_gmv"], 0)
        self.assertLess(city_kpis["total_gmv"], expected_gmv)

    def test_02_customer_overview_churn_distribution_parity(self) -> None:
        resp = self.client.get("/api/customer/overview")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()

        self.assertEqual(payload["churn_data_status"], "available")
        dist = payload["churn_distribution"]
        self.assertGreater(len(dist), 0)

        dist_map = {item["risk_level"]: item["count"] for item in dist}
        expected_counts = self.churn["Churn_Risk"].value_counts().to_dict()
        self.assertEqual(dist_map, expected_counts)

        expected_high = int((self.churn["Churn_Risk"] == "High Risk").sum())
        expected_high_pct = round(expected_high / len(self.churn) * 100.0, 2)
        self.assertEqual(payload["kpis"]["high_risk_customers"], expected_high)
        self.assertEqual(payload["kpis"]["high_churn_rate_pct"], expected_high_pct)

        # Net AOV certified parity
        delivered = self.orders[self.orders["order_status"] == "Delivered"]
        expected_net_aov = round(float(delivered["final_amount"].sum()) / len(delivered), 2)
        self.assertEqual(payload["kpis"]["avg_aov"], expected_net_aov)

    def test_03_customer_list_parity_and_no_fake_fallbacks(self) -> None:
        resp = self.client.get("/api/customer/list?limit=20")
        self.assertEqual(resp.status_code, 200)
        rows = resp.json()
        self.assertEqual(len(rows), 20)

        churn_lookup = self.churn.set_index("customer_id").to_dict("index")
        cust_lookup = self.customers.set_index("customer_id").to_dict("index")

        for item in rows:
            cid = item["customer_id"]
            self.assertEqual(item["customer_name"], cust_lookup[cid]["customer_name"])
            self.assertFalse(item["customer_name"].startswith("Customer #"))
            self.assertEqual(item["churn_risk"], churn_lookup[cid]["Churn_Risk"])
            self.assertAlmostEqual(
                item["churn_probability"],
                round(float(churn_lookup[cid]["Churn_Probability"]), 4),
                places=4,
            )
            self.assertEqual(item["churn_probability_status"], "available")

        # Partial missing churn predictions must return None + unavailable (never 0.15 / "Low")
        mock_data = {
            "customers": self.customers.head(3).copy(),
            "orders": self.orders.head(10).copy(),
            "customer_churn_predictions": pd.DataFrame(),
        }
        with patch("api.main.load_data", return_value=(mock_data, "MockEmptyChurn")):
            r_missing = self.client.get("/api/customer/list?limit=3")
            self.assertEqual(r_missing.status_code, 200)
            for item in r_missing.json():
                self.assertIsNone(item["churn_probability"])
                self.assertEqual(item["churn_probability_status"], "unavailable")
                self.assertIsNone(item["churn_risk"])
                self.assertEqual(item["churn_risk_status"], "unavailable")

    def test_04_operations_overview_real_forecasts_fleet_anomalies(self) -> None:
        resp = self.client.get("/api/operations/overview")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        kpis = payload["kpis"]

        self.assertEqual(kpis["total_deliveries"], len(self.orders))
        self.assertEqual(kpis["active_riders"], len(self.riders))
        self.assertEqual(kpis["anomalies_detected"], len(self.anomalies))

        # Demand forecast has both historical actuals > 0 and future horizon actuals == None with reason
        forecasts = payload["demand_forecast"]
        self.assertGreater(len(forecasts), 14)
        hist_points = [pt for pt in forecasts if pt["has_actual"]]
        future_points = [pt for pt in forecasts if not pt["has_actual"]]
        self.assertGreater(len(hist_points), 0)
        self.assertGreater(len(future_points), 0)
        for pt in hist_points:
            self.assertIsNotNone(pt["actual"])
            self.assertGreater(pt["actual"], 0)
            self.assertGreater(pt["forecast"], 0)
        for pt in future_points:
            self.assertIsNone(pt["actual"])
            self.assertIsNotNone(pt["missing_actual_reason"])
            self.assertGreater(pt["forecast"], 0)

        # Demand heatmap matches CSV
        heat_cities = {h["city"] for h in payload["demand_heatmap"]}
        self.assertEqual(heat_cities, set(self.heatmap["City"]))

        # Rider allocation uses real fleet counts and avoids fake deficit=10
        rider_counts_csv = self.riders["city"].value_counts().to_dict()
        alloc_map = {r["city"]: r for r in payload["rider_allocation"]}
        for city, count in rider_counts_csv.items():
            self.assertEqual(alloc_map[city]["current_riders"], int(count))
            self.assertIsNone(alloc_map[city]["recommended_riders"])
            self.assertIsNone(alloc_map[city]["deficit"])

        # Anomalies are genuine CSV rows, zero placeholders
        anomalies = payload["anomalies"]
        self.assertGreater(len(anomalies), 0)
        valid_ids = set(self.anomalies["Entity_ID"].astype(str))
        for a in anomalies:
            self.assertIn(a["id"], valid_ids)
            self.assertNotEqual(a["id"], "ANM-01")
            self.assertNotIn("East Hub", a["description"])
            self.assertIs(a["is_confirmed_incident"], False)

    def test_05_financial_overview_certified_kpis_leakage_and_promotions(self) -> None:
        resp = self.client.get("/api/financial/overview")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        kpis = payload["kpis"]
        ue = payload["unit_economics"]

        non_cancelled = self.orders[self.orders["order_status"] != "Cancelled"]
        delivered = self.orders[self.orders["order_status"] == "Delivered"]
        eng_deliv = self.orders_eng[self.orders_eng["order_status"] == "Delivered"]

        exp_gmv = round(float(non_cancelled["order_amount"].sum()), 2)
        exp_net_rev = round(float(delivered["final_amount"].sum()), 2)
        exp_comm = round(float(eng_deliv["commission_revenue"].sum()), 2)
        exp_profit = round(float(eng_deliv["estimated_profit"].sum()), 2)
        exp_margin = round((exp_profit / exp_net_rev) * 100.0, 2)
        exp_net_aov = round(exp_net_rev / len(delivered), 2)
        exp_leakage = round(float(self.leakage["potential_leakage_amount"].sum()), 2)

        self.assertEqual(kpis["gross_merchandise_value"], exp_gmv)
        self.assertEqual(kpis["net_platform_revenue"], exp_net_rev)
        self.assertEqual(kpis["commission_revenue"], exp_comm)
        self.assertEqual(kpis["realized_operating_profit"], exp_profit)
        self.assertEqual(kpis["profit_margin_pct"], exp_margin)
        self.assertEqual(kpis["total_potential_risk_exposure"], exp_leakage)
        self.assertEqual(kpis["total_revenue_leakage"], exp_leakage)
        self.assertIs(kpis["leakage_confirmed"], False)

        # Unit economics strictly use Delivered denominator (47,994)
        self.assertEqual(ue["denominator_orders"], len(delivered))
        self.assertEqual(ue["aov"], exp_net_aov)

        # Leakage breakdown matches CSV categories & sums exactly
        cat_sum = round(sum(item["amount"] for item in payload["revenue_leakage"]), 2)
        self.assertAlmostEqual(cat_sum, exp_leakage, places=2)
        for item in payload["revenue_leakage"]:
            self.assertIs(item["is_confirmed_loss"], False)
            self.assertEqual(item["classification"], "Investigation Candidate")
            self.assertNotEqual(item["recommended_action"], "Cap maximum promo subsidy")

        # Promotions use real promotions.csv fields without fake redemptions/ROI
        promos = payload["promotions"]
        self.assertGreater(len(promos), 0)
        valid_pids = set(self.promotions["promo_id"].astype(str))
        for p in promos:
            self.assertIn(p["promo_id"], valid_pids)
            self.assertIsNone(p["redemptions"])
            self.assertIsNone(p["gmv_driven"])
            self.assertIsNone(p["roi_multiple"])
            self.assertIn("Unavailable", p["attribution_status"])

    def test_06_decision_actions_honest_confidence(self) -> None:
        resp = self.client.get("/api/decision/actions")
        self.assertEqual(resp.status_code, 200)
        actions = resp.json()
        self.assertGreater(len(actions), 0)

        for act in actions:
            self.assertIsNone(act["confidence_pct"])
            self.assertIn("Unavailable", act["confidence_status"])
            self.assertTrue(act["model_readiness"])
            self.assertTrue(act["model_evaluation_metric"])
            self.assertIs(act["is_confirmed_loss"], False)

    def test_07_empty_and_missing_csv_resilience(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_file = Path(tmpdir) / "does_not_exist.csv"
            empty_file = Path(tmpdir) / "empty.csv"
            empty_file.write_text("", encoding="utf-8")
            self.assertTrue(_safe_read_csv(missing_file).empty)
            self.assertTrue(_safe_read_csv(empty_file).empty)

        empty_store = {
            k: pd.DataFrame()
            for k in [
                "customers",
                "restaurants",
                "menu_items",
                "riders",
                "orders",
                "payments",
                "deliveries",
                "app_events",
                "promotions",
                "ratings_reviews",
                "orders_engineered",
                "customer_churn_predictions",
                "restaurant_predictions",
                "demand_forecasts",
                "demand_heatmap",
                "eta_predictions",
                "rider_allocation",
                "operational_anomalies",
                "revenue_leakage",
                "operational_alerts",
            ]
        }
        with patch("api.main.load_data", return_value=(empty_store, "EmptyMock")):
            r_ov = self.client.get("/api/overview")
            self.assertEqual(r_ov.status_code, 200)
            self.assertEqual(r_ov.json()["kpis"]["total_gmv"], 0.0)
            self.assertEqual(r_ov.json()["kpis"]["net_platform_revenue"], 0.0)

            r_cust = self.client.get("/api/customer/overview")
            self.assertEqual(r_cust.status_code, 200)
            self.assertEqual(r_cust.json()["churn_distribution"], [])
            self.assertEqual(r_cust.json()["churn_data_status"], "unavailable")

            r_list = self.client.get("/api/customer/list?limit=10")
            self.assertEqual(r_list.status_code, 200)
            self.assertEqual(r_list.json(), [])

            r_ops = self.client.get("/api/operations/overview")
            self.assertEqual(r_ops.status_code, 200)
            self.assertEqual(r_ops.json()["kpis"]["avg_duration_mins"], 0.0)
            self.assertEqual(r_ops.json()["kpis"]["ontime_rate_pct"], 0.0)
            self.assertEqual(r_ops.json()["anomalies"], [])

            r_fin = self.client.get("/api/financial/overview")
            self.assertEqual(r_fin.status_code, 200)
            self.assertEqual(r_fin.json()["kpis"]["profit_margin_pct"], 0.0)
            self.assertEqual(r_fin.json()["promotions"], [])

            r_dec = self.client.get("/api/decision/actions")
            self.assertEqual(r_dec.status_code, 200)
            self.assertEqual(r_dec.json(), [])

    def test_08_invalid_http_requests(self) -> None:
        self.assertEqual(self.client.get("/api/customer/list?limit=abc").status_code, 422)
        self.assertEqual(self.client.get("/api/customer/list?limit=-5").status_code, 422)
        self.assertEqual(self.client.get("/api/customer/list?limit=0").status_code, 422)
        self.assertEqual(self.client.get("/api/customer/360/UNKNOWN_CUSTOMER_XYZ").status_code, 404)
        self.assertEqual(self.client.post("/api/ai/ask", json={"question": "   "}).status_code, 400)
        self.assertEqual(self.client.post("/api/ai/ask", json={}).status_code, 422)
        self.assertEqual(self.client.delete("/api/overview").status_code, 405)
        self.assertEqual(self.client.get("/api/does_not_exist").status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)

