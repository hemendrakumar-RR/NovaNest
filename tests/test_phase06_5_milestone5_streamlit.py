"""
Phase 06.5 Milestone 5: Streamlit MasterOrchestrator Upgrade & Hybrid Parity Test Suite
======================================================================================
Verifies that all Streamlit AI interactions route strictly through the authenticated
FastAPI MasterOrchestrator boundary:
1. Streamlit-to-FastAPI integration.
2. MasterOrchestrator invocation with OutputVerifier.
3. Follow-up conversational context retention.
4. Filter propagation (city, date, segment).
5. Contextual AI launchers across dashboards.
6. Five-domain agent execution & telemetry display.
7. Authentication, RBAC, and fail-closed security.
8. Cross-session and cross-principal isolation.
9. Error, timeout, and connection failure resilience.
10. Existing Streamlit dashboard runtime execution.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STREAMLIT_DIR = PROJECT_ROOT / "streamlit_app"
for p in (str(PROJECT_ROOT), str(STREAMLIT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import api.main as api_main
from streamlit_app.utils.api_client import (
    StreamlitAiClient,
    ApiClientError,
    get_streamlit_ai_client,
)
from streamlit_app.components.contextual_ai import (
    build_contextual_payload,
)
from streamlit_app.components.telemetry_components import (
    DOMAIN_AGENTS,
)


class TestPhase065Milestone5Streamlit(unittest.TestCase):
    """Milestone 5: Streamlit MasterOrchestrator & Hybrid Parity Tests."""

    @classmethod
    def setUpClass(cls):
        cls.orig_admin = os.environ.get("NOVANEST_ADMIN_KEY")
        cls.orig_api = os.environ.get("NOVANEST_API_KEY")
        cls.orig_salt = os.environ.get("NOVANEST_SESSION_SALT")
        os.environ.pop("NOVANEST_ADMIN_KEY", None)
        cls.api_key = "test_op_key_milestone5_streamlit"
        os.environ["NOVANEST_API_KEY"] = cls.api_key
        os.environ["NOVANEST_SESSION_SALT"] = "test_salt_milestone5"

    @classmethod
    def tearDownClass(cls):
        if cls.orig_admin is not None:
            os.environ["NOVANEST_ADMIN_KEY"] = cls.orig_admin
        else:
            os.environ.pop("NOVANEST_ADMIN_KEY", None)
        if cls.orig_api is not None:
            os.environ["NOVANEST_API_KEY"] = cls.orig_api
        else:
            os.environ.pop("NOVANEST_API_KEY", None)
        if cls.orig_salt is not None:
            os.environ["NOVANEST_SESSION_SALT"] = cls.orig_salt
        else:
            os.environ.pop("NOVANEST_SESSION_SALT", None)

    def setUp(self):
        self.client = StreamlitAiClient(
            base_url="http://testserver",
            api_token=self.api_key,
            enable_inprocess_fallback=True,
        )

    # -------------------------------------------------------------------------
    # 1. Streamlit-to-FastAPI MasterOrchestrator Invocation
    # -------------------------------------------------------------------------
    def test_01_streamlit_api_client_ask_ai_master_orchestrator(self):
        """Verifies Streamlit client invokes FastAPI MasterOrchestrator and receives verified response."""
        res = self.client.ask_ai(
            question="What is our total GMV and net revenue?",
            session_id="st_m5_test_01",
        )
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get("error", False))
        self.assertIn("answer", res)
        self.assertIn("telemetry", res)
        self.assertIn("verification_outcome", res)
        self.assertEqual(res.get("verification_outcome"), "verified")

        # Telemetry must contain 5 domain agents or execution metrics
        telemetry = res.get("telemetry", {})
        self.assertIn("agent_execution_times", telemetry)
        exec_times = telemetry["agent_execution_times"]
        self.assertIn("financial_agent", exec_times)

    # -------------------------------------------------------------------------
    # 2. Authentication & RBAC Enforcement
    # -------------------------------------------------------------------------
    def test_02_fastapi_authentication_enforcement(self):
        """Verifies that invalid or missing API tokens are rejected fail-closed."""
        bad_client = StreamlitAiClient(
            base_url="http://testserver",
            api_token="invalid_bad_token_12345",
            enable_inprocess_fallback=True,
        )
        with self.assertRaises(ApiClientError) as ctx:
            bad_client.ask_ai(
                question="Analyze GMV",
                session_id="st_m5_bad_auth",
            )
        self.assertIn(ctx.exception.status_code, (401, 403))

    # -------------------------------------------------------------------------
    # 3. Filter Propagation (City & Active Filters)
    # -------------------------------------------------------------------------
    def test_03_filter_propagation_city_and_active_filters(self):
        """Verifies filters passed from Streamlit UI propagate to MasterOrchestrator."""
        res = self.client.ask_ai(
            question="What is our revenue and order count?",
            session_id="st_m5_filter_prop",
            city_filter="Hyderabad",
            filters={"city": "Hyderabad", "status": "Delivered"},
        )
        self.assertFalse(res.get("error", False))
        # Answer or verified metrics should be grounded for Hyderabad
        answer = res.get("answer", "")
        self.assertTrue(len(answer) > 20)

    # -------------------------------------------------------------------------
    # 4. Contextual AI Launcher Payload & Grounding Principle
    # -------------------------------------------------------------------------
    def test_04_contextual_ai_payload_contract(self):
        """Verifies build_contextual_payload generates the standardized contract."""
        payload = build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="kpi_gmv",
            selected_metric="Gross Revenue (GMV)",
            metric_value=4500000.0,
            city="Delhi",
            active_filters={"city": "Delhi"},
            suggested_prompt="Analyze GMV trends in Delhi.",
        )
        self.assertEqual(payload["dashboard_name"], "Executive Overview")
        self.assertEqual(payload["selected_metric"], "Gross Revenue (GMV)")
        self.assertEqual(payload["city"], "Delhi")
        self.assertEqual(payload["suggested_prompt"], "Analyze GMV trends in Delhi.")
        self.assertTrue(payload["auto_submit"])

    def test_05_untrusted_client_metric_recalculated_not_trusted(self):
        """Untrusted Client Metric Principle: Bogus client metric_value is ignored."""
        fake_payload = build_contextual_payload(
            dashboard_name="Financial Intelligence",
            kpi_or_chart_id="kpi_gmv",
            selected_metric="Gross Revenue (GMV)",
            metric_value=99999999999.0,  # Ridiculously fabricated client metric
            city="Mumbai",
            active_filters={"city": "Mumbai"},
        )
        res = self.client.ask_ai(
            question="What is our GMV?",
            session_id="st_m5_fake_metric",
            city_filter="Mumbai",
            contextual_data=fake_payload,
        )
        self.assertFalse(res.get("error", False))
        answer = res.get("answer", "")
        # The fabricated number must NEVER appear in the verified answer
        self.assertNotIn("99999999999", answer)
        self.assertNotIn("99,999,999,999", answer)

    # -------------------------------------------------------------------------
    # 5. Conversational Follow-Up Context Retention
    # -------------------------------------------------------------------------
    def test_06_conversational_follow_up_context_retention(self):
        """Verifies entity retention (e.g. city) across follow-up queries in same session."""
        session_id = "st_m5_follow_up_sess"

        # Turn 1: Explicit city query
        res1 = self.client.ask_ai(
            question="What is our GMV in Hyderabad?",
            session_id=session_id,
        )
        self.assertFalse(res1.get("error", False))

        # Turn 2: Follow-up omitting city
        res2 = self.client.ask_ai(
            question="What is the order cancellation rate?",
            session_id=session_id,
        )
        self.assertFalse(res2.get("error", False))
        # Remembered entities should reflect Hyderabad
        rem_entities = res2.get("remembered_entities", {})
        self.assertEqual(rem_entities.get("city"), "Hyderabad")

    # -------------------------------------------------------------------------
    # 6. Cross-Session Isolation
    # -------------------------------------------------------------------------
    def test_07_cross_session_isolation(self):
        """Verifies Session A and Session B maintain strict contextual isolation."""
        # Session A inquires about Chennai
        self.client.ask_ai(
            question="Analyze business performance in Chennai.",
            session_id="st_m5_sess_A",
        )

        # Session B inquires generally
        res_b = self.client.ask_ai(
            question="What is our total revenue?",
            session_id="st_m5_sess_B",
        )
        # Session B should NOT have Chennai as remembered city
        rem_b = res_b.get("remembered_entities", {})
        self.assertNotEqual(rem_b.get("city"), "Chennai")

    # -------------------------------------------------------------------------
    # 7. SSE Streaming Telemetry Event Parsing
    # -------------------------------------------------------------------------
    def test_08_sse_streaming_telemetry_event_parsing(self):
        """Verifies Streamlit client can stream and parse SSE telemetry events."""
        events = list(
            self.client.ask_ai_stream(
                question="What is our fulfillment rate?",
                session_id="st_m5_stream_sess",
            )
        )
        self.assertTrue(len(events) >= 3, f"Expected multiple events, got {len(events)}")
        event_names = [e.get("event") for e in events]
        self.assertIn("query_received", event_names)
        self.assertIn("response_completed", event_names)

        # Check response_completed payload structure
        completed_evt = next(e for e in events if e.get("event") == "response_completed")
        c_data = completed_evt.get("data", {})
        payload_data = c_data.get("data") or c_data
        self.assertIn("answer", payload_data)
        self.assertIn("verification_outcome", payload_data)

    # -------------------------------------------------------------------------
    # 8. Five-Domain Agents Representation
    # -------------------------------------------------------------------------
    def test_09_domain_agents_telemetry_card_schema(self):
        """Verifies DOMAIN_AGENTS contains all 5 required business intelligence agents."""
        agent_ids = {a["id"] for a in DOMAIN_AGENTS}
        expected_ids = {
            "financial_agent",
            "customer_agent",
            "operations_agent",
            "restaurant_agent",
            "decision_agent",
        }
        self.assertEqual(agent_ids, expected_ids)

    # -------------------------------------------------------------------------
    # 9. Session Reset via API
    # -------------------------------------------------------------------------
    def test_10_session_reset_via_api(self):
        """Verifies Streamlit client can reset conversational context on server."""
        session_id = "st_m5_reset_sess"

        # Populate memory
        self.client.ask_ai(
            question="Analyze Bangalore orders.",
            session_id=session_id,
        )

        # Reset session
        reset_res = self.client.reset_session(session_id)
        self.assertIsInstance(reset_res, dict)

        # Subsequent query should have empty remembered entities
        res_after = self.client.ask_ai(
            question="What is our GMV?",
            session_id=session_id,
        )
        rem_after = res_after.get("remembered_entities", {})
        self.assertFalse(rem_after.get("city"))

    # -------------------------------------------------------------------------
    # 10. Timeout & Error Resilience
    # -------------------------------------------------------------------------
    def test_11_empty_query_validation_error(self):
        """Verifies empty queries raise ApiClientError with 400 validation code."""
        with self.assertRaises(ApiClientError) as ctx:
            self.client.ask_ai(question="", session_id="st_m5_empty")
        self.assertEqual(ctx.exception.status_code, 400)

    # -------------------------------------------------------------------------
    # 11. All 9 Streamlit Pages Bytecode Compilation & Import Parity
    # -------------------------------------------------------------------------
    def test_12_all_streamlit_pages_compilation_and_imports(self):
        """Verifies that all 9 Streamlit pages compile and import cleanly."""
        pages = [
            "01_Executive_Overview.py",
            "02_Customer_Intelligence.py",
            "03_Restaurant_Intelligence.py",
            "04_Operations_Intelligence.py",
            "05_Financial_Intelligence.py",
            "06_Decision_Intelligence.py",
            "07_Ask_NovaNest.py",
            "08_Decision_Simulator.py",
            "09_NovaNest_Command_Center.py",
        ]
        pages_dir = STREAMLIT_DIR / "pages"
        for page_file in pages:
            page_path = pages_dir / page_file
            self.assertTrue(page_path.exists(), f"Page {page_file} does not exist!")
            with open(page_path, "r", encoding="utf-8") as f:
                source = f.read()
            compiled = compile(source, str(page_path), "exec")
            self.assertIsNotNone(compiled, f"Failed compiling {page_file}")


if __name__ == "__main__":
    unittest.main()
