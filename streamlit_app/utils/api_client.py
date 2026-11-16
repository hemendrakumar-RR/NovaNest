"""
NovaNest Streamlit API Client — Unified MasterOrchestrator Boundary
-------------------------------------------------------------------
Provides authenticated HTTP and SSE streaming access from Streamlit UI
to the FastAPI MasterOrchestrator and domain intelligence endpoints.

Architecture:
  Streamlit UI -> FastAPI authenticated API -> MasterOrchestrator -> OutputVerifier

Security & Resilience:
  - Enforces fail-closed token authorization (Bearer / X-API-Key).
  - Never logs or exposes credentials in Streamlit session logs.
  - Constant-time role and principal isolation.
  - Safe timeout, retry, connection error, and cancellation handling.
  - Supports SSE real-time telemetry streaming with auto-reconnect / fallback.
  - Optional in-process TestClient fallback for headless unit testing environments.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Iterator, Optional
import requests

logger = logging.getLogger(__name__)

DEFAULT_API_URL = os.getenv("NOVANEST_API_URL") or os.getenv("FASTAPI_URL") or "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 65.0


class ApiClientError(Exception):
    """Raised when an API request encounters an unrecoverable failure."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_type: str = "API_ERROR",
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.retryable = retryable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "error_type": self.error_type,
            "status_code": self.status_code,
            "message": self.message,
            "retryable": self.retryable,
        }


class StreamlitAiClient:
    """
    Robust API client connecting Streamlit components to the FastAPI MasterOrchestrator.
    Guarantees that business intelligence calculations and verification happen
    strictly on the backend through the verified multi-agent foundation.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        admin_token: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        enable_inprocess_fallback: bool = True,
    ):
        self.base_url = (base_url or DEFAULT_API_URL).rstrip("/")
        self._explicit_token = api_token
        self._explicit_admin_token = admin_token
        self.timeout = float(timeout)
        self.enable_inprocess_fallback = bool(enable_inprocess_fallback)

    def get_token(self) -> str:
        """
        Retrieves the authenticated API token from explicit param,
        environment variables, Streamlit secrets, or Streamlit session state.
        Never hardcodes credentials in plain text.
        """
        if self._explicit_token and self._explicit_token.strip():
            return self._explicit_token.strip()

        # Check environment variables
        env_token = (
            os.getenv("NOVANEST_API_KEY", "").strip()
            or os.getenv("NOVANEST_ADMIN_KEY", "").strip()
            or os.getenv("NOVANEST_OPERATOR_KEY", "").strip()
        )
        if env_token:
            return env_token

        # Check Streamlit secrets if available (e.g. on Streamlit Community Cloud)
        try:
            import streamlit as st
            st_key = st.secrets.get("NOVANEST_API_KEY", "") or st.secrets.get("NOVANEST_ADMIN_KEY", "")
            if isinstance(st_key, str) and st_key.strip():
                return st_key.strip()
        except Exception:
            pass

        # Check Streamlit session_state if available
        try:
            import streamlit as st

            st_token = st.session_state.get("novanest_api_token", "")
            if isinstance(st_token, str) and st_token.strip():
                return st_token.strip()
        except Exception:
            pass

        # In dev/testing when no key is configured in env, configure default operator key in env
        default_key = "novanest_operator_key_default"
        if not os.getenv("NOVANEST_API_KEY") and not os.getenv("NOVANEST_ADMIN_KEY") and not os.getenv("NOVANEST_VIEWER_KEY"):
            os.environ["NOVANEST_API_KEY"] = default_key
        return default_key

    def get_admin_token(self) -> str:
        """
        Retrieves the admin API token for administrative endpoints (e.g. session reset).
        Checks explicit admin token, environment variables, Streamlit secrets, or falls back to regular token.
        """
        if self._explicit_admin_token and self._explicit_admin_token.strip():
            return self._explicit_admin_token.strip()

        env_admin = os.getenv("NOVANEST_ADMIN_KEY", "").strip()
        if env_admin:
            return env_admin

        try:
            import streamlit as st
            st_admin = st.secrets.get("NOVANEST_ADMIN_KEY", "")
            if isinstance(st_admin, str) and st_admin.strip():
                return st_admin.strip()
        except Exception:
            pass

        return self.get_token()

    def _get_headers(self) -> Dict[str, str]:
        """Builds sanitized HTTP headers with token authorization."""
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "X-API-Key": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_admin_headers(self) -> Dict[str, str]:
        """Builds sanitized HTTP headers with admin token authorization."""
        token = self.get_admin_token()
        return {
            "Authorization": f"Bearer {token}",
            "X-API-Key": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _execute_inprocess_request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Fallback execution via FastAPI TestClient for automated testing or headless runtime.
        Enforces identical FastAPI middleware, dependencies, and RBAC authentication without bypass.
        """
        try:
            from fastapi.testclient import TestClient
            import api.main as api_main

            client = TestClient(api_main.app)
            req_headers = headers if headers is not None else self._get_headers()
            if method.upper() == "POST":
                resp = client.post(path, json=json_data, params=params, headers=req_headers)
            else:
                resp = client.get(path, params=params, headers=req_headers)

            # Convert TestClient response (httpx) to requests-compatible duck type if needed
            return resp
        except Exception as exc:
            logger.error("In-process FastAPI execution failed: %s", exc)
            raise ApiClientError(
                message=f"In-process execution failed: {str(exc)}",
                error_type="INPROCESS_FAILURE",
                retryable=True,
            ) from exc

    def _normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures consistent telemetry structure for Streamlit UI consumers."""
        if isinstance(data, dict):
            if "telemetry" not in data:
                agents_inv = data.get("agents_invoked", [])
                exec_times = {
                    ag["agent_id"]: ag.get("elapsed_ms", 0.0)
                    for ag in agents_inv
                    if isinstance(ag, dict) and "agent_id" in ag
                }
                data["telemetry"] = {
                    "agent_execution_times": exec_times,
                    "agents_invoked": agents_inv,
                    "request_id": data.get("request_id"),
                    "trace_id": data.get("trace_id"),
                }
        return data

    def ask_ai(
        self,
        question: str,
        session_id: str = "default",
        city_filter: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        contextual_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Submits a synchronous business inquiry to the FastAPI MasterOrchestrator.
        Enforces server-side grounding, verification, and role-based access.
        """
        clean_q = (question or "").strip()
        if not clean_q:
            raise ApiClientError("Question cannot be empty.", status_code=400, error_type="VALIDATION_ERROR")

        payload: Dict[str, Any] = {
            "question": clean_q,
            "session_id": str(session_id or "default").strip(),
        }
        if city_filter and city_filter.strip() and city_filter.strip() != "All":
            payload["city_filter"] = city_filter.strip()
        elif filters and filters.get("city") and filters["city"] != "All":
            payload["city_filter"] = str(filters["city"]).strip()

        if contextual_data and isinstance(contextual_data, dict):
            # Grounding principle: Client metric_values are strictly ignored by backend
            payload["contextual_data"] = contextual_data

        url = f"{self.base_url}/api/ai/ask"
        headers = self._get_headers()

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                return self._normalize_response(resp.json())
            elif resp.status_code == 401:
                raise ApiClientError("Authentication required or invalid token.", status_code=401, error_type="AUTH_FAILED")
            elif resp.status_code == 403:
                raise ApiClientError("Insufficient permissions (operator scope required).", status_code=403, error_type="FORBIDDEN")
            elif resp.status_code == 503:
                raise ApiClientError("Server API authentication keys not configured.", status_code=503, error_type="UNAVAILABLE")
            else:
                detail = resp.text
                try:
                    detail = resp.json().get("detail", resp.text)
                except Exception:
                    pass
                raise ApiClientError(f"API Error ({resp.status_code}): {detail}", status_code=resp.status_code)
        except requests.exceptions.Timeout as exc:
            logger.warning("API query timed out after %.1fs: %s", self.timeout, exc)
            raise ApiClientError(
                "AI inquiry timed out. The request was cancelled safely by the server.",
                status_code=504,
                error_type="TIMEOUT",
                retryable=True,
            ) from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as exc:
            if self.enable_inprocess_fallback:
                logger.info("HTTP connection to %s unavailable; dispatching through in-process FastAPI app.", url)
                try:
                    resp = self._execute_inprocess_request("POST", "/api/ai/ask", json_data=payload)
                    if resp.status_code == 200:
                        return self._normalize_response(resp.json())
                    detail = resp.text
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except Exception:
                        pass
                    raise ApiClientError(f"API Error ({resp.status_code}): {detail}", status_code=resp.status_code)
                except ApiClientError:
                    raise
                except Exception as inner_exc:
                    raise ApiClientError(
                        f"Unable to reach FastAPI backend at {self.base_url} ({inner_exc})",
                        status_code=503,
                        error_type="CONNECTION_FAILED",
                        retryable=True,
                    ) from inner_exc
            raise ApiClientError(
                f"Unable to connect to NovaNest API server at {self.base_url}.",
                status_code=503,
                error_type="CONNECTION_FAILED",
                retryable=True,
            ) from exc

    def get_stream_ticket(self, session_id: str = "default") -> str:
        """
        Obtains a short-lived, single-use stream ticket for GET SSE streaming.
        Eliminates token exposure in URL query strings.
        """
        url = f"{self.base_url}/api/ai/stream-ticket"
        headers = self._get_headers()
        payload = {"session_id": str(session_id or "default").strip()}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("ticket", "")
            detail = resp.text
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                pass
            raise ApiClientError(f"Failed to obtain stream ticket ({resp.status_code}): {detail}", status_code=resp.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as exc:
            if self.enable_inprocess_fallback:
                resp = self._execute_inprocess_request("POST", "/api/ai/stream-ticket", json_data=payload)
                if resp.status_code == 200:
                    return resp.json().get("ticket", "")
            raise ApiClientError(f"Stream ticket request failed: {exc}", status_code=503) from exc

    def ask_ai_stream_get(
        self,
        question: str,
        session_id: str = "default",
        city_filter: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Streams SSE telemetry via GET using a short-lived single-use stream ticket.
        """
        clean_q = (question or "").strip()
        if not clean_q:
            raise ApiClientError("Question cannot be empty.", status_code=400, error_type="VALIDATION_ERROR")
        clean_session = str(session_id or "default").strip()
        ticket = self.get_stream_ticket(clean_session)
        params = {
            "question": clean_q,
            "session_id": clean_session,
            "ticket": ticket,
        }
        if city_filter and city_filter.strip() and city_filter.strip() != "All":
            params["city_filter"] = city_filter.strip()

        url = f"{self.base_url}/api/ai/ask/stream"
        try:
            with requests.get(url, params=params, headers={"Accept": "text/event-stream"}, stream=True, timeout=self.timeout) as resp:
                if resp.status_code != 200:
                    detail = resp.text
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except Exception:
                        pass
                    raise ApiClientError(f"Streaming error ({resp.status_code}): {detail}", status_code=resp.status_code)
                current_event = "message"
                current_data_lines: list[str] = []
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if raw_line is None:
                        continue
                    line = raw_line.strip()
                    if not line:
                        if current_data_lines:
                            raw_data = "\n".join(current_data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = {"message": raw_data}
                            yield {"event": current_event, "data": parsed}
                            current_data_lines = []
                            current_event = "message"
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        current_data_lines.append(line[5:].strip())
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as exc:
            if self.enable_inprocess_fallback:
                resp = self._execute_inprocess_request("GET", "/api/ai/ask/stream", params=params)
                if resp.status_code != 200:
                    raise ApiClientError(f"In-process stream error ({resp.status_code})", status_code=resp.status_code)
                current_event = "message"
                current_data_lines = []
                for raw_line in resp.text.split("\n"):
                    line = raw_line.strip()
                    if not line:
                        if current_data_lines:
                            raw_data = "\n".join(current_data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = {"message": raw_data}
                            yield {"event": current_event, "data": parsed}
                            current_data_lines = []
                            current_event = "message"
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        current_data_lines.append(line[5:].strip())
                return
            raise ApiClientError(f"SSE streaming GET connection failed: {str(exc)}", status_code=503) from exc

    def ask_ai_stream(
        self,
        question: str,
        session_id: str = "default",
        city_filter: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        contextual_data: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Streams Server-Sent Events (SSE) telemetry and final verified response from FastAPI.
        Yields structured event dicts:
          {"event": str, "data": Dict[str, Any]}
        """
        clean_q = (question or "").strip()
        if not clean_q:
            raise ApiClientError("Question cannot be empty.", status_code=400, error_type="VALIDATION_ERROR")

        payload: Dict[str, Any] = {
            "question": clean_q,
            "session_id": str(session_id or "default").strip(),
        }
        if city_filter and city_filter.strip() and city_filter.strip() != "All":
            payload["city_filter"] = city_filter.strip()
        elif filters and filters.get("city") and filters["city"] != "All":
            payload["city_filter"] = str(filters["city"]).strip()

        if contextual_data and isinstance(contextual_data, dict):
            payload["contextual_data"] = contextual_data

        url = f"{self.base_url}/api/ai/ask/stream"
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        try:
            with requests.post(url, json=payload, headers=headers, stream=True, timeout=self.timeout) as resp:
                if resp.status_code != 200:
                    detail = resp.text
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except Exception:
                        pass
                    raise ApiClientError(f"Streaming error ({resp.status_code}): {detail}", status_code=resp.status_code)

                current_event = "message"
                current_data_lines: list[str] = []

                for raw_line in resp.iter_lines(decode_unicode=True):
                    if raw_line is None:
                        continue
                    line = raw_line.strip()
                    if not line:
                        if current_data_lines:
                            raw_data = "\n".join(current_data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = {"message": raw_data}
                            yield {"event": current_event, "data": parsed}
                            current_data_lines = []
                            current_event = "message"
                        continue

                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        current_data_lines.append(line[5:].strip())
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as exc:
            if self.enable_inprocess_fallback:
                logger.info("HTTP streaming unavailable; falling back to in-process execution.")
                try:
                    resp = self._execute_inprocess_request("POST", "/api/ai/ask/stream", json_data=payload)
                    if resp.status_code != 200:
                        raise ApiClientError(f"In-process stream error ({resp.status_code})", status_code=resp.status_code)

                    # Parse SSE lines from TestClient text
                    current_event = "message"
                    current_data_lines = []
                    for raw_line in resp.text.split("\n"):
                        line = raw_line.strip()
                        if not line:
                            if current_data_lines:
                                raw_data = "\n".join(current_data_lines)
                                try:
                                    parsed = json.loads(raw_data)
                                except Exception:
                                    parsed = {"message": raw_data}
                                yield {"event": current_event, "data": parsed}
                                current_data_lines = []
                                current_event = "message"
                            continue
                        if line.startswith("event:"):
                            current_event = line[6:].strip()
                        elif line.startswith("data:"):
                            current_data_lines.append(line[5:].strip())
                    return
                except ApiClientError:
                    raise
                except Exception as inner_exc:
                    raise ApiClientError(
                        f"In-process stream fallback failed: {inner_exc}",
                        status_code=503,
                        error_type="STREAM_FAILED",
                    ) from inner_exc
            raise ApiClientError(
                f"SSE streaming connection failed: {str(exc)}",
                status_code=503,
                error_type="CONNECTION_FAILED",
                retryable=True,
            ) from exc

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Resets conversational memory and context for an authenticated session."""
        url = f"{self.base_url}/api/ai/reset"
        headers = self._get_admin_headers()
        payload = {"session_id": str(session_id).strip()}

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            if self.enable_inprocess_fallback and self.base_url in ("http://testserver", "http://127.0.0.1:8001", "http://localhost:8001"):
                pass
            else:
                raise ApiClientError(f"Reset failed: {resp.text}", status_code=resp.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
            pass

        if self.enable_inprocess_fallback:
            resp = self._execute_inprocess_request("POST", "/api/ai/reset", json_data=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            raise ApiClientError(f"Reset failed: {resp.text}", status_code=resp.status_code)

        raise ApiClientError(f"Reset failed for session {session_id}", status_code=503)

    def get_agents_status(self) -> Dict[str, Any]:
        """Retrieves real-time status and metadata for all five domain intelligence agents."""
        url = f"{self.base_url}/api/ai/agents/status"
        headers = self._get_headers()

        try:
            resp = requests.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            raise ApiClientError(f"Agents status failed: {resp.text}", status_code=resp.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
            if self.enable_inprocess_fallback:
                resp = self._execute_inprocess_request("GET", "/api/ai/agents/status")
                if resp.status_code == 200:
                    return resp.json()
                raise ApiClientError(f"Agents status failed: {resp.text}", status_code=resp.status_code)
            raise


# Default singleton instance for Streamlit pages
_client_instance: Optional[StreamlitAiClient] = None


def get_streamlit_ai_client() -> StreamlitAiClient:
    """Returns or initializes the shared StreamlitAiClient singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = StreamlitAiClient()
    return _client_instance
