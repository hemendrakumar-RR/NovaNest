"""
NovaNest Multi-Agent Foundation - Execution Tracing & Safe Telemetry
--------------------------------------------------------------------
Provides thread-safe, bounded, secret-redacted execution traces capturing
request lifecycle timings, per-agent spans, errors, data sources used, and
verification outcomes across multi-agent workflows.
"""

from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import threading
import time
from typing import Any, Dict, Iterator, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from python.ai.agents.contracts import (
    AgentDomain,
    AgentError,
    AgentResult,
    AgentStatus,
    new_id,
    sanitize_text,
    utc_now,
    validate_no_forbidden_runtime_objects,
)


MAX_TRACES_IN_MEMORY = 500
MAX_SPANS_PER_TRACE = 50
MAX_DATA_SOURCES_PER_SPAN = 30
MAX_ERRORS_PER_SPAN = 20


class TraceVerificationOutcome(str, Enum):
    NOT_RUN = "not_run"
    VERIFIED = "verified"
    PARTIAL = "partial"
    REJECTED = "rejected"


class AgentSpanTrace(BaseModel):
    """Execution telemetry for a single agent invocation inside a request trace."""

    model_config = ConfigDict(extra="forbid")

    span_id: str = Field(default_factory=lambda: new_id("span_"), max_length=80)
    request_id: str = Field(min_length=1, max_length=80)
    agent_id: str = Field(min_length=1, max_length=80)
    domain: AgentDomain = AgentDomain.GENERAL
    started_at_utc: datetime = Field(default_factory=utc_now)
    finished_at_utc: Optional[datetime] = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    status: AgentStatus = AgentStatus.PENDING
    errors: List[AgentError] = Field(default_factory=list, max_length=MAX_ERRORS_PER_SPAN)
    data_sources_used: List[str] = Field(default_factory=list, max_length=MAX_DATA_SOURCES_PER_SPAN)
    verification_outcome: TraceVerificationOutcome = TraceVerificationOutcome.NOT_RUN
    verification_notes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("data_sources_used", "verification_notes")
    @classmethod
    def _sanitize_lists(cls, items: List[str]) -> List[str]:
        return [sanitize_text(item) for item in items if item and str(item).strip()]

    @field_validator("metadata")
    @classmethod
    def _sanitize_meta(cls, meta: Dict[str, Any]) -> Dict[str, Any]:
        return validate_no_forbidden_runtime_objects(meta, path="AgentSpanTrace.metadata")


class ExecutionTrace(BaseModel):
    """Top-level execution trace spanning a single multi-agent request lifecycle."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(default_factory=lambda: new_id("trace_"), max_length=80)
    request_id: str = Field(min_length=1, max_length=80)
    principal_id: str = Field(default="anon:local", min_length=1, max_length=80)
    session_id: str = Field(default="default", min_length=1, max_length=64)
    started_at_utc: datetime = Field(default_factory=utc_now)
    finished_at_utc: Optional[datetime] = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    status: AgentStatus = AgentStatus.PENDING
    spans: List[AgentSpanTrace] = Field(default_factory=list, max_length=MAX_SPANS_PER_TRACE)
    data_sources_used: List[str] = Field(default_factory=list)
    errors: List[AgentError] = Field(default_factory=list)
    verification_outcome: TraceVerificationOutcome = TraceVerificationOutcome.NOT_RUN

    def to_safe_dict(self) -> Dict[str, Any]:
        """Return bounded, secret-redacted JSON-compatible trace dictionary."""
        return self.model_dump(mode="json")


class _ActiveSpanTimer:
    """Internal monotonic clock tracker paired with a live span."""

    __slots__ = ("trace_request_id", "span", "start_mono")

    def __init__(self, trace_request_id: str, span: AgentSpanTrace, start_mono: float) -> None:
        self.trace_request_id = trace_request_id
        self.span = span
        self.start_mono = start_mono


class ExecutionTracer:
    """Thread-safe LRU-bounded execution trace store with automatic secret/PII redaction."""

    def __init__(
        self,
        max_traces: int = MAX_TRACES_IN_MEMORY,
        max_spans_per_trace: int = MAX_SPANS_PER_TRACE,
    ) -> None:
        self._max_traces = max(1, int(max_traces))
        self._max_spans_per_trace = max(1, int(max_spans_per_trace))
        self._lock = threading.RLock()
        self._traces: "OrderedDict[str, ExecutionTrace]" = OrderedDict()
        self._trace_start_mono: Dict[str, float] = {}
        self._active_spans: Dict[str, _ActiveSpanTimer] = {}

    def start_trace(
        self,
        request_id: str,
        principal_id: str = "anon:local",
        session_id: str = "default",
    ) -> ExecutionTrace:
        """Create or retrieve a trace record for `request_id`."""
        safe_principal = sanitize_text(principal_id or "anon:local")[:80] or "anon:local"
        safe_session = sanitize_text(session_id or "default")[:64] or "default"

        with self._lock:
            existing = self._traces.get(request_id)
            if existing is not None:
                self._traces.move_to_end(request_id)
                return existing.model_copy(deep=True)

            trace = ExecutionTrace(
                request_id=request_id,
                principal_id=safe_principal,
                session_id=safe_session,
            )
            self._traces[request_id] = trace
            self._trace_start_mono[request_id] = time.monotonic()
            self._evict_overflow_locked()
            return trace.model_copy(deep=True)

    def _evict_overflow_locked(self) -> None:
        while len(self._traces) > self._max_traces:
            evicted_req_id, _ = self._traces.popitem(last=False)
            self._trace_start_mono.pop(evicted_req_id, None)

    def start_span(
        self,
        request_id: str,
        agent_id: str,
        domain: AgentDomain = AgentDomain.GENERAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Begin a timed agent execution span inside `request_id` trace and return `span_id`."""
        with self._lock:
            if request_id not in self._traces:
                self.start_trace(request_id=request_id)

            trace = self._traces[request_id]
            span = AgentSpanTrace(
                request_id=request_id,
                agent_id=agent_id,
                domain=domain,
                metadata=metadata or {},
            )
            if len(trace.spans) >= self._max_spans_per_trace:
                trace.spans.pop(0)
            trace.spans.append(span)
            self._active_spans[span.span_id] = _ActiveSpanTimer(
                trace_request_id=request_id,
                span=span,
                start_mono=time.monotonic(),
            )
            return span.span_id

    def finish_span(
        self,
        span_id: str,
        status: AgentStatus = AgentStatus.SUCCESS,
        data_sources_used: Optional[List[str]] = None,
        errors: Optional[List[AgentError]] = None,
        verification_outcome: TraceVerificationOutcome = TraceVerificationOutcome.NOT_RUN,
        verification_notes: Optional[List[str]] = None,
    ) -> Optional[AgentSpanTrace]:
        """Complete a running span, computing elapsed duration and redacting fields."""
        with self._lock:
            timer = self._active_spans.pop(span_id, None)
            if timer is None:
                return None

            elapsed = max(0.0, (time.monotonic() - timer.start_mono) * 1000.0)
            span = timer.span
            span.finished_at_utc = utc_now()
            span.duration_ms = round(elapsed, 3)
            span.status = status
            span.verification_outcome = verification_outcome

            if data_sources_used:
                deduped_sources: List[str] = []
                for src in span.data_sources_used + list(data_sources_used):
                    clean_src = sanitize_text(str(src)).strip()
                    if clean_src and clean_src not in deduped_sources:
                        deduped_sources.append(clean_src)
                span.data_sources_used = deduped_sources[:MAX_DATA_SOURCES_PER_SPAN]

            if errors:
                combined_errors = span.errors + list(errors)
                span.errors = combined_errors[:MAX_ERRORS_PER_SPAN]

            if verification_notes:
                span.verification_notes = [
                    sanitize_text(str(note)) for note in verification_notes if note
                ]

            trace = self._traces.get(timer.trace_request_id)
            if trace is not None:
                for src in span.data_sources_used:
                    if src not in trace.data_sources_used:
                        trace.data_sources_used.append(src)
                if errors:
                    trace.errors.extend(errors[:MAX_ERRORS_PER_SPAN])

            return span.model_copy(deep=True)

    def record_agent_result(
        self,
        span_id: str,
        result: AgentResult,
        verification_outcome: TraceVerificationOutcome = TraceVerificationOutcome.NOT_RUN,
        verification_notes: Optional[List[str]] = None,
    ) -> Optional[AgentSpanTrace]:
        """Finish a span directly from a typed `AgentResult`."""
        sources = [
            p.dataset_or_table or p.source_name
            for p in result.provenance
            if p.dataset_or_table or p.source_name
        ]
        return self.finish_span(
            span_id=span_id,
            status=result.status,
            data_sources_used=sources,
            errors=result.errors,
            verification_outcome=verification_outcome,
            verification_notes=verification_notes,
        )

    def finish_trace(
        self,
        request_id: str,
        status: Optional[AgentStatus] = None,
        verification_outcome: Optional[TraceVerificationOutcome] = None,
    ) -> Optional[ExecutionTrace]:
        """Mark the request trace finished and return a safe deep copy."""
        with self._lock:
            trace = self._traces.get(request_id)
            if trace is None:
                return None

            start_mono = self._trace_start_mono.get(request_id)
            if start_mono is not None:
                trace.duration_ms = round(max(0.0, (time.monotonic() - start_mono) * 1000.0), 3)
            trace.finished_at_utc = utc_now()

            if status is not None:
                trace.status = status
            elif trace.status == AgentStatus.PENDING:
                if any(s.status in (AgentStatus.ERROR, AgentStatus.BLOCKED) for s in trace.spans):
                    trace.status = AgentStatus.PARTIAL
                elif trace.spans and all(s.status == AgentStatus.SUCCESS for s in trace.spans):
                    trace.status = AgentStatus.SUCCESS

            if verification_outcome is not None:
                trace.verification_outcome = verification_outcome

            return trace.model_copy(deep=True)

    def get_trace(self, request_id: str, principal_id: Optional[str] = None) -> Optional[ExecutionTrace]:
        """
        Return a deep copy of the trace for `request_id`.
        If `principal_id` is provided, enforce principal isolation (returns None on mismatch).
        """
        with self._lock:
            trace = self._traces.get(request_id)
            if trace is None:
                return None
            if principal_id is not None and trace.principal_id != principal_id:
                return None
            return trace.model_copy(deep=True)

    @contextmanager
    def span(
        self,
        request_id: str,
        agent_id: str,
        domain: AgentDomain = AgentDomain.GENERAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Context manager wrapping an agent execution block to automatically capture
        start/end timestamps, exceptions, data sources, and completion status.
        """
        span_id = self.start_span(request_id=request_id, agent_id=agent_id, domain=domain, metadata=metadata)
        outcome: Dict[str, Any] = {
            "span_id": span_id,
            "status": AgentStatus.SUCCESS,
            "data_sources_used": [],
            "errors": [],
            "verification_outcome": TraceVerificationOutcome.NOT_RUN,
            "verification_notes": [],
        }
        try:
            yield outcome
        except Exception as exc:
            outcome["status"] = AgentStatus.ERROR
            outcome["errors"].append(
                AgentError(
                    code="SPAN_UNHANDLED_ERROR",
                    message=sanitize_text(str(exc)),
                    agent_id=agent_id,
                    recoverable=False,
                )
            )
            raise
        finally:
            self.finish_span(
                span_id=span_id,
                status=outcome["status"],
                data_sources_used=outcome.get("data_sources_used"),
                errors=outcome.get("errors"),
                verification_outcome=outcome.get("verification_outcome", TraceVerificationOutcome.NOT_RUN),
                verification_notes=outcome.get("verification_notes"),
            )

