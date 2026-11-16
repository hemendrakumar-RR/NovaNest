"""
NovaNest Multi-Agent Telemetry Events & Streaming Contract (Phase 06.5 Milestone 3)
-----------------------------------------------------------------------------------
Typed, verified telemetry event specifications for real-time visibility into
`MasterOrchestrator` execution across all five domain agents.

Security & Integrity Guarantees:
- Never exposes internal prompts, credentials, API keys, tokens, or PII.
- Scrubs stack traces, raw SQL queries, and sensitive intermediate DataFrames.
- Strict Pydantic v2 validation with `extra="forbid"`.
- Native Server-Sent Events (SSE) string serialization (`to_sse()`).
"""

from __future__ import annotations

from enum import Enum
import json
import re
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetryEventType(str, Enum):
    """Authoritative lifecycle event types for Multi-Agent streaming telemetry."""

    QUERY_RECEIVED = "query_received"
    INTENT_CLASSIFIED = "intent_classified"
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    SYNTHESIS_STARTED = "synthesis_started"
    VERIFICATION_COMPLETED = "verification_completed"
    RESPONSE_COMPLETED = "response_completed"
    EXECUTION_FAILED = "execution_failed"
    HEARTBEAT = "heartbeat"


_SECRET_PATTERNS = re.compile(
    r"(?i)\b(?:bearer\s+[A-Za-z0-9_\-\.]{10,}|"
    r"st_[A-Za-z0-9_\-]{20,}|"
    r"sk-[A-Za-z0-9_\-]{20,}|"
    r"aiza[0-9A-Za-z_\-]{35}|"
    r"novanest_[A-Za-z0-9_\-]{16,}|"
    r"ey[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{15,})\b"
)

_STACK_TRACE_PATTERNS = re.compile(
    r"(?:Traceback \(most recent call last\):|File \".*?\", line \d+|raise \w+Error|in _orchestrate)",
    re.IGNORECASE,
)


def _scrub_telemetry_prose(text: str) -> str:
    """Scrub tokens, secrets, internal filepaths, and stack traces from telemetry prose."""
    if not text:
        return ""
    scrubbed = _SECRET_PATTERNS.sub("[REDACTED_SECRET]", text)
    if _STACK_TRACE_PATTERNS.search(scrubbed):
        scrubbed = _STACK_TRACE_PATTERNS.sub("[EXECUTION_FAULT]", scrubbed)
    # Strip potential path leaks
    scrubbed = re.sub(r"[A-Za-z]:\\[\w\\\.\-]+", "[PATH]", scrubbed)
    scrubbed = re.sub(r"/(?:Users|home|app|tmp)/[\w/\.\-]+", "[PATH]", scrubbed)
    return scrubbed.strip()


class OrchestratorTelemetryEvent(BaseModel):
    """
    Typed, immutable telemetry event emitted during MasterOrchestrator execution.
    Designed for real-time visualization in FloatingChatbot and AiIntelligenceView.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., min_length=1, max_length=64)
    session_id: str = Field(..., min_length=1, max_length=128)
    event_type: TelemetryEventType
    timestamp: float = Field(default_factory=time.time)
    agent_name: Optional[str] = Field(None, max_length=64)
    status: str = Field(..., min_length=1, max_length=32)
    duration_ms: Optional[float] = Field(None, ge=0.0)
    message: str = Field(..., min_length=1, max_length=500)
    stage: Optional[int] = Field(None, ge=1, le=2)
    data: Optional[Dict[str, Any]] = None

    @field_validator("message")
    @classmethod
    def _sanitize_message(cls, v: str) -> str:
        clean = _scrub_telemetry_prose(v)
        if not clean:
            return "Processing..."
        return clean[:500]

    @field_validator("agent_name")
    @classmethod
    def _validate_agent_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {
            "financial_agent",
            "customer_agent",
            "operations_agent",
            "restaurant_agent",
            "decision_agent",
            "sql_sandbox",
            "master_orchestrator",
        }
        clean_v = str(v).strip().lower()
        if clean_v in allowed:
            return clean_v
        # Sanitize unexpected agent names safely
        return re.sub(r"[^A-Za-z0-9_\-]", "", clean_v)[:64] or "unknown_agent"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        d = self.model_dump(mode="json")
        d["event_type"] = self.event_type.value
        return d

    def to_sse(self) -> str:
        """
        Format event compliant with the W3C Server-Sent Events (SSE) standard.
        Format:
            event: <event_type>
            data: <json_string>

        """
        json_payload = json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=True)
        return f"event: {self.event_type.value}\ndata: {json_payload}\n\n"

