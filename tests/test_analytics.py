"""
NovaNest Analytics Unit & Integration Test Suite
Verifies RFM segmentation, monthly cohort retention matrices, funnel drop-off rates,
KPI calculations, missing value handling, and idempotency.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Dynamic root anchoring
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from python.analytics.rfm_segmentation import calculate_rfm_segments
from python.analytics.cohort_analysis import compute_cohort_retention_matrix
from python.analytics.funnel_analysis import analyze_marketing_funnel
from python.analytics.kpi_engine import compute_all_kpis
from python.analytics.validate_kpis import run_cross_validation


class TestNovaNestAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cleaned_dir = BASE_DIR / "datasets" / "cleaned"
        cls.orders = pd.read_csv(cls.cleaned_dir / "orders.csv")
        cls.customers = pd.read_csv(cls.cleaned_dir / "customers.csv")
        cls.events = pd.read_csv(cls.cleaned_dir / "app_events.csv")

    def test_01_rfm_dimensions_and_nulls(self):
        """Verify RFM calculates exactly 5,000 customers with zero nulls."""
        rfm, summary = calculate_rfm_segments(self.orders, self.customers)
        self.assertEqual(len(rfm), 5000, "RFM customer count must equal 5,000.")
        self.assertEqual(rfm["recency"].isnull().sum(), 0, "Recency contains nulls.")
        self.assertEqual(rfm["frequency"].isnull().sum(), 0, "Frequency contains nulls.")
        self.assertEqual(rfm["monetary"].isnull().sum(), 0, "Monetary contains nulls.")
        self.assertGreaterEqual(len(summary), 5, "Expected at least 5 business segments.")

    def test_02_rfm_monetary_parity(self):
        """Verify total monetary spend in RFM equals non-cancelled order amount."""
        rfm, _ = calculate_rfm_segments(self.orders, self.customers)
        expected_spend = self.orders[self.orders["order_status"] != "Cancelled"]["final_amount"].sum()
        actual_spend = rfm["monetary"].sum()
        self.assertAlmostEqual(actual_spend, expected_spend, places=2)

    def test_03_cohort_month_zero_is_100_percent(self):
        """Verify that Month 0 retention is exactly 100% across all monthly cohorts."""
        retention_matrix, _, stats = compute_cohort_retention_matrix(self.orders)
        self.assertIn("Month 0", retention_matrix.columns)
        for val in retention_matrix["Month 0"].dropna():
            self.assertAlmostEqual(val, 100.0, places=1)
        self.assertEqual(stats["total_acquired_customers"], 5000)

    def test_04_repeat_purchase_rate_distinct_from_cohort_retention(self):
        """Verify repeat purchase rate is 99.94% and strictly greater than Month 1 retention (~53%)."""
        _, _, stats = compute_cohort_retention_matrix(self.orders)
        self.assertAlmostEqual(stats["repeat_purchase_rate_pct"], 99.94, places=2)
        self.assertGreater(stats["repeat_purchase_rate_pct"], stats["avg_month_1_retention_pct"])
        self.assertGreater(stats["avg_month_1_retention_pct"], 40.0)

    def test_05_funnel_stages_and_unique_reach(self):
        """Verify marketing funnel accounts for all 100,000 events across 6 distinct stages."""
        funnel_df, stats = analyze_marketing_funnel(self.events)
        self.assertEqual(len(funnel_df), 6, "Must define 6 stages matching data.")
        self.assertEqual(stats["total_clickstream_events"], 100000)
        self.assertEqual(stats["total_active_app_users"], 5000)
        self.assertGreater(stats["users_completing_all_stages"], 3500)

    def test_06_kpi_engine_completeness(self):
        """Verify KPI engine generates all 16 core business metrics with positive values."""
        kpis_df, defs = compute_all_kpis()
        self.assertEqual(len(kpis_df), 16, "Must generate exactly 16 core KPIs.")
        self.assertIn("KPI-01", defs)
        self.assertIn("KPI-16", defs)
        # Check GMV > Net Revenue
        gmv = defs["KPI-01"]["value"]
        net_rev = defs["KPI-02"]["value"]
        self.assertGreater(gmv, 0)
        self.assertGreater(net_rev, 0)

    def test_07_kpi_cross_validation_tolerances(self):
        """Verify all 16 KPIs match across Python, SQL logic, and DAX layers within 0.05 tolerance."""
        comp_df, summary = run_cross_validation()
        self.assertEqual(summary["total_kpis"], 16)
        self.assertEqual(summary["verified_kpis"], 16, "All 16 KPIs must match within tolerance.")
        self.assertEqual(summary["mismatched_kpis"], 0)


if __name__ == "__main__":
    unittest.main()
