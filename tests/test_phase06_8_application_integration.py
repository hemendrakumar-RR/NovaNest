"""
Phase 06.8 Verification Suite — MySQL Application Integration and Validation
-----------------------------------------------------------------------------
Validates live MySQL read paths, relational joins, KPI parity, AI domain agents,
FastAPI endpoints, Streamlit connectors, and safe DATA_SOURCE switching/rollback.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.loader import load_data, get_db_connection
from api.main import app
from python.ai.agents import (
    AgentContext,
    AgentRequest,
    AgentStatus,
    AgentDomain,
    ExecutionTracer,
    OutputVerifier,
    FinancialAgent,
    CustomerAgent,
    OperationsAgent,
    RestaurantAgent,
    DecisionAgent,
)


class TestPhase068MySQLApplicationIntegration(unittest.TestCase):
    """Rigorous integration test suite for Phase 06.8 MySQL application validation."""

    @classmethod
    def setUpClass(cls):
        cls.test_env = {
            "DATA_SOURCE": "mysql",
            "NOVANEST_API_KEY": "test-operator-key-phase06-8",
            "NOVANEST_VIEWER_KEY": "test-viewer-key-phase06-8",
            "NOVANEST_ADMIN_KEY": "test-admin-key-phase06-8",
        }
        cls.headers = {"X-API-Key": "test-operator-key-phase06-8"}
        with patch.dict(os.environ, cls.test_env):
            cls.live_data, cls.source_label = load_data(force_reload=True)
        cls.verifier = OutputVerifier(load_default_kpis=True)

    # -------------------------------------------------------------
    # 1. READ-PATH AND RECORD INTEGRITY
    # -------------------------------------------------------------

    def test_01_mysql_read_path_row_counts(self):
        """Verifies all 10 datasets can be queried through application layer with exact row counts."""
        expected_counts = {
            "customers": 5000,
            "restaurants": 1500,
            "menu_items": 15000,
            "riders": 4000,
            "orders": 49971,
            "payments": 49971,
            "deliveries": 49971,
            "ratings_reviews": 28792,
            "app_events": 100000,
            "promotions": 200,
        }
        for tbl, expected in expected_counts.items():
            self.assertIn(tbl, self.live_data, f"Table `{tbl}` missing from live dataset store")
            self.assertEqual(len(self.live_data[tbl]), expected, f"Table `{tbl}` row count mismatch")

        total_rows = sum(len(self.live_data[tbl]) for tbl in expected_counts)
        self.assertEqual(total_rows, 304405, "Total loaded records must equal 304,405")

    def test_02_mysql_read_path_representative_records(self):
        """Verifies schema structure, non-empty columns, and representative IDs in live MySQL data."""
        orders = self.live_data["orders"]
        self.assertIn("order_id", orders.columns)
        self.assertIn("order_status", orders.columns)
        self.assertIn("order_amount", orders.columns)
        self.assertFalse(orders["order_id"].isnull().any(), "Order IDs must not contain nulls")

        customers = self.live_data["customers"]
        self.assertIn("customer_id", customers.columns)
        self.assertIn("city", customers.columns)
        self.assertEqual(customers["city"].nunique(), 5, "Must encompass all 5 operating metro cities")

    def test_03_relational_joins_integrity(self):
        """Verifies multi-table SQL joins execute cleanly through live MySQL connection."""
        conn, _ = get_db_connection()
        self.assertIsNotNone(conn, "Must obtain active MySQL connection")
        try:
            cur = conn.cursor()
            join_sql = """
                SELECT 
                    o.order_id,
                    c.customer_name,
                    r.restaurant_name,
                    m.item_name,
                    d.delivery_duration,
                    p.payment_status
                FROM orders_table o
                JOIN customers c ON o.customer_id = c.customer_id
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                JOIN menu_items m ON o.item_id = m.item_id
                JOIN deliveries d ON o.order_id = d.order_id
                JOIN payments p ON o.order_id = p.order_id
                LIMIT 50;
            """
            cur.execute(join_sql)
            rows = cur.fetchall()
            self.assertEqual(len(rows), 50, "Multi-table join query must return requested rows")
            cur.close()
        finally:
            conn.close()

    # -------------------------------------------------------------
    # 2. KPI PARITY & FINANCIAL GROUNDING
    # -------------------------------------------------------------

    def test_04_kpi_parity_gmv_and_aov(self):
        """Verifies delivered GMV and AOV calculated from MySQL match canonical certified figures."""
        orders = self.live_data["orders"]
        delivered = orders[orders["order_status"] == "Delivered"]

        deliv_gmv = float(delivered["order_amount"].sum())
        self.assertEqual(deliv_gmv, 46590125.00, "Delivered GMV must match certified ₹46,590,125.00")

        deliv_count = len(delivered)
        self.assertEqual(deliv_count, 47994, "Delivered orders count must match 47,994")

        aov = deliv_gmv / deliv_count
        self.assertAlmostEqual(aov, 970.75, places=2)

    def test_05_kpi_parity_customer_and_restaurant(self):
        """Verifies customer count and active restaurant counts."""
        customers = self.live_data["customers"]
        orders = self.live_data["orders"]
        self.assertEqual(len(customers), 5000)
        self.assertEqual(orders["restaurant_id"].nunique(), 1499)

    def test_06_kpi_parity_rider_and_retention(self):
        """Verifies active rider count and customer repeat order rate."""
        deliveries = self.live_data["deliveries"]
        orders = self.live_data["orders"]
        self.assertEqual(deliveries["rider_id"].nunique(), 4000)

        repeat_cust = (orders.groupby("customer_id")["order_id"].count() > 1).sum()
        repeat_rate = (repeat_cust / orders["customer_id"].nunique()) * 100
        self.assertAlmostEqual(repeat_rate, 99.94, places=2)

    # -------------------------------------------------------------
    # 3. AI DOMAIN AGENTS UNDER MYSQL
    # -------------------------------------------------------------

    def test_07_ai_financial_agent_under_mysql(self):
        """Verifies FinancialAgent executes successfully using live MySQL data."""
        tracer = ExecutionTracer()
        ctx = AgentContext(
            principal_id="exec_1",
            principal_role="operator",
            principal_scopes=["read", "operator"],
            session_id="sess_fin_test",
            user_query="Provide full financial GMV and net revenue breakdown",
        )
        req = AgentRequest(agent_id="financial_agent", domain=AgentDomain.FINANCIAL, principal_id=ctx.principal_id, user_query=ctx.user_query)
        agent = FinancialAgent()
        res = agent.execute(req, ctx, data=self.live_data, tracer=tracer, verifier=self.verifier)

        self.assertEqual(res.status, AgentStatus.SUCCESS)
        self.assertAlmostEqual(res.metrics["gmv_inr"], 46590125.00, places=2)
        self.assertAlmostEqual(res.metrics["net_revenue_inr"], 46425992.00, places=2)
        self.assertTrue(any(p.dataset_or_table == "orders" for p in res.provenance))

    def test_08_ai_customer_agent_under_mysql(self):
        """Verifies CustomerAgent executes successfully under MySQL data."""
        first_cust = str(self.live_data["customers"]["customer_id"].iloc[0])
        ctx = AgentContext(
            principal_id="ops_1",
            principal_role="operator",
            principal_scopes=["read", "operator"],
            session_id="sess_cust_test",
            user_query=f"Analyze customer {first_cust} churn risk",
        )
        req = AgentRequest(agent_id="customer_agent", domain=AgentDomain.CUSTOMER, principal_id=ctx.principal_id, user_query=ctx.user_query)
        agent = CustomerAgent()
        res = agent.execute(req, ctx, data=self.live_data, tracer=ExecutionTracer(), verifier=self.verifier)
        self.assertEqual(res.status, AgentStatus.SUCCESS)

    def test_09_ai_operations_agent_under_mysql(self):
        """Verifies OperationsAgent executes successfully under MySQL data."""
        ctx = AgentContext(
            principal_id="ops_1",
            principal_role="operator",
            principal_scopes=["read", "operator"],
            session_id="sess_ops_test",
            user_query="Analyze fleet delivery times and on-time performance",
        )
        req = AgentRequest(agent_id="operations_agent", domain=AgentDomain.OPERATIONS, principal_id=ctx.principal_id, user_query=ctx.user_query)
        agent = OperationsAgent()
        res = agent.execute(req, ctx, data=self.live_data, tracer=ExecutionTracer(), verifier=self.verifier)
        self.assertEqual(res.status, AgentStatus.SUCCESS)

    def test_10_ai_restaurant_agent_under_mysql(self):
        """Verifies RestaurantAgent executes successfully under MySQL data."""
        first_rest = str(self.live_data["restaurants"]["restaurant_id"].iloc[0])
        ctx = AgentContext(
            principal_id="rest_lead",
            principal_role="operator",
            principal_scopes=["read", "operator"],
            session_id="sess_rest_test",
            user_query=f"Analyze restaurant {first_rest} performance",
        )
        req = AgentRequest(agent_id="restaurant_agent", domain=AgentDomain.RESTAURANT, principal_id=ctx.principal_id, user_query=ctx.user_query)
        agent = RestaurantAgent()
        res = agent.execute(req, ctx, data=self.live_data, tracer=ExecutionTracer(), verifier=self.verifier)
        self.assertEqual(res.status, AgentStatus.SUCCESS)

    def test_11_ai_decision_agent_under_mysql(self):
        """Verifies DecisionAgent executes successfully under MySQL data."""
        ctx = AgentContext(
            principal_id="ceo_1",
            principal_role="operator",
            principal_scopes=["read", "operator"],
            session_id="sess_dec_test",
            user_query="Review pending decisions and operational bottlenecks",
        )
        req = AgentRequest(agent_id="decision_agent", domain=AgentDomain.DECISION, principal_id=ctx.principal_id, user_query=ctx.user_query)
        agent = DecisionAgent()
        res = agent.execute(req, ctx, data=self.live_data, tracer=ExecutionTracer(), verifier=self.verifier)
        self.assertEqual(res.status, AgentStatus.SUCCESS)

    # -------------------------------------------------------------
    # 4. FASTAPI ENDPOINTS & SOURCE SWITCHING
    # -------------------------------------------------------------

    def test_12_fastapi_endpoints_mysql_parity(self):
        """Tests that all core FastAPI endpoints return 200 OK with verified MySQL counts."""
        with patch.dict(os.environ, self.test_env):
            client = TestClient(app)

            # Overview endpoint
            resp = client.get("/api/overview", headers=self.headers)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["data_source"], "MySQL Database")
            self.assertEqual(resp.json()["kpis"]["total_orders"], 49971)

            # Operations overview endpoint
            resp_ops = client.get("/api/operations/overview", headers=self.headers)
            self.assertEqual(resp_ops.status_code, 200)
            self.assertEqual(resp_ops.json()["kpis"]["total_deliveries"], 49971)

            # Customer overview endpoint
            resp_cust = client.get("/api/customer/overview", headers=self.headers)
            self.assertEqual(resp_cust.status_code, 200)
            self.assertEqual(resp_cust.json()["kpis"]["total_customers"], 5000)

    def test_13_data_source_selection_mechanism(self):
        """Verifies that setting DATA_SOURCE dynamically switches between MySQL and CSV."""
        # 1. Test CSV mode
        with patch.dict(os.environ, {"DATA_SOURCE": "csv"}):
            data_csv, src_csv = load_data(force_reload=True)
            self.assertIn("CSV File Store", src_csv)
            self.assertEqual(len(data_csv["orders"]), 49971)

        # 2. Test MySQL mode
        with patch.dict(os.environ, {"DATA_SOURCE": "mysql"}):
            data_sql, src_sql = load_data(force_reload=True)
            self.assertEqual(src_sql, "MySQL Database")
            self.assertEqual(len(data_sql["orders"]), 49971)

    def test_14_data_source_rollback_safety(self):
        """Verifies that if MySQL is unreachable or fails, the application falls back safely to CSV."""
        with patch.dict(os.environ, {"DATA_SOURCE": "mysql", "DB_HOST": "192.0.2.1", "DB_PORT": "3306"}):
            data_fb, src_fb = load_data(force_reload=True)
            self.assertIn("CSV File Store", src_fb)
            self.assertEqual(len(data_fb["orders"]), 49971)

    def test_15_data_source_consistency_and_diagnostics(self):
        """Verifies single-source consistency, zero silent mixing, observable fallback, and diagnostics endpoints."""
        from api.loader import get_data_source_diagnostics

        # 1. Verify CSV diagnostics
        with patch.dict(os.environ, {"DATA_SOURCE": "csv"}):
            load_data(force_reload=True)
            diag = get_data_source_diagnostics()
            self.assertEqual(diag["configured_data_source"], "csv")
            self.assertFalse(diag["fallback_active"])
            self.assertTrue(diag["consistent_source"])
            self.assertFalse(diag["mixed_sources_detected"])

        # 2. Verify MySQL diagnostics
        with patch.dict(os.environ, {"DATA_SOURCE": "mysql"}):
            load_data(force_reload=True)
            diag_mysql = get_data_source_diagnostics()
            self.assertEqual(diag_mysql["configured_data_source"], "mysql")
            self.assertEqual(diag_mysql["active_data_source"], "MySQL Database")
            self.assertFalse(diag_mysql["fallback_active"])
            self.assertTrue(diag_mysql["consistent_source"])

        # 3. Verify Observable Fallback diagnostics
        with patch.dict(os.environ, {"DATA_SOURCE": "mysql", "DB_HOST": "192.0.2.1"}):
            load_data(force_reload=True)
            diag_fb = get_data_source_diagnostics()
            self.assertEqual(diag_fb["configured_data_source"], "mysql")
            self.assertIn("CSV File Store", diag_fb["active_data_source"])
            self.assertTrue(diag_fb["fallback_active"])
            self.assertIsNotNone(diag_fb["fallback_reason"])
            self.assertTrue(diag_fb["consistent_source"])
            self.assertFalse(diag_fb["mixed_sources_detected"])

        # 4. Verify API endpoints
        with patch.dict(os.environ, {"NOVANEST_API_KEY": "phase06_8_test_key"}):
            client = TestClient(app)
            # Health endpoint
            res_health = client.get("/api/health")
            self.assertEqual(res_health.status_code, 200)
            self.assertIn("data_source_diagnostics", res_health.json())

            # Diagnostics endpoint
            res_diag = client.get("/api/diagnostics/data-source", headers={"X-API-Key": "phase06_8_test_key"})
            self.assertEqual(res_diag.status_code, 200)
            self.assertTrue(res_diag.json()["consistent_source"])
            self.assertFalse(res_diag.json()["mixed_sources_detected"])


if __name__ == "__main__":
    unittest.main()

