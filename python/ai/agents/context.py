"""
NovaNest Multi-Agent Foundation - Shared Execution Context & Principal Isolation
--------------------------------------------------------------------------------
Provides bounded, thread-safe, principal-isolated execution contexts for
multi-agent orchestration without retaining raw DataFrames, credentials, or PII.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from python.ai.agents.contracts import (
    AgentDomain,
    AgentExecutionMetadata,
    AgentStatus,
    contains_secret_pattern,
    new_id,
    sanitize_text,
    utc_now,
    validate_no_forbidden_runtime_objects,
)
from python.ai.analyst.conversation_manager import make_scoped_session_key, resolve_principal_key


_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_KPI_PATH = _REPO_ROOT / "datasets" / "analytics" / "kpi_definitions.json"

MAX_CONVERSATION_TURNS = 12
MAX_TURN_TEXT_CHARS = 2000
MAX_EXECUTION_HISTORY_ENTRIES = 25
MAX_DATASET_METADATA_ENTRIES = 30
MAX_KPI_ENTRIES = 32
MAX_COLUMNS_PER_DATASET = 80
MAX_CONTEXT_JSON_BYTES = 131_072  # 128 KB bounded context ceiling
MAX_MANAGED_CONTEXTS = 250


class DatasetMetadataEntry(BaseModel):
    """Lightweight schema descriptor for a dataset (strictly metadata, never DataFrames)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_name: str = Field(min_length=1, max_length=100)
    layer: str = Field(default="cleaned", max_length=40)
    row_count: Optional[int] = Field(default=None, ge=0)
    columns: List[str] = Field(default_factory=list, max_length=MAX_COLUMNS_PER_DATASET)
    primary_key: Optional[str] = Field(default=None, max_length=80)
    source_path: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=400)

    @field_validator("columns")
    @classmethod
    def _cap_columns(cls, cols: List[str]) -> List[str]:
        return [sanitize_text(str(c))[:80] for c in cols[:MAX_COLUMNS_PER_DATASET]]

    @field_validator("source_path", "notes")
    @classmethod
    def _sanitize_optional(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v) if v is not None else None


class KpiDefinitionEntry(BaseModel):
    """Certified KPI specification loaded from `kpi_definitions.json`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kpi_id: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=160)
    value: Optional[float] = None
    unit: str = Field(default="INR", max_length=40)
    mathematical_formula: str = Field(default="", max_length=300)
    source_tables: str = Field(default="", max_length=160)
    filters: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=500)


class ConversationTurnSummary(BaseModel):
    """Redacted, bounded single turn stored inside shared conversation context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str = Field(min_length=1, max_length=32)
    content: str = Field(min_length=1, max_length=MAX_TURN_TEXT_CHARS)
    intent: Optional[str] = Field(default=None, max_length=64)
    context_topic: Optional[str] = Field(default=None, max_length=64)
    timestamp_utc: datetime = Field(default_factory=utc_now)
    filters: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None

    @field_validator("content")
    @classmethod
    def _sanitize_turn(cls, v: str) -> str:
        return sanitize_text(v)[:MAX_TURN_TEXT_CHARS]


class AgentExecutionHistoryEntry(BaseModel):
    """Compact bounded record of a prior agent step executed within this request context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str = Field(min_length=1, max_length=80)
    domain: AgentDomain
    status: AgentStatus
    elapsed_ms: float = Field(default=0.0, ge=0.0)
    summary: str = Field(default="", max_length=500)
    data_sources_used: List[str] = Field(default_factory=list)
    recorded_at_utc: datetime = Field(default_factory=utc_now)

    @field_validator("summary")
    @classmethod
    def _sanitize_summary(cls, v: str) -> str:
        return sanitize_text(v)[:500]


class AgentContextSnapshot(BaseModel):
    """Immutable, JSON-safe snapshot of `AgentContext` shared with agents or traces."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    principal_id: str
    principal_role: str
    principal_scopes: List[str]
    session_id: str
    scoped_session_key: str
    user_query: str
    business_domains: List[AgentDomain]
    conversation_context: List[ConversationTurnSummary]
    dataset_metadata: Dict[str, DatasetMetadataEntry]
    kpi_definitions: Dict[str, KpiDefinitionEntry]
    agent_execution_history: List[AgentExecutionHistoryEntry]
    created_at_utc: datetime
    deadline_utc: datetime
    remaining_seconds: float
    cancelled: bool
    cancellation_reason: Optional[str]
    filters: Dict[str, Any]
    remembered_entities: Dict[str, Any] = Field(default_factory=dict)


def load_certified_kpi_entries(
    kpi_path: Optional[Path] = None,
    kpi_ids: Optional[List[str]] = None,
) -> Dict[str, KpiDefinitionEntry]:
    """Load certified KPI definitions cleanly without modifying source JSON."""
    path = kpi_path or _DEFAULT_KPI_PATH
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    entries: Dict[str, KpiDefinitionEntry] = {}
    filter_set = {k.upper() for k in kpi_ids} if kpi_ids else None
    for key, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        kid = str(payload.get("kpi_id") or key)
        if filter_set is not None and kid.upper() not in filter_set:
            continue
        if len(entries) >= MAX_KPI_ENTRIES:
            break
        val = payload.get("value")
        entries[kid] = KpiDefinitionEntry(
            kpi_id=kid,
            name=str(payload.get("name", kid)),
            value=float(val) if isinstance(val, (int, float)) else None,
            unit=str(payload.get("unit", "")),
            mathematical_formula=str(payload.get("mathematical_formula", "")),
            source_tables=str(payload.get("source_tables", "")),
            filters=str(payload.get("filters", "")),
            notes=str(payload.get("notes", "")),
        )
    return entries


def extract_dataset_metadata_from_frames(
    data: Dict[str, Any],
    max_entries: int = MAX_DATASET_METADATA_ENTRIES,
) -> Dict[str, DatasetMetadataEntry]:
    """
    Build lightweight metadata descriptors from DataFrames without storing DataFrame references.
    """
    out: Dict[str, DatasetMetadataEntry] = {}
    for name, frame in data.items():
        if len(out) >= min(max_entries, MAX_DATASET_METADATA_ENTRIES):
            break
        cols = getattr(frame, "columns", None)
        shape = getattr(frame, "shape", None)
        row_cnt = int(shape[0]) if isinstance(shape, tuple) and len(shape) >= 1 else None
        col_list = [str(c) for c in list(cols)][:MAX_COLUMNS_PER_DATASET] if cols is not None else []
        layer = "engineered" if any(
            k in name for k in ("prediction", "forecast", "anomaly", "leakage", "alert", "allocation", "engineered")
        ) else "cleaned"
        out[str(name)] = DatasetMetadataEntry(
            dataset_name=str(name),
            layer=layer,
            row_count=row_cnt,
            columns=col_list,
        )
    return out


def _validate_principal_id_safe(principal_id: str) -> str:
    clean = (principal_id or "").strip()
    if not clean or any(ch.isspace() for ch in clean):
        raise ValueError("principal_id must be a non-empty identifier without whitespace.")
    if contains_secret_pattern(clean):
        raise ValueError("principal_id cannot contain raw Bearer tokens, JWTs, or API keys.")
    return clean


class AgentContext:
    """
    Concurrent-safe, bounded shared execution context for a single multi-agent request.
    Enforces strict principal isolation, deadline tracking, cooperative cancellation,
    and zero retention of raw DataFrames or credentials.
    """

    def __init__(
        self,
        *,
        principal_id: str,
        user_query: str,
        session_id: str = "default",
        principal_role: str = "viewer",
        principal_scopes: Optional[FrozenSet[str] | List[str]] = None,
        business_domains: Optional[List[AgentDomain | str]] = None,
        request_id: Optional[str] = None,
        timeout_seconds: float = 15.0,
        filters: Optional[Dict[str, Any]] = None,
        remembered_entities: Optional[Dict[str, Any]] = None,
        dataset_metadata: Optional[Dict[str, DatasetMetadataEntry]] = None,
        kpi_definitions: Optional[Dict[str, KpiDefinitionEntry]] = None,
        conversation_context: Optional[List[ConversationTurnSummary]] = None,
        load_default_kpis: bool = False,
        parent_context: Optional["AgentContext"] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._parent_context = parent_context
        self._principal_id = _validate_principal_id_safe(principal_id)
        self._principal_role = (principal_role or "viewer").strip().lower()
        scopes = principal_scopes or ("read",)
        self._principal_scopes: FrozenSet[str] = frozenset(str(s).strip().lower() for s in scopes)

        clean_query = sanitize_text((user_query or "").strip())
        if not clean_query:
            raise ValueError("user_query cannot be blank.")
        self._user_query = clean_query[:4000]

        clean_session = sanitize_text((session_id or "default").strip())[:64] or "default"
        self._session_id = clean_session
        self._scoped_session_key = f"{self._principal_id}::{self._session_id}"
        self._request_id = (request_id or new_id("req_")).strip()

        resolved_domains: List[AgentDomain] = []
        for dom in business_domains or [AgentDomain.GENERAL]:
            resolved_domains.append(dom if isinstance(dom, AgentDomain) else AgentDomain(str(dom).lower()))
        self._business_domains: List[AgentDomain] = resolved_domains

        self._created_at_utc = utc_now()
        bounded_timeout = max(0.05, min(float(timeout_seconds), 300.0))
        self._deadline_utc = self._created_at_utc + timedelta(seconds=bounded_timeout)
        self._deadline_monotonic = time.monotonic() + bounded_timeout

        self._cancelled_event = threading.Event()
        self._cancellation_reason: Optional[str] = None

        self._filters: Dict[str, Any] = validate_no_forbidden_runtime_objects(
            filters or {}, path="AgentContext.filters"
        )
        self._remembered_entities: Dict[str, Any] = validate_no_forbidden_runtime_objects(
            remembered_entities or {}, path="AgentContext.remembered_entities"
        )
        self._conversation_context: List[ConversationTurnSummary] = list(
            (conversation_context or [])[-MAX_CONVERSATION_TURNS:]
        )

        self._dataset_metadata: Dict[str, DatasetMetadataEntry] = {}
        if dataset_metadata:
            for k, entry in list(dataset_metadata.items())[:MAX_DATASET_METADATA_ENTRIES]:
                self._dataset_metadata[k] = entry

        self._kpi_definitions: Dict[str, KpiDefinitionEntry] = {}
        if kpi_definitions:
            for k, entry in list(kpi_definitions.items())[:MAX_KPI_ENTRIES]:
                self._kpi_definitions[k] = entry
        elif load_default_kpis:
            self._kpi_definitions = load_certified_kpi_entries()

        self._execution_history: List[AgentExecutionHistoryEntry] = []

    @classmethod
    def from_auth_principal(
        cls,
        principal: Any,
        *,
        user_query: str,
        session_id: str = "default",
        business_domains: Optional[List[AgentDomain | str]] = None,
        timeout_seconds: float = 15.0,
        load_default_kpis: bool = False,
    ) -> "AgentContext":
        """Construct an `AgentContext` from an `api.auth.AuthPrincipal` or safe identifier."""
        pid = getattr(principal, "principal_id", None) or resolve_principal_key(principal)
        role = getattr(principal, "role", "viewer")
        scopes = getattr(principal, "scopes", frozenset({"read"}))
        return cls(
            principal_id=str(pid),
            principal_role=str(role),
            principal_scopes=scopes,
            session_id=session_id,
            user_query=user_query,
            business_domains=business_domains,
            timeout_seconds=timeout_seconds,
            load_default_kpis=load_default_kpis,
        )

    @property
    def principal_id(self) -> str:
        return self._principal_id

    @property
    def principal_role(self) -> str:
        return self._principal_role

    @property
    def principal_scopes(self) -> FrozenSet[str]:
        return self._principal_scopes

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def scoped_session_key(self) -> str:
        return self._scoped_session_key

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def user_query(self) -> str:
        return self._user_query

    @property
    def filters(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._filters)

    @property
    def remembered_entities(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._remembered_entities)

    def assert_principal(self, caller_principal_id: str) -> None:
        """Fail closed if a different principal attempts to access this context."""
        if (caller_principal_id or "").strip() != self._principal_id:
            raise PermissionError(
                f"Principal isolation violation: caller '{sanitize_text(str(caller_principal_id))}' "
                f"is not authorized for session context '{self._session_id}'."
            )

    def has_scope(self, scope: str) -> bool:
        return scope.strip().lower() in self._principal_scopes

    def remaining_seconds(self) -> float:
        with self._lock:
            rem = max(0.0, self._deadline_monotonic - time.monotonic())
        if self._parent_context is not None:
            rem = min(rem, self._parent_context.remaining_seconds())
        return rem

    def is_expired(self) -> bool:
        return self.remaining_seconds() <= 0.0

    def cancel(self, reason: str = "Execution cancelled") -> None:
        with self._lock:
            self._cancellation_reason = sanitize_text(reason)[:300]
            self._cancelled_event.set()

    def is_cancelled(self) -> bool:
        if self._cancelled_event.is_set():
            return True
        if self._parent_context is not None:
            return self._parent_context.is_cancelled()
        return False

    @property
    def cancel_reason(self) -> Optional[str]:
        return self._cancellation_reason

    @property
    def cancellation_reason(self) -> Optional[str]:
        return self._cancellation_reason

    def fork_for_agent(
        self,
        *,
        agent_id: str,
        timeout_seconds: Optional[float] = None,
    ) -> "AgentContext":
        """
        Create a child attempt context linked to this parent context:
        - Propagates parent cancellations automatically to the child
        - Allows cancelling an individual timed-out attempt without cancelling siblings
        - Bounds child deadline to parent's remaining budget
        """
        rem = self.remaining_seconds()
        child_timeout = max(0.05, min(rem, float(timeout_seconds))) if timeout_seconds is not None else max(0.05, rem)
        with self._lock:
            snap_turns = list(self._conversation_context)
            snap_ds = dict(self._dataset_metadata)
            snap_kpis = dict(self._kpi_definitions)
            snap_filters = dict(self._filters)
            snap_entities = dict(self._remembered_entities)
            snap_domains = list(self._business_domains)
        return AgentContext(
            principal_id=self._principal_id,
            user_query=self._user_query,
            session_id=self._session_id,
            principal_role=self._principal_role,
            principal_scopes=self._principal_scopes,
            business_domains=snap_domains,
            request_id=self._request_id,
            timeout_seconds=child_timeout,
            filters=snap_filters,
            remembered_entities=snap_entities,
            dataset_metadata=snap_ds,
            kpi_definitions=snap_kpis,
            conversation_context=snap_turns,
            load_default_kpis=False,
            parent_context=self,
        )

    def record_turn(
        self,
        role: str,
        content: str,
        intent: Optional[str] = None,
        context_topic: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        entities: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a bounded redacted conversation turn safely under lock."""
        turn = ConversationTurnSummary(
            role=sanitize_text(role)[:32] or "user",
            content=content,
            intent=intent,
            context_topic=context_topic,
            filters=dict(filters) if filters else None,
            entities=dict(entities) if entities else None,
        )
        with self._lock:
            self._conversation_context.append(turn)
            if len(self._conversation_context) > MAX_CONVERSATION_TURNS:
                self._conversation_context = self._conversation_context[-MAX_CONVERSATION_TURNS:]

    def record_execution_step(self, entry: AgentExecutionHistoryEntry) -> None:
        """Append a bounded execution history entry safely under lock."""
        with self._lock:
            self._execution_history.append(entry)
            if len(self._execution_history) > MAX_EXECUTION_HISTORY_ENTRIES:
                self._execution_history = self._execution_history[-MAX_EXECUTION_HISTORY_ENTRIES:]

    def register_dataset_metadata(self, entry: DatasetMetadataEntry) -> None:
        """Store lightweight dataset schema metadata safely (strictly bounded)."""
        with self._lock:
            if (
                entry.dataset_name not in self._dataset_metadata
                and len(self._dataset_metadata) >= MAX_DATASET_METADATA_ENTRIES
            ):
                raise ValueError(
                    f"Dataset metadata cap ({MAX_DATASET_METADATA_ENTRIES}) reached for context '{self._request_id}'."
                )
            self._dataset_metadata[entry.dataset_name] = entry

    def register_kpi_definition(self, entry: KpiDefinitionEntry) -> None:
        """Store a KPI definition safely (strictly bounded)."""
        with self._lock:
            if (
                entry.kpi_id not in self._kpi_definitions
                and len(self._kpi_definitions) >= MAX_KPI_ENTRIES
            ):
                raise ValueError(
                    f"KPI definition cap ({MAX_KPI_ENTRIES}) reached for context '{self._request_id}'."
                )
            self._kpi_definitions[entry.kpi_id] = entry

    def snapshot(self, caller_principal_id: Optional[str] = None) -> AgentContextSnapshot:
        """Return an immutable deep snapshot, enforcing principal ownership if supplied."""
        if caller_principal_id is not None:
            self.assert_principal(caller_principal_id)

        with self._lock:
            remaining = round(max(0.0, self._deadline_monotonic - time.monotonic()), 4)
            return AgentContextSnapshot(
                request_id=self._request_id,
                principal_id=self._principal_id,
                principal_role=self._principal_role,
                principal_scopes=sorted(self._principal_scopes),
                session_id=self._session_id,
                scoped_session_key=self._scoped_session_key,
                user_query=self._user_query,
                business_domains=list(self._business_domains),
                conversation_context=list(self._conversation_context),
                dataset_metadata=dict(self._dataset_metadata),
                kpi_definitions=dict(self._kpi_definitions),
                agent_execution_history=list(self._execution_history),
                created_at_utc=self._created_at_utc,
                deadline_utc=self._deadline_utc,
                remaining_seconds=remaining,
                cancelled=self._cancelled_event.is_set(),
                cancellation_reason=self._cancellation_reason,
                filters=validate_no_forbidden_runtime_objects(self._filters, path="AgentContext.filters"),
                remembered_entities=validate_no_forbidden_runtime_objects(
                    self._remembered_entities, path="AgentContext.remembered_entities"
                ),
            )

    def to_safe_dict(self, caller_principal_id: Optional[str] = None) -> Dict[str, Any]:
        """Serialize context snapshot to JSON-safe dict within `MAX_CONTEXT_JSON_BYTES`."""
        payload = self.snapshot(caller_principal_id=caller_principal_id).model_dump(mode="json")
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_CONTEXT_JSON_BYTES:
            raise ValueError(
                f"Serialized AgentContext exceeds {MAX_CONTEXT_JSON_BYTES} byte limit ({len(encoded)} bytes)."
            )
        return payload


class AgentContextManager:
    """Thread-safe, principal-isolated, LRU-bounded registry of active execution contexts."""

    def __init__(self, max_contexts: int = MAX_MANAGED_CONTEXTS) -> None:
        self._max_contexts = max(1, int(max_contexts))
        self._lock = threading.RLock()
        self._contexts: "OrderedDict[str, AgentContext]" = OrderedDict()

    @staticmethod
    def _scope_key(principal_id: str, session_id: str) -> str:
        safe_pid = _validate_principal_id_safe(principal_id)
        return make_scoped_session_key(session_id, safe_pid)

    def put_context(self, context: AgentContext) -> str:
        """Register an `AgentContext` under its principal-scoped key."""
        key = self._scope_key(context.principal_id, context.session_id)
        with self._lock:
            self._contexts[key] = context
            self._contexts.move_to_end(key)
            while len(self._contexts) > self._max_contexts:
                self._contexts.popitem(last=False)
        return key

    def get_context(self, principal_id: str, session_id: str) -> Optional[AgentContext]:
        """Retrieve a context strictly belonging to `(principal_id, session_id)`."""
        key = self._scope_key(principal_id, session_id)
        with self._lock:
            ctx = self._contexts.get(key)
            if ctx is None:
                return None
            ctx.assert_principal(principal_id)
            self._contexts.move_to_end(key)
            return ctx

    def remove_context(self, principal_id: str, session_id: str) -> bool:
        """Delete only the caller's own scoped context entry."""
        key = self._scope_key(principal_id, session_id)
        with self._lock:
            ctx = self._contexts.get(key)
            if ctx is None:
                return False
            ctx.assert_principal(principal_id)
            self._contexts.pop(key, None)
            return True

    def active_count(self) -> int:
        with self._lock:
            return len(self._contexts)

