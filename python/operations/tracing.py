"""
NovaNest Platform — OpenTelemetry Distributed Tracing & W3C Trace Context
-------------------------------------------------------------------------
Delivers distributed tracing across the full request lifecycle:
React SPA -> Nginx Reverse Proxy -> FastAPI Gateway -> Master Orchestrator -> Domain Agents -> MySQL.
Enforces strict secret and PII redaction across all span attributes.
"""

from __future__ import annotations

from contextlib import contextmanager
import contextvars
from datetime import datetime, timezone
import os
import re
import secrets
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# ------------------------------------------------------------------------------
# 1. OpenTelemetry Initialization & Resource Configuration
# ------------------------------------------------------------------------------
SERVICE_NAME = "novanest-platform"
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("APP_ENV", "production")

_RESOURCE = Resource.create({
    "service.name": SERVICE_NAME,
    "service.version": SERVICE_VERSION,
    "deployment.environment": ENVIRONMENT,
})

_PROVIDER = TracerProvider(resource=_RESOURCE)
_SPAN_EXPORTER = InMemorySpanExporter()
_PROVIDER.add_span_processor(SimpleSpanProcessor(_SPAN_EXPORTER))
trace.set_tracer_provider(_PROVIDER)

TRACER = trace.get_tracer(SERVICE_NAME, SERVICE_VERSION)

# ------------------------------------------------------------------------------
# 2. Strict Redaction Patterns for Secrets & PII
# ------------------------------------------------------------------------------
FORBIDDEN_KEY_PATTERNS = re.compile(
    r"(password|secret|token|api_key|auth|bearer|credential|cookie|private_key|card_number|cvv)",
    re.IGNORECASE,
)
PII_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PII_PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b")


def sanitize_attribute_value(key: str, value: Any) -> Any:
    """Redacts secrets and PII from span attributes."""
    if FORBIDDEN_KEY_PATTERNS.search(key):
        return "[REDACTED_SECRET]"

    val_str = str(value)
    if FORBIDDEN_KEY_PATTERNS.search(val_str):
        return "[REDACTED_SECRET]"

    val_str = PII_EMAIL_PATTERN.sub("[REDACTED_EMAIL]", val_str)
    val_str = PII_PHONE_PATTERN.sub("[REDACTED_PHONE]", val_str)
    return val_str


# ------------------------------------------------------------------------------
# 3. W3C Trace Context Utilities (W3C Recommendation)
# ------------------------------------------------------------------------------
# Format: 00-{trace_id:32hex}-{parent_id:16hex}-{trace_flags:02hex}
TRACEPARENT_REGEX = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def generate_trace_id() -> str:
    """Generates a 32-character lowercase hex string for W3C trace ID."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generates a 16-character lowercase hex string for W3C span ID."""
    return secrets.token_hex(8)


def parse_traceparent(header_val: Optional[str]) -> Optional[Tuple[str, str, str]]:
    """Parses W3C traceparent header into (trace_id, parent_span_id, flags)."""
    if not header_val:
        return None
    match = TRACEPARENT_REGEX.match(header_val.strip())
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None


def format_traceparent(trace_id: str, span_id: str, flags: str = "01") -> str:
    """Formats trace ID and span ID into compliant W3C traceparent header."""
    return f"00-{trace_id.lower():0>32}-{span_id.lower():0>16}-{flags}"


# ------------------------------------------------------------------------------
# 4. In-Memory Thread-Safe Trace History (Bounded Ring Buffer)
# ------------------------------------------------------------------------------
MAX_TRACE_HISTORY = 1000
_TRACE_HISTORY_LOCK = threading.Lock()
_RECENT_TRACES: List[Dict[str, Any]] = []


class SpanRecord:
    """Structured representation of an executed span for observability reporting."""

    def __init__(
        self,
        span_id: str,
        trace_id: str,
        name: str,
        service: str,
        start_time_utc: str,
        parent_span_id: Optional[str] = None,
    ):
        self.span_id = span_id
        self.trace_id = trace_id
        self.name = name
        self.service = service
        self.start_time_utc = start_time_utc
        self.end_time_utc: Optional[str] = None
        self.duration_ms: float = 0.0
        self.status: str = "OK"
        self.parent_span_id = parent_span_id
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = sanitize_attribute_value(key, value)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        sanitized_attrs = {}
        if attributes:
            for k, v in attributes.items():
                sanitized_attrs[k] = sanitize_attribute_value(k, v)
        self.events.append({
            "name": name,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "attributes": sanitized_attrs,
        })

    def finish(self, status: str = "OK", error_msg: Optional[str] = None) -> None:
        self.end_time_utc = datetime.now(timezone.utc).isoformat()
        self.status = status
        if error_msg:
            self.attributes["error.message"] = sanitize_attribute_value("error", error_msg)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "service": self.service,
            "start_time_utc": self.start_time_utc,
            "end_time_utc": self.end_time_utc,
            "duration_ms": round(self.duration_ms, 3),
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


# Context variable tracking active span hierarchy per thread & asyncio context
_CURRENT_SPAN_CV: contextvars.ContextVar[Optional[SpanRecord]] = contextvars.ContextVar("current_span", default=None)
_CURRENT_SPAN_TLS = threading.local()


def get_current_span() -> Optional[SpanRecord]:
    """Retrieves the active span record from contextvars or thread-local storage."""
    span = _CURRENT_SPAN_CV.get()
    if span is not None:
        return span
    return getattr(_CURRENT_SPAN_TLS, "current_span", None)


@contextmanager
def start_span(
    name: str,
    service: str = SERVICE_NAME,
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Iterator[SpanRecord]:
    """
    Context manager that starts and finishes an OpenTelemetry-compatible span.
    Propagates parent trace and span IDs across caller boundaries.
    """
    parent = get_current_span()
    active_trace_id = trace_id or (parent.trace_id if parent else generate_trace_id())
    active_parent_id = parent_span_id or (parent.span_id if parent else None)
    span_id = generate_span_id()

    start_ts = time.perf_counter()
    start_utc = datetime.now(timezone.utc).isoformat()

    span_record = SpanRecord(
        span_id=span_id,
        trace_id=active_trace_id,
        name=name,
        service=service,
        start_time_utc=start_utc,
        parent_span_id=active_parent_id,
    )

    if attributes:
        for k, v in attributes.items():
            span_record.set_attribute(k, v)

    prev_span = parent
    _CURRENT_SPAN_TLS.current_span = span_record
    cv_token = _CURRENT_SPAN_CV.set(span_record)

    try:
        yield span_record
        span_record.finish(status="OK")
    except Exception as exc:
        span_record.finish(status="ERROR", error_msg=str(exc))
        raise
    finally:
        span_record.duration_ms = (time.perf_counter() - start_ts) * 1000.0
        _CURRENT_SPAN_TLS.current_span = prev_span
        _CURRENT_SPAN_CV.reset(cv_token)

        with _TRACE_HISTORY_LOCK:
            _RECENT_TRACES.append(span_record.to_dict())
            if len(_RECENT_TRACES) > MAX_TRACE_HISTORY:
                _RECENT_TRACES.pop(0)


def get_recent_traces(limit: int = 50, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns recent recorded spans, optionally filtered by trace_id."""
    with _TRACE_HISTORY_LOCK:
        if trace_id:
            filtered = [s for s in _RECENT_TRACES if s["trace_id"] == trace_id]
            return filtered[-limit:]
        return _RECENT_TRACES[-limit:]


def clear_trace_history() -> None:
    """Clears the in-memory trace history buffer (used in tests)."""
    with _TRACE_HISTORY_LOCK:
        _RECENT_TRACES.clear()
