"""
NovaNest Phase 06.0 — Legacy AI Stabilization & Data Grounding Regression Suite
================================================================================
Tests all 12 stabilization targets without mocking core analytical logic:
1. Data grounding schema & zero fake fallbacks (restaurants, rider_allocation, ETA, leakage)
2. Financial aggregation & unconfirmed leakage classification (is_confirmed_loss=False)
3. Empirical root-cause calculation & strict anti-hardcoding assertions
4. Broad & natural-language business performance routing
5. Multi-domain synthesis (financial + operational comparison)
6. Live Next Best Action (NBA) recommendation engine integration
7. 9-table SQLite data parity & explicit dataset-to-table mapping
8. SQL AST security enforcement preservation (sqlite_master, UNION, multi-stmt, writes)
9. Conversation manager: principal isolation, 30m TTL, 250-session LRU, 12-turn cap, PII redaction, no DataFrames
10. FastAPI RBAC & principal-scoped /api/ai/ask and /api/ai/reset isolation
11. Certified business_insights.py math & Streamlit Page 07 + Page 09 AppTest execution
"""

import os
import secrets
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
PYTHON_DIR = PROJECT_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from api import main as api_main
from api.auth import AuthPrincipal
from api.loader import load_data
from python.ai.analyst.conversation_manager import (
    _SESSIONS,
    get_session_history,
    make_scoped_session_key,
    record_turn,
    redact_pii,
    reset_session,
    resolve_follow_up_query,
)
from python.ai.analyst.data_grounding import retrieve_grounded_business_context
from python.ai.analyst.orchestrator import analyze_business_inquiry
from python.ai.analyst.root_cause import perform_root_cause_analysis
from python.ai.analyst.sql_agent import (
    ALLOWED_TABLES,
    DATASET_TO_SQLITE_TABLE_MAP,
    build_readonly_sqlite_connection,
    execute_safe_sql,
    verify_sqlite_table_parity,
)
from python.ai.analyst.universal_router import classify_query
from python.ai.insights.business_insights import generate_business_insights
from python.ai.provider.base import AIProviderResult, ProviderStatus


class _StubProvider:
    def is_configured(self):
        return False

    def get_status(self):
        return {"status": "unconfigured", "message": "Offline empirical verification"}


class TestPhase060Stabilization(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.source = load_data(force_reload=True)
        cls.sqlite_conn = build_readonly_sqlite_connection(cls.data)
        cls.stub_ai = _StubProvider()

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "sqlite_conn", None) is not None:
            cls.sqlite_conn.close()

    # ------------------------------------------------------------------
    # 1 & 2. Data Grounding Schema, Financial Accuracy & Leakage Caveat
    # ------------------------------------------------------------------
    def test_01_data_grounding_schema_and_no_fake_fallbacks(self) -> None:
        # Restaurants: real avg_rating (4.25), not hardcoded 4.2
        ctx_rest = retrieve_grounded_business_context("Show restaurant partner ratings", self.data, self.source)
        self.assertEqual(ctx_rest["domain"], "restaurants")
        m_rest = {m["label"]: m["value"] for m in ctx_rest["verified_metrics"]}
        self.assertIn("4.25", m_rest["Average Store Rating"])
        self.assertNotIn("4.20", m_rest["Average Store Rating"])

        # Operations & rider_allocation: real duration (37.38 mins), SLA (67.74% / 32.26%), real order_city assignments
        ctx_ops = retrieve_grounded_business_context("Show delivery ETA and rider allocation", self.data, self.source)
        self.assertEqual(ctx_ops["domain"], "operations")
        m_ops = {m["label"]: m["value"] for m in ctx_ops["verified_metrics"]}
        self.assertIn("37.38", m_ops["Average Delivery ETA"])
        self.assertIn("67.74%", m_ops["On-Time SLA Compliance (<=45m)"])
        self.assertIn("16,119", m_ops["SLA Breaches (>45m)"])
        self.assertTrue(len(ctx_ops["table_data"]) >= 5)
        for row in ctx_ops["table_data"]:
            self.assertIn("recommended_assignments", row)
            self.assertNotIn("current", row)
            self.assertNotEqual(row.get("recommended_assignments"), 60)

        # Leakage: aggregated by leakage_type (~₹5.54L / ₹553,946.31), explicitly unconfirmed (is_confirmed_loss=False)
        ctx_leak = retrieve_grounded_business_context("Where is revenue leakage occurring?", self.data, self.source)
        self.assertEqual(ctx_leak["domain"], "financial_leakage")
        self.assertFalse(ctx_leak["is_confirmed_loss"])
        m_leak = {m["label"]: m["value"] for m in ctx_leak["verified_metrics"]}
        val_str = m_leak["Potential Revenue Leakage Exposure (Unverified)"]
        self.assertIn("553,946.31", val_str)
        self.assertNotIn("12.50L", val_str)
        # Aggregated into distinct leakage types (not 4,669 raw rows!)
        self.assertEqual(len(ctx_leak["table_data"]), 3)
        self.assertTrue(all(r["is_confirmed_loss"] is False for r in ctx_leak["table_data"]))

        # Cancellations: Coimbatore highest, no fake North Hub / 96.2
        ctx_canc = retrieve_grounded_business_context("What is our cancellation rate?", self.data, self.source)
        self.assertEqual(ctx_canc["domain"], "cancellations")
        self.assertIn("3.96%", ctx_canc["context_summary"])
        self.assertIn("Coimbatore", ctx_canc["context_summary"])
        self.assertNotIn("North Hub", ctx_canc["context_summary"])

    def test_02_financial_overview_and_empty_missing_column_no_fake_fallback(self) -> None:
        empty_data = {k: pd.DataFrame() for k in self.data}
        ctx = retrieve_grounded_business_context("Show delivery ETA and restaurant rating", empty_data, "EmptyMock")
        summary_blob = ctx["context_summary"] + " " + " ".join(m["value"] for m in ctx["verified_metrics"])
        for fake in ["32.4", "94.2", "96.2", "North Hub", "12.50L", "4.20"]:
            self.assertNotIn(fake, summary_blob)

    # ------------------------------------------------------------------
    # 3. Empirical Root-Cause Analysis & Anti-Hardcoding Enforcement
    # ------------------------------------------------------------------
    def test_03_root_cause_empirical_and_zero_hardcoded_fiction(self) -> None:
        queries = [
            "Why is delivery performance declining?",
            "Why are cancellations increasing?",
            "Why do we have revenue leakage and margin compression?",
            "Which restaurant factors drive poor ratings?",
            "Why are customers churning?",
        ]
        forbidden_legacy_claims = [
            "32.4 minutes",
            "5.8% (",
            "East Hub",
            "8.9 km transit distance compared to 4.3 km",
            "18 partner kitchens exceed 24 minutes",
            "2.4x higher cancellation",
            "64% of cancellations occurred after",
            "22% of cancellations occurred within 5 minutes",
            "412 accounts",
            "(8.2% of registered",
            "₹12.50 Lakhs",
            "18.2%",
            "average 64 days",
            "compared to 14 days",
            "3.1 stars vs 4.4",
            "78% of at-risk patrons",
        ]

        all_outputs = []
        for q in queries:
            rca = perform_root_cause_analysis(q, self.data)
            self.assertIn("observed_facts", rca)
            self.assertIn("contributing_factors", rca)
            self.assertIn("uncertainties", rca)
            self.assertIn("recommended_actions", rca)
            blob = " ".join(
                rca["observed_facts"]
                + rca["uncertainties"]
                + rca["recommended_actions"]
                + [f["evidence"] for f in rca["contributing_factors"]]
            )
            all_outputs.append((q, rca, blob))
            for legacy in forbidden_legacy_claims:
                self.assertNotIn(legacy, blob, f"Legacy fabricated string '{legacy}' found in RCA for '{q}'")

        # Check specific verified numbers appear empirically
        _, _, deliv_blob = all_outputs[0]
        self.assertIn("37.38", deliv_blob)
        self.assertIn("16,119", deliv_blob)
        self.assertIn("32.26%", deliv_blob)

        _, canc_rca, canc_blob = all_outputs[1]
        self.assertIn("3.96%", canc_blob)
        self.assertIn("1.16x", canc_blob)

        _, leak_rca, leak_blob = all_outputs[2]
        self.assertFalse(leak_rca.get("is_confirmed_loss", True))
        self.assertIn("553,946.31", leak_blob)

        _, _, churn_blob = all_outputs[4]
        self.assertIn("781", churn_blob)
        self.assertIn("15.62%", churn_blob)
        self.assertIn("0.5161", churn_blob)

    # ------------------------------------------------------------------
    # 4 & 5. Broad Routing & Multi-Domain Query Support
    # ------------------------------------------------------------------
    def test_04_benchmark_routing_and_multi_domain_synthesis(self) -> None:
        # 1. Broad performance
        r1 = analyze_business_inquiry("Analyze my business performance.", self.data, self.source, self.sqlite_conn, "p60_b1", ai_provider=self.stub_ai)
        self.assertEqual(r1["route"], "BUSINESS_DATA")
        self.assertTrue(r1["requires_business_data"])
        m1 = {m["label"]: m["value"] for m in r1["verified_metrics"]}
        self.assertIn("₹4.66 Cr", m1["Gross Merchandise Value (GMV)"])
        self.assertIn("₹4.64 Cr", m1["Net Revenue (Delivered)"])

        # 2. High churn customers
        r2 = analyze_business_inquiry("How many high churn customers do we have?", self.data, self.source, self.sqlite_conn, "p60_b2", ai_provider=self.stub_ai)
        self.assertEqual(r2["route"], "BUSINESS_DATA")
        self.assertIn("781", r2["answer"])
        self.assertIn("15.62%", r2["answer"])
        self.assertIn("0.5161", r2["answer"])

        # 3. Multi-domain financial + operational comparison
        r3 = analyze_business_inquiry("Compare financial and operational performance.", self.data, self.source, self.sqlite_conn, "p60_b3", ai_provider=self.stub_ai)
        self.assertEqual(r3["route"], "BUSINESS_DATA")
        self.assertTrue(r3["is_multi_domain"])
        self.assertIn("financial", r3["domains"])
        self.assertIn("operations", r3["domains"])
        labels3 = {m["label"] for m in r3["verified_metrics"]}
        self.assertIn("Gross Merchandise Value (GMV)", labels3)
        self.assertIn("Average Delivery ETA", labels3)

        # 4. Delivery RCA
        r4 = analyze_business_inquiry("Why is delivery performance declining?", self.data, self.source, self.sqlite_conn, "p60_b4", ai_provider=self.stub_ai)
        self.assertEqual(r4["route"], "ROOT_CAUSE")
        self.assertIsNotNone(r4["root_cause_analysis"])
        self.assertIn("37.38", r4["answer"])

        # 5. Restaurants attention (SQLite NL2SQL)
        r5 = analyze_business_inquiry("Which restaurants need attention?", self.data, self.source, self.sqlite_conn, "p60_b5", ai_provider=self.stub_ai)
        self.assertEqual(r5["route"], "NL2SQL")
        self.assertTrue(r5["sql_valid"])
        self.assertGreater(len(r5["data_rows"]), 0)

        # 6. Recommendations via live NBA engine
        r6 = analyze_business_inquiry("Recommend actions to improve profitability.", self.data, self.source, self.sqlite_conn, "p60_b6", ai_provider=self.stub_ai)
        self.assertEqual(r6["route"], "RECOMMENDATIONS")
        self.assertGreater(len(r6["recommendations"]), 0)
        self.assertNotIn("₹12.5L", r6["answer"])
        self.assertNotIn("Preserve ₹12.5L", str(r6["recommendations"]))

        # Verify general routing remained intact
        for non_biz_q in ["What is Python?", "Calculate compound interest on 2000 at 10% for 2 years", "Explain machine learning in simple words"]:
            clf = classify_query(non_biz_q)
            self.assertFalse(clf["requires_business_data"], f"Non-business query '{non_biz_q}' must not require business data")

    # ------------------------------------------------------------------
    # 7 & 8. SQLite 9-Table Parity & AST Security Preservation
    # ------------------------------------------------------------------
    def test_05_sqlite_9_table_parity_and_security_preservation(self) -> None:
        self.assertEqual(len(ALLOWED_TABLES), 9)
        self.assertEqual(set(DATASET_TO_SQLITE_TABLE_MAP.keys()), set(ALLOWED_TABLES))

        parity = verify_sqlite_table_parity(self.sqlite_conn, self.data)
        self.assertEqual(set(parity.keys()), set(ALLOWED_TABLES))
        for tbl, report in parity.items():
            self.assertTrue(report["loaded"], f"SQLite table '{tbl}' missing: {report}")
            self.assertTrue(report["row_parity"], f"Row count mismatch for '{tbl}': {report}")
            self.assertGreater(report["actual_rows"], 0)

        # Query previously missing tables (payments, menu_items, ratings_reviews, promotions)
        for tbl in ("payments", "menu_items", "ratings_reviews", "promotions"):
            df_res, msg = execute_safe_sql(f"SELECT COUNT(*) AS row_cnt FROM {tbl}", self.sqlite_conn)
            self.assertIsNotNone(df_res, f"Query on {tbl} failed: {msg}")
            self.assertGreater(int(df_res.iloc[0]["row_cnt"]), 0)

        # Verify security blocks stay intact
        unsafe_probes = [
            "SELECT name FROM sqlite_master WHERE type='table'",
            "SELECT * FROM sqlite_schema",
            "SELECT customer_id FROM customers UNION SELECT name FROM sqlite_master",
            "SELECT * FROM customers, sqlite_master LIMIT 5",
            "SELECT * FROM orders; DROP TABLE orders",
            "DELETE FROM orders WHERE order_id = 'O0000001'",
            "PRAGMA table_info(orders)",
        ]
        for probe in unsafe_probes:
            df_bad, msg_bad = execute_safe_sql(probe, self.sqlite_conn)
            self.assertIsNone(df_bad, f"Unsafe SQL probe was NOT blocked: {probe}")
            self.assertTrue(len(msg_bad) > 0)

    # ------------------------------------------------------------------
    # 9. Conversation Manager: Isolation, TTL, LRU, Turn Cap, PII, No DF
    # ------------------------------------------------------------------
    def test_06_conversation_manager_isolation_ttl_lru_and_pii_redaction(self) -> None:
        p1 = AuthPrincipal(role="operator", scopes=frozenset({"read", "operator"}), principal_id="operator:aaa111")
        p2 = AuthPrincipal(role="operator", scopes=frozenset({"read", "operator"}), principal_id="operator:bbb222")
        reset_session("shared_sess", principal=p1)
        reset_session("shared_sess", principal=p2)

        # Cross-principal isolation under same session_id
        record_turn("shared_sess", "user", "What is our cancellation rate?", "BUSINESS_DATA", "cancellations", principal=p1)
        record_turn("shared_sess", "user", "What is our total revenue?", "BUSINESS_DATA", "financial", principal=p2)

        aug1, _, topic1 = resolve_follow_up_query("Which city is the worst?", "shared_sess", principal=p1)
        aug2, _, topic2 = resolve_follow_up_query("Which city is the worst?", "shared_sess", principal=p2)
        self.assertEqual(topic1, "cancellations")
        self.assertIn("cancellation", aug1.lower())
        self.assertEqual(topic2, "financial")

        # Reset by p1 clears ONLY p1, leaves p2 intact
        self.assertTrue(reset_session("shared_sess", principal=p1))
        self.assertEqual(len(get_session_history("shared_sess", principal=p1)), 0)
        self.assertEqual(len(get_session_history("shared_sess", principal=p2)), 1)
        self.assertFalse(reset_session("shared_sess", principal=p1))

        # No raw DataFrame stored & PII redaction leaves currency intact
        df_dummy = pd.DataFrame({"a": [1, 2]})
        record_turn(
            "shared_sess",
            "user",
            "Contact me at user@example.com or phone 9876543210 with Bearer my_secret_token_12345 regarding ₹46,590,125.00 revenue",
            "BUSINESS_DATA",
            "financial",
            principal=p1,
            metadata={"raw_df": df_dummy, "note": "ok"},
        )
        hist_p1 = get_session_history("shared_sess", principal=p1)
        self.assertIn("[REDACTED_EMAIL]", hist_p1[0]["content"])
        self.assertIn("[REDACTED_PHONE]", hist_p1[0]["content"])
        self.assertIn("[REDACTED_TOKEN]", hist_p1[0]["content"])
        self.assertIn("46,590,125.00", hist_p1[0]["content"])
        stored_entry = _SESSIONS[make_scoped_session_key("shared_sess", p1)]
        for turn in stored_entry["turns"]:
            self.assertNotIsInstance(turn.get("metadata", {}).get("raw_df"), pd.DataFrame)

        # Turn cap (12 turns)
        reset_session("cap_sess", principal=p1)
        for idx in range(16):
            record_turn("cap_sess", "user", f"Turn message #{idx}", "GENERAL", "general", principal=p1)
        self.assertLessEqual(len(get_session_history("cap_sess", limit=20, principal=p1)), 12)

        # Idle TTL (30 mins = 1800s)
        reset_session("ttl_sess", principal=p1)
        record_turn("ttl_sess", "user", "Short lived context", "GENERAL", "cancellations", principal=p1)
        ttl_key = make_scoped_session_key("ttl_sess", p1)
        _SESSIONS[ttl_key]["last_accessed"] -= 1900.0
        self.assertEqual(len(get_session_history("ttl_sess", principal=p1)), 0)
        self.assertNotIn(ttl_key, _SESSIONS)

        # LRU eviction (cap = 250)
        _SESSIONS.clear()
        for i in range(255):
            record_turn(f"lru_{i}", "user", f"Msg {i}", "GENERAL", "general", principal=p1)
        self.assertLessEqual(len(_SESSIONS), 250)
        self.assertNotIn(make_scoped_session_key("lru_0", p1), _SESSIONS)
        self.assertIn(make_scoped_session_key("lru_254", p1), _SESSIONS)

    # ------------------------------------------------------------------
    # 10. FastAPI RBAC & Session Ownership Enforcement
    # ------------------------------------------------------------------
    def test_07_fastapi_ai_rbac_and_cross_principal_reset_isolation(self) -> None:
        v_key = secrets.token_urlsafe(24)
        o_key = secrets.token_urlsafe(24)
        a_key = secrets.token_urlsafe(24)
        prev = {k: os.environ.get(k) for k in ("NOVANEST_VIEWER_KEY", "NOVANEST_API_KEY", "NOVANEST_ADMIN_KEY")}
        try:
            os.environ["NOVANEST_VIEWER_KEY"] = v_key
            os.environ["NOVANEST_API_KEY"] = o_key
            os.environ["NOVANEST_ADMIN_KEY"] = a_key

            client = TestClient(api_main.app)
            h_view = {"X-API-Key": v_key}
            h_op = {"X-API-Key": o_key}
            h_adm = {"X-API-Key": a_key}

            # Unauthenticated -> 401
            self.assertEqual(client.post("/api/ai/ask", json={"question": "hi"}).status_code, 401)
            self.assertEqual(client.post("/api/ai/reset", json={"session_id": "s_iso"}).status_code, 401)

            # Viewer -> 403
            self.assertEqual(client.post("/api/ai/ask", json={"question": "Analyze my business performance."}, headers=h_view).status_code, 403)
            self.assertEqual(client.post("/api/ai/reset", json={"session_id": "s_iso"}, headers=h_view).status_code, 403)

            # Operator asks about cancellations under session_id='s_iso'
            res_op1 = client.post("/api/ai/ask", json={"question": "What is our cancellation rate?", "session_id": "s_iso"}, headers=h_op)
            self.assertEqual(res_op1.status_code, 200)
            self.assertIn("3.96%", res_op1.json()["answer"])

            # Admin cannot wipe operator's principal-scoped session when calling reset on 's_iso'
            self.assertEqual(client.post("/api/ai/reset", json={"session_id": "s_iso"}, headers=h_op).status_code, 403)
            res_adm_reset = client.post("/api/ai/reset", json={"session_id": "s_iso"}, headers=h_adm)
            self.assertEqual(res_adm_reset.status_code, 200)
            self.assertFalse(res_adm_reset.json()["cleared"])

            # Operator follow-up STILL resolves against operator's cancellation session!
            res_op2 = client.post("/api/ai/ask", json={"question": "Which region is the worst?", "session_id": "s_iso"}, headers=h_op)
            self.assertEqual(res_op2.status_code, 200)
            self.assertIn("cancellation", (res_op2.json().get("resolved_query") or "").lower())

            # Operator can query payments via 9-table FastAPI SQLite engine
            res_sql = client.post("/api/ai/ask", json={"question": "SELECT payment_method, COUNT(*) AS cnt FROM payments GROUP BY payment_method", "session_id": "s_sql"}, headers=h_op)
            self.assertEqual(res_sql.status_code, 200)
            self.assertTrue(res_sql.json()["sql_valid"])
            self.assertGreater(len(res_sql.json()["data_rows"]), 0)
        finally:
            for k, v in prev.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    # ------------------------------------------------------------------
    # 11. Certified business_insights.py + Streamlit Page 07 & 09 AppTest
    # ------------------------------------------------------------------
    def test_08_certified_business_insights(self) -> None:
        points = generate_business_insights(self.data["orders"], self.data["customers"])
        joined = "\n".join(points)
        self.assertIn("46,590,125.00", joined)
        self.assertIn("46,425,992.00", joined)
        self.assertIn("967.33", joined)
        self.assertIn("3.96%", joined)

    def test_09_streamlit_page07_and_page09_runtime(self) -> None:
        from streamlit.testing.v1 import AppTest

        at7 = AppTest.from_file(str(PROJECT_ROOT / "streamlit_app" / "pages" / "07_Ask_NovaNest.py"), default_timeout=45)
        at7.run()
        self.assertEqual(len(at7.exception), 0, f"Page 07 initial render exception: {at7.exception}")

        # Click broad business performance quick prompt button
        perf_buttons = [b for b in at7.button if "Analyze my business performance" in b.label]
        self.assertEqual(len(perf_buttons), 1)
        perf_buttons[0].click().run()
        self.assertEqual(len(at7.exception), 0, f"Page 07 prompt execution exception: {at7.exception}")
        md_text = "\n".join(m.value for m in at7.markdown)
        self.assertIn("BUSINESS_DATA", md_text)
        self.assertIn("4.66", md_text)

        # Page 09 Command Center sanity
        at9 = AppTest.from_file(str(PROJECT_ROOT / "streamlit_app" / "pages" / "09_NovaNest_Command_Center.py"), default_timeout=45)
        at9.run()
        self.assertEqual(len(at9.exception), 0, f"Page 09 exception: {at9.exception}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
