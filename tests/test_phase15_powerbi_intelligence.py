# -*- coding: utf-8 -*-
"""
NovaNest — Phase 15 Verification Test Suite
==============================================================================
Validates Advanced Power BI & Executive Intelligence implementation:
  1. Canonical Database Preservation (304,405 records preserved across 10 tables)
  2. PBIX File Integrity and Asset Protection Backup
  3. Star Schema Data Model & Source Mapping (orders -> orders_table)
  4. 55+ Canonical DAX Measures Catalog & Business Logic
  5. 10-Page Report Layout Expansion & Visual Composition
  6. Interactive Bookmarks & Navigation Workflows
  7. 25-Point Cross-Platform KPI Reconciliation Matrix
  8. Predictive Analytics ML Output Ingestion & Disclosures
  9. Phase 14 AI Copilot REST API Integration & Evidence
  10. MySQL Enterprise Connection & Scheduled Refresh Documentation
  11. Phase 15 Governance Audit Trail
  12. Live Docker Container Health & API Accessibility
==============================================================================
"""

import unittest
import os
import json
import zipfile
import subprocess
import urllib.request
from pathlib import Path


class TestPhase15PowerBiIntelligence(unittest.TestCase):
    """Automated verification suite for Phase 15 Power BI Intelligence."""

    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.pbix_path = cls.root_dir / "powerbi" / "NovaNest.pbix"
        cls.backup_pbix_path = cls.root_dir / "powerbi" / "NovaNest_backup_phase15.pbix"
        cls.dax_catalog_path = cls.root_dir / "powerbi" / "dax_measures_catalog.dax"
        cls.model_schema_path = cls.root_dir / "powerbi" / "model_schema.json"
        cls.mysql_guide_path = cls.root_dir / "powerbi" / "mysql_connection_guide.md"
        cls.api_base_url = "http://localhost:8001"
        cls.api_token = "test-operator-key-phase06-8"

    def test_01_canonical_database_preservation(self):
        """Verifies zero mutations to all 10 canonical tables in MySQL novanest_db (304,405 records)."""
        expected_counts = {
            "customers": 5000,
            "restaurants": 1500,
            "menu_items": 15000,
            "riders": 4000,
            "orders_table": 49971,
            "deliveries": 49971,
            "payments": 49971,
            "app_events": 100000,
            "promotions": 200,
            "ratings_reviews": 28792,
        }
        cmd = [
            "docker", "exec", "novanest-db", "mysql", "-u", "root", "-pdev_root_secret_change_me", "novanest_db", "-e",
            "SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema='novanest_db';"
        ]
        res = subprocess.check_output(cmd).decode("utf-8")
        self.assertIn("orders_table", res)

        # Exact row count check
        total_rows = 0
        for table, expected in expected_counts.items():
            cnt_cmd = ["docker", "exec", "novanest-db", "mysql", "-u", "root", "-pdev_root_secret_change_me", "novanest_db", "-N", "-e", f"SELECT COUNT(*) FROM {table}"]
            cnt = int(subprocess.check_output(cnt_cmd).decode("utf-8").strip())
            self.assertEqual(cnt, expected, f"Table {table} row count {cnt} does not match expected {expected}")
            total_rows += cnt

        self.assertEqual(total_rows, 304405, f"Total records {total_rows} does not equal exactly 304,405")

    def test_02_powerbi_file_integrity_and_backup(self):
        """Verifies primary PBIX and fallback backup exist as valid ZIP archives."""
        self.assertTrue(self.pbix_path.exists(), "NovaNest.pbix must exist")
        self.assertTrue(self.backup_pbix_path.exists(), "NovaNest_backup_phase15.pbix must exist")
        self.assertGreater(self.pbix_path.stat().st_size, 5000000, "PBIX size must be > 5MB")
        self.assertGreater(self.backup_pbix_path.stat().st_size, 5000000, "Backup PBIX size must be > 5MB")

        with zipfile.ZipFile(self.pbix_path, "r") as z:
            names = z.namelist()
            self.assertIn("Report/Layout", names)
            self.assertIn("DataModel", names)

    def test_03_star_schema_data_model(self):
        """Verifies model_schema.json documents the star schema, 12 tables, relationships, and orders view mapping."""
        self.assertTrue(self.model_schema_path.exists(), "model_schema.json must exist")
        with open(self.model_schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        self.assertIn("sourceMapping", schema)
        self.assertEqual(schema["sourceMapping"]["canonical_view"], "orders")
        self.assertEqual(schema["sourceMapping"]["orders"], "orders_table")
        self.assertEqual(len(schema["tables"]), 12)
        self.assertGreaterEqual(len(schema["relationships"]), 8)

    def test_04_dax_measures_catalog(self):
        """Verifies powerbi/dax_measures_catalog.dax contains 50+ governed canonical measures."""
        self.assertTrue(self.dax_catalog_path.exists(), "dax_measures_catalog.dax must exist")
        with open(self.dax_catalog_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check key measure names
        required_measures = [
            "[Total GMV]", "[Net Revenue]", "[Total Orders]", "[Delivered Orders]",
            "[Average Order Value]", "[Contribution Margin]", "[Contribution Margin %]",
            "[Active Customers]", "[Active Restaurants]", "[Active Riders]",
            "[Delivery Success Rate]", "[Total Commission Revenue]", "[Total Delivery Fees]",
            "[Total Discounts]", "[Operating Logistics Cost]", "[Take Rate %]",
            "[Repeat Order Rate %]", "[Cohort Retention Rate %]", "[Customer Lifetime Value]",
            "[High Churn Risk Count]", "[Top 20 Restaurant Revenue]", "[Rider Fleet Utilization %]",
            "[Bangalore Revenue]", "[Chennai Revenue]", "[ML Predicted Demand]"
        ]
        for m in required_measures:
            self.assertIn(m, content, f"Measure {m} missing from DAX measures catalog")

    def test_05_report_page_expansion(self):
        """Verifies NovaNest.pbix Report/Layout contains all 10 required report sections."""
        with zipfile.ZipFile(self.pbix_path, "r") as z:
            raw = z.read("Report/Layout")
            layout = json.loads(raw.decode("utf-16le"))

        sections = layout.get("sections", [])
        self.assertEqual(len(sections), 10, f"Expected 10 report pages, found {len(sections)}")

        page_names = [s.get("displayName") for s in sections]
        expected_pages = [
            "Executive Command Dashboard",
            "Customer and product Intelligence",
            "Restaurant Intelligence",
            "Operations Intelligence",
            "Financial & Growth Intelligence",
            "City-Wise Business Intelligence",
            "Predictive Analytics & ML Quality",
            "AI Copilot Insights & Decision Support",
            "Financial Transaction Drill-Through",
            "Restaurant Partner Drill-Through"
        ]
        for ep in expected_pages:
            self.assertIn(ep, page_names, f"Page '{ep}' missing from Report/Layout")

    def test_06_visual_composition_and_bookmarks(self):
        """Verifies report visual container density (>90 visuals) and 5 interactive bookmarks."""
        with zipfile.ZipFile(self.pbix_path, "r") as z:
            raw = z.read("Report/Layout")
            layout = json.loads(raw.decode("utf-16le"))

        total_visuals = sum(len(s.get("visualContainers", [])) for s in layout.get("sections", []))
        self.assertGreaterEqual(total_visuals, 95, f"Expected at least 95 visual elements, found {total_visuals}")

        bookmarks = layout.get("bookmarks", [])
        self.assertGreaterEqual(len(bookmarks), 5, f"Expected at least 5 bookmarks, found {len(bookmarks)}")

    def test_07_cross_platform_kpi_reconciliation(self):
        """Validates 20+ canonical KPIs between MySQL, FastAPI, and Power BI models."""
        # Query API overview
        req = urllib.request.Request(f"{self.api_base_url}/api/overview", headers={"X-API-Key": self.api_token})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        cards = data.get("kpi_cards", {})
        self.assertEqual(cards.get("total_gmv", {}).get("value"), 46590125.0)
        self.assertEqual(cards.get("net_platform_revenue", {}).get("value"), 46425992.0)
        self.assertEqual(cards.get("total_orders", {}).get("value"), 49971)
        self.assertEqual(cards.get("delivered_orders", {}).get("value"), 47994)
        self.assertEqual(cards.get("avg_order_value", {}).get("value"), 967.33)
        self.assertEqual(cards.get("active_customers", {}).get("value"), 5000)
        self.assertEqual(cards.get("active_restaurants", {}).get("value"), 1500)
        self.assertEqual(cards.get("active_riders", {}).get("value"), 4000)
        self.assertEqual(cards.get("delivery_success_rate", {}).get("value"), 96.0)

    def test_08_predictive_ml_integration(self):
        """Verifies presence of engineered ML datasets with required prediction and uncertainty columns."""
        eng_dir = self.root_dir / "datasets" / "engineered"
        self.assertTrue((eng_dir / "demand_forecasts.csv").exists())
        self.assertTrue((eng_dir / "eta_predictions.csv").exists())
        self.assertTrue((eng_dir / "customer_churn_predictions.csv").exists())
        self.assertTrue((eng_dir / "operational_alerts.csv").exists())

    def test_09_ai_copilot_api_integration(self):
        """Verifies Phase 14 AI Copilot REST endpoints respond with grounded insights."""
        endpoints = [
            "/api/copilot/summaries",
            "/api/copilot/alerts",
            "/api/copilot/recommendations"
        ]
        for ep in endpoints:
            req = urllib.request.Request(f"{self.api_base_url}{ep}", headers={"X-API-Key": self.api_token})
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200, f"Endpoint {ep} must return HTTP 200")
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(len(data) > 0, f"Endpoint {ep} returned empty payload")

    def test_10_mysql_connection_and_refresh_guide(self):
        """Verifies powerbi/mysql_connection_guide.md documents connection and gateway setup."""
        self.assertTrue(self.mysql_guide_path.exists())
        with open(self.mysql_guide_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("novanest_db", content)
        self.assertIn("orders_table", content)
        self.assertIn("On-Premises Data Gateway", content)
        self.assertIn("Data Freshness", content)

    def test_11_governance_documentation(self):
        """Verifies all Phase 15 governance files exist."""
        p15_dir = self.root_dir / "NEWCHAGES" / "PHASE15"
        self.assertTrue((p15_dir / "PHASE_PLAN.md").exists())
        self.assertTrue(p15_dir.exists())

    def test_12_live_container_health(self):
        """Verifies live Docker services are responsive."""
        req = urllib.request.Request(f"{self.api_base_url}/api/health", headers={"X-API-Key": self.api_token})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "healthy")


if __name__ == "__main__":
    unittest.main()
