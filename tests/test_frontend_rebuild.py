"""
Automated Test Suite for Rebuilt Frontend Architecture
------------------------------------------------------
Validates:
1. All bootstrap, config, components and pages can be imported without error.
2. Data loading with fallback works.
3. NL2SQL safety validation works.
4. Recommendations, Decision Simulator, Digital Twin engines work.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "streamlit_app"))

class TestFrontendRebuild(unittest.TestCase):

    def test_imports_components(self):
        """Verifies that all new components import successfully."""
        import bootstrap
        import config.settings
        import components.navigation
        import components.page_header
        import components.kpi_components
        import components.chart_components
        import components.status_components
        import components.insight_components
        self.assertIsNotNone(bootstrap.inject_theme)

    def test_data_loader_and_database(self):
        """Verifies data loader and database connector with fallback."""
        from database.connection import get_db_connection
        from utils.data_loader import load_all_datasets
        
        conn, source = get_db_connection()
        self.assertIn(source, ["MySQL Database", "CSV File Store"])

        data, data_source = load_all_datasets()
        self.assertIn("orders", data)
        self.assertIn("customers", data)
        self.assertIn("restaurants", data)
        self.assertFalse(data["orders"].empty, "Orders dataset should not be empty")

    def test_sql_safety(self):
        """Verifies SQL validator security barriers."""
        from ai.conversational.sql_validator import validate_sql
        self.assertTrue(validate_sql("SELECT * FROM orders WHERE order_id = 1"))
        self.assertFalse(validate_sql("DROP TABLE orders"))
        self.assertFalse(validate_sql("DELETE FROM customers"))

    def test_recommender_engine(self):
        """Verifies hybrid recommender runs against datasets."""
        from utils.data_loader import load_all_datasets
        from ai.recommendations.hybrid_recommender import get_hybrid_recommendations
        data, _ = load_all_datasets()
        cust_id = data["customers"]["customer_id"].iloc[0]
        recs = get_hybrid_recommendations(cust_id, data["orders"], data["menu_items"], top_k=3)
        self.assertTrue(isinstance(recs, (list, pd.DataFrame)))

    def test_decision_simulator(self):
        """Verifies scenario engine runs successfully."""
        from utils.data_loader import load_all_datasets
        from decision_simulation.scenario_engine import run_scenario
        data, _ = load_all_datasets()
        params = {
            "commission_change_pct": 5.0,
            "delivery_fee_change_pct": 0.0,
            "discount_change_pct": -10.0,
            "demand_change_pct": 5.0,
            "churn_reduction_pct": 10.0
        }
        res = run_scenario("Test Run", params, data)
        self.assertIn("results", res)
        self.assertIn("recommendation", res)

    def test_digital_twin_engine(self):
        """Verifies digital twin state builds correctly."""
        from utils.data_loader import load_all_datasets
        from digital_twin.twin_engine import build_digital_twin_state
        from digital_twin.twin_dependencies import get_impact_chain
        data, _ = load_all_datasets()
        twin = build_digital_twin_state(data)
        self.assertIsNotNone(twin)
        self.assertIn("Gross_Revenue", twin.financial_state)
        chain = get_impact_chain("demand_spike")
        self.assertTrue(len(chain) > 0)

if __name__ == "__main__":
    unittest.main()
