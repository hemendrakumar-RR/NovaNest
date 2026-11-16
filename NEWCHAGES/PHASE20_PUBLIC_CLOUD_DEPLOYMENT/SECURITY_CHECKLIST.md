# NovaNest — Production Security Hardening Checklist
## Pre-Flight Cloud Deployment Verification & Compliance Audit

**Document Version**: 1.0.0  
**Phase**: PHASE 20 (Public Cloud Deployment)  
**Standard**: OWASP Top 10 & CIS Benchmark Compliant  
**Status**: AUDITED & VERIFIED  

---

## 1. Network & Infrastructure Boundary Security

| Check Item | Status | Verification Detail |
|---|:---:|---|
| **Host Firewall (UFW)** | **VERIFIED** | Default policy set to `deny incoming`. Only ports `22` (SSH), `80` (HTTP), and `443` (HTTPS) are exposed. |
| **MySQL Isolation** | **VERIFIED** | Port 3306 is NOT mapped to the host interface. MySQL is reachable exclusively via private bridge `novanest_internal_network`. |
| **Prometheus Isolation** | **VERIFIED** | Port 9090 is completely unexposed to the host and internet; accessible only internally by Grafana. |
| **Grafana Ingress** | **VERIFIED** | Port 3000 is internal only; proxied through Nginx at `/grafana/` with anonymous access disabled (`GF_AUTH_ANONYMOUS_ENABLED: "false"`). |
| **SSH Hardening** | **VERIFIED** | Password authentication disabled (`PasswordAuthentication no`). Pubkey authentication only. Fail2ban enabled. |

---

## 2. Secrets & Identity Management

| Check Item | Status | Verification Detail |
|---|:---:|---|
| **Development Credential Purge** | **VERIFIED** | All default passwords (`dev_root_secret_change_me`, `Chinnu_2311`, `test-operator-key`) replaced with high-entropy hex secrets generated via `openssl rand -hex 32`. |
| **Source Control Protection** | **VERIFIED** | `.env`, `.env.production`, and `.sql.enc` are listed in `.gitignore`. Zero credentials present in Git history. |
| **Template Validation** | **VERIFIED** | Deployment script (`deploy_production.sh`) actively checks for `REPLACE_WITH_` strings and aborts if detected. |
| **Database Least Privilege** | **VERIFIED** | Application user `novanest_prod_app` granted `SELECT` on master tables and `INSERT/UPDATE` on transactional tables. Zero DDL privileges (`CREATE`, `DROP`, `ALTER`). |

---

## 3. Web & Edge Proxy Hardening (Nginx & TLS)

| Check Item | Status | Verification Detail |
|---|:---:|---|
| **HTTPS Redirection** | **VERIFIED** | Port 80 unconditionally issues `301 Moved Permanently` to `https://$host$request_uri` (except ACME challenges). |
| **TLS Protocols** | **VERIFIED** | Enforces `TLSv1.2` and `TLSv1.3` strictly. Obsolete ciphers disabled. |
| **HSTS Enforcement** | **VERIFIED** | `Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;` |
| **DDoS Rate Limiting** | **VERIFIED** | General API limited to 50 req/sec (burst 30); AI streaming limited to 10 req/sec; auth limited to 5 req/sec with HTTP 429 status. |
| **Security Headers** | **VERIFIED** | `X-Frame-Options SAMEORIGIN`, `X-Content-Type-Options nosniff`, `X-XSS-Protection "1; mode=block"`, `Referrer-Policy strict-origin-when-cross-origin`. |
| **Content Security Policy** | **VERIFIED** | Strict CSP restricting script, style, frame, and connect origins. |

---

## 4. Application Logic & Data Protection

| Check Item | Status | Verification Detail |
|---|:---:|---|
| **SQL Injection Defense** | **VERIFIED** | Recursive SQL AST validation (`sql_ast.py`) enforced on all natural-language and dynamic queries; parameterized queries throughout. |
| **PII Data Access Control** | **VERIFIED** | Customer entity queries (`/api/records/customers`) restricted to `operator` role scope with HTTP 403 on `viewer`. |
| **Fail-Closed Pagination** | **VERIFIED** | Whitelist validation on `sort_by` query parameters; non-whitelisted columns immediately rejected with HTTP 400. |
| **Log Sanitization** | **VERIFIED** | Database credentials, JWT tokens, and customer contact numbers are scrubbed from Uvicorn and Nginx access logs. |
| **Container User Privileges** | **VERIFIED** | Containers run with `security_opt: ["no-new-privileges:true"]` and non-root service accounts where applicable. |
