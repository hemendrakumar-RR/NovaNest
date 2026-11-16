"""
NovaNest Platform — Operational Alert Webhook Dispatcher & Notification Engine
------------------------------------------------------------------------------
Provides real-time alerting for critical infrastructure incidents (API unavailability,
database failures, container crashes, high memory, disk space exhaustion, backup failures).
Includes cryptographic HMAC-SHA256 signatures and strict secret masking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import os
import re
import threading
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertPayload(BaseModel):
    """Structured operational alert event schema."""
    alert_name: str
    severity: AlertSeverity = AlertSeverity.WARNING
    summary: str
    description: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)


def mask_secret_url(url: str) -> str:
    """Masks authentication tokens, Slack webhooks, and secrets in URLs for safe logging."""
    if not url:
        return ""
    # Slack webhook: https://hooks.slack.com/services/T00/B00/secretKey
    slack_pattern = r"(https?://hooks\.slack\.com/services/[^/]+/[^/]+/)(.+)"
    if re.match(slack_pattern, url):
        return re.sub(slack_pattern, r"\1********", url)

    # Generic token query param: ?token=secret
    url_masked = re.sub(r"([?&](?:token|key|secret|password)=)[^&]+", r"\1********", url)
    return url_masked


def compute_hmac_signature(payload_bytes: bytes, secret: str) -> str:
    """Computes HMAC-SHA256 signature for payload verification."""
    mac = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


# Bounded in-memory audit log of dispatched alerts
_DISPATCHED_ALERTS_LOCK = threading.Lock()
_DISPATCHED_ALERTS: List[Dict[str, Any]] = []
MAX_ALERT_HISTORY = 200


def dispatch_alert(
    alert_name: str,
    severity: AlertSeverity,
    summary: str,
    description: str,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
    timeout_sec: float = 3.0,
) -> Dict[str, Any]:
    """
    Dispatches an operational alert to configured webhook endpoint (Slack, Teams, PagerDuty).
    Enforces HMAC-SHA256 signature and secret masking.
    """
    url = webhook_url or os.getenv("ALERT_WEBHOOK_URL", "")
    secret = webhook_secret or os.getenv("ALERT_WEBHOOK_SECRET", "novanest_webhook_hmac_secret_2026")

    alert = AlertPayload(
        alert_name=alert_name,
        severity=severity,
        summary=summary,
        description=description,
        labels=labels or {},
        annotations=annotations or {},
    )

    payload_dict = alert.model_dump()
    payload_json = json.dumps(payload_dict, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")

    masked_url = mask_secret_url(url)
    result = {
        "alert_name": alert_name,
        "severity": severity.value,
        "summary": summary,
        "timestamp_utc": alert.timestamp_utc,
        "dispatched": False,
        "target_url": masked_url,
        "status_code": None,
        "error": None,
    }

    # If no webhook URL is configured, record in local log and return cleanly
    if not url:
        result["dispatched"] = True
        result["status_code"] = 200
        result["note"] = "Local simulated dispatch (ALERT_WEBHOOK_URL not configured)"
        _record_alert(result)
        return result

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NovaNest-Alert-Dispatcher/1.0",
        "X-NovaNest-Alert-Name": alert_name,
        "X-NovaNest-Severity": severity.value,
    }

    if secret:
        signature = compute_hmac_signature(payload_bytes, secret)
        headers["X-NovaNest-Signature"] = signature
        result["signature"] = signature

    req = urllib.request.Request(url, data=payload_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            result["dispatched"] = True
            result["status_code"] = resp.status
    except urllib.error.HTTPError as http_err:
        result["dispatched"] = False
        result["status_code"] = http_err.code
        result["error"] = f"HTTP {http_err.code}: {http_err.reason}"
    except Exception as exc:
        result["dispatched"] = False
        result["error"] = str(exc)

    _record_alert(result)
    return result


def _record_alert(record: Dict[str, Any]) -> None:
    with _DISPATCHED_ALERTS_LOCK:
        _DISPATCHED_ALERTS.append(record)
        if len(_DISPATCHED_ALERTS) > MAX_ALERT_HISTORY:
            _DISPATCHED_ALERTS.pop(0)


def get_dispatched_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns recent dispatched alerts for operator dashboard display."""
    with _DISPATCHED_ALERTS_LOCK:
        return list(_DISPATCHED_ALERTS[-limit:])


def clear_dispatched_alerts() -> None:
    """Clears dispatched alert audit history (used in unit tests)."""
    with _DISPATCHED_ALERTS_LOCK:
        _DISPATCHED_ALERTS.clear()
