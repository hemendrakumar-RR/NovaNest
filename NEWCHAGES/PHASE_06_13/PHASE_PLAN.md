# PHASE 06.13: PRODUCTION SECURITY HARDENING & SECURITY ASSURANCE
## Phase Plan & Execution Blueprint

### 1. Executive Summary & Objectives
Phase 06.13 establishes enterprise-grade security posture across the entire NovaNest platform prior to production release. The primary objective is to harden every layer of the architecture—including Docker container images, API endpoints, AI agent orchestration, reverse-proxy network boundaries, and database access controls—while preserving existing application logic, active services, and all 304,405 records in `novanest_db`.

---

### 2. Architectural Scope & Hardening Workstreams

#### Workstream 1: Docker Image Vulnerability Remediation
- **Baseline Audit**: Scan active container images (`novanest-platform-api`, `novanest-platform-frontend`, `novanest-platform-streamlit`, `mysql:8.0.46`) using Docker Scout.
- **Frontend Hardening**: Migrate from outdated base images to `nginx:alpine-slim` with latest OS security patches (`apk upgrade --no-cache`).
- **Dependency Hardening**: Upgrade vulnerable Python dependencies (Pillow >= 11.1.0, Tornado >= 6.4.2, Setuptools >= 78.1.1, Wheel >= 0.46.1).
- **Non-Root Runtime**: Enforce non-root application users (`novanest:10001` and `nginx:101`).

#### Workstream 2: API Security & Fail-Closed RBAC
- **Token Authorization**: Implement constant-time comparison (`hmac.compare_digest`) across Admin, Operator, and Viewer roles.
- **URL Parameter Protection**: Strictly reject static API tokens passed via query parameters (`?token=...`), mandating `Authorization: Bearer` or `X-API-Key` headers.
- **Ephemeral Stream Tickets**: Deploy single-use stream tickets (`StreamTicketManager`) bound to authenticated principals and session IDs with a 60-second TTL.
- **Brute-Force & Rate Limiting**: Deploy thread-safe sliding-window `RateLimiter` (300 req/min general, 60 req/min AI) with 10-failure IP lockout (60-second lockout).
- **OWASP HTTP Headers**: Inject `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and strict `Content-Security-Policy`. Suppress server banners.
- **CORS Hardening**: Strict trusted origin allowlist; disallow wildcard `*` with credentials.

#### Workstream 3: AI Multi-Agent Prompt Injection & Privacy Protection
- **Injection Defense**: Regex & AST-based detection for instruction overrides, secret exfiltration, script injection, and jailbreak persona hijacking (`DAN mode`).
- **Markdown Image Exfiltration**: Neutralize untrusted markdown image tags pointing to external URLs.
- **SQL Grounding Protection**: Block prompts attempting to bypass AST validation or query ungrounded schemas.
- **Session Isolation**: HMAC peppered principal key isolation (`make_scoped_session_key`) ensuring distinct principals sharing a `session_id` maintain completely isolated conversation states.
- **PII Redaction**: Automatic masking of emails, Indian phone numbers (+91), PAN IDs, and API tokens.

#### Workstream 4: Database Least Privilege & Data Preservation
- **Permission Boundary**: Verify `novanest_app` is restricted to read-only `SELECT` on dimensional tables and scoped `INSERT, UPDATE` on operational tables with zero `DROP`, `TRUNCATE`, `DELETE`, or `ALTER` permissions.
- **Integrity Guarantee**: Preserve all 304,405 records across all 10 canonical MySQL tables.

#### Workstream 5: Nginx Reverse-Proxy Hardening
- **Rate-Limiting Zones**: Configure `limit_req_zone` for general API calls (50 r/s) and AI streaming (10 r/s).
- **SSE Unbuffered Proxying**: Ensure `proxy_buffering off` and `X-Accel-Buffering no` for low-latency telemetry streaming.
- **Information Disclosure**: Set `server_tokens off;` and restrict allowed HTTP methods.

#### Workstream 6: Encrypted Disaster Recovery & RTO/RPO Certification
- **Automated Backup**: Transaction-safe `mysqldump` with `--single-transaction --quick`.
- **Military-Grade Encryption**: AES-256-CBC encryption using OpenSSL with PBKDF2 (100,000 iterations) and cryptographic salt.
- **Integrity Roundtrip**: Bit-for-bit SHA-256 checksum verification between pre-encryption and decrypted SQL dumps.
- **Disaster Recovery Metrics**: Validate RTO (< 30 seconds) and RPO (< 24 hours).

#### Workstream 7: Automated Security Regression Testing & CI Integration
- Author `tests/test_phase06_13_security_hardening.py` covering 25 test cases across 10 security vectors.
- Integrate into `tests/run_ci_pipeline.py`.
