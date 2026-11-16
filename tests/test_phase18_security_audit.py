"""
Phase 18 — Comprehensive Defensive Security Audit & Penetration Testing Suite
============================================================================
Validates security postures, authorization boundaries (RBAC), authentication mechanics,
fail-closed defenses, SQL AST and query parameter sanitization, PII redaction,
Nginx security headers, MySQL privilege boundaries, and database record integrity.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
import urllib.request
import urllib.error

API_BASE = "http://localhost:8001"
NGINX_BASE = "http://localhost:80"

ADMIN_KEY = "test-admin-key-phase06-8"
OPERATOR_KEY = "test-operator-key-phase06-8"
VIEWER_KEY = "test-viewer-key-phase06-8"
INVALID_KEY = "invalid-unauthorized-key-xyz"


def http_request(
    path: str,
    method: str = "GET",
    token: str | None = None,
    data: dict | None = None,
    headers: dict | None = None,
    base: str = API_BASE,
) -> tuple[int, dict | list | str, dict]:
    """Helper to send HTTP requests and capture status, payload, and response headers."""
    req_headers = dict(headers or {})
    if token is not None:
        req_headers["X-API-Key"] = token
        req_headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    url = f"{base}{path}"
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return resp.status, parsed, resp_headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        resp_headers = {k.lower(): v for k, v in e.headers.items()}
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed, resp_headers


class TestPhase18SecurityAudit(unittest.TestCase):
    """Phase 18 Security Hardening & Penetration Verification Test Suite."""

    # -------------------------------------------------------------------------
    # 1. Authentication Mechanics & Fail-Closed Guardrails
    # -------------------------------------------------------------------------

    def test_01_missing_auth_header_fails_closed(self):
        """Unauthenticated requests to protected endpoints must return HTTP 401."""
        status, body, _ = http_request("/api/overview", token=None)
        self.assertEqual(status, 401, f"Expected 401 without auth, got {status}: {body}")

    def test_02_invalid_token_rejected(self):
        """Invalid API key/token must return HTTP 401 Unauthorized."""
        status, body, _ = http_request("/api/overview", token=INVALID_KEY)
        self.assertEqual(status, 401, f"Expected 401 for invalid token, got {status}: {body}")

    def test_03_query_param_token_rejected_as_insecure(self):
        """Tokens passed via query string (?token= or ?api_key=) must not authenticate."""
        status, body, _ = http_request(f"/api/overview?api_key={VIEWER_KEY}", token=None)
        self.assertEqual(
            status, 401,
            f"Query parameter token should be rejected (CWE-598), got {status}: {body}"
        )

    # -------------------------------------------------------------------------
    # 2. Role-Based Access Control (RBAC) & Principle of Least Privilege
    # -------------------------------------------------------------------------

    def test_04_viewer_role_access_aggregated_endpoints(self):
        """Viewer role must have access to aggregated operational and executive views."""
        status, body, _ = http_request("/api/overview", token=VIEWER_KEY)
        self.assertEqual(status, 200, f"Viewer should access overview, got {status}")
        self.assertIn("kpis", body)

        status, body, _ = http_request("/api/prescriptive/recommendations", token=VIEWER_KEY)
        self.assertEqual(status, 200, f"Viewer should access recommendations, got {status}")
        self.assertIsInstance(body, list)

    def test_05_viewer_role_forbidden_on_customer_pii(self):
        """Viewer role must be blocked (HTTP 403) from accessing raw Customer PII."""
        status, body, _ = http_request("/api/records/customers?page=1&page_size=10", token=VIEWER_KEY)
        self.assertEqual(
            status, 403,
            f"Viewer must be forbidden from accessing raw customers table (CWE-285), got {status}: {body}"
        )

    def test_06_operator_role_permitted_on_customer_pii(self):
        """Operator role must be permitted to access customer records for support operations."""
        status, body, _ = http_request("/api/records/customers?page=1&page_size=10", token=OPERATOR_KEY)
        self.assertEqual(status, 200, f"Operator should access customers, got {status}")
        self.assertIn("records", body)
        self.assertEqual(len(body["records"]), 10)

    def test_07_viewer_role_forbidden_on_session_reset(self):
        """Viewer role must be blocked from state-mutating / session-reset operations."""
        status, body, _ = http_request(
            "/api/ai/reset",
            method="POST",
            token=VIEWER_KEY,
            data={"session_id": "test_security_session"},
        )
        self.assertIn(status, [403, 401], f"Viewer must not reset AI sessions, got {status}")

    # -------------------------------------------------------------------------
    # 3. SQL Injection Defense & Input Validation (CWE-89)
    # -------------------------------------------------------------------------

    def test_08_sql_injection_sort_by_whitelist(self):
        """Invalid or SQL-injected sort_by column names must be rejected."""
        malicious_sorts = [
            "name; DROP TABLE customers;--",
            "name UNION SELECT 1,2,3,4--",
            "(SELECT 1 FROM (SELECT SLEEP(2))x)",
            "nonexistent_column_injection",
        ]
        for inj in malicious_sorts:
            enc = urllib.request.quote(inj)
            status, body, _ = http_request(
                f"/api/records/orders?page=1&page_size=10&sort_by={enc}",
                token=OPERATOR_KEY,
            )
            self.assertIn(
                status, [400, 422],
                f"SQL injection in sort_by ('{inj}') must return 400/422, got {status}: {body}"
            )

    def test_09_sql_injection_table_name_whitelist(self):
        """Direct attempts to access unauthorized or injected table names must be rejected."""
        malicious_entities = [
            "information_schema.tables",
            "mysql.user",
            "customers; DROP TABLE payments;--",
            "nonexistent_entity",
        ]
        for ent in malicious_entities:
            enc = urllib.request.quote(ent)
            status, body, _ = http_request(
                f"/api/records/{enc}?page=1&page_size=10",
                token=OPERATOR_KEY,
            )
            self.assertIn(
                status, [400, 404, 422],
                f"Unauthorized entity ('{ent}') must return 400/404/422, got {status}: {body}"
            )

    def test_10_bounded_pagination_limits(self):
        """Excessive page_size (> 100) or negative pages must be rejected."""
        status, body, _ = http_request("/api/records/orders?page=1&page_size=1000", token=OPERATOR_KEY)
        self.assertIn(status, [400, 422], f"page_size=1000 must be rejected, got {status}")

        status, body, _ = http_request("/api/records/orders?page=-5&page_size=10", token=OPERATOR_KEY)
        self.assertIn(status, [400, 422], f"page=-5 must be rejected, got {status}")

    # -------------------------------------------------------------------------
    # 4. Nginx Reverse Proxy & HTTP Security Headers (CWE-693)
    # -------------------------------------------------------------------------

    def test_11_nginx_security_headers_on_root(self):
        """Nginx root endpoint must return all mandatory HTTP security headers."""
        status, _, headers = http_request("/", base=NGINX_BASE)
        self.assertEqual(status, 200)

        required_headers = [
            "x-frame-options",
            "x-content-type-options",
            "x-xss-protection",
            "referrer-policy",
            "permissions-policy",
            "content-security-policy",
        ]
        for h in required_headers:
            self.assertIn(h, headers, f"Missing mandatory security header: {h}")

        self.assertEqual(headers["x-frame-options"], "SAMEORIGIN")
        self.assertEqual(headers["x-content-type-options"], "nosniff")

    # -------------------------------------------------------------------------
    # 5. MySQL Application Least Privilege Verification
    # -------------------------------------------------------------------------

    def test_12_mysql_app_user_cannot_ddl(self):
        """novanest_app user must NOT be permitted to execute DDL statements (CREATE/DROP)."""
        cmd = [
            "docker", "exec", "novanest-db",
            "mysql", "-u", "novanest_app", "-pChinnu_2311", "novanest_db",
            "-e", "CREATE TABLE test_security_probe_ddl (id int);"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0, "novanest_app should fail when attempting DDL CREATE TABLE")
        self.assertIn("command denied", res.stderr.lower(), f"Expected access denied, got: {res.stderr}")

    # -------------------------------------------------------------------------
    # 6. Data Integrity & Canonical Record Invariance
    # -------------------------------------------------------------------------

    def test_13_canonical_dataset_integrity(self):
        """Verify that exactly 304,405 records remain intact across all 10 tables."""
        cmd = [
            "docker", "exec", "novanest-db",
            "mysql", "-u", "root", "-pdev_root_secret_change_me", "-N", "-e",
            "SELECT sum(cnt) FROM ("
            "SELECT count(*) as cnt FROM novanest_db.customers UNION ALL "
            "SELECT count(*) FROM novanest_db.restaurants UNION ALL "
            "SELECT count(*) FROM novanest_db.menu_items UNION ALL "
            "SELECT count(*) FROM novanest_db.riders UNION ALL "
            "SELECT count(*) FROM novanest_db.orders_table UNION ALL "
            "SELECT count(*) FROM novanest_db.deliveries UNION ALL "
            "SELECT count(*) FROM novanest_db.payments UNION ALL "
            "SELECT count(*) FROM novanest_db.ratings_reviews UNION ALL "
            "SELECT count(*) FROM novanest_db.promotions UNION ALL "
            "SELECT count(*) FROM novanest_db.app_events"
            ") as t;"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"MySQL query failed: {res.stderr}")
        total = int(res.stdout.strip())
        self.assertEqual(total, 304405, f"Canonical record count altered! Expected 304405, got {total}")

    # -------------------------------------------------------------------------
    # 7. UI Data Contracts & Crash Resilience
    # -------------------------------------------------------------------------

    def test_14_prescriptive_recommendations_contract(self):
        """Prescriptive recommendations must guarantee non-null list for supporting_evidence."""
        status, body, _ = http_request("/api/prescriptive/recommendations", token=VIEWER_KEY)
        self.assertEqual(status, 200)
        self.assertIsInstance(body, list)
        self.assertGreater(len(body), 0)
        for rec in body:
            self.assertIn("supporting_evidence", rec)
            self.assertIsInstance(rec["supporting_evidence"], list, "supporting_evidence must be list")
            self.assertIn("problem_statement", rec)
            self.assertIsInstance(rec["problem_statement"], str)

    def test_15_prescriptive_financial_charts_contract(self):
        """Financial charts must guarantee arrays for contribution_margin_waterfall."""
        status, body, _ = http_request("/api/prescriptive/financial-charts", token=VIEWER_KEY)
        self.assertEqual(status, 200)
        self.assertIn("contribution_margin_waterfall", body)
        self.assertIsInstance(body["contribution_margin_waterfall"], list)
        self.assertIn("revenue_vs_cost_comparison", body)
        self.assertIsInstance(body["revenue_vs_cost_comparison"], list)


if __name__ == "__main__":
    unittest.main()
