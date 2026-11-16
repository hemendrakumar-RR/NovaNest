"""
NovaNest Multi-Agent Foundation - Shared Typed Contracts
---------------------------------------------------------
Pydantic v2 validated schemas for multi-agent requests, messages, results,
provenance, execution metadata, caveats, and bounded structured outputs.

Security & Serialization Guarantees:
- Forbids raw pandas DataFrames/Series/Index or arbitrary non-JSON-safe objects.
- Rejects raw credentials/Bearer tokens/API keys in identity fields and redacts
  accidental secret/PII leakage in prose, payloads, and error diagnostics.
- Deterministic JSON serialization via Pydantic v2 `model_dump(mode="json")`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union
import uuid

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from python.ai.analyst.conversation_manager import redact_pii
from python.ai.analyst.sql_ast import ALLOWED_TABLES, MAX_ROW_LIMIT


MAX_CONTRACT_TABLE_ROWS = MAX_ROW_LIMIT  # 100 rows max per contract boundary
MAX_CONTRACT_CHART_ROWS = 200
MAX_QUERY_CHARS = 4000
MAX_SUMMARY_CHARS = 8000

_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_SECRET_KV_RE = re.compile(
    r"((?:x-api-key|api_key|apikey|secret|password|passwd|access_token|auth_token|novanest_admin_key|novanest_api_key|novanest_viewer_key)\s*[:=]\s*)([^\s,;'\"]+)",
    re.IGNORECASE,
)
_NOVANEST_KEY_TOKEN_RE = re.compile(r"\b(?:nv|novanest)[_-](?:admin|ops|operator|viewer|secret)[_-][A-Za-z0-9_-]{6,}\b", re.IGNORECASE)

_INJECTION_RULES: List[Tuple[str, re.Pattern[str]]] = [
    (
        "instruction_override",
        re.compile(
            r"(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+|any\s+|every\s+|the\s+|your\s+|previous\s+|prior\s+|above\s+){1,3}"
            r"(?:instructions?|rules?|prompts?|constraints?|safeguards?|guardrails?|output\s*verifier|verifier|rbac|acl|security|checks?)\b"
            r"(?:[^.!?\n]{0,160})?",
            re.IGNORECASE,
        ),
    ),
    (
        "role_delimiter_hijack",
        re.compile(
            r"(?:<\|(?:im_start|im_end|system|assistant|user)\|>|\[/?INST\]|</?system>|"
            r"(?:^|\n|\[\s*)(?:###\s*)?(?:system|assistant|developer)\s*(?:override|prompt|instruction|message)?\s*:\s*[^\n\]]{0,220}\s*\]?)",
            re.IGNORECASE,
        ),
    ),
    (
        "secret_exfiltration",
        re.compile(
            r"\b(?:reveal|print|dump|leak|expose|exfiltrate|output|return|show)\s+"
            r"(?:all\s+|the\s+|your\s+|raw\s+)?(?:novanest_[a-z_]*key|api[_ ]?key|admin[_ ]?key|secret|password|bearer\s+token|"
            r"access[_ ]?token|credentials?|sqlite_master|sqlite_schema|\.env|env(?:ironment)?\s+vars?)\b"
            r"(?:[^.!?\n]{0,120})?",
            re.IGNORECASE,
        ),
    ),
    (
        "fabricated_directive",
        re.compile(
            r"\b(?:report|state|declare|fabricate|invent|claim|set|treat)\s+"
            r"(?:revenue|gmv|profit|loss|leakage|churn|eta)\s+(?:as|=|to\s+be)\s+"
            r"(?:confirmed\s+(?:net\s+|financial\s+|revenue\s+)?loss|production[- ]?ready|₹?\s*\d[\d,\.]*\s*(?:cr|crores?|l|lakhs?|%))\b"
            r"(?:[^.!?\n]{0,100})?",
            re.IGNORECASE,
        ),
    ),
    (
        "script_injection",
        re.compile(
            r"(?:<\s*script\b[^>]*>[\s\S]*?<\s*/\s*script\s*>|<\s*script\b[^>]*>|"
            r"\bon(?:error|load|click|mouseover)\s*=\s*['\"][^'\"]*['\"])",
            re.IGNORECASE,
        ),
    ),
    (
        "jailbreak_or_persona_hijack",
        re.compile(
            r"\b(?:DAN|Do\s+Anything\s+Now|jailbreak|unrestricted\s+mode|developer\s+mode|aim\s+mode|evil\s+twin|always\s+comply)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "markdown_image_exfiltration",
        re.compile(
            r"!\[[^\]]*\]\(\s*https?://[^\s)]+\b",
            re.IGNORECASE,
        ),
    ),
    (
        "sql_grounding_bypass",
        re.compile(
            r"\b(?:bypass|skip|ignore|disable)\s+(?:sql\s+validation|ast\s+checks?|readonly\s+mode|grounding|table\s+whitelist)\b",
            re.IGNORECASE,
        ),
    ),
]


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    """Generate a compact deterministic-format UUIDv4 identifier."""
    token = uuid.uuid4().hex[:16]
    return f"{prefix}{token}" if prefix else token


def contains_secret_pattern(value: str) -> bool:
    """Detect raw credentials, Bearer tokens, JWTs, or secret key assignments."""
    if not value:
        return False
    if re.search(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", value, re.IGNORECASE):
        return True
    if re.search(r"\b(?:AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9_-]{12,})\b", value):
        return True
    if _JWT_RE.search(value) or _NOVANEST_KEY_TOKEN_RE.search(value):
        return True
    if _SECRET_KV_RE.search(value):
        return True
    return False


def sanitize_text(value: str) -> str:
    """Redact credentials, Bearer tokens, JWTs, API keys, and PII from strings."""
    if not value:
        return ""
    cleaned = redact_pii(str(value))
    cleaned = _JWT_RE.sub("[REDACTED_JWT]", cleaned)
    cleaned = _NOVANEST_KEY_TOKEN_RE.sub("[REDACTED_KEY]", cleaned)
    cleaned = _SECRET_KV_RE.sub(r"\1[REDACTED_SECRET]", cleaned)
    return cleaned


def detect_prompt_injection(value: str) -> List[str]:
    """Detect prompt-injection, role-delimiter, exfiltration, and script patterns cleanly."""
    if not value:
        return []
    text = str(value)
    hits: List[str] = []
    for tag, pattern in _INJECTION_RULES:
        if pattern.search(text):
            hits.append(tag)
    return hits


def neutralize_untrusted_text(value: str, *, replacement: str = "[FILTERED_DIRECTIVE]") -> str:
    """
    Sanitize secrets/PII AND neutralize untrusted prompt-injection or script payloads
    in CSV cell text, retrieved records, and inter-agent messages.
    """
    if not value:
        return ""
    cleaned = sanitize_text(value)
    for _, pattern in _INJECTION_RULES:
        cleaned = pattern.sub(replacement, cleaned)
    cleaned = re.sub(r"(?:\[FILTERED_DIRECTIVE\]\s*){2,}", f"{replacement} ", cleaned)
    return cleaned.strip()


def sanitize_user_query(value: str) -> Tuple[str, List[str], bool]:
    """
    Inspect an incoming user query for prompt injection or exfiltration payloads.
    Returns `(cleaned_query, detected_flags, should_block_pure_attack)`.
    Hybrid queries keep legitimate business/technical text after stripping injected directives;
    pure attacks or secret/system-exfiltration requests fail closed cleanly.
    """
    raw = sanitize_text(value or "").strip()
    if not raw:
        return "", [], False
    flags = detect_prompt_injection(raw)
    if not flags:
        return raw, [], False

    # Pure secret exfiltration or role/override without remaining meaningful business inquiry fails closed
    stripped = raw
    for _, pattern in _INJECTION_RULES:
        stripped = pattern.sub(" ", stripped)
    # Remove leftover filler connectors like "and then", punctuation, etc.
    meaningful = re.sub(r"[\s,;:.!?\"'`\-]+", " ", stripped).strip()
    meaningful_words = [
        w
        for w in meaningful.split()
        if w.lower() not in {"and", "then", "also", "please", "now", "to", "the", "a", "an", "for", "of", "me"}
    ]
    is_pure_attack = (
        ("secret_exfiltration" in flags)
        or (len(meaningful_words) < 2)
    )
    cleaned_out = re.sub(r"\s{2,}", " ", stripped).strip(" .;,:!?")
    return (cleaned_out or raw), flags, is_pure_attack


def _sanitize_untrusted_payload_value(value: Any, path: str = "payload") -> Any:
    """Recursively neutralize untrusted strings in inter-agent message payloads."""
    validated = validate_no_forbidden_runtime_objects(value, path=path)
    if isinstance(validated, str):
        return neutralize_untrusted_text(validated)
    if isinstance(validated, dict):
        return {k: _sanitize_untrusted_payload_value(v, path=f"{path}.{k}") for k, v in validated.items()}
    if isinstance(validated, list):
        return [_sanitize_untrusted_payload_value(item, path=f"{path}[{idx}]") for idx, item in enumerate(validated)]
    return validated


def validate_no_forbidden_runtime_objects(value: Any, path: str = "value") -> Any:
    """
    Recursively verify `value` contains no pandas DataFrames/Series/Index,
    callables, or non-JSON-primitive runtime objects, and sanitize string leaves.
    """
    if isinstance(value, (pd.DataFrame, pd.Series, pd.Index)):
        raise ValueError(
            f"Raw pandas {type(value).__name__} is forbidden inside agent contracts at '{path}'. "
            "Pass bounded summary metrics or row dictionaries instead."
        )
    if callable(value):
        raise ValueError(f"Callable objects are forbidden inside agent contracts at '{path}'.")

    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and (pd.isna(value) or value in (float("inf"), float("-inf"))):
            return None
        return value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, str):
        return sanitize_text(value)

    if isinstance(value, dict):
        sanitized_dict: Dict[str, Any] = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(f"Non-string dict key '{k!r}' is forbidden at '{path}'.")
            key_lower = k.lower()
            if any(
                sec_name in key_lower
                for sec_name in ("password", "passwd", "secret", "bearer", "api_key", "apikey", "access_token", "auth_token", "authorization", "x-api-key")
            ):
                sanitized_dict[k] = "[REDACTED_SECRET]"
            else:
                sanitized_dict[k] = validate_no_forbidden_runtime_objects(v, path=f"{path}.{k}")
        return sanitized_dict

    if isinstance(value, (list, tuple)):
        return [
            validate_no_forbidden_runtime_objects(item, path=f"{path}[{idx}]")
            for idx, item in enumerate(value)
        ]

    raise ValueError(
        f"Unsupported non-JSON-serializable object of type '{type(value).__name__}' at '{path}'."
    )


class AgentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    USER = "user"
    ORCHESTRATOR = "orchestrator"
    AGENT = "agent"
    VERIFIER = "verifier"
    SYSTEM = "system"
    TOOL = "tool"


class AgentDomain(str, Enum):
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    OPERATIONS = "operations"
    RESTAURANT = "restaurant"
    DECISION = "decision"
    GENERAL = "general"
    ORCHESTRATION = "orchestration"
    VERIFICATION = "verification"


class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataProvenance(BaseModel):
    """Describes the authoritative dataset, SQL view/table, or engine behind a fact/result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_name: str = Field(min_length=1, max_length=160)
    source_type: Literal[
        "csv",
        "sqlite",
        "mysql",
        "kpi_definition",
        "ml_artifact",
        "analytics_engine",
        "simulation",
    ] = "csv"
    dataset_or_table: Optional[str] = Field(default=None, max_length=120)
    row_count: Optional[int] = Field(default=None, ge=0)
    filters_applied: List[str] = Field(default_factory=list)
    as_of_utc: Optional[str] = None
    is_confirmed_loss: Optional[bool] = None

    @field_validator("source_name", "dataset_or_table")
    @classmethod
    def _sanitize_names(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v) if v is not None else None

    @field_validator("filters_applied")
    @classmethod
    def _sanitize_filters(cls, v: List[str]) -> List[str]:
        return [sanitize_text(item) for item in v]


class AgentError(BaseModel):
    """Structured error record carried cleanly across agent boundaries without secrets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=1000)
    agent_id: Optional[str] = Field(default=None, max_length=80)
    recoverable: bool = False
    severity: SeverityLevel = SeverityLevel.ERROR
    detail: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("message", "detail")
    @classmethod
    def _sanitize_error_text(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v) if v is not None else None


class AgentExecutionMetadata(BaseModel):
    """Timing and lifecycle metadata emitted for an individual agent invocation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1, max_length=80)
    execution_id: str = Field(min_length=1, max_length=80)
    agent_id: str = Field(min_length=1, max_length=80)
    agent_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    started_at_utc: datetime = Field(default_factory=utc_now)
    finished_at_utc: Optional[datetime] = None
    elapsed_ms: float = Field(default=0.0, ge=0.0)
    timed_out: bool = False
    cancelled: bool = False
    cache_hit: bool = False
    retry_count: int = Field(default=0, ge=0)


class GroundedFact(BaseModel):
    """Verified quantitative or factual assertion tied to an authoritative source."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(default_factory=lambda: new_id("fact_"), max_length=80)
    label: str = Field(min_length=1, max_length=200)
    value: Union[float, int, str]
    unit: Optional[str] = Field(default=None, max_length=40)
    kpi_id: Optional[str] = Field(default=None, max_length=32)
    source: str = Field(default="", max_length=160)
    formula: Optional[str] = Field(default=None, max_length=300)
    is_confirmed: bool = True
    is_confirmed_loss: Optional[bool] = None
    tolerance_rel: float = Field(default=0.005, ge=0.0, le=0.5)
    tolerance_abs: float = Field(default=0.0, ge=0.0)

    @field_validator("value")
    @classmethod
    def _validate_value(cls, v: Union[float, int, str]) -> Union[float, int, str]:
        if isinstance(v, (pd.DataFrame, pd.Series, pd.Index)):
            raise ValueError("GroundedFact.value cannot contain pandas objects.")
        if isinstance(v, float) and (pd.isna(v) or v in (float("inf"), float("-inf"))):
            raise ValueError("GroundedFact.value cannot be NaN or Infinity.")
        if isinstance(v, str):
            return sanitize_text(v)
        return v

    @field_validator("label", "source", "formula")
    @classmethod
    def _sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v) if v is not None else None


class ModelCaveat(BaseModel):
    """Explicit reliability disclosure for any Phase 05 ML / experimental output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_name: str = Field(min_length=1, max_length=120)
    domain: str = Field(min_length=1, max_length=60)
    validation_status: str = Field(min_length=1, max_length=60)
    metric_summary: str = Field(min_length=1, max_length=300)
    warning: str = Field(min_length=1, max_length=500)
    is_production_ready: bool = False


class SqlAuditTrace(BaseModel):
    """Read-only SQL execution trace compliant with Phase 05.3/06.0 AST sandbox rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sql: str = Field(min_length=1, max_length=4000)
    tables_accessed: List[str] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0, le=MAX_CONTRACT_TABLE_ROWS)
    execution_ms: float = Field(default=0.0, ge=0.0)
    validated_by_ast: bool = True

    @field_validator("tables_accessed")
    @classmethod
    def _check_allowed_tables(cls, tables: List[str]) -> List[str]:
        normalized: List[str] = []
        for tbl in tables:
            clean = tbl.strip().lower()
            if clean not in ALLOWED_TABLES:
                raise ValueError(f"Unauthorized SQL table '{tbl}' in SqlAuditTrace.")
            normalized.append(clean)
        return normalized


class ChartSpec(BaseModel):
    """Structured visualization specification safe for UI rendering."""

    model_config = ConfigDict(extra="forbid")

    chart_type: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=200)
    x_key: Optional[str] = Field(default=None, max_length=80)
    y_key: Optional[str] = Field(default=None, max_length=80)
    data: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_CONTRACT_CHART_ROWS)

    @field_validator("data")
    @classmethod
    def _validate_chart_data(cls, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(rows) > MAX_CONTRACT_CHART_ROWS:
            raise ValueError(f"ChartSpec.data exceeds {MAX_CONTRACT_CHART_ROWS} row limit.")
        return validate_no_forbidden_runtime_objects(rows, path="ChartSpec.data")


class ActionRecommendation(BaseModel):
    """Grounded action recommendation emitted by decision/analytics flows."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    target_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(default="", max_length=80)
    evidence: str = Field(default="", max_length=500)
    expected_impact: str = Field(default="", max_length=500)
    confidence: str = Field(default="", max_length=200)
    action: str = Field(default="", max_length=500)
    priority: str = Field(default="Medium", max_length=32)

    # Phase 08 Prescriptive & Financial Governance Fields
    recommendation_id: str = Field(default="", max_length=80)
    business_problem: str = Field(default="", max_length=500)
    proposed_action: str = Field(default="", max_length=500)
    expected_benefit: str = Field(default="", max_length=500)
    implementation_cost: float = Field(default=0.0)
    net_financial_impact: float = Field(default=0.0)
    risk_and_uncertainty: str = Field(default="", max_length=500)
    confidence_tier: str = Field(default="MODERATE", max_length=64)
    measurement_period: str = Field(default="30 days", max_length=64)
    success_metric: str = Field(default="", max_length=200)
    lifecycle_status: str = Field(default="Proposed", max_length=32)
    human_approval_required: bool = Field(default=True)
    is_simulation_projection: bool = Field(default=True)
    realized_outcome: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator(
        "title",
        "evidence",
        "expected_impact",
        "confidence",
        "action",
        "business_problem",
        "proposed_action",
        "expected_benefit",
        "risk_and_uncertainty",
        "success_metric",
        check_fields=False,
    )
    @classmethod
    def _sanitize_rec_strings(cls, v: str) -> str:
        return sanitize_text(v)


class AgentMessage(BaseModel):
    """Validated inter-agent or user-to-orchestrator communication envelope."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(default_factory=lambda: new_id("msg_"), max_length=80)
    request_id: str = Field(min_length=1, max_length=80)
    session_id: str = Field(default="default", min_length=1, max_length=64)
    role: MessageRole
    sender: str = Field(min_length=1, max_length=80)
    recipient: str = Field(min_length=1, max_length=80)
    content: str = Field(default="", max_length=MAX_SUMMARY_CHARS)
    timestamp_utc: datetime = Field(default_factory=utc_now)
    payload: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def _sanitize_content(cls, v: str) -> str:
        return neutralize_untrusted_text(v)

    @field_validator("payload")
    @classmethod
    def _validate_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        return _sanitize_untrusted_payload_value(v, path="AgentMessage.payload")


class AgentRequest(BaseModel):
    """Typed task request dispatched toward an individual agent or capability."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: new_id("req_"), max_length=80)
    execution_id: str = Field(default_factory=lambda: new_id("exec_"), max_length=80)
    agent_id: str = Field(min_length=1, max_length=80)
    domain: AgentDomain
    principal_id: str = Field(min_length=1, max_length=80)
    session_id: str = Field(default="default", min_length=1, max_length=64)
    user_query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    intent: Optional[str] = Field(default=None, max_length=80)
    filters: Dict[str, Any] = Field(default_factory=dict)
    allowed_tables: List[str] = Field(default_factory=list)
    required_scopes: List[str] = Field(default_factory=lambda: ["read"])
    timeout_seconds: float = Field(default=3.0, gt=0.0, le=60.0)
    trace_id: Optional[str] = Field(default=None, max_length=80)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("principal_id")
    @classmethod
    def _reject_secret_principal(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned or any(ch.isspace() for ch in cleaned):
            raise ValueError("principal_id must be a non-empty identifier without whitespace.")
        if contains_secret_pattern(cleaned):
            raise ValueError("principal_id must never contain raw credentials, Bearer tokens, JWTs, or API keys.")
        return cleaned

    @field_validator("user_query")
    @classmethod
    def _sanitize_query(cls, v: str) -> str:
        cleaned = sanitize_text(v.strip())
        if not cleaned:
            raise ValueError("user_query cannot be blank.")
        return cleaned

    @field_validator("allowed_tables")
    @classmethod
    def _validate_tables(cls, v: List[str]) -> List[str]:
        out: List[str] = []
        for tbl in v:
            clean = tbl.strip().lower()
            if clean not in ALLOWED_TABLES:
                raise ValueError(f"Unsupported SQL table '{tbl}' in AgentRequest.allowed_tables.")
            if clean not in out:
                out.append(clean)
        return out

    @field_validator("required_scopes")
    @classmethod
    def _validate_scopes(cls, v: List[str]) -> List[str]:
        valid: Set[str] = {"read", "operator", "admin"}
        out: List[str] = []
        for scope in v:
            s = scope.strip().lower()
            if s not in valid:
                raise ValueError(f"Invalid scope '{scope}'. Must be one of {sorted(valid)}.")
            if s not in out:
                out.append(s)
        return out or ["read"]

    @field_validator("filters", "metadata")
    @classmethod
    def _validate_dicts(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        return validate_no_forbidden_runtime_objects(v, path=f"AgentRequest.{info.field_name}")


class AgentResult(BaseModel):
    """Validated structured response emitted by any NovaNest agent component."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=80)
    execution_id: str = Field(default_factory=lambda: new_id("exec_"), max_length=80)
    agent_id: str = Field(min_length=1, max_length=80)
    domain: AgentDomain
    status: AgentStatus
    summary: str = Field(default="", max_length=MAX_SUMMARY_CHARS)
    narrative: str = Field(default="", max_length=MAX_SUMMARY_CHARS)
    facts: List[GroundedFact] = Field(default_factory=list)
    metrics: Dict[str, Union[float, int, str, bool, None]] = Field(default_factory=dict)
    table_rows: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_CONTRACT_TABLE_ROWS)
    charts: List[ChartSpec] = Field(default_factory=list)
    recommendations: List[ActionRecommendation] = Field(default_factory=list)
    caveats: List[ModelCaveat] = Field(default_factory=list)
    provenance: List[DataProvenance] = Field(default_factory=list)
    sql_traces: List[SqlAuditTrace] = Field(default_factory=list)
    errors: List[AgentError] = Field(default_factory=list)
    execution: Optional[AgentExecutionMetadata] = None
    is_confirmed_loss: Optional[bool] = None
    data_gaps: List[str] = Field(default_factory=list)

    @field_validator("summary", "narrative")
    @classmethod
    def _sanitize_prose(cls, v: str) -> str:
        return sanitize_text(v)

    @field_validator("data_gaps")
    @classmethod
    def _sanitize_gaps(cls, v: List[str]) -> List[str]:
        return [sanitize_text(item) for item in v if item and item.strip()]

    @field_validator("metrics")
    @classmethod
    def _validate_metrics(
        cls, v: Dict[str, Any]
    ) -> Dict[str, Union[float, int, str, bool, None]]:
        cleaned = validate_no_forbidden_runtime_objects(v, path="AgentResult.metrics")
        for key, item in cleaned.items():
            if not isinstance(item, (float, int, str, bool)) and item is not None:
                raise ValueError(f"AgentResult.metrics['{key}'] must be scalar, got {type(item).__name__}.")
        return cleaned

    @field_validator("table_rows")
    @classmethod
    def _validate_table_rows(cls, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(rows) > MAX_CONTRACT_TABLE_ROWS:
            raise ValueError(f"AgentResult.table_rows exceeds max limit ({MAX_CONTRACT_TABLE_ROWS}).")
        return validate_no_forbidden_runtime_objects(rows, path="AgentResult.table_rows")

    @model_validator(mode="after")
    def _validate_error_status_consistency(self) -> "AgentResult":
        if self.status in (AgentStatus.ERROR, AgentStatus.BLOCKED, AgentStatus.TIMEOUT):
            if not self.errors and not self.summary.strip():
                raise ValueError(
                    f"AgentResult with status '{self.status.value}' must include at least one AgentError or summary."
                )
        return self

    def to_safe_dict(self) -> Dict[str, Any]:
        """Return strictly JSON-serializable, secret-redacted representation."""
        return self.model_dump(mode="json")

