"""
NovaNest Phase 05.3 — Security Hardening, API Contract & Dashboard Reliability Test Suite
=======================================================================================
Covers:
1. CORS allowlist enforcement (trusted origin allowed with credentials; wildcard & untrusted rejected)
2. SQL AST validation + recursive subquery/CTE/system-table checks + SQLite authorizer read-only lock
3. API fail-closed authentication and role-based scopes (viewer / operator / admin; /api/health open)
4. API data contracts (/api/overview, /api/customer/360/{id}, /api/restaurant/overview,
   /api/decision/simulate, /api/digital-twin/state empirical + unavailable state)
5. Streamlit AppTest runtime checks across core multipage dashboards
6. MySQL canonical DB/table alignment checks
"""

from __future__ import annotations

import os
import secrets
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = PROJECT_ROOT / "python"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import api.auth as api_auth
import api.main as api_main
from api.loader import load_data
from python.ai.analyst.sql_agent import configure_readonly_sqlite, execute_safe_sql, validate_and_sanitize_sql
from python.ai.analyst.sql_ast import validate_sql_ast
from python.ai.conversational.sql_validator import validate_sql


class TestPhase053SecurityAndContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.viewer_key = secrets.token_urlsafe(32)
        cls.operator_key = secrets.token_urlsafe(32)
        cls.admin_key = secrets.token_urlsafe(32)
        cls._prev_env = {
            k: os.environ.get(k)
            for k in ("NOVANEST_VIEWER_KEY", "NOVANEST_API_KEY", "NOVANEST_ADMIN_KEY")
        }
        os.environ["NOVANEST_VIEWER_KEY"] = cls.viewer_key
        os.environ["NOVANEST_API_KEY"] = cls.operator_key
        os.environ["NOVANEST_ADMIN_KEY"] = cls.admin_key

        load_data(force_reload=True)
        cls.client = TestClient(api_main.app)
        cls.operator_headers = {"X-API-Key": cls.operator_key}
        cls.viewer_headers = {"X-API-Key": cls.viewer_key}
        cls.admin_headers = {"X-API-Key": cls.admin_key}

    @classmethod
    def tearDownClass(cls) -> None:
        for k, prev in cls._prev_env.items():
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev

    # ------------------------------------------------------------------
    # 1. CORS Hardening
    # ------------------------------------------------------------------
    def test_01_cors_explicit_allowlist_no_wildcard(self) -> None:
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "*,http://localhost:5173,https://app.novanest.local"}):
            origins = api_auth.get_allowed_cors_origins()
            self.assertNotIn("*", origins)
            self.assertIn("http://localhost:5173", origins)
            self.assertIn("https://app.novanest.local", origins)

        preflight_ok = self.client.options(
            "/api/overview",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(preflight_ok.status_code, 200)
        self.assertEqual(preflight_ok.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertEqual(preflight_ok.headers.get("access-control-allow-credentials"), "true")

        preflight_evil = self.client.options(
            "/api/overview",
            headers={
                "Origin": "https://untrusted-attacker.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertIsNone(preflight_evil.headers.get("access-control-allow-origin"))

    # ------------------------------------------------------------------
    # 2. SQL AST Validation & SQLite Read-Only Authorizer
    # ------------------------------------------------------------------
    def test_02_sql_ast_blocks_system_table_and_bypass_attacks(self) -> None:
        attack_queries = [
            "SELECT name FROM orders, sqlite_master LIMIT 2",
            "SELECT * FROM sqlite_schema LIMIT 5",
            "SELECT * FROM main.orders LIMIT 5",
            "SELECT order_id FROM orders WHERE restaurant_id IN (SELECT tbl_name FROM sqlite_temp_master)",
            "WITH RECURSIVE r(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM r) SELECT * FROM r",
            "SELECT COUNT(*) FROM orders; DROP TABLE orders;",
            "SELECT randomblob(1000000) FROM orders LIMIT 1",
            "SELECT load_extension('evil.so') FROM orders LIMIT 1",
            "PRAGMA table_info(orders)",
            "SELECT * FROM unknown_secret_table LIMIT 5",
            "DELETE FROM orders WHERE 1=1",
        ]
        for q in attack_queries:
            ast_ok, ast_sql, _ = validate_sql_ast(q)
            self.assertFalse(ast_ok, f"AST validator failed to reject attack: {q}")
            self.assertEqual(ast_sql, "")
            ok, sanitized, _ = validate_and_sanitize_sql(q)
            self.assertFalse(ok, f"sql_agent failed to reject attack: {q}")
            self.assertEqual(sanitized, "")
            self.assertFalse(validate_sql(q), f"conversational sql_validator failed to reject: {q}")

        valid_cte_no_limit = (
            "WITH city_counts AS ("
            "SELECT r.city, COUNT(*) AS total_orders "
            "FROM orders o JOIN restaurants r ON o.restaurant_id = r.restaurant_id "
            "GROUP BY r.city"
            ") SELECT city, total_orders FROM city_counts ORDER BY total_orders DESC"
        )
        ok, sanitized, msg = validate_and_sanitize_sql(valid_cte_no_limit)
        self.assertTrue(ok, f"Expected valid CTE query to pass, got: {msg}")
        self.assertIn("LIMIT 25", sanitized.upper())

        excess_limit_cte = f"{valid_cte_no_limit} LIMIT 500"
        ok_excess, _, msg_excess = validate_and_sanitize_sql(excess_limit_cte)
        self.assertFalse(ok_excess)
        self.assertIn("exceeds maximum allowed", msg_excess)

    def test_03_sqlite_readonly_authorizer_enforces_kernel_lock(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE orders (order_id TEXT, final_amount REAL)")
        conn.execute("INSERT INTO orders VALUES ('O1', 150.0)")
        conn.commit()
        configure_readonly_sqlite(conn)

        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("SELECT name FROM sqlite_master")
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("INSERT INTO orders VALUES ('O2', 200.0)")
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("PRAGMA table_info(orders)")

        df_out, err = execute_safe_sql("SELECT order_id, final_amount FROM orders LIMIT 5", conn)
        self.assertEqual(err, "Query executed successfully.")
        self.assertIsNotNone(df_out)
        self.assertEqual(len(df_out), 1)
        conn.close()

    # ------------------------------------------------------------------
    # 3. API Authentication & Scope RBAC
    # ------------------------------------------------------------------
    def test_04_api_authentication_and_rbac_scopes(self) -> None:
        # /api/health remains open without leaking secret material
        h = self.client.get("/api/health")
        self.assertEqual(h.status_code, 200)
        self.assertTrue(h.json().get("auth_enabled"))

        # Unauthenticated calls fail closed with 401
        protected = [
            ("GET", "/api/overview", None),
            ("GET", "/api/customer/list?limit=5", None),
            ("GET", "/api/restaurant/overview", None),
            ("POST", "/api/ai/ask", {"question": "What is total revenue?"}),
            ("POST", "/api/ai/reset", {"session_id": "s1"}),
            ("GET", "/api/digital-twin/state", None),
        ]
        for method, path, body in protected:
            r = self.client.get(path) if method == "GET" else self.client.post(path, json=body)
            self.assertEqual(r.status_code, 401, f"{method} {path} should require authentication")

        # Invalid credential rejected with 401
        bad = self.client.get("/api/overview", headers={"X-API-Key": "invalid-wrong-token"})
        self.assertEqual(bad.status_code, 401)

        # Viewer key: read allowed, operator & admin denied (403)
        self.assertEqual(self.client.get("/api/overview", headers=self.viewer_headers).status_code, 200)
        self.assertEqual(self.client.get("/api/digital-twin/state", headers=self.viewer_headers).status_code, 200)
        self.assertEqual(self.client.get("/api/customer/list?limit=5", headers=self.viewer_headers).status_code, 403)
        self.assertEqual(
            self.client.post("/api/ai/ask", json={"question": "hi"}, headers=self.viewer_headers).status_code,
            403,
        )
        self.assertEqual(
            self.client.post("/api/ai/reset", json={"session_id": "s1"}, headers=self.viewer_headers).status_code,
            403,
        )

        # Operator key: operator allowed, admin denied (403 when NOVANEST_ADMIN_KEY configured)
        self.assertEqual(
            self.client.get("/api/customer/list?limit=5", headers=self.operator_headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/ai/reset", json={"session_id": "s1"}, headers=self.operator_headers).status_code,
            403,
        )

        # Admin key: admin allowed
        self.assertEqual(
            self.client.post("/api/ai/reset", json={"session_id": "s1"}, headers=self.admin_headers).status_code,
            200,
        )

    # ------------------------------------------------------------------
    # 4. API Data Contract & Empirical Grounding
    # ------------------------------------------------------------------
    def test_05_overview_and_customer_360_contracts(self) -> None:
        ov = self.client.get("/api/overview", headers=self.operator_headers)
        self.assertEqual(ov.status_code, 200)
        ov_body = ov.json()
        ov_kpis = ov_body["kpis"]
        rest_df = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "restaurants.csv")
        expected_rating = round(float(pd.to_numeric(rest_df["avg_rating"], errors="coerce").mean()), 2)
        self.assertAlmostEqual(ov_kpis["avg_rating"], expected_rating, places=2)
        self.assertGreater(len(ov_body["top_restaurants"]), 0)
        self.assertIsNotNone(ov_body["top_restaurants"][0]["rating"])

        customers_df = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "customers.csv")
        first_cid = str(customers_df["customer_id"].iloc[0])
        c360 = self.client.get(f"/api/customer/360/{first_cid}", headers=self.operator_headers)
        self.assertEqual(c360.status_code, 200)
        c360_json = c360.json()
        self.assertIn("customer_name", c360_json)
        self.assertIsNone(c360_json["email"])
        self.assertEqual(c360_json["email_status"], "unavailable")
        self.assertIn("Recency_Days", c360_json["profile"]["metrics"])
        self.assertIsNotNone(c360_json["profile"]["metrics"]["Recency_Days"])

    def test_06_restaurant_simulator_and_digital_twin_contracts(self) -> None:
        rest = self.client.get("/api/restaurant/overview", headers=self.operator_headers)
        self.assertEqual(rest.status_code, 200)
        rest_json = rest.json()
        self.assertGreater(len(rest_json["risk_distribution"]), 1)
        self.assertEqual(rest_json["kpis"]["critical_risk_count"], 3)

        sim = self.client.post(
            "/api/decision/simulate",
            json={
                "commission_change_pct": 2.0,
                "delivery_fee_change_pct": 0.0,
                "discount_change_pct": 0.0,
                "demand_change_pct": 0.0,
                "churn_reduction_pct": 0.0,
                "aov_change_pct": 0.0,
            },
            headers=self.operator_headers,
        )
        self.assertEqual(sim.status_code, 200)
        sim_json = sim.json()
        fin_sim = sim_json["results"]["financial"]
        self.assertIn("Orders", fin_sim["baseline"])
        self.assertIn("Profit_Margin", fin_sim["baseline"])
        self.assertIn("Orders_Diff", fin_sim["impact"])
        self.assertIn("metadata", fin_sim)
        self.assertIn("Decision", sim_json["recommendation"])
        self.assertIn("scenario_assumptions", sim_json)

        dt = self.client.get("/api/digital-twin/state", headers=self.operator_headers)
        self.assertEqual(dt.status_code, 200)
        dt_json = dt.json()
        self.assertEqual(dt_json["vitality_status"], "available")
        self.assertIsInstance(dt_json["vitality_index"], int)
        self.assertGreater(dt_json["pillars"]["restaurant_twin"]["active_merchants"], 0)
        deliveries_df = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "deliveries.csv")
        expected_eta = round(float(deliveries_df["delivery_duration"].dropna().mean()), 2)
        self.assertEqual(dt_json["pillars"]["operations_twin"]["avg_eta_mins"], expected_eta)
        self.assertTrue(len(dt_json["impact_ripple_chains"]) >= 3)
        first_chain = dt_json["impact_ripple_chains"][0]
        self.assertIsInstance(first_chain, dict)
        self.assertIn("trigger", first_chain)
        self.assertIn("ripple_steps", first_chain)
        self.assertIn("impact", first_chain)

        # Empty datasets report unavailable status instead of fake constants
        empty_store = {
            k: pd.DataFrame()
            for k in (
                "customers",
                "restaurants",
                "orders",
                "deliveries",
                "riders",
                "ratings_reviews",
                "orders_engineered",
                "customer_churn_predictions",
                "restaurant_predictions",
                "operational_anomalies",
                "revenue_leakage",
            )
        }
        with patch("api.main.load_data", return_value=(empty_store, "EmptyMock")):
            dt_empty = self.client.get("/api/digital-twin/state", headers=self.operator_headers)
            self.assertEqual(dt_empty.status_code, 200)
            de_json = dt_empty.json()
            self.assertIsNone(de_json["vitality_index"])
            self.assertEqual(de_json["vitality_status"], "unavailable")
            self.assertIsNone(de_json["pillars"]["restaurant_twin"]["active_merchants"])
            self.assertEqual(de_json["pillars"]["financial_twin"]["status"], "unavailable")

    # ------------------------------------------------------------------
    # 5. Streamlit Runtime & MySQL Canonical Alignment
    # ------------------------------------------------------------------
    def test_07_streamlit_pages_runtime_apptest(self) -> None:
        from streamlit.testing.v1 import AppTest

        pages = [
            PROJECT_ROOT / "streamlit_app" / "app.py",
            PROJECT_ROOT / "streamlit_app" / "pages" / "01_Executive_Overview.py",
            PROJECT_ROOT / "streamlit_app" / "pages" / "02_Customer_Intelligence.py",
            PROJECT_ROOT / "streamlit_app" / "pages" / "03_Restaurant_Intelligence.py",
            PROJECT_ROOT / "streamlit_app" / "pages" / "08_Decision_Simulator.py",
            PROJECT_ROOT / "streamlit_app" / "pages" / "09_NovaNest_Command_Center.py",
        ]
        for page_path in pages:
            at = AppTest.from_file(str(page_path), default_timeout=45)
            at.run()
            self.assertFalse(
                at.exception,
                f"Streamlit runtime raised exception in {page_path.name}: {at.exception}",
            )

    def test_08_mysql_canonical_config_and_sql_alignment(self) -> None:
        sql_08 = (PROJECT_ROOT / "mysql" / "08_phase3_intelligence.sql").read_text(encoding="utf-8")
        sql_09 = (PROJECT_ROOT / "mysql" / "09_phase4_operations.sql").read_text(encoding="utf-8")
        self.assertIn("USE novanest_db;", sql_08)
        self.assertIn("FROM orders_table", sql_08)
        self.assertNotIn("FROM orders\n", sql_08)
        self.assertIn("FROM orders_table", sql_09)

        loader_src = (PROJECT_ROOT / "api" / "loader.py").read_text(encoding="utf-8")
        conn_src = (PROJECT_ROOT / "streamlit_app" / "database" / "connection.py").read_text(encoding="utf-8")
        sys_cfg_src = (PROJECT_ROOT / "python" / "system_config.py").read_text(encoding="utf-8")
        self.assertIn('os.getenv("DB_NAME", "novanest_db")', loader_src)
        self.assertIn('os.getenv("DB_NAME", "novanest_db")', conn_src)
        self.assertIn('os.getenv("DB_NAME", "novanest_db")', sys_cfg_src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
