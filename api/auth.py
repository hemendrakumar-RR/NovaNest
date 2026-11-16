"""
NovaNest FastAPI Security, CORS Allowlist & Token Authorization Module
----------------------------------------------------------------------
Implements environment-driven CORS origin allowlisting and fail-closed
constant-time API token authentication with role-based scopes.
Zero hardcoded credentials are stored anywhere in source code.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import logging
import os
import re
import secrets
import threading
import time
from typing import Dict, FrozenSet, List, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)

DEFAULT_CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

PROD_CORS_ORIGINS: List[str] = [
    "https://novanest.app",
    "https://app.novanest.app",
    "https://admin.novanest.app",
]


def get_allowed_cors_origins() -> List[str]:
    """
    Resolves explicit trusted CORS origins from CORS_ALLOWED_ORIGINS env var.
    Never permits wildcard '*' when credentials are enabled.
    In production without custom origins, defaults strictly to production HTTPS domains.
    """
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    is_prod = (os.getenv("APP_ENV", "").lower() == "production" or os.getenv("ENVIRONMENT", "").lower() == "production")
    if not raw:
        return list(PROD_CORS_ORIGINS) if is_prod else list(DEFAULT_CORS_ORIGINS)

    origins: List[str] = []
    for entry in raw.split(","):
        origin = entry.strip().rstrip("/")
        if not origin:
            continue
        if origin == "*":
            logger.warning("Ignoring unsafe wildcard '*' in CORS_ALLOWED_ORIGINS while credentials are enabled.")
            continue
        if origin not in origins:
            origins.append(origin)

    return origins if origins else list(DEFAULT_CORS_ORIGINS)


# Ephemeral server-side HMAC pepper for non-reversible principal hashing (overridable cleanly via NOVANEST_SESSION_SALT)
_PROCESS_SESSION_PEPPER = os.getenv("NOVANEST_SESSION_SALT", "").encode("utf-8") or secrets.token_bytes(32)


def _derive_principal_id(role: str, token: str) -> str:
    """Derives an opaque, non-reversible principal identifier without retaining raw tokens."""
    digest = hmac.new(_PROCESS_SESSION_PEPPER, token.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
    return f"{role}:{digest}"


@dataclass(frozen=True)
class AuthPrincipal:
    role: str
    scopes: FrozenSet[str]
    principal_id: str = "anonymous"


security_logger = logging.getLogger("novanest.security")


def log_security_event(event_type: str, client_ip: str, detail: str, severity: str = "INFO") -> None:
    """Standardized security event logger with automatic sensitive data redaction."""
    safe_detail = re.sub(r'(?i)(password|token|key|secret)=([^\s,]+)', r'\1=[REDACTED]', detail)
    msg = f"[SECURITY_AUDIT] event={event_type} client={client_ip} detail={safe_detail}"
    if severity == "ERROR":
        security_logger.error(msg)
    elif severity == "WARNING":
        security_logger.warning(msg)
    else:
        security_logger.info(msg)


class RateLimiter:
    """
    Thread-safe, sliding-window rate limiter for brute-force protection and DDoS mitigation.
    Tracks requests per client IP with automatic expiration and temporary lockout.
    """
    def __init__(
        self,
        general_limit_per_minute: Optional[int] = None,
        ai_limit_per_minute: Optional[int] = None,
        auth_failure_threshold: int = 10,
        lockout_duration_seconds: float = 60.0,
    ):
        self._general_limit = general_limit_per_minute or int(os.getenv("RATE_LIMIT_GENERAL_PER_MINUTE", 1200))
        self._ai_limit = ai_limit_per_minute or int(os.getenv("RATE_LIMIT_AI_PER_MINUTE", 240))
        self._auth_threshold = auth_failure_threshold
        self._lockout_duration = lockout_duration_seconds
        self._requests: Dict[str, List[float]] = {}
        self._auth_failures: Dict[str, List[float]] = {}
        self._lockouts: Dict[str, float] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, client_id: str, endpoint_type: str = "general") -> Tuple[bool, int]:
        now = time.time()
        window = 60.0
        limit = self._ai_limit if endpoint_type == "ai" else self._general_limit

        with self._lock:
            # Check if client is locked out
            if client_id in self._lockouts:
                expiry = self._lockouts[client_id]
                if now < expiry:
                    return False, max(1, int(expiry - now))
                else:
                    del self._lockouts[client_id]

            # Slide window
            history = self._requests.setdefault(client_id, [])
            cutoff = now - window
            self._requests[client_id] = [t for t in history if t > cutoff]
            history = self._requests[client_id]

            if len(history) >= limit:
                oldest = history[0] if history else now
                retry_after = max(1, int(window - (now - oldest)))
                return False, retry_after

            history.append(now)
            return True, 0

    def record_auth_failure(self, client_id: str) -> Tuple[bool, int]:
        now = time.time()
        window = 60.0
        with self._lock:
            history = self._auth_failures.setdefault(client_id, [])
            cutoff = now - window
            self._auth_failures[client_id] = [t for t in history if t > cutoff]
            history = self._auth_failures[client_id]
            history.append(now)

            if len(history) >= self._auth_threshold:
                expiry = now + self._lockout_duration
                self._lockouts[client_id] = expiry
                return True, int(self._lockout_duration)
            return False, 0

    def record_auth_success(self, client_id: str) -> None:
        with self._lock:
            self._auth_failures.pop(client_id, None)

    def is_locked_out(self, client_id: str) -> Tuple[bool, int]:
        now = time.time()
        with self._lock:
            if client_id in self._lockouts:
                expiry = self._lockouts[client_id]
                if now < expiry:
                    return True, max(1, int(expiry - now))
                else:
                    del self._lockouts[client_id]
            return False, 0

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()
            self._auth_failures.clear()
            self._lockouts.clear()


rate_limiter = RateLimiter()


def has_configured_auth_keys() -> bool:
    """Returns True when at least one API key environment variable is configured."""
    return bool(
        os.getenv("NOVANEST_ADMIN_KEY", "").strip()
        or os.getenv("NOVANEST_API_KEY", "").strip()
        or os.getenv("NOVANEST_VIEWER_KEY", "").strip()
    )


def _extract_token(request: Request) -> Optional[str]:
    """Extracts API credential from X-API-Key or Authorization: Bearer headers."""
    x_api_key = (request.headers.get("X-API-Key") or "").strip()
    if x_api_key:
        return x_api_key

    auth_header = (request.headers.get("Authorization") or "").strip()
    if auth_header:
        parts = auth_header.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
            return parts[1].strip()

    return None


def _authenticate_token(token: str) -> Optional[AuthPrincipal]:
    """Validates candidate token against env keys using constant-time comparison."""
    admin_key = os.getenv("NOVANEST_ADMIN_KEY", "").strip()
    operator_key = os.getenv("NOVANEST_API_KEY", "").strip()
    viewer_key = os.getenv("NOVANEST_VIEWER_KEY", "").strip()

    if admin_key and hmac.compare_digest(token, admin_key):
        return AuthPrincipal(
            role="admin",
            scopes=frozenset({"read", "operator", "admin"}),
            principal_id=_derive_principal_id("admin", token),
        )

    if operator_key and hmac.compare_digest(token, operator_key):
        scopes = {"read", "operator"} if admin_key else {"read", "operator", "admin"}
        return AuthPrincipal(
            role="operator",
            scopes=frozenset(scopes),
            principal_id=_derive_principal_id("operator", token),
        )

    if viewer_key and hmac.compare_digest(token, viewer_key):
        return AuthPrincipal(
            role="viewer",
            scopes=frozenset({"read"}),
            principal_id=_derive_principal_id("viewer", token),
        )

    return None


@dataclass
class StreamTicket:
    """Short-lived, single-use ticket for authenticated SSE stream connections."""
    ticket_id: str
    principal: AuthPrincipal
    session_id: str
    created_at: float
    expires_at: float
    consumed: bool = False


class StreamTicketManager:
    """
    Thread-safe, ephemeral in-memory registry for short-lived, single-use stream tickets.
    Eliminates exposure of static/permanent API tokens in URL query strings (SSE / GET).
    Tickets are bound to a verified AuthPrincipal and session_id with a strict 60s TTL.
    """
    def __init__(self, default_ttl_seconds: float = 60.0):
        self._default_ttl = default_ttl_seconds
        self._tickets: Dict[str, StreamTicket] = {}
        self._lock = threading.Lock()

    def create_ticket(
        self,
        principal: AuthPrincipal,
        session_id: str = "default",
        ttl_seconds: Optional[float] = None,
    ) -> StreamTicket:
        now = time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        ticket_id = f"st_{secrets.token_urlsafe(32)}"
        clean_session = (session_id or "default").strip()
        ticket = StreamTicket(
            ticket_id=ticket_id,
            principal=principal,
            session_id=clean_session,
            created_at=now,
            expires_at=now + ttl,
            consumed=False,
        )
        with self._lock:
            self._purge_expired_locked(now)
            self._tickets[ticket_id] = ticket
        return ticket

    def consume_ticket(
        self,
        ticket_id: str,
        expected_session_id: Optional[str] = None,
        expected_principal_id: Optional[str] = None,
    ) -> Optional[AuthPrincipal]:
        """
        Validates and atomically consumes a ticket (single-use).
        Returns the bound AuthPrincipal if valid, or None if invalid, expired, already consumed,
        or if session_id/principal_id mismatch.
        """
        now = time.time()
        with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                return None

            if ticket.consumed:
                self._tickets.pop(ticket_id, None)
                return None

            if now > ticket.expires_at:
                self._tickets.pop(ticket_id, None)
                return None

            if expected_session_id is not None:
                clean_expected = (expected_session_id or "default").strip()
                if ticket.session_id != clean_expected:
                    return None

            if expected_principal_id is not None:
                if ticket.principal.principal_id != expected_principal_id:
                    return None

            ticket.consumed = True
            self._tickets.pop(ticket_id, None)
            return ticket.principal

    def _purge_expired_locked(self, now: float) -> None:
        expired = [k for k, v in self._tickets.items() if now > v.expires_at or v.consumed]
        for k in expired:
            self._tickets.pop(k, None)

    def clear(self) -> None:
        """Testing utility to reset ticket state."""
        with self._lock:
            self._tickets.clear()


stream_ticket_manager = StreamTicketManager()


def authenticate_stream_principal(
    request: Request,
    ticket: Optional[str] = None,
    session_id: Optional[str] = None,
    required_scope: str = "operator",
) -> AuthPrincipal:
    """
    Authenticates a streaming SSE connection.
    Strictly forbids static API tokens in URL query strings.
    Accepts:
      1. Single-use stream ticket (?ticket=st_...) bound to session and principal.
      2. Standard Authorization: Bearer / X-API-Key request headers.
    """
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "127.0.0.1")
    )

    locked_out, lockout_remaining = rate_limiter.is_locked_out(client_ip)
    if locked_out:
        log_security_event("AUTH_LOCKOUT", client_ip, "blocked stream attempt during lockout", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed authentication attempts. Account temporarily locked out. Retry after {lockout_remaining} seconds.",
            headers={"Retry-After": str(lockout_remaining)},
        )

    allowed, retry_after = rate_limiter.check_rate_limit(client_ip, endpoint_type="ai")
    if not allowed:
        log_security_event("RATE_LIMIT_EXCEEDED", client_ip, f"endpoint={request.url.path} limit_type=ai", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for streaming endpoints. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # 1. Reject static token in query param immediately
    if request.query_params.get("token"):
        rate_limiter.record_auth_failure(client_ip)
        log_security_event("AUTH_FAILURE", client_ip, "static token in SSE query params", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Static API tokens in URL query parameters are disabled for security. Exchange your token for a single-use stream ticket via POST /api/ai/stream-ticket.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check ticket if provided
    query_ticket = ticket or request.query_params.get("ticket")
    if query_ticket:
        clean_ticket = query_ticket.strip()
        principal = stream_ticket_manager.consume_ticket(clean_ticket, expected_session_id=session_id)
        if principal is None:
            rate_limiter.record_auth_failure(client_ip)
            log_security_event("AUTH_FAILURE", client_ip, "invalid or expired stream ticket", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or already consumed stream ticket.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if required_scope not in principal.scopes:
            log_security_event("AUTH_FORBIDDEN", client_ip, f"stream ticket principal lacks {required_scope}", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{required_scope}' scope required (current role: '{principal.role}').",
            )
        rate_limiter.record_auth_success(client_ip)
        log_security_event("AUTH_SUCCESS", client_ip, f"stream ticket authenticated principal={principal.principal_id}")
        return principal

    # 3. Check standard headers (X-API-Key or Authorization: Bearer)
    token = _extract_token(request)
    if not token:
        rate_limiter.record_auth_failure(client_ip)
        log_security_event("AUTH_FAILURE", client_ip, "missing credentials on stream endpoint", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: supply valid stream ticket via ?ticket=<id> or Bearer token header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not has_configured_auth_keys():
        log_security_event("AUTH_FAILURE", client_ip, "server auth keys not configured", severity="ERROR")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server API authentication keys are not configured in environment.",
        )

    principal = _authenticate_token(token)
    if principal is None:
        rate_limiter.record_auth_failure(client_ip)
        log_security_event("AUTH_FAILURE", client_ip, "invalid token on stream endpoint", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if required_scope not in principal.scopes:
        log_security_event("AUTH_FORBIDDEN", client_ip, f"principal lacks {required_scope} on stream", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: '{required_scope}' scope required (current role: '{principal.role}').",
        )

    rate_limiter.record_auth_success(client_ip)
    log_security_event("AUTH_SUCCESS", client_ip, f"principal={principal.principal_id} on stream")
    return principal


def require_scope(required_scope: str):
    """
    FastAPI dependency enforcing fail-closed authentication and role scope check.
    Scopes:
      - 'read': aggregated dashboard analytics endpoints
      - 'operator': PII endpoints (Customer 360 / list), AI Ask, Decision Simulator
      - 'admin': state-mutating / session-reset operations
    """

    def _dependency(request: Request) -> AuthPrincipal:
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "127.0.0.1")
        )

        # 1. Check if client IP is currently locked out
        locked_out, lockout_remaining = rate_limiter.is_locked_out(client_ip)
        if locked_out:
            log_security_event("AUTH_LOCKOUT", client_ip, f"blocked attempt during lockout (remaining: {lockout_remaining}s)", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed authentication attempts. Account temporarily locked out. Retry after {lockout_remaining} seconds.",
                headers={"Retry-After": str(lockout_remaining)},
            )

        # 2. Check general / AI rate limit
        endpoint_type = "ai" if "/ai/" in request.url.path else "general"
        allowed, retry_after = rate_limiter.check_rate_limit(client_ip, endpoint_type=endpoint_type)
        if not allowed:
            log_security_event("RATE_LIMIT_EXCEEDED", client_ip, f"endpoint={request.url.path} limit_type={endpoint_type}", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {endpoint_type} endpoints. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        if request.query_params.get("token"):
            rate_limiter.record_auth_failure(client_ip)
            log_security_event("AUTH_FAILURE", client_ip, "static token passed in query parameter", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Static API tokens in URL query parameters are disabled for security. Supply Bearer token or X-API-Key header.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = _extract_token(request)
        if not token:
            rate_limiter.record_auth_failure(client_ip)
            log_security_event("AUTH_FAILURE", client_ip, f"missing credentials for {request.url.path}", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: supply Bearer token or X-API-Key header.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not has_configured_auth_keys():
            log_security_event("AUTH_FAILURE", client_ip, "server auth keys not configured", severity="ERROR")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Server API authentication keys are not configured in environment.",
            )

        principal = _authenticate_token(token)
        if principal is None:
            is_now_locked, lock_dur = rate_limiter.record_auth_failure(client_ip)
            if is_now_locked:
                log_security_event("AUTH_LOCKOUT", client_ip, f"threshold reached after invalid token on {request.url.path}", severity="WARNING")
            else:
                log_security_event("AUTH_FAILURE", client_ip, f"invalid token on {request.url.path}", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if required_scope not in principal.scopes:
            log_security_event("AUTH_FORBIDDEN", client_ip, f"principal={principal.principal_id} role={principal.role} lacks scope {required_scope}", severity="WARNING")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{required_scope}' scope required (current role: '{principal.role}').",
            )

        rate_limiter.record_auth_success(client_ip)
        log_security_event("AUTH_SUCCESS", client_ip, f"principal={principal.principal_id} role={principal.role} path={request.url.path}")
        return principal

    return Depends(_dependency)

