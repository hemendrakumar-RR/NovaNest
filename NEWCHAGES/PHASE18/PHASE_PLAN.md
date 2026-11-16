# NovaNest — Phase 18 Phase Plan: Independent Security Audit & Penetration Testing

**Phase**: 18  
**Title**: Independent Security Audit & Penetration Testing  
**Lead Agent**: Principal Security Architect & Defensive Penetration Tester  
**Status**: IN_PROGRESS  
**Governance Directory**: `NEWCHAGES/PHASE18/`  
**Timestamp**: 2026-11-15T19:45:00+05:30  

---

## 1. Objectives & Scope

Execute a thorough, defensive, and authorized security assessment of the owner's NovaNest platform across all architectural layers in the local development environment:

1. **Authentication Architecture**: Audit login, token generation, constant-time token comparison, session isolation, expiration, token revocation, rate limiting, and brute-force lockout. Ensure sensitive authentication info never appears in logs.
2. **Authorization & RBAC**: Test role-based permissions (`admin`, `operator`, `analyst`, `viewer`), user-level data isolation, horizontal and vertical privilege escalation, administrative endpoint boundaries, and agent-level tool permissions.
3. **API Security Assessment**: Test OWASP Top 10 API vulnerabilities: SQL injection, cross-site scripting (XSS), cross-site request forgery (CSRF), server-side request forgery (SSRF), path traversal, mass assignment, IDOR, excessive data exposure, rate-limit bypass, CORS misconfiguration, and error handling.
4. **AI & Agent Security Audit**: Evaluate all 5 domain agents, Master Orchestrator, and AI Business Copilot against OWASP LLM Top 10 (direct/indirect prompt injection, instruction overrides, system prompt extraction, untrusted SQL generation, ungrounded business claims, PII redaction, tool permission gating).
5. **MySQL Database Security**: Inspect user privileges (`novanest_app`, `novanest_loader`, `novanest_backup`, `root`), network exposure, connection encryption/TLS settings, injection protections, and audit logging.
6. **Docker & Container Infrastructure**: Scan all 6 active container images (`novanest-api`, `novanest-frontend`, `novanest-db`, `novanest-streamlit`, `novanest-prometheus`, `novanest-grafana`), check non-root user execution, container capabilities, sensitive volume mounts, Docker socket exposure, and CVEs.
7. **Secrets & Dependency Audit**: Inspect environment variables, `.env` files, Git tracking history, Python and npm packages for known vulnerabilities (`safety`/`pip audit`, `npm audit`), and verify secret masking.
8. **Network & Monitoring Security**: Audit Nginx reverse proxy headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy), rate limiting zones, `/api/metrics` authentication, Grafana authentication and user signup settings.
9. **Backup & Disaster Recovery Security**: Verify AES-256-CBC encryption, PBKDF2 100k iteration key derivation, cryptographic checksums (SHA-256), isolated restore verification, and RTO/RPO enforcement.
10. **Vulnerability Remediation & Retesting**: Log every finding using CVSS 3.1 scoring, apply defensive remediations, retest to confirm remediation, and run full Phase 15–17 regression suites.

---

## 2. Strict Governance & Architectural Constraints

- **Strict Boundary**: Defensive testing conducted exclusively on the owner's authorized local environment (`localhost:80`, `localhost:8001`, `localhost:8502`, `127.0.0.1:3001`, `127.0.0.1:9090`). Zero calls to third-party or external infrastructure.
- **Zero Data Loss / Mutation**: Exactly 304,405 records across all 10 canonical MySQL tables in `novanest_db` must remain 100% unaltered.
- **Fail-Closed Security**: Never disable or weaken authentication, rate limiting, or validation logic to make tests pass.
- **Secret Redaction**: Never print or leak real passwords, tokens, API keys, or private keys in logs, test output, or reports.
- **Git Policy**: ZERO `git commit` or `git push` commands.
- **Exact Governance Spelling**: Strictly use `NEWCHAGES/PHASE18/`.

---

## 3. Work Breakdown Structure (Milestones)

### Milestone 1: Pre-Audit Inventory & Security Baseline
- [x] Inspect container health, running services, and database row counts (304,405 rows confirmed).
- [x] Document pre-audit security architecture across all 10 components.
- [ ] Author `NEWCHAGES/PHASE18/SECURITY_BASELINE.md` and `PHASE_PLAN.md`.

### Milestone 2: Authentication & RBAC Penetration Testing
- [ ] Test authentication failures, invalid bearer tokens, query param token rejections.
- [ ] Test brute-force rate limiting and client IP lockout mechanics.
- [ ] Test vertical privilege escalation (Viewer attempting Operator endpoints, Operator attempting Admin actions).
- [ ] Test horizontal privilege escalation (cross-principal session interference).

### Milestone 3: API Vulnerability & Injection Assessment
- [ ] Test SQL injection payloads on `/api/records/*`, `/api/overview`, and custom filter endpoints.
- [ ] Test path traversal payloads (`../`, encoded dots) on file/record endpoints.
- [ ] Test Cross-Site Scripting (XSS) reflection and stored payloads.
- [ ] Test CORS headers with unauthorized origins and verify reject behavior.
- [ ] Test excessive payload size and request-rate limits.

### Milestone 4: AI Copilot & Agent Security Audit
- [ ] Test direct prompt injection ("Ignore previous instructions", "Reveal your system prompt").
- [ ] Test indirect prompt injection via simulated malicious data or poisoned context.
- [ ] Test untrusted SQL generation and AST validation rejection (`DROP TABLE`, `sqlite_master`, system queries).
- [ ] Verify OutputVerifier numeric grounding, claim validation, and epistemic tag enforcement.
- [ ] Verify PII redaction (emails, phone numbers, PAN IDs, bearer tokens) in copilot inputs and outputs.

### Milestone 5: MySQL Database Security & Privilege Review
- [ ] Review MySQL user grants for `novanest_app`, `novanest_loader`, `novanest_backup`, and `root`.
- [ ] Verify database port is NOT exposed on public/host network interfaces.
- [ ] Verify transaction isolation and verify 304,405 records remain intact.

### Milestone 6: Docker Container & Infrastructure Security
- [ ] Inspect container configurations for non-root execution, capabilities, and privileged flags.
- [ ] Verify no Docker socket (`/var/run/docker.sock`) exposure in untrusted containers.
- [ ] Audit container network isolation on `novanest_net`.

### Milestone 7: Secrets, Dependencies & Monitoring Security
- [ ] Audit repository and environment files for unmasked hardcoded secrets.
- [ ] Scan Python and npm dependencies for known CVEs.
- [ ] Verify `/api/metrics` token enforcement and Grafana anonymous access prohibition.

### Milestone 8: Backup & Disaster Recovery Security
- [ ] Verify AES-256-CBC backup encryption with PBKDF2 (100k iterations) and SHA-256 checksums.
- [ ] Execute non-destructive isolated restore verification.
- [ ] Verify zero plaintext leaks in encrypted archives.

### Milestone 9: Vulnerability Logging & Remediation
- [ ] Author `NEWCHAGES/PHASE18/SECURITY_FINDINGS.md` and `REMEDIATION_LOG.md`.
- [ ] Implement targeted security hardenings (Nginx headers, CORS validation, error sanitization, etc.).
- [ ] Retest all remediated vulnerabilities to confirm fix effectiveness.

### Milestone 10: Automated Security Test Suite & Regression
- [ ] Author dedicated test suite `tests/test_phase18_security_audit.py`.
- [ ] Run test suite and achieve 100% pass rate.
- [ ] Run Phase 15, 16, and 17 regression suites.
- [ ] Confirm 304,405 records intact.

### Milestone 11: Governance & Final Security Report
- [ ] Complete all NEWCHAGES governance files.
- [ ] Update master registers (`CHANGELOG.md`, `DECISIONS_AND_REASONS.md` with ADR-044, `ROADMAP_STATUS.md`, etc.).
- [ ] Author final comprehensive artifact: `phase18_independent_security_audit_report.md`.
