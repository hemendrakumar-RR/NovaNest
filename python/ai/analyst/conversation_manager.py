"""
NovaNest Multi-Turn Conversation & Principal-Scoped Session Context Manager
----------------------------------------------------------------------------
Maintains thread-safe, TTL-bounded, LRU-capped conversation memory isolated per
authenticated principal identity with PII/credential redaction, entity persistence,
active filter resolution, and zero raw DataFrame retention.
"""

from __future__ import annotations

from collections import OrderedDict
import hashlib
import hmac
import re
import secrets
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

_SESSION_TTL_SECONDS = 1800  # 30-minute idle TTL
_MAX_SESSIONS = 250          # Maximum concurrent LRU sessions
_MAX_HISTORY_TURNS = 12      # Maximum retained turns per session
_MAX_TURN_CHARS = 4000       # Maximum preserved content characters per turn
_MAX_ENTITIES = 16           # Maximum stored active entities per session
_MAX_RECENT_FACTS = 20       # Maximum remembered verified facts per session

_SESSION_PEPPER = secrets.token_bytes(32)
_SESSION_LOCK = threading.RLock()

# OrderedDict keyed by scoped key -> session entry dict:
# {
#     "principal_key": str,
#     "session_id": str,
#     "turns": list,
#     "active_filters": dict,
#     "remembered_entities": dict,
#     "recent_facts": dict,
#     "last_topic": Optional[str],
#     "last_intent": Optional[str],
#     "last_domain": Optional[str],
#     "last_accessed": float
# }
_SESSIONS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE)
_API_KEY_RE = re.compile(r"\b(?:AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9_-]{12,})\b")
_PHONE_CONTEXT_RE = re.compile(
    r"((?:phone|mobile|contact|tel|whatsapp)\s*[:=]?\s*)(?:\+?\d[\d\s\-().]{7,15}\d)",
    re.IGNORECASE,
)
_INDIAN_MOBILE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?)[6-9]\d{9}(?!\d)")
_INTL_PHONE_RE = re.compile(r"(?<!\d)\+\d{1,3}[\s-]\d{3,5}[\s-]\d{4,6}(?!\d)")
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")


# ----------------------------------------------------------------------
# Entity Extraction Constants & Patterns
# ----------------------------------------------------------------------

_CANONICAL_CITIES = {
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "chennai": "Chennai",
    "madras": "Chennai",
    "hyderabad": "Hyderabad",
    "coimbatore": "Coimbatore",
    "vijayawada": "Vijayawada",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "pune": "Pune",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "chandigarh": "Chandigarh",
}

_CITY_PATTERNS = re.compile(
    r"\b(?:in|at|for|from|around|across)?\s*\b("
    + "|".join(re.escape(k) for k in _CANONICAL_CITIES.keys())
    + r")\b",
    re.IGNORECASE,
)

_RESET_CITY_PATTERNS = re.compile(
    r"\b(?:all cities|across all cities|nationwide|countrywide|platform-wide|overall|all regions|across India|every city)\b",
    re.IGNORECASE,
)

_CUSTOMER_SEGMENTS = {
    "champions": "Champions",
    "loyal customers": "Loyal Customers",
    "loyal customer": "Loyal Customers",
    "potential loyalists": "Potential Loyalists",
    "potential loyalist": "Potential Loyalists",
    "recent customers": "Recent Customers",
    "promising": "Promising",
    "needing attention": "Customers Needing Attention",
    "about to sleep": "About to Sleep",
    "at risk": "At Risk",
    "at-risk": "At Risk",
    "cant lose them": "Can't Lose Them",
    "can't lose them": "Can't Lose Them",
    "hibernating": "Hibernating",
    "lost": "Lost",
    "vip": "VIP",
}

_SEGMENT_PATTERNS = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _CUSTOMER_SEGMENTS.keys()) + r")\b",
    re.IGNORECASE,
)

_RESET_SEGMENT_PATTERNS = re.compile(
    r"\b(?:all segments|all customers|overall customers|across all segments)\b",
    re.IGNORECASE,
)

_RESET_RESTAURANT_PATTERNS = re.compile(
    r"\b(?:all restaurants|all merchants|all partners|across all restaurants|platform-wide restaurants)\b",
    re.IGNORECASE,
)

_RESTAURANT_NAME_PATTERN = re.compile(
    r"\b(?:restaurant|merchant|partner|outlet)\s+['\"]?([A-Za-z0-9\s&',.-]{2,50}?)['\"]?(?:\s+(?:in|at|with|has|is|metrics|performance|health|rating)|$|\?|,)",
    re.IGNORECASE,
)

_DATE_RANGE_PATTERNS = [
    (re.compile(r"\b(?:last\s+quarter|q[1-4]\s*202[4-6]|q[1-4])\b", re.IGNORECASE), "last_quarter"),
    (re.compile(r"\b(?:last\s+month|previous\s+month)\b", re.IGNORECASE), "last_month"),
    (re.compile(r"\b(?:last\s+year|full\s+year|annual|202[4-6])\b", re.IGNORECASE), "annual"),
    (re.compile(r"\b(?:last\s+week|past\s+7\s+days)\b", re.IGNORECASE), "last_week"),
]


def redact_pii(text: str) -> str:
    """Redacts emails, bearer tokens, API keys, PAN IDs, and explicit phone strings before storage."""
    if not text:
        return ""
    cleaned = _BEARER_RE.sub("Bearer [REDACTED_TOKEN]", text)
    cleaned = _API_KEY_RE.sub("[REDACTED_KEY]", cleaned)
    cleaned = _EMAIL_RE.sub("[REDACTED_EMAIL]", cleaned)
    cleaned = _PHONE_CONTEXT_RE.sub(r"\1[REDACTED_PHONE]", cleaned)
    cleaned = _INDIAN_MOBILE_RE.sub("[REDACTED_PHONE]", cleaned)
    cleaned = _INTL_PHONE_RE.sub("[REDACTED_PHONE]", cleaned)
    cleaned = _PAN_RE.sub("[REDACTED_ID]", cleaned)
    return cleaned


def _neutralize_text_safe(text: str) -> str:
    """Safely neutralizes prompt injection directives using contracts helper or fallback regex."""
    if not text:
        return ""
    try:
        from python.ai.agents.contracts import neutralize_untrusted_text
        return neutralize_untrusted_text(text)
    except Exception:
        cleaned = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", cleaned).strip()


def _hmac_short(raw: str) -> str:
    return hmac.new(_SESSION_PEPPER, raw.encode("utf-8"), hashlib.sha256).hexdigest()[:12]


def resolve_principal_key(principal: Any = None) -> str:
    """
    Resolves a safe non-reversible principal key.
    Never uses raw bearer tokens or secret strings directly as identifiers.
    """
    if principal is None:
        return "anon:local"

    pid = getattr(principal, "principal_id", None)
    if isinstance(pid, str) and pid.strip():
        clean_pid = pid.strip()
        if ":" in clean_pid and len(clean_pid) <= 32:
            return clean_pid
        return f"principal:{_hmac_short(clean_pid)}"

    role = getattr(principal, "role", None)
    if isinstance(role, str) and role.strip():
        return f"{role.strip().lower()}:default"

    if isinstance(principal, str) and principal.strip():
        raw = principal.strip()
        if re.fullmatch(r"[a-zA-Z0-9_-]{2,20}:[0-9a-f]{8,24}", raw):
            return raw
        return f"user:{_hmac_short(raw)}"

    return "anon:local"


def _sanitize_session_id(session_id: Optional[str]) -> str:
    raw = (session_id or "default").strip()
    clean = re.sub(r"[^a-zA-Z0-9_.:-]", "_", raw)[:64]
    return clean or "default"


def make_scoped_session_key(session_id: Optional[str], principal: Any = None) -> str:
    """Constructs the principal-isolated session store key."""
    return f"{resolve_principal_key(principal)}::{_sanitize_session_id(session_id)}"


def _evict_expired_locked(now_mono: float) -> None:
    """Removes sessions exceeding the 30-minute idle TTL (caller must hold _SESSION_LOCK)."""
    expired_keys = [
        k for k, entry in _SESSIONS.items()
        if (now_mono - float(entry.get("last_accessed", 0.0))) > _SESSION_TTL_SECONDS
    ]
    for k in expired_keys:
        _SESSIONS.pop(k, None)


def _enforce_lru_cap_locked() -> None:
    """Enforces 250-session LRU ceiling (caller must hold _SESSION_LOCK)."""
    while len(_SESSIONS) > _MAX_SESSIONS:
        _SESSIONS.popitem(last=False)


# ----------------------------------------------------------------------
# Entity Extraction Engine
# ----------------------------------------------------------------------

def extract_conversational_entities(text: str) -> Dict[str, Any]:
    """
    Extracts structured entities (city, restaurant, customer_segment, date_range, business_domain)
    and reset triggers from natural language queries.
    All outputs are sanitized, neutralized against injection directives, and PII-redacted.
    """
    if not text:
        return {}

    neutralized = _neutralize_text_safe(text)
    clean_text = redact_pii(neutralized).strip()
    lowered = clean_text.lower()
    entities: Dict[str, Any] = {}
    reset_flags: List[str] = []

    # 1. Reset triggers
    if _RESET_CITY_PATTERNS.search(lowered):
        reset_flags.append("city")
    if _RESET_SEGMENT_PATTERNS.search(lowered):
        reset_flags.append("customer_segment")
    if _RESET_RESTAURANT_PATTERNS.search(lowered):
        reset_flags.append("restaurant")
    if re.search(r"\b(?:clear\s+(?:all\s+)?filters?|reset\s+(?:all\s+)?filters?)\b", lowered):
        reset_flags.extend(["city", "customer_segment", "restaurant", "date_range"])

    if reset_flags:
        entities["_reset_entities"] = list(set(reset_flags))

    # 2. City entity extraction
    if "city" not in reset_flags:
        city_m = _CITY_PATTERNS.search(lowered)
        if city_m:
            matched_city = city_m.group(1).lower()
            canonical_city = _CANONICAL_CITIES.get(matched_city)
            if canonical_city:
                entities["city"] = canonical_city

    # 3. Customer Segment extraction
    if "customer_segment" not in reset_flags:
        seg_m = _SEGMENT_PATTERNS.search(lowered)
        if seg_m:
            matched_seg = seg_m.group(1).lower()
            canonical_seg = _CUSTOMER_SEGMENTS.get(matched_seg)
            if canonical_seg:
                entities["customer_segment"] = canonical_seg

    # 4. Restaurant extraction
    if "restaurant" not in reset_flags:
        rest_m = _RESTAURANT_NAME_PATTERN.search(clean_text)
        if rest_m:
            raw_rest = rest_m.group(1).strip(" '\"")
            if len(raw_rest) >= 2 and raw_rest.lower() not in {
                "performance", "health", "metrics", "risk", "status", "scores", "all", "each", "my", "our", "the"
            }:
                entities["restaurant"] = raw_rest[:50]
        else:
            quoted_m = re.search(
                r"(?:for|at|restaurant|merchant)\s+['\"]([A-Za-z0-9\s&',.-]{2,40})['\"]",
                clean_text,
                re.IGNORECASE,
            )
            if quoted_m:
                entities["restaurant"] = quoted_m.group(1).strip()[:50]

    # 5. Date Range extraction
    if "date_range" not in reset_flags:
        for pat, range_label in _DATE_RANGE_PATTERNS:
            if pat.search(lowered):
                entities["date_range"] = range_label
                break

    # 5b. Specific Business Entity IDs (customer_id, restaurant_id, rider_id)
    cust_m = re.search(r"\b(cust[_-]?\d+)\b", lowered)
    if not cust_m:
        cust_m = re.search(r"\bcustomer\s+(?:id|#|code|num|number)\s*[:=]?\s*([A-Za-z0-9_-]+)\b", lowered)
    if not cust_m:
        cust_m = re.search(r"\bcustomer\s+#?(\d{1,10})\b", lowered)
    if cust_m:
        entities["customer_id"] = cust_m.group(1).upper()

    rest_id_m = re.search(r"\b(rest[_-]?\d+)\b", lowered)
    if not rest_id_m:
        rest_id_m = re.search(r"\brestaurant\s+(?:id|#|code|num|number)\s*[:=]?\s*([A-Za-z0-9_-]+)\b", lowered)
    if not rest_id_m:
        rest_id_m = re.search(r"\brestaurant\s+#?(\d{1,10})\b", lowered)
    if rest_id_m:
        entities["restaurant_id"] = rest_id_m.group(1).upper()

    rider_m = re.search(r"\b(rider[_-]?\d+)\b", lowered)
    if not rider_m:
        rider_m = re.search(r"\brider\s+(?:id|#|code|num|number)\s*[:=]?\s*([A-Za-z0-9_-]+)\b", lowered)
    if not rider_m:
        rider_m = re.search(r"\brider\s+#?(\d{1,10})\b", lowered)
    if rider_m:
        entities["rider_id"] = rider_m.group(1).upper()

    # 6. Business Domain extraction
    if any(k in lowered for k in ("revenue", "gmv", "profit", "margin", "take rate", "financial", "earnings", "aov")):
        entities["business_domain"] = "financial"
    elif any(k in lowered for k in ("customer", "churn", "retention", "rfm", "clv", "ltv", "cohort")):
        entities["business_domain"] = "customer"
    elif any(k in lowered for k in ("delivery", "sla", "rider", "delay", "eta", "fulfillment", "operations", "courier")):
        entities["business_domain"] = "operations"
    elif any(k in lowered for k in ("restaurant", "merchant", "menu", "rating", "kitchen", "outlet")):
        entities["business_domain"] = "restaurant"
    elif any(k in lowered for k in ("what if", "scenario", "root cause", "why", "recommend", "next best action", "simulate")):
        entities["business_domain"] = "decision"

    return entities


# ----------------------------------------------------------------------
# Session Memory Accessors & Management
# ----------------------------------------------------------------------

def get_session_history(
    session_id: str,
    limit: int = 8,
    principal: Any = None,
) -> List[Dict[str, Any]]:
    """Retrieves the recent principal-isolated conversation history for a session."""
    if not session_id:
        return []
    key = make_scoped_session_key(session_id, principal)
    now_mono = time.monotonic()

    with _SESSION_LOCK:
        _evict_expired_locked(now_mono)
        entry = _SESSIONS.get(key)
        if not entry:
            return []
        entry["last_accessed"] = now_mono
        _SESSIONS.move_to_end(key)
        turns = entry.get("turns", [])
        return [dict(t) for t in turns[-max(1, int(limit)):]]


def get_session_state(session_id: str, principal: Any = None) -> Dict[str, Any]:
    """Retrieves a safe copy of active session state (turns, active filters, entities, facts)."""
    if not session_id:
        return {}
    key = make_scoped_session_key(session_id, principal)
    now_mono = time.monotonic()

    with _SESSION_LOCK:
        _evict_expired_locked(now_mono)
        entry = _SESSIONS.get(key)
        if not entry:
            return {
                "principal_key": resolve_principal_key(principal),
                "session_id": _sanitize_session_id(session_id),
                "turns": [],
                "active_filters": {},
                "remembered_entities": {},
                "recent_facts": {},
                "last_topic": None,
                "last_intent": None,
                "last_domain": None,
                "last_accessed": now_mono,
            }
        entry["last_accessed"] = now_mono
        _SESSIONS.move_to_end(key)
        return {
            "principal_key": entry.get("principal_key"),
            "session_id": entry.get("session_id"),
            "turns": [dict(t) for t in entry.get("turns", [])],
            "active_filters": dict(entry.get("active_filters", {})),
            "remembered_entities": dict(entry.get("remembered_entities", {})),
            "recent_facts": dict(entry.get("recent_facts", {})),
            "last_topic": entry.get("last_topic"),
            "last_intent": entry.get("last_intent"),
            "last_domain": entry.get("last_domain"),
            "last_accessed": entry.get("last_accessed", now_mono),
        }


def get_session_filters(session_id: str, principal: Any = None) -> Dict[str, Any]:
    """Retrieves current active filters for the principal-scoped session."""
    state = get_session_state(session_id, principal=principal)
    return dict(state.get("active_filters", {}))


def get_session_entities(session_id: str, principal: Any = None) -> Dict[str, Any]:
    """Retrieves remembered entities for the principal-scoped session."""
    state = get_session_state(session_id, principal=principal)
    return dict(state.get("remembered_entities", {}))


def update_session_state(
    session_id: str,
    *,
    principal: Any = None,
    active_filters: Optional[Dict[str, Any]] = None,
    remembered_entities: Optional[Dict[str, Any]] = None,
    recent_facts: Optional[Dict[str, Any]] = None,
    last_topic: Optional[str] = None,
    last_intent: Optional[str] = None,
    last_domain: Optional[str] = None,
) -> None:
    """Updates active filters, remembered entities, and recent facts for a session."""
    if not session_id:
        return
    key = make_scoped_session_key(session_id, principal)
    clean_sid = _sanitize_session_id(session_id)
    p_key = resolve_principal_key(principal)
    now_mono = time.monotonic()

    with _SESSION_LOCK:
        _evict_expired_locked(now_mono)
        entry = _SESSIONS.get(key)
        if entry is None:
            entry = {
                "principal_key": p_key,
                "session_id": clean_sid,
                "turns": [],
                "active_filters": {},
                "remembered_entities": {},
                "recent_facts": {},
                "last_topic": None,
                "last_intent": None,
                "last_domain": None,
                "last_accessed": now_mono,
            }
            _SESSIONS[key] = entry
        elif entry.get("principal_key") != p_key:
            raise PermissionError("Session principal ownership mismatch.")

        entry["last_accessed"] = now_mono

        if active_filters is not None:
            clean_f: Dict[str, Any] = {}
            for fk, fv in list(active_filters.items())[:_MAX_ENTITIES]:
                if isinstance(fv, (str, int, float, bool)):
                    clean_f[str(fk)[:32]] = str(fv)[:64] if isinstance(fv, str) else fv
            entry["active_filters"] = clean_f

        if remembered_entities is not None:
            clean_e: Dict[str, Any] = {}
            for ek, ev in list(remembered_entities.items())[:_MAX_ENTITIES]:
                if isinstance(ev, (str, int, float, bool)):
                    clean_e[str(ek)[:32]] = str(ev)[:64] if isinstance(ev, str) else ev
            entry["remembered_entities"] = clean_e

        if recent_facts is not None:
            clean_facts = entry.setdefault("recent_facts", {})
            for k, fv in list(recent_facts.items())[:_MAX_RECENT_FACTS]:
                if isinstance(fv, dict):
                    clean_facts[str(k)[:64]] = {
                        "value": fv.get("value"),
                        "label": str(fv.get("label", ""))[:80],
                        "source": str(fv.get("source", ""))[:80],
                        "unit": str(fv.get("unit", ""))[:20],
                        "timestamp": time.time(),
                    }
                elif isinstance(fv, (int, float, str, bool)):
                    clean_facts[str(k)[:64]] = {
                        "value": fv,
                        "label": str(k)[:80],
                        "timestamp": time.time(),
                    }

        if last_topic is not None:
            entry["last_topic"] = str(last_topic)[:64]
        if last_intent is not None:
            entry["last_intent"] = str(last_intent)[:64]
        if last_domain is not None:
            entry["last_domain"] = str(last_domain)[:64]

        _SESSIONS.move_to_end(key)
        _enforce_lru_cap_locked()


def record_turn(
    session_id: str,
    role: str,
    content: str,
    intent: Optional[str] = None,
    context_topic: Optional[str] = None,
    principal: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    entities: Optional[Dict[str, Any]] = None,
    facts: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Records a conversation turn in the caller's principal-isolated session memory.
    Applies PII/token redaction, rejects raw DataFrame/row payloads, and updates entity states.
    """
    if not session_id:
        return

    key = make_scoped_session_key(session_id, principal)
    clean_sid = _sanitize_session_id(session_id)
    p_key = resolve_principal_key(principal)
    now_mono = time.monotonic()

    redacted = redact_pii(content or "")
    clean_content = redacted[:_MAX_TURN_CHARS]

    safe_meta: Dict[str, Any] = {}
    if isinstance(metadata, dict):
        for mk, mv in metadata.items():
            if mk in {"data_rows", "table_data", "df", "dataframe"}:
                continue
            if isinstance(mv, (str, int, float, bool)):
                safe_meta[str(mk)] = mv[:128] if isinstance(mv, str) else mv
            elif isinstance(mv, dict):
                # Allow shallow safe dicts (e.g. filters or entities)
                sub_dict = {
                    str(sk)[:32]: str(sv)[:64] if isinstance(sv, str) else sv
                    for sk, sv in list(mv.items())[:10]
                    if isinstance(sv, (str, int, float, bool))
                }
                if sub_dict:
                    safe_meta[str(mk)] = sub_dict

    turn_record: Dict[str, Any] = {
        "role": role,
        "content": clean_content,
        "intent": intent,
        "context_topic": context_topic,
        "timestamp": time.time(),
    }
    if safe_meta:
        turn_record["meta"] = safe_meta

    with _SESSION_LOCK:
        _evict_expired_locked(now_mono)
        entry = _SESSIONS.get(key)
        if entry is None:
            entry = {
                "principal_key": p_key,
                "session_id": clean_sid,
                "turns": [],
                "active_filters": {},
                "remembered_entities": {},
                "recent_facts": {},
                "last_topic": context_topic,
                "last_intent": intent,
                "last_domain": None,
                "last_accessed": now_mono,
            }
            _SESSIONS[key] = entry
        else:
            if entry.get("principal_key") != p_key:
                raise PermissionError("Session principal ownership mismatch.")
            entry["last_accessed"] = now_mono

        entry["turns"].append(turn_record)
        if len(entry["turns"]) > _MAX_HISTORY_TURNS:
            entry["turns"] = entry["turns"][-_MAX_HISTORY_TURNS:]

        if filters is not None:
            clean_f = {
                str(k)[:32]: str(v)[:64] if isinstance(v, str) else v
                for k, v in list(filters.items())[:_MAX_ENTITIES]
                if isinstance(v, (str, int, float, bool))
            }
            entry["active_filters"] = clean_f

        if entities is not None:
            clean_e = {
                str(k)[:32]: str(v)[:64] if isinstance(v, str) else v
                for k, v in list(entities.items())[:_MAX_ENTITIES]
                if isinstance(v, (str, int, float, bool))
            }
            entry["remembered_entities"].update(clean_e)

        if facts is not None and isinstance(facts, dict):
            recent = entry.setdefault("recent_facts", {})
            for fk, fv in list(facts.items())[:_MAX_RECENT_FACTS]:
                if isinstance(fv, dict):
                    recent[str(fk)[:64]] = {
                        "value": fv.get("value"),
                        "label": str(fv.get("label", ""))[:80],
                        "source": str(fv.get("source", ""))[:80],
                        "unit": str(fv.get("unit", ""))[:20],
                        "timestamp": time.time(),
                    }

        if context_topic:
            entry["last_topic"] = context_topic
        if intent:
            entry["last_intent"] = intent

        _SESSIONS.move_to_end(key)
        _enforce_lru_cap_locked()


def reset_session(session_id: str, principal: Any = None) -> bool:
    """
    Clears history, active filters, and remembered entities strictly for the caller's principal-owned session.
    Never allows one principal to delete another principal's session.
    """
    if not session_id:
        return False
    key = make_scoped_session_key(session_id, principal)
    expected_p_key = resolve_principal_key(principal)

    with _SESSION_LOCK:
        entry = _SESSIONS.get(key)
        if not entry:
            return False
        if entry.get("principal_key") != expected_p_key:
            return False
        _SESSIONS.pop(key, None)
        return True


def session_exists(session_id: str, principal: Any = None) -> bool:
    """Helper used in isolation tests/diagnostics to verify principal-scoped session presence."""
    key = make_scoped_session_key(session_id, principal)
    with _SESSION_LOCK:
        _evict_expired_locked(time.monotonic())
        return key in _SESSIONS


def get_active_session_count() -> int:
    """Returns count of currently active (non-expired) scoped sessions."""
    with _SESSION_LOCK:
        _evict_expired_locked(time.monotonic())
        return len(_SESSIONS)


# ----------------------------------------------------------------------
# Follow-Up & Context-Aware Query Resolution
# ----------------------------------------------------------------------

def resolve_follow_up_query_and_context(
    query: str,
    session_id: str,
    principal: Any = None,
    explicit_filters: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[str], Optional[str], Dict[str, Any], Dict[str, Any]]:
    """
    Detects contextual follow-ups, extracts and persists conversational entities,
    and resolves active filters within the caller's principal-scoped session.

    Returns:
        augmented_query: str
        resolved_intent: Optional[str]
        context_topic: Optional[str]
        effective_filters: Dict[str, Any]
        remembered_entities: Dict[str, Any]
    """
    session_state = get_session_state(session_id, principal=principal)
    history = session_state.get("turns", [])
    active_filters = dict(session_state.get("active_filters", {}))
    remembered_entities = dict(session_state.get("remembered_entities", {}))
    last_topic = session_state.get("last_topic")
    if not last_topic and history:
        last_topic = history[-1].get("context_topic")

    q = query.strip()
    q_low = q.lower()

    # 1. Extract newly mentioned entities & reset directives
    extracted = extract_conversational_entities(q)
    resets = extracted.pop("_reset_entities", [])

    # 2. Process reset directives
    for r in resets:
        active_filters.pop(r, None)
        remembered_entities.pop(r, None)

    # 3. Update filters & entities with newly extracted values (safe replacement!)
    if "city" in extracted:
        active_filters["city"] = extracted["city"]
        remembered_entities["city"] = extracted["city"]
    if "customer_segment" in extracted:
        active_filters["customer_segment"] = extracted["customer_segment"]
        remembered_entities["customer_segment"] = extracted["customer_segment"]
    if "restaurant" in extracted:
        active_filters["restaurant"] = extracted["restaurant"]
        remembered_entities["restaurant"] = extracted["restaurant"]
    if "date_range" in extracted:
        active_filters["date_range"] = extracted["date_range"]
        remembered_entities["date_range"] = extracted["date_range"]
    if "customer_id" in extracted:
        active_filters["customer_id"] = extracted["customer_id"]
        remembered_entities["customer_id"] = extracted["customer_id"]
    if "restaurant_id" in extracted:
        active_filters["restaurant_id"] = extracted["restaurant_id"]
        remembered_entities["restaurant_id"] = extracted["restaurant_id"]
    if "rider_id" in extracted:
        active_filters["rider_id"] = extracted["rider_id"]
        remembered_entities["rider_id"] = extracted["rider_id"]
    if "business_domain" in extracted:
        remembered_entities["business_domain"] = extracted["business_domain"]

    # 4. Merge caller's explicit filters (caller-provided filters take precedence)
    if explicit_filters and isinstance(explicit_filters, dict):
        for ek, ev in explicit_filters.items():
            if ev is not None:
                active_filters[str(ek)] = ev
                if ek in {
                    "city", "restaurant", "restaurant_id", "customer_segment",
                    "customer_id", "rider_id", "date_range", "dashboard_name",
                    "kpi_or_chart_id", "selected_metric"
                }:
                    remembered_entities[str(ek)] = ev

    # 5. Determine follow-up cues
    follow_up_starters = [
        "which region", "which city", "which restaurant", "which merchant", "which partner", "which one",
        "who is the worst", "who is the best", "what about", "and in", "what in",
        "where is it", "why", "how come", "why did that happen",
        "how can we improve", "how can we fix", "how to improve", "how to fix", "suggest ways",
        "give an example", "can you show an example", "how does it work",
        "what does that mean", "explain more", "explain that",
        "how many orders", "what was the revenue", "what is gmv", "how is delivery", "how is sla",
        "what is the average", "what are the ratings"
    ]
    is_follow_up = bool(history) and (
        any(q_low.startswith(phrase) for phrase in follow_up_starters)
        or any(w in q_low.split() for w in ["it", "that", "this", "they", "them", "rate", "why?", "how?"])
        or (len(q.split()) <= 4 and ("?" in q or any(k in q_low for k in ("what", "how", "and", "in", "about"))))
    )

    resolved_intent: Optional[str] = None
    augmented_query = q

    # 6. Apply topic-based query expansion if follow-up
    if is_follow_up and last_topic:
        active_city = active_filters.get("city")
        city_suffix = f" in {active_city}" if active_city and active_city.lower() not in q_low else ""

        if last_topic == "cancellations":
            if any(w in q_low for w in ["restaurant", "merchant", "partner"]):
                augmented_query = f"Which restaurants have the highest cancellation rates{city_suffix}?"
                resolved_intent = "NL2SQL"
            elif any(w in q_low for w in ["city", "region", "where"]):
                augmented_query = "Which city or region has the highest cancellation rate?"
                resolved_intent = "ROOT_CAUSE"
            elif any(w in q_low for w in ["improve", "fix", "reduce", "solve", "actions"]):
                augmented_query = f"Suggest actionable ways to reduce order cancellations and improve fulfillment{city_suffix}."
                resolved_intent = "RECOMMENDATIONS"
            elif any(w in q_low for w in ["why", "cause", "reason"]):
                augmented_query = f"Why did order cancellations occur{city_suffix}?"
                resolved_intent = "ROOT_CAUSE"
            elif any(w in q_low for w in ["which", "worst", "highest"]):
                augmented_query = f"Which restaurants have the highest cancellation rates{city_suffix}?"
                resolved_intent = "NL2SQL"

        elif last_topic in ("financial", "financial_leakage"):
            if any(w in q_low for w in ["city", "region", "where"]):
                augmented_query = "Which city generates the highest revenue?"
                resolved_intent = "NL2SQL"
            elif any(w in q_low for w in ["why", "cause", "leakage", "margin"]):
                augmented_query = f"Why is revenue leakage or margin compression occurring{city_suffix}?"
                resolved_intent = "ROOT_CAUSE"
            elif any(w in q_low for w in ["improve", "grow", "increase", "profitability", "fix"]):
                augmented_query = f"Recommend actions to improve profitability and reduce unverified leakage risk{city_suffix}."
                resolved_intent = "RECOMMENDATIONS"
            elif any(w in q_low for w in ["orders", "order count", "volume", "how many"]):
                augmented_query = f"What is total order volume and completed order count{city_suffix}?"
                resolved_intent = "BUSINESS_DATA"

        elif last_topic == "customers":
            if any(w in q_low for w in ["why", "at risk", "churn"]):
                augmented_query = f"Why are customers churning and which customer segments are at risk{city_suffix}?"
                resolved_intent = "ROOT_CAUSE"
            elif any(w in q_low for w in ["improve", "retention", "save", "fix"]):
                augmented_query = f"Suggest ways to improve customer retention and save at-risk VIP accounts{city_suffix}."
                resolved_intent = "RECOMMENDATIONS"

        elif last_topic in ("operations", "delivery"):
            if any(w in q_low for w in ["why", "delay", "slow", "declin"]):
                augmented_query = f"Why is delivery performance declining{city_suffix}?"
                resolved_intent = "ROOT_CAUSE"
            elif any(w in q_low for w in ["improve", "fix", "reduce", "actions"]):
                augmented_query = f"Recommend actions to reduce delivery delays and SLA breaches{city_suffix}."
                resolved_intent = "RECOMMENDATIONS"

        elif last_topic == "restaurants":
            if any(w in q_low for w in ["which", "risk", "attention", "worst"]):
                augmented_query = f"Which restaurants need attention{city_suffix}?"
                resolved_intent = "NL2SQL"
            elif any(w in q_low for w in ["improve", "fix", "actions"]):
                augmented_query = f"Recommend actions to improve restaurant partner performance{city_suffix}."
                resolved_intent = "RECOMMENDATIONS"

        # General follow-up entity preservation (e.g., "What about in Hyderabad?" or "What about Delhi?")
        if q_low.startswith(("what about in ", "what about ", "and in ", "how about in ")):
            if "city" in extracted:
                c_name = extracted["city"]
                domain = remembered_entities.get("business_domain", "business")
                augmented_query = f"What is {domain} performance in {c_name}?"
                resolved_intent = "BUSINESS_DATA"

    # Persist the updated session state
    update_session_state(
        session_id,
        principal=principal,
        active_filters=active_filters,
        remembered_entities=remembered_entities,
        last_topic=last_topic,
        last_intent=resolved_intent,
        last_domain=remembered_entities.get("business_domain"),
    )

    return augmented_query, resolved_intent, last_topic, active_filters, remembered_entities


def resolve_follow_up_query(
    query: str,
    session_id: str,
    principal: Any = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Detects contextual follow-ups within the caller's own principal-scoped session history.
    Preserves exact 3-tuple return signature (augmented_query, resolved_intent, context_topic)
    for backward compatibility with existing tests and modules.
    """
    aug_q, res_intent, topic, _, _ = resolve_follow_up_query_and_context(
        query,
        session_id,
        principal=principal,
    )
    return aug_q, res_intent, topic
