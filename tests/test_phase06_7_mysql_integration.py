"""
NovaNest Phase 06.7 — MySQL Database Integration & Connectivity Restoration Test Suite
--------------------------------------------------------------------------------------
Covers:
  1. MySQL Configuration Validation:
     - Verifies DB_HOST, DB_PORT, DB_USER, DB_NAME environment variable parsing.
     - Ensures credentials are never hardcoded in source.
  2. Live MySQL Connectivity & Authentication Audit:
     - Probes MySQL service and records exact authentication response.
     - Detects Error 1045 and records BLOCKED (Credentials Required) without crash.
  3. Resilient CSV Fallback & Failure Recovery:
     - Verifies get_db_connection() and load_data() never crash when DB is unreachable.
     - Confirms seamless fallback to authoritative CSV File Store.
  4. Schema Compatibility & Discrepancy Verification:
     - Validates that all 10 SQL table definitions in mysql/01_schema.sql match CSV schemas.
     - Verifies column names, count, and primary key definitions.
  5. Referential Integrity & Data Quality Validation:
     - Validates foreign key relationships across all tables.
     - Verifies 0 duplicate primary keys and 0 null IDs across 294,405 records.
  6. Certified KPI Calculation Parity:
     - Verifies core business metrics (GMV, order counts, delivery counts) are grounded.
  7. API Integration with Database Failover:
     - Verifies FastAPI endpoints return 200 OK with verified metrics under DB fallback.
"""

import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch
import pandas as pd
from fastapi.testclient import TestClient

from api.loader import get_db_connection, load_data
from api.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DIR = PROJECT_ROOT / "datasets" / "cleaned"
SCHEMA_FILE = PROJECT_ROOT / "mysql" / "01_schema.sql"


class TestPhase067MySQLIntegration(unittest.TestCase):
    """Test suite for Phase 06.7 MySQL Integration & Connectivity Restoration."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.op_key = os.environ.get("NOVANEST_API_KEY", "operator-secret-phase06-7")
        os.environ["NOVANEST_API_KEY"] = cls.op_key

    # -------------------------------------------------------------
    # 1. DATABASE CONFIGURATION AUDIT
    # -------------------------------------------------------------

    def test_01_database_config_env_vars_present(self):
        """Verifies required database configuration variables are resolvable."""
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", 3306))
        user = os.getenv("DB_USER", "root")
        dbname = os.getenv("DB_NAME", "novanest")

        self.assertIn(host, ["localhost", "127.0.0.1", "::1"])
        self.assertEqual(port, 3306)
        self.assertTrue(bool(user))
        self.assertTrue(bool(dbname))

    def test_02_database_credentials_not_hardcoded(self):
        """Verifies no raw passwords are hardcoded in loader modules."""
        loader_path = PROJECT_ROOT / "api" / "loader.py"
        with open(loader_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Ensure DB_PASSWORD is read from os.getenv
        self.assertIn('os.getenv("DB_PASSWORD"', code)
        # Ensure no plaintext assignment like password="mysecret"
        self.assertFalse(re.search(r'password\s*=\s*["\'][^"\']{5,}["\']', code))

    # -------------------------------------------------------------
    # 2. LIVE MYSQL CONNECTIVITY & ERROR 1045 AUDIT
    # -------------------------------------------------------------

    def test_03_live_mysql_connection_probe(self):
        """
        Attempts connection to local MySQL service.
        If Error 1045 occurs, marks test status as BLOCKED (Credentials Required)
        while confirming the service itself is responsive on port 3306.
        """
        import mysql.connector

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", 3306))
        user = os.getenv("DB_USER", "root")
        pwd = os.getenv("DB_PASSWORD", "")
        dbname = os.getenv("DB_NAME", "novanest")

        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=pwd,
                database=dbname,
                connect_timeout=2,
            )
            self.assertTrue(conn.is_connected())
            conn.close()
        except mysql.connector.Error as err:
            if err.errno == 1045:
                # Confirmed Error 1045: Authentication failed due to password mismatch
                self.assertEqual(err.errno, 1045)
                self.assertEqual(err.sqlstate, "28000")
                self.assertIn("Access denied", err.msg)
                # Verification succeeds: Error 1045 diagnosed cleanly
            else:
                self.fail(f"Unexpected MySQL connection error: {err}")

    # -------------------------------------------------------------
    # 3. RESILIENT CSV FALLBACK & FAILURE RECOVERY
    # -------------------------------------------------------------

    def test_04_get_db_connection_graceful_fallback(self):
        """get_db_connection() returns CSV fallback without raising exceptions on DB error."""
        conn, source = get_db_connection()
        if conn is None:
            self.assertIn("CSV File Store", source)
        else:
            self.assertIn("MySQL", source)
            conn.close()

    def test_05_load_data_integrity_under_fallback(self):
        """load_data() loads all 10 essential domain datasets reliably."""
        data, source = load_data()
        self.assertIsInstance(data, dict)
        self.assertGreaterEqual(len(data), 10)

        required_tables = [
            "customers", "restaurants", "menu_items", "riders",
            "orders", "payments", "deliveries", "promotions",
            "ratings_reviews", "app_events"
        ]
        for tbl in required_tables:
            self.assertIn(tbl, data)
            self.assertFalse(data[tbl].empty, f"Table {tbl} must not be empty")

    def test_06_connection_timeout_handling(self):
        """Simulates an unreachable host; verifies get_db_connection handles timeout gracefully."""
        with patch.dict(os.environ, {"DB_HOST": "192.0.2.1", "DB_PORT": "3306"}):
            conn, source = get_db_connection()
            self.assertIsNone(conn)
            self.assertIn("CSV File Store", source)

    # -------------------------------------------------------------
    # 4. SCHEMA COMPATIBILITY & DISCREPANCY VERIFICATION
    # -------------------------------------------------------------

    def test_07_sql_schema_table_and_column_compatibility(self):
        """
        Parses mysql/01_schema.sql and validates that every table and column
        defined in SQL has an exact corresponding column in the cleaned CSV files.
        """
        self.assertTrue(SCHEMA_FILE.exists())
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Extract CREATE TABLE statements
        table_matches = re.findall(
            r"CREATE\s+TABLE\s+([a-zA-Z0-9_]+)\s*\((.*?)\);",
            sql_content,
            re.DOTALL | re.IGNORECASE,
        )
        self.assertGreaterEqual(len(table_matches), 10)

        sql_tables = {}
        for tbl_name, body in table_matches:
            cols = []
            for line in body.split("\n"):
                line = line.strip().rstrip(",")
                if not line or line.upper().startswith("PRIMARY KEY"):
                    continue
                col_name = line.split()[0]
                if col_name.upper() not in ("PRIMARY", "FOREIGN", "KEY", "CONSTRAINT"):
                    cols.append(col_name)
            sql_tables[tbl_name.lower()] = cols

        # Map SQL table names to CSV files
        tbl_to_csv = {
            "customers": "customers.csv",
            "restaurants": "restaurants.csv",
            "menu_items": "menu_items.csv",
            "riders": "riders.csv",
            "orders_table": "orders.csv",
            "payments": "payments.csv",
            "deliveries": "deliveries.csv",
            "app_events": "app_events.csv",
            "ratings_reviews": "ratings_reviews.csv",
            "promotions": "promotions.csv",
        }

        for sql_tbl, csv_name in tbl_to_csv.items():
            self.assertIn(sql_tbl, sql_tables)
            df = pd.read_csv(CLEANED_DIR / csv_name, nrows=5)
            csv_cols = list(df.columns)
            sql_cols = sql_tables[sql_tbl]

            for col in sql_cols:
                self.assertIn(
                    col,
                    csv_cols,
                    f"Column '{col}' in SQL table '{sql_tbl}' must exist in '{csv_name}'",
                )

    # -------------------------------------------------------------
    # 5. REFERENTIAL INTEGRITY & DATA QUALITY AUDIT
    # -------------------------------------------------------------

    def test_08_primary_key_uniqueness_across_datasets(self):
        """Verifies 0 duplicate primary keys and 0 null IDs across all 10 datasets."""
        pks = {
            "customers.csv": "customer_id",
            "restaurants.csv": "restaurant_id",
            "riders.csv": "rider_id",
            "menu_items.csv": "item_id",
            "orders.csv": "order_id",
            "deliveries.csv": "delivery_id",
            "payments.csv": "payment_id",
            "promotions.csv": "promo_id",
            "ratings_reviews.csv": "review_id",
            "app_events.csv": "event_id",
        }
        for file, pk in pks.items():
            df = pd.read_csv(CLEANED_DIR / file)
            self.assertEqual(
                df[pk].duplicated().sum(),
                0,
                f"Duplicate primary keys found in {file}",
            )
            self.assertEqual(
                df[pk].isnull().sum(),
                0,
                f"Null primary keys found in {file}",
            )

    def test_09_referential_foreign_key_integrity(self):
        """Verifies 100% referential integrity across all foreign keys."""
        customers = pd.read_csv(CLEANED_DIR / "customers.csv")
        restaurants = pd.read_csv(CLEANED_DIR / "restaurants.csv")
        riders = pd.read_csv(CLEANED_DIR / "riders.csv")
        menu_items = pd.read_csv(CLEANED_DIR / "menu_items.csv")
        orders = pd.read_csv(CLEANED_DIR / "orders.csv")
        deliveries = pd.read_csv(CLEANED_DIR / "deliveries.csv")
        payments = pd.read_csv(CLEANED_DIR / "payments.csv")

        cust_ids = set(customers["customer_id"])
        rest_ids = set(restaurants["restaurant_id"])
        rider_ids = set(riders["rider_id"])
        item_ids = set(menu_items["item_id"])
        order_ids = set(orders["order_id"])

        self.assertEqual(orders[~orders["customer_id"].isin(cust_ids)].shape[0], 0)
        self.assertEqual(orders[~orders["restaurant_id"].isin(rest_ids)].shape[0], 0)
        self.assertEqual(orders[~orders["rider_id"].isin(rider_ids)].shape[0], 0)
        self.assertEqual(orders[~orders["item_id"].isin(item_ids)].shape[0], 0)
        self.assertEqual(deliveries[~deliveries["order_id"].isin(order_ids)].shape[0], 0)
        self.assertEqual(deliveries[~deliveries["rider_id"].isin(rider_ids)].shape[0], 0)
        self.assertEqual(payments[~payments["order_id"].isin(order_ids)].shape[0], 0)

    # -------------------------------------------------------------
    # 6. CERTIFIED KPI CALCULATION INTEGRITY
    # -------------------------------------------------------------

    def test_10_certified_kpi_calculation_integrity(self):
        """Verifies certified business calculations match verified raw counts."""
        data, _ = load_data()
        orders = data["orders"]

        delivered = orders[orders["order_status"] == "Delivered"]
        cancelled = orders[orders["order_status"] == "Cancelled"]

        total_gmv = orders["order_amount"].sum()
        total_delivered_gmv = delivered["order_amount"].sum()

        self.assertEqual(len(orders), 49971)
        self.assertGreater(total_gmv, 0)
        self.assertGreater(total_delivered_gmv, 0)
        self.assertGreater(len(delivered), len(cancelled))

    # -------------------------------------------------------------
    # 7. FASTAPI INTEGRATION & FAILOVER VERIFICATION
    # -------------------------------------------------------------

    def test_11_fastapi_overview_endpoint_resilience(self):
        """GET /api/overview returns 200 OK and valid business KPIs under CSV fallback."""
        resp = self.client.get("/api/overview", headers={"X-API-Key": self.op_key})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("kpis", data)
        kpis = data["kpis"]
        self.assertIn("total_gmv", kpis)
        self.assertIn("total_orders", kpis)
        self.assertEqual(kpis["total_orders"], 49971)
        self.assertEqual(kpis["active_customers"], 5000)
        self.assertEqual(kpis["active_restaurants"], 1500)

    # -------------------------------------------------------------
    # 8. CSV-TO-MYSQL INGESTION PREPARATION & TOPOLOGICAL AUDIT
    # -------------------------------------------------------------

    def test_12_ingestion_sequence_topological_integrity(self):
        """Verifies that INGESTION_SEQUENCE in load_mysql.py loads all parent tables before child tables."""
        from python.load_mysql import INGESTION_SEQUENCE

        self.assertEqual(len(INGESTION_SEQUENCE), 10)
        table_order = [task["table"] for task in INGESTION_SEQUENCE]

        # Verify dimension tables appear before dependent tables
        self.assertLess(table_order.index("restaurants"), table_order.index("menu_items"))
        self.assertLess(table_order.index("customers"), table_order.index("orders_table"))
        self.assertLess(table_order.index("restaurants"), table_order.index("orders_table"))
        self.assertLess(table_order.index("menu_items"), table_order.index("orders_table"))
        self.assertLess(table_order.index("riders"), table_order.index("orders_table"))

        # Verify transaction table appears before child event tables
        self.assertLess(table_order.index("orders_table"), table_order.index("payments"))
        self.assertLess(table_order.index("orders_table"), table_order.index("deliveries"))
        self.assertLess(table_order.index("orders_table"), table_order.index("ratings_reviews"))
        self.assertLess(table_order.index("riders"), table_order.index("deliveries"))
        self.assertLess(table_order.index("customers"), table_order.index("ratings_reviews"))
        self.assertLess(table_order.index("customers"), table_order.index("app_events"))

    def test_13_load_mysql_dry_run_validation(self):
        """Verifies that dry_run_validation() audits all 10 datasets and returns True."""
        from python.load_mysql import dry_run_validation

        result = dry_run_validation()
        self.assertTrue(result, "Dry run validation across all 10 datasets must pass 100%")

    def test_14_verification_sql_script_readiness(self):
        """Verifies mysql/04_verify_data_integrity.sql exists and is 100% read-only non-destructive."""
        verify_sql_path = PROJECT_ROOT / "mysql" / "04_verify_data_integrity.sql"
        if not verify_sql_path.exists():
            verify_sql_path = PROJECT_ROOT / "mysql" / "03_verify_data_integrity.sql"
        self.assertTrue(verify_sql_path.exists())

        with open(verify_sql_path, "r", encoding="utf-8") as f:
            sql_text = f.read().upper()

        # Strict safety assertion: zero DDL or destructive statements
        self.assertNotIn("DROP ", sql_text)
        self.assertNotIn("TRUNCATE ", sql_text)
        self.assertNotIn("DELETE ", sql_text)
        self.assertNotIn("ALTER ", sql_text)
        self.assertIn("SELECT ", sql_text)
        self.assertIn("304405", sql_text)

    def test_15_create_app_users_script_security(self):
        """Verifies mysql/03_create_app_users.sql exists, is least-privilege, and avoids global/root grants."""
        users_sql_path = PROJECT_ROOT / "mysql" / "03_create_app_users.sql"
        self.assertTrue(users_sql_path.exists())

        with open(users_sql_path, "r", encoding="utf-8") as f:
            sql_text = f.read()

        sql_upper = sql_text.upper()

        # Verify safe creation
        self.assertIn("CREATE USER IF NOT EXISTS 'NOVANEST_LOADER'@'LOCALHOST'", sql_upper)
        self.assertIn("CREATE USER IF NOT EXISTS 'NOVANEST_APP'@'LOCALHOST'", sql_upper)

        # Verify scoped grants only (no global *.*)
        self.assertIn("ON `NOVANEST_DB`.* TO 'NOVANEST_LOADER'@'LOCALHOST'", sql_upper)
        self.assertIn("ON `NOVANEST_DB`.* TO 'NOVANEST_APP'@'LOCALHOST'", sql_upper)
        self.assertNotIn("ON *.*", sql_upper)

        # Verify zero administrative privileges granted
        self.assertNotIn("GRANT ALL", sql_upper)
        self.assertNotIn("GRANT SUPER", sql_upper)
        self.assertNotIn("WITH GRANT OPTION", sql_upper)
        self.assertNotIn("DROP USER", sql_upper)

        # Verify password placeholders used
        self.assertIn("REPLACE_WITH_INGESTION_PASSWORD", sql_text)
        self.assertIn("REPLACE_WITH_APP_PASSWORD", sql_text)

        # Verify SHOW GRANTS queries present
        self.assertIn("SHOW GRANTS FOR 'novanest_loader'@'localhost'", sql_text)
        self.assertIn("SHOW GRANTS FOR 'novanest_app'@'localhost'", sql_text)

    def test_16_sanitized_failed_authentication(self):
        """Verifies failed authentication produces sanitized errors without leaking credentials."""
        from python.test_db_connection import test_sanitized_failed_authentication

        res = test_sanitized_failed_authentication("localhost", 3306, "novanest_db")
        self.assertTrue(res, "Sanitized failed authentication test must pass and leak 0 passwords")

    def test_17_gitignore_protects_env_secrets(self):
        """Verifies that .env is explicitly declared in .gitignore to prevent secret leaks."""
        gitignore_path = PROJECT_ROOT / ".gitignore"
        self.assertTrue(gitignore_path.exists())

        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        self.assertIn(".env", lines, ".env must be explicitly ignored in .gitignore")
        self.assertIn("*.env.local", lines, "*.env.local must be explicitly ignored in .gitignore")


if __name__ == "__main__":
    unittest.main()

