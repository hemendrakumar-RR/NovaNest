# NOVANEST PHASE 10.1 — FILE CHANGES REGISTER
## SRE Evidence Validation & Operational Defect Rectification

**Governance Reference:** `NOVANEST-PHASE-10-1-FILES`  
**Phase:** 10.1  
**Date:** 2026-11-15  
**Author:** Principal SRE & Reliability Certification Auditor  

---

### 1. Summary of Changes

Phase 10.1 rectified operational defects identified during empirical evidence validation. Changes include:
- Resolving Python dependency conflicts and container filesystem permission bottlenecks.
- Fixing Grafana provisioning directory shadowing.
- Upgrading distributed tracing context propagation to `contextvars`.
- Integrating child database query tracing spans.
- Enforcing strict token authentication for Prometheus metrics endpoints.
- Implementing Encrypt-then-MAC (HMAC-SHA256 sidecars) for database backups.
- Updating Docker Compose configurations and Nginx proxy configs.

---

### 2. Modified Files

| File Path | Description of Changes |
| :--- | :--- |
| `docker/requirements-api.txt` | Relaxed Starlette constraint from `>=0.49.1` to `>=0.40.0,<0.47.0` to resolve incompatibility with FastAPI 0.115. |
| `docker/Dockerfile.api` | Added directory creation and ownership assignment for `/app/backup/automated` and `/app/scratch` to non-root user `novanest:10001`. |
| `docker-compose.monitoring.yml` | Remapped Grafana dashboard mount to `/var/lib/grafana/dashboards:ro` to prevent shadowing `/etc/grafana/provisioning/dashboards`. |
| `docker/grafana/provisioning/dashboards/dashboards.yml` | Updated dashboard provider path from `/etc/grafana/provisioning/dashboards` to `/var/lib/grafana/dashboards`. |
| `python/operations/tracing.py` | Migrated trace context from thread-local storage to `contextvars.ContextVar` to preserve parent span context across async coroutines and threadpool workers. |
| `python/operations/health_circuit_breaker.py` | Added child query tracing spans (`mysql.ping`, `mysql.query`) to provide granular database timing in distributed traces. |
| `python/operations/prometheus_metrics.py` | Enforced strict token validation in `verify_monitoring_auth` if an Authorization header is provided, preventing unauthenticated access on localhost. |
| `python/operations/backup_automation.py` | Safeguarded backup directory creation with exception handling; implemented `compute_backup_hmac()` and `verify_backup_hmac()` for Encrypt-then-MAC authenticated encryption. |

---

### 3. New Files Created

| File Path | Description of File |
| :--- | :--- |
| `NEWCHAGES/PHASE_10_1/PHASE_PLAN.md` | Strategic plan, scope, and objectives for Phase 10.1 reliability certification. |
| `NEWCHAGES/PHASE_10_1/IMPLEMENTATION_LOG.md` | Detailed step-by-step audit, remediation, and empirical verification log. |
| `NEWCHAGES/PHASE_10_1/FILE_CHANGES.md` | Comprehensive file changes and configuration tracking register. |
| `NEWCHAGES/PHASE_10_1/TEST_RESULTS.md` | Test execution evidence, empirical benchmark measurements, and validation logs. |
| `NEWCHAGES/PHASE_10_1/PHASE_SUMMARY.md` | Executive validation summary and final go-live reliability certification report. |
| `tests/test_phase10_1_certification.py` | Dedicated Phase 10.1 SRE certification test suite. |

---

### 4. Untouched Critical Assets

- `novanest_db` MySQL database: 0 schema changes, 0 records modified (304,405 rows preserved).
- Historical phase logs: `NEWCHAGES/PHASE_01` through `NEWCHAGES/PHASE_10` completely intact.
- ML models and artifacts: All Phase 07 models in `artifacts/models/` unchanged.
- Analytics calculations: All financial & KPI algorithms preserved.
