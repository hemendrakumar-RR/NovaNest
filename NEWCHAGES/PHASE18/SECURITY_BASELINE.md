# NovaNest — Phase 18 Security Baseline & Pre-Audit Inventory

**Phase**: 18  
**Audit Date**: 2026-11-15T19:45:00+05:30  
**Target Environment**: Authorized Local Development Platform (`localhost`)  
**Auditor**: Independent Defensive Security Assessment Team  
**Database Record Count**: 304,405 Records (Verified Across 10 Tables)  

---

## 1. Container & Infrastructure Topology

| Container Name | Service | Base Image / Version | Host Port | Container Port | Non-Root User | Privileged |
|---|---|---|---|---|---|---|
| `novanest-frontend` | Nginx SPA & Edge Proxy | `nginx:1.25-alpine` | `0.0.0.0:80` | `80/tcp` | `nginx` | `false` |
| `novanest-api` | FastAPI & Multi-Agent | `python:3.11-slim` | `0.0.0.0:8001` | `8000/tcp` | `root` (audit item) | `false` |
| `novanest-db` | MySQL Relational Store | `mysql:8.0.46` | None (internal) | `3306/tcp` | `mysql` | `false` |
| `novanest-streamlit` | Streamlit Dashboard | `python:3.11-slim` | `0.0.0.0:8502` | `8501/tcp` | `root` (audit item) | `false` |
| `novanest-prometheus` | Metrics Collector | `prom/prometheus:v2.51.0` | `127.0.0.1:9090` | `9090/tcp` | `nobody` | `false` |
| `novanest-grafana` | Telemetry Dashboard | `grafana/grafana:10.4.0` | `127.0.0.1:3001` | `3000/tcp` | `grafana` | `false` |

### Network Segmentation
- All containers operate within isolated Docker bridge network `novanest_net` (`novanest_network`).
- `novanest-db` exposes port 3306 exclusively within `novanest_net` (not bound to host `0.0.0.0`).
- Prometheus (9090) and Grafana (3001) are strictly bound to host loopback `127.0.0.1`.

---

## 2. Authentication & Credential Architecture

### Token Mechanisms
- **Header Auth**: Supports `X-API-Key: <token>` and `Authorization: Bearer <token>`.
- **Query Param Tokens**: Explicitly forbidden (`?token=...` triggers HTTP 401 and security audit event).
- **SSE Streaming Tickets**: Short-lived, single-use stream tickets (`StreamTicketManager`, 60-second TTL) bound to `AuthPrincipal` and `session_id`.
- **Token Comparison**: Constant-time comparison using `hmac.compare_digest` to prevent timing attacks.
- **Principal Derivation**: `_derive_principal_id` uses an HMAC pepper (`NOVANEST_SESSION_SALT`) to derive non-reversible hashes (`role:hash12`) for audit logging without storing raw tokens.

### Brute-Force & Rate Limiting
- **General Rate Limit**: 1,200 req/min sliding-window per client IP.
- **AI Rate Limit**: 240 req/min sliding-window per client IP.
- **Lockout Policy**: 10 consecutive failed authentication attempts trigger a 60-second lockout returning HTTP 429 with `Retry-After`.

---

## 3. Role-Based Access Control (RBAC) Architecture

| Role | Associated Scopes | Allowed Capabilities |
|---|---|---|
| `admin` | `read`, `operator`, `admin` | All analytical endpoints, PII endpoints, session-reset, model parameter changes, disaster recovery verification. |
| `operator` | `read`, `operator` | All analytical endpoints, Customer 360 single lookup, AI Copilot, Decision Simulator. |
| `viewer` | `read` | Read-only aggregated analytics, KPI cards, charts. Cannot access PII or run simulations. |
| `unauthenticated` | None | Denied access to protected endpoints (HTTP 401). |

---

## 4. MySQL Database Permissions & User Accounts

| MySQL User | Host | Plugin | Current Privileges |
|---|---|---|---|
| `novanest_app` | `%` | `caching_sha2_password` | `SELECT` on `novanest_db.*`, `INSERT, UPDATE` on transaction tables (`orders_table`, `deliveries`, `payments`, `ratings_reviews`, `app_events`). |
| `novanest_loader` | `%` | `caching_sha2_password` | `SELECT, INSERT, UPDATE` on `novanest_db.*`. |
| `novanest_backup` | `%` | `caching_sha2_password` | `SELECT` on `novanest_db.*`, `RELOAD, PROCESS, LOCK TABLES, REPLICATION CLIENT` on `*.*`. Least-privilege compliant. |
| `root` | `%` / `localhost` | `caching_sha2_password` | Full administrative privileges (internal network only). |

---

## 5. AI Safety & Defensive Controls

1. **SQL AST Parser & Validator (`sql_ast.py`)**:
   - Pure recursive-descent AST parser enforcing strict read-only query semantics.
   - Forbids all DDL/DML keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `EXEC`, etc.).
   - Blocks all system schemas (`sqlite_master`, `mysql`, `information_schema`, `performance_schema`, `sys`).
   - Automatically injects bounded row limits (`LIMIT 25`, max 100).
2. **OutputVerifier Grounding Engine (`output_verifier.py`)**:
   - Rejects ungrounded or fabricated numeric claims.
   - Enforces certified KPI formulas.
   - Preserves unconfirmed financial screening flags.
3. **PII Redaction Engine (`conversation_manager.py`)**:
   - Regex scrubbers redact emails, phone numbers, Indian mobile numbers, PAN numbers, and Bearer tokens before session context persistence.

---

## 6. Nginx Edge Security Headers

- `X-Frame-Options`: `SAMEORIGIN`
- `X-Content-Type-Options`: `nosniff`
- `X-XSS-Protection`: `1; mode=block`
- `Referrer-Policy`: `strict-origin-when-cross-origin`
- `Permissions-Policy`: `camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy`: `default-src 'self'; script-src 'self' 'unsafe-inline'; ...`
- `server_tokens`: `off`
- Rate-limiting zones: `api_general_limit` (50r/s) and `ai_stream_limit` (10r/s).

---

## 7. Monitoring & Observability Security

- **Prometheus Scrape Endpoint (`/api/metrics`)**: Protected by `verify_monitoring_auth`. Requires `Authorization: Bearer <token>`, `x-monitoring-token`, or trusted Docker network loopback.
- **Grafana Security**: Anonymous authentication disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`), user self-registration disabled (`GF_USERS_ALLOW_SIGN_UP=false`), admin password enforced via environment variable.

---

## 8. Backup & Disaster Recovery Baseline

- **Algorithm**: Military-grade AES-256-CBC with PBKDF2 (100,000 iterations) and cryptographic salt.
- **Checksums**: SHA-256 cryptographic digests computed for raw and encrypted dumps.
- **Zero Plaintext Leak**: Encrypted dumps verified to contain zero plaintext SQL keywords or table definitions.
- **Isolated Replay**: Restore tests performed in memory or isolated scratch files without touching live `novanest_db`.
- **RTO / RPO**: Measured RTO < 2 seconds (target < 30s), RPO policy daily with binary logs (target < 24h).

---

## 9. Canonical Data Baseline

- `customers`: 5,000
- `restaurants`: 1,500
- `menu_items`: 15,000
- `riders`: 4,000
- `orders_table`: 49,971
- `deliveries`: 49,971
- `payments`: 49,971
- `ratings_reviews`: 28,792
- `promotions`: 200
- `app_events`: 100,000
- **Total Records**: **304,405**
