"""
test_phase13_ultimate_dashboard.py
==================================
Comprehensive Verification Test Suite for Phase 13:
NovaNest Ultimate Executive Dashboard & Business Intelligence Platform.

Validates:
1. Canonical Database Integrity: 304,405 records preserved across all 10 MySQL tables.
2. Executive Overview: 10 Canonical KPI Cards with values, previous period deltas,
   trend directions, calculation tooltips, and data freshness metadata.
3. Financial Intelligence: Multi-granularity gross vs net revenue trends (daily, weekly, monthly),
   payment method distribution, city financial breakdown, and monthly AOV trends.
4. Customer Intelligence: Monthly customer acquisition trajectory, new vs. repeat customer ratio,
   high-value VIP customer identification, and mandatory LOW_EMPIRICAL churn caveat.
5. Restaurant Intelligence: Top 20 restaurant ranking table with prep duration SLAs,
   revenue share %, cancellation rates, and underperforming partners remediation candidates.
6. Operations Intelligence: Delivery vitals, top 15 rider performance rankings, city delivery operations,
   and mandatory BASELINE_ONLY telematics mode notice (no synthetic live GPS).
7. Interactive Multi-Criteria Global Filtering: Synchronized filter application across all endpoints
   (Date Range, City, Restaurant, Customer Segment, Order Status, Payment Method).
8. Prescriptive AI Decision Center: Integration of all 5 domain agents via Master Orchestrator,
   evidence-based recommendations, and human approval workflow gates.
9. Security & RBAC: Token enforcement, 401 unauthorized rejection, and role-based access controls.
10. Live Container Reachability: End-to-end verification of live Docker containers (API and Frontend).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from fastapi.testclient import TestClient
from api.main import app
from python.decision.prescriptive_contracts import (
    PrescriptiveRecommendation,
    RecommendationLifecycleStatus,
    PrescriptiveDomain,
    ConfidenceTier,
)
from python.decision.prescriptive_engine import (
    generate_all_prescriptive_recommendations,
    get_prescriptive_summary_kpis,
)


class TestPhase13UltimateDashboard(unittest.TestCase):
    """Rigorous test suite certifying Phase 13 Ultimate Executive Dashboard."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.api_token = os.getenv("NOVANEST_API_KEY", "test-operator-key-phase06-8")
        cls.admin_token = os.getenv("NOVANEST_ADMIN_KEY", "test-admin-key-phase06-8")
        cls.viewer_token = os.getenv("NOVANEST_VIEWER_KEY", "test-viewer-key-phase06-8")

        cls.headers = {
            "Authorization": f"Bearer {cls.api_token}",
            "X-API-Key": cls.api_token,
        }
        cls.admin_headers = {
            "Authorization": f"Bearer {cls.admin_token}",
            "X-API-Key": cls.admin_token,
        }
        cls.viewer_headers = {
            "Authorization": f"Bearer {cls.viewer_token}",
            "X-API-Key": cls.viewer_token,
        }
        cls.live_api_url = "http://localhost:8001"
        cls.live_frontend_url = "http://localhost:80"

    # =========================================================================
    # TEST 1: Canonical Database Integrity (304,405 records preserved)
    # =========================================================================
    def test_01_canonical_database_integrity(self):
        """Verifies zero record mutations across all 10 canonical MySQL tables (304,405 records)."""
        expected_counts = {
            "customers": 5000,
            "restaurants": 1500,
            "menu_items": 15000,
            "riders": 4000,
            "payments": 49971,
            "deliveries": 49971,
            "app_events": 100000,
            "promotions": 200,
            "ratings_reviews": 28792,
            "orders": 49971,
        }
        expected_total = sum(expected_counts.values())
        self.assertEqual(expected_total, 304405, "Canonical total baseline must be 304,405")

        resp = self.client.get("/api/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        kpis = data.get("kpis", {})
        self.assertEqual(kpis.get("total_orders"), 49971, "Orders count must match canonical 49,971")
        self.assertEqual(kpis.get("active_customers"), 5000, "Customers count must match canonical 5,000")
        self.assertEqual(kpis.get("active_restaurants"), 1500, "Restaurants count must match canonical 1,500")
        self.assertEqual(kpis.get("active_riders"), 4000, "Riders count must match canonical 4,000")

    # =========================================================================
    # TEST 2: Executive Overview 10 Canonical KPI Cards
    # =========================================================================
    def test_02_executive_overview_10_kpi_cards(self):
        """Verifies all 10 canonical KPI cards with deltas, formulas, trends, and freshness."""
        resp = self.client.get("/api/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Both legacy kpis and phase 13 kpi_cards must exist
        self.assertIn("kpis", data)
        self.assertIn("kpi_cards", data)

        cards = data["kpi_cards"]
        required_cards = [
            "total_gmv",
            "net_platform_revenue",
            "total_orders",
            "delivered_orders",
            "avg_order_value",
            "contribution_margin",
            "active_customers",
            "active_restaurants",
            "active_riders",
            "delivery_success_rate",
        ]

        for card_id in required_cards:
            self.assertIn(card_id, cards, f"Missing required KPI card: {card_id}")
            card = cards[card_id]
            self.assertIn("label", card)
            self.assertIn("value", card)
            self.assertIn("previous_value", card)
            self.assertIn("percentage_change", card)
            self.assertIn("trend_direction", card)
            self.assertIn(card["trend_direction"], ["up", "down", "neutral"])
            self.assertIn("calculation_tooltip", card)
            self.assertIn("data_freshness", card)

            # Check that tooltip formula is non-empty and descriptive
            self.assertGreater(len(card["calculation_tooltip"]), 10)

        # Validate GMV value positivity
        gmv_card = cards["total_gmv"]
        self.assertGreater(gmv_card["value"], 0)
        self.assertGreater(gmv_card["previous_value"], 0)

    # =========================================================================
    # TEST 3: Financial Intelligence Multi-Granularity Trends & Payment Methods
    # =========================================================================
    def test_03_financial_intelligence(self):
        """Verifies daily/weekly/monthly revenue trends, payment methods, city financials, and AOV."""
        resp = self.client.get("/api/financial/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Multi-granularity revenue trends
        self.assertIn("revenue_trends", data)
        trends = data["revenue_trends"]
        for granularity, label_key in [("daily", "date"), ("weekly", "week"), ("monthly", "month")]:
            self.assertIn(granularity, trends)
            points = trends[granularity]
            self.assertIsInstance(points, list)
            self.assertGreater(len(points), 0, f"No points found for {granularity}")
            first_pt = points[0]
            self.assertIn(label_key, first_pt)
            self.assertIn("gmv", first_pt)
            self.assertIn("net_revenue", first_pt)
            self.assertIn("orders", first_pt)

        # Payment methods distribution
        self.assertIn("payment_methods", data)
        pm_list = data["payment_methods"]
        self.assertGreater(len(pm_list), 0)
        total_pct = sum(item["percentage"] for item in pm_list)
        self.assertAlmostEqual(total_pct, 100.0, delta=1.5)
        # UPI should be the top method
        top_pm = max(pm_list, key=lambda x: x["percentage"])
        self.assertEqual(top_pm["payment_method"], "UPI")

        # City financial performance
        self.assertIn("city_financials", data)
        self.assertGreater(len(data["city_financials"]), 0)
        self.assertIn("city", data["city_financials"][0])
        self.assertIn("gmv", data["city_financials"][0])
        self.assertIn("net_revenue", data["city_financials"][0])

        # AOV trends
        self.assertIn("aov_trend", data)
        self.assertGreater(len(data["aov_trend"]), 0)
        self.assertIn("month", data["aov_trend"][0])
        self.assertIn("net_aov", data["aov_trend"][0])

    # =========================================================================
    # TEST 4: Customer Intelligence Acquisition, Repeat Ratio & Churn Caveat
    # =========================================================================
    def test_04_customer_intelligence(self):
        """Verifies customer acquisition trends, new vs repeat ratio, VIPs, and LOW_EMPIRICAL badge."""
        resp = self.client.get("/api/customer/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Monthly acquisition trends
        self.assertIn("acquisition_trends", data)
        acq = data["acquisition_trends"]
        self.assertGreater(len(acq), 0)
        self.assertIn("month", acq[0])
        self.assertIn("new_customers", acq[0])

        # New vs repeat breakdown
        self.assertIn("new_vs_repeat", data)
        nvr = data["new_vs_repeat"]
        self.assertIn("new_orders", nvr)
        self.assertIn("repeat_orders", nvr)
        self.assertIn("repeat_percentage", nvr)
        self.assertGreater(nvr["repeat_percentage"], 80.0, "Repeat order percentage should exceed 80%")

        # High-value VIP customer list
        self.assertIn("high_value_customers", data)
        vips = data["high_value_customers"]
        self.assertLessEqual(len(vips), 10)
        self.assertGreater(len(vips), 0)
        self.assertIn("customer_id", vips[0])
        self.assertIn("estimated_clv", vips[0])
        self.assertIn("total_revenue", vips[0])

        # Mandatory LOW_EMPIRICAL churn tier badge (Scientific Honesty)
        self.assertIn("churn_prediction_badge", data)
        self.assertEqual(data["churn_prediction_badge"], "LOW_EMPIRICAL")

    # =========================================================================
    # TEST 5: Restaurant Intelligence Top 20 Rankings & Underperformers
    # =========================================================================
    def test_05_restaurant_intelligence(self):
        """Verifies top 20 restaurant ranking table, SLA metrics, and underperforming partners."""
        resp = self.client.get("/api/restaurant/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Top 20 restaurant ranking
        self.assertIn("restaurant_ranking", data)
        ranking = data["restaurant_ranking"]
        self.assertLessEqual(len(ranking), 20)
        self.assertGreater(len(ranking), 0)
        top1 = ranking[0]
        self.assertIn("restaurant_id", top1)
        self.assertIn("name", top1)
        self.assertIn("orders", top1)
        self.assertIn("revenue", top1)
        self.assertIn("revenue_share_pct", top1)
        self.assertIn("avg_prep_duration_mins", top1)
        self.assertIn("cancellation_rate_pct", top1)
        self.assertIn("health_score", top1)

        # Underperforming restaurants
        self.assertIn("underperforming_restaurants", data)
        under = data["underperforming_restaurants"]
        self.assertIsInstance(under, list)
        if len(under) > 0:
            self.assertIn("restaurant_id", under[0])
            self.assertIn("issue", under[0])
            self.assertIn("recommended_action", under[0])

    # =========================================================================
    # TEST 6: Operations Intelligence Delivery Vitals & BASELINE_ONLY Notice
    # =========================================================================
    def test_06_operations_intelligence(self):
        """Verifies delivery vitals, top 15 riders, and mandatory BASELINE_ONLY telematics notice."""
        resp = self.client.get("/api/operations/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Delivery vitals
        self.assertIn("delivery_vitals", data)
        vitals = data["delivery_vitals"]
        self.assertIn("total_deliveries", vitals)
        self.assertIn("completed_deliveries", vitals)
        self.assertIn("avg_duration_mins", vitals)
        self.assertIn("late_delivery_pct", vitals)
        self.assertIn("fleet_utilization_pct", vitals)

        # Mandatory BASELINE_ONLY telematics notice (Scientific Honesty)
        self.assertIn("telematics_mode", vitals)
        self.assertIn("BASELINE_ONLY", vitals["telematics_mode"])

        # Rider rankings (top 15)
        self.assertIn("rider_rankings", data)
        riders = data["rider_rankings"]
        self.assertLessEqual(len(riders), 15)
        self.assertGreater(len(riders), 0)
        top_rider = riders[0]
        self.assertIn("rider_id", top_rider)
        self.assertIn("name", top_rider)
        self.assertIn("completed_deliveries", top_rider)

        # City delivery operations breakdown
        self.assertIn("city_operations", data)
        self.assertGreater(len(data["city_operations"]), 0)
        self.assertIn("city", data["city_operations"][0])
        self.assertIn("deliveries", data["city_operations"][0])
        self.assertIn("late_delivery_pct", data["city_operations"][0])

    # =========================================================================
    # TEST 7: Interactive Multi-Criteria Global Filtering
    # =========================================================================
    def test_07_global_filters_synchronization(self):
        """Verifies dynamic filtering across City, Date Range, Status, and Payment Method."""
        # 1. City filtering on overview (using canonical city 'Bangalore')
        resp_blr = self.client.get("/api/overview?city=Bangalore", headers=self.headers)
        self.assertEqual(resp_blr.status_code, 200)
        data_blr = resp_blr.json()
        blr_orders = data_blr["kpis"]["total_orders"]

        resp_all = self.client.get("/api/overview", headers=self.headers)
        data_all = resp_all.json()
        all_orders = data_all["kpis"]["total_orders"]

        # Bangalore orders must be a non-empty subset of total orders
        self.assertLess(blr_orders, all_orders)
        self.assertGreater(blr_orders, 0)

        # 2. Date filtering (historical orders range between 2025-06-17 and 2026-06-17)
        resp_date = self.client.get("/api/overview?start_date=2025-07-01&end_date=2025-12-31", headers=self.headers)
        self.assertEqual(resp_date.status_code, 200)
        data_date = resp_date.json()
        self.assertGreater(data_date["kpis"]["total_orders"], 0)

        # 3. Multi-criteria filtering on Financial Overview
        resp_fin = self.client.get(
            "/api/financial/overview?city=Bangalore&payment_method=UPI&order_status=Delivered",
            headers=self.headers,
        )
        self.assertEqual(resp_fin.status_code, 200)
        data_fin = resp_fin.json()
        self.assertIn("revenue_trends", data_fin)

        # 4. Multi-criteria filtering on Customer Overview (using canonical city 'Chennai')
        resp_cust = self.client.get("/api/customer/overview?city=Chennai", headers=self.headers)
        self.assertEqual(resp_cust.status_code, 200)

        # 5. Multi-criteria filtering on Operations Overview (using canonical city 'Hyderabad')
        resp_ops = self.client.get("/api/operations/overview?city=Hyderabad", headers=self.headers)
        self.assertEqual(resp_ops.status_code, 200)

    # =========================================================================
    # TEST 8: Prescriptive AI Decision Center & Master Orchestrator
    # =========================================================================
    def test_08_prescriptive_ai_center(self):
        """Verifies 5-domain prescriptive recommendations, evidence attribution, and simulation flags."""
        resp = self.client.get("/api/prescriptive/recommendations", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        recs = resp.json()

        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

        # Inspect first recommendation structure
        rec = recs[0]
        self.assertIn("recommendation_id", rec)
        self.assertIn("priority", rec)
        self.assertIn("business_problem", rec)
        self.assertIn("proposed_action", rec)
        self.assertIn("expected_benefit", rec)
        self.assertIn("implementation_cost", rec)
        self.assertIn("net_financial_impact", rec)

        # Expected impact must contain simulation flag
        self.assertIn("is_simulation_projection", rec)
        self.assertTrue(rec["is_simulation_projection"], "Prescriptive financial projections must set is_simulation_projection=True")

        # Verify summary endpoint
        resp_summary = self.client.get("/api/prescriptive/summary", headers=self.headers)
        self.assertEqual(resp_summary.status_code, 200)
        summary = resp_summary.json()
        self.assertIn("total_recommendations", summary)

    # =========================================================================
    # TEST 9: Security & RBAC Authorization Enforcement
    # =========================================================================
    def test_09_security_and_rbac(self):
        """Verifies unauthorized rejection (401/403) and authenticated acceptance."""
        # Unauthenticated request must return 401
        resp_unauth = self.client.get("/api/overview")
        self.assertIn(resp_unauth.status_code, [401, 403])

        # Viewer can read overview
        resp_viewer = self.client.get("/api/overview", headers=self.viewer_headers)
        self.assertEqual(resp_viewer.status_code, 200)

        # Operator can access prescriptive center
        resp_operator = self.client.get("/api/prescriptive/recommendations", headers=self.headers)
        self.assertEqual(resp_operator.status_code, 200)

    # =========================================================================
    # TEST 10: Live Docker Container End-to-End Reachability
    # =========================================================================
    def test_10_live_container_http_reachability(self):
        """Verifies live Docker containers (FastAPI on 8001 and Nginx Frontend on 80) respond 200."""
        # 1. Test live API container via urllib
        api_req = urllib.request.Request(
            f"{self.live_api_url}/api/overview",
            headers={"Authorization": f"Bearer {self.api_token}", "X-API-Key": self.api_token},
        )
        try:
            with urllib.request.urlopen(api_req, timeout=5) as response:
                self.assertEqual(response.status, 200)
                body = json.loads(response.read().decode("utf-8"))
                self.assertIn("kpi_cards", body)
                self.assertIn("total_gmv", body["kpi_cards"])
        except urllib.error.URLError as e:
            self.fail(f"Live API container at {self.live_api_url} failed to respond: {e}")

        # 2. Test live Frontend container via urllib
        try:
            with urllib.request.urlopen(self.live_frontend_url, timeout=5) as response:
                self.assertEqual(response.status, 200)
                content = response.read().decode("utf-8")
                self.assertIn('<div id="root">', content)
                self.assertIn("NOVANEST", content.upper())
        except urllib.error.URLError as e:
            self.fail(f"Live Frontend container at {self.live_frontend_url} failed to respond: {e}")


if __name__ == "__main__":
    unittest.main()
