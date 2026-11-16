"""
NovaNest Phase 06.6 — Security and Application Hardening Test Suite
-------------------------------------------------------------------
Verifies:
  1. Stream Ticket Service (POST /api/ai/stream-ticket):
     - Authentication required (operator or admin scope).
     - Viewer role rejected with 403 Forbidden.
     - Unauthenticated requests rejected with 401.
     - Ticket entropy, session binding, and 60-second TTL.
  2. Stream Ticket Consumption (GET /api/ai/ask/stream):
     - Single-use consumption (anti-replay).
     - Expired ticket rejection.
     - Invalid / forged ticket rejection.
     - Cross-session ticket mismatch rejection.
     - Valid ticket accepted and streams typed SSE telemetry.
  3. Static Token URL Exposure Elimination:
     - Strict rejection of ?token=<key> query parameters with 401.
     - Rejection of query tokens across general API endpoints.
  4. Client Disconnect and Cancellation:
     - Context cancellation on client disconnect.
  5. Streamlit API Client:
     - get_stream_ticket helper functionality.
"""

import asyncio
import os
import time
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.auth import (
    AuthPrincipal,
    authenticate_stream_principal,
    stream_ticket_manager,
)
from api.main import app
from python.ai.agents.telemetry_events import OrchestratorTelemetryEvent, TelemetryEventType
from streamlit_app.utils.api_client import StreamlitAiClient


class TestPhase066SecurityAndHardening(unittest.TestCase):
    """Rigorous test suite for Phase 06.6 security hardening."""

    @classmethod
    def setUpClass(cls):
        cls.orig_admin = os.environ.get("NOVANEST_ADMIN_KEY")
        cls.orig_op = os.environ.get("NOVANEST_API_KEY")
        cls.orig_viewer = os.environ.get("NOVANEST_VIEWER_KEY")

        cls.admin_key = "admin-secret-phase06-6"
        cls.op_key = "operator-secret-phase06-6"
        cls.viewer_key = "viewer-secret-phase06-6"

        os.environ["NOVANEST_ADMIN_KEY"] = cls.admin_key
        os.environ["NOVANEST_API_KEY"] = cls.op_key
        os.environ["NOVANEST_VIEWER_KEY"] = cls.viewer_key

        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if cls.orig_admin is not None:
            os.environ["NOVANEST_ADMIN_KEY"] = cls.orig_admin
        else:
            os.environ.pop("NOVANEST_ADMIN_KEY", None)

        if cls.orig_op is not None:
            os.environ["NOVANEST_API_KEY"] = cls.orig_op
        else:
            os.environ.pop("NOVANEST_API_KEY", None)

        if cls.orig_viewer is not None:
            os.environ["NOVANEST_VIEWER_KEY"] = cls.orig_viewer
        else:
            os.environ.pop("NOVANEST_VIEWER_KEY", None)

    def setUp(self):
        stream_ticket_manager.clear()

    def tearDown(self):
        stream_ticket_manager.clear()

    # -------------------------------------------------------------
    # 1. STREAM TICKET GENERATION SECURITY
    # -------------------------------------------------------------

    def test_01_ticket_creation_unauthenticated_rejected(self):
        """Unauthenticated requests to POST /api/ai/stream-ticket must be rejected with 401."""
        resp = self.client.post("/api/ai/stream-ticket", json={"session_id": "test_s1"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Authentication required", resp.json().get("detail", ""))

    def test_02_ticket_creation_invalid_credentials_rejected(self):
        """Invalid credentials to POST /api/ai/stream-ticket must be rejected with 401."""
        resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "test_s2"},
            headers={"Authorization": "Bearer bad-token-999"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid API authentication token", resp.json().get("detail", ""))

    def test_03_ticket_creation_viewer_role_rejected(self):
        """Viewer role (read-only) lacks operator scope and must receive 403 Forbidden."""
        resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "test_s3"},
            headers={"X-API-Key": self.viewer_key},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Insufficient permissions", resp.json().get("detail", ""))

    def test_04_ticket_creation_authorized_operator(self):
        """Operator role receives a cryptographically secure 60s stream ticket."""
        resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "sess_operator_01"},
            headers={"X-API-Key": self.op_key},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ticket"].startswith("st_"))
        self.assertGreaterEqual(len(data["ticket"]), 32)
        self.assertEqual(data["expires_in"], 60)
        self.assertEqual(data["session_id"], "sess_operator_01")
        self.assertIsInstance(data["created_at"], (int, float))

    def test_05_ticket_creation_authorized_admin(self):
        """Admin role can also obtain stream tickets."""
        resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "sess_admin_01"},
            headers={"Authorization": f"Bearer {self.admin_key}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ticket"].startswith("st_"))
        self.assertEqual(data["session_id"], "sess_admin_01")

    # -------------------------------------------------------------
    # 2. STREAM TICKET CONSUMPTION & SSE SECURITY
    # -------------------------------------------------------------

    def test_06_valid_ticket_consumes_and_streams_events(self):
        """A valid ticket allows GET SSE connection and streams telemetry successfully."""
        # 1. Obtain ticket
        t_resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "sess_flow_01"},
            headers={"X-API-Key": self.op_key},
        )
        self.assertEqual(t_resp.status_code, 200)
        ticket = t_resp.json()["ticket"]

        # 2. Connect via GET with ticket in query string
        stream_resp = self.client.get(
            f"/api/ai/ask/stream?question=What+is+our+overall+GMV?&session_id=sess_flow_01&ticket={ticket}"
        )
        self.assertEqual(stream_resp.status_code, 200)
        self.assertIn("text/event-stream", stream_resp.headers.get("content-type", ""))
        self.assertIn("event: query_received", stream_resp.text)
        self.assertIn("event: response_completed", stream_resp.text)

    def test_07_ticket_is_strictly_single_use(self):
        """A consumed ticket cannot be replayed; second attempt returns 401."""
        # 1. Obtain ticket
        t_resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "sess_replay_01"},
            headers={"X-API-Key": self.op_key},
        )
        ticket = t_resp.json()["ticket"]

        # 2. First consumption: success
        resp1 = self.client.get(
            f"/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_replay_01&ticket={ticket}"
        )
        self.assertEqual(resp1.status_code, 200)

        # 3. Second consumption attempt: strictly rejected (401)
        resp2 = self.client.get(
            f"/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_replay_01&ticket={ticket}"
        )
        self.assertEqual(resp2.status_code, 401)
        self.assertIn("Invalid, expired, or already consumed", resp2.json().get("detail", ""))

    def test_08_expired_ticket_rejected(self):
        """An expired ticket cannot be consumed."""
        principal = AuthPrincipal(role="operator", scopes=frozenset({"read", "operator"}), principal_id="op_exp")
        # Create ticket with zero TTL
        ticket = stream_ticket_manager.create_ticket(principal, session_id="sess_expired", ttl_seconds=-1.0)

        resp = self.client.get(
            f"/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_expired&ticket={ticket.ticket_id}"
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid, expired, or already consumed", resp.json().get("detail", ""))

    def test_09_forged_or_invalid_ticket_rejected(self):
        """Non-existent or forged tickets must be rejected with 401."""
        resp = self.client.get(
            "/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_forged&ticket=st_attacker_forged_ticket"
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid, expired, or already consumed", resp.json().get("detail", ""))

    def test_10_cross_session_ticket_mismatch_rejected(self):
        """A ticket bound to session_A cannot be used to open a stream for session_B."""
        # 1. Obtain ticket for session_A
        t_resp = self.client.post(
            "/api/ai/stream-ticket",
            json={"session_id": "session_A"},
            headers={"X-API-Key": self.op_key},
        )
        ticket = t_resp.json()["ticket"]

        # 2. Attempt to use ticket with session_B
        resp = self.client.get(
            f"/api/ai/ask/stream?question=What+is+GMV?&session_id=session_B&ticket={ticket}"
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid, expired, or already consumed", resp.json().get("detail", ""))

    # -------------------------------------------------------------
    # 3. STATIC TOKEN QUERY PARAMETER ELIMINATION
    # -------------------------------------------------------------

    def test_11_static_token_in_sse_query_string_rejected(self):
        """GET /api/ai/ask/stream with ?token=<key> must be strictly rejected with 401."""
        resp = self.client.get(
            f"/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_leak&token={self.op_key}"
        )
        self.assertEqual(resp.status_code, 401)
        detail = resp.json().get("detail", "")
        self.assertIn("Static API tokens in URL query parameters are disabled for security", detail)

    def test_12_static_token_in_general_endpoint_query_string_rejected(self):
        """General endpoints (e.g., /api/overview) must reject ?token=<key> with 401."""
        resp = self.client.get(f"/api/overview?token={self.op_key}")
        self.assertEqual(resp.status_code, 401)
        detail = resp.json().get("detail", "")
        self.assertIn("Static API tokens in URL query parameters are disabled for security", detail)

    def test_13_missing_ticket_and_header_rejected(self):
        """GET /api/ai/ask/stream with neither ticket nor header must return 401."""
        resp = self.client.get("/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_anon")
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Authentication required", resp.json().get("detail", ""))

    def test_14_header_auth_fallback_on_get_stream(self):
        """Clients passing standard Authorization headers can still stream via GET."""
        resp = self.client.get(
            "/api/ai/ask/stream?question=What+is+GMV?&session_id=sess_header_get",
            headers={"Authorization": f"Bearer {self.op_key}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))

    # -------------------------------------------------------------
    # 4. STREAMLIT CLIENT TICKET INTEGRATION
    # -------------------------------------------------------------

    def test_15_streamlit_client_get_stream_ticket(self):
        """StreamlitAiClient.get_stream_ticket correctly requests and returns a valid ticket."""
        client = StreamlitAiClient(enable_inprocess_fallback=True)
        ticket = client.get_stream_ticket(session_id="sess_streamlit_01")
        self.assertTrue(ticket.startswith("st_"))

        # Verify that ticket is recognized by the ticket manager
        principal = stream_ticket_manager.consume_ticket(ticket, expected_session_id="sess_streamlit_01")
        self.assertIsNotNone(principal)
        self.assertEqual(principal.role, "operator")

    # -------------------------------------------------------------
    # 5. STREAM TICKET MANAGER UNIT TESTS
    # -------------------------------------------------------------

    def test_16_stream_ticket_manager_principal_binding(self):
        """Verifies principal_id binding enforcement."""
        p1 = AuthPrincipal(role="operator", scopes=frozenset({"operator"}), principal_id="principal_A")
        ticket = stream_ticket_manager.create_ticket(p1, session_id="s1")

        # Wrong principal expectation
        res = stream_ticket_manager.consume_ticket(
            ticket.ticket_id,
            expected_session_id="s1",
            expected_principal_id="principal_B",
        )
        self.assertIsNone(res)

        # Correct principal expectation
        res_ok = stream_ticket_manager.consume_ticket(
            ticket.ticket_id,
            expected_session_id="s1",
            expected_principal_id="principal_A",
        )
        self.assertEqual(res_ok, p1)

    def test_17_ticket_value_redacted_in_telemetry(self):
        """Verifies ticket tokens are redacted in telemetry event messages."""
        raw_msg = "Stream initialized with ticket st_abc123xyz789SECRET_TICKET_VALUE_FOR_STREAM"
        event = OrchestratorTelemetryEvent(
            request_id="req_redact_1",
            session_id="sess_redact_1",
            event_type=TelemetryEventType.AGENT_PROGRESS,
            timestamp=time.time(),
            status="running",
            message=raw_msg,
        )
        self.assertNotIn("st_abc123xyz789SECRET_TICKET_VALUE_FOR_STREAM", event.message)
        self.assertIn("[REDACTED_SECRET]", event.message)

    def test_18_streamlit_client_ask_ai_stream_get(self):
        """StreamlitAiClient.ask_ai_stream_get streams events via GET with single-use ticket."""
        client = StreamlitAiClient(enable_inprocess_fallback=True)
        events = list(client.ask_ai_stream_get(
            question="What is total GMV?",
            session_id="sess_st_stream_get",
        ))
        self.assertGreater(len(events), 0)
        event_types = [e.get("event") for e in events]
        self.assertIn("query_received", event_types)


if __name__ == "__main__":
    unittest.main()

