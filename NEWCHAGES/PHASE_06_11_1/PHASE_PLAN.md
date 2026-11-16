# PHASE 06.11.1 — EXECUTION BLUEPRINT
## Docker Runtime Enablement & Validation Audit

### 1. Objective & Scope
Phase 06.11.1 provides the runtime enablement audit and pre-flight validation for the Docker containerization foundation established in Phase 06.11. Because Docker Engine was unavailable on the local Windows host, this phase inspects the host environment, audits all Docker configurations for defects, enforces database safety for `novanest_db`, provides turnkey installation instructions for Docker Desktop and WSL2, and requests user approval before altering system-level components.

Core Workstreams:
1. **Environment Readiness**:
   - Inspect Windows OS version, kernel build, and virtualization features.
   - Audit WSL2 status and Docker CLI/Engine presence.
   - Verify non-interference with existing active services (FastAPI on `:8000`, Streamlit on `:8501`, MySQL on `:3306`).
2. **Deep Configuration Audit**:
   - Inspect `docker/Dockerfile.api`, `docker/Dockerfile.streamlit`, `docker/Dockerfile.frontend`, `docker/nginx.conf`, `docker-compose.yml`, `docker-compose.prod.yml`, `docker/mysql/init/*.sql`, `.dockerignore`, `.env.docker.example`.
   - Identify missing paths (e.g. `datasets/engineered/` in Streamlit), configuration conflicts, and credential exposure.
3. **Database Safety & Restore Validation**:
   - Safeguard live `novanest_db` (304,405 records) from accidental overwrite or directory mounting.
   - Verify isolated Docker named volume (`novanest_mysql_data`).
   - Validate live backup file `scratch/novanest_backup_live.sql` (15.10 MB, 10 tables, 304,405 records).
4. **Step-by-Step Installation Runbook & Approval Request**:
   - Provide concrete commands for installing WSL2 and Docker Desktop on Windows 11 Home.
   - Request explicit user approval prior to installing or changing system-level components.
5. **Governance Traceability**:
   - Record all findings, test results, and ADR-028 in `NEWCHAGES`.

### 2. Safety & Governance Restrictions
- **Zero Destructive Operations**: Zero modifications or drops on `novanest_db`.
- **Zero Service Interruption**: Active processes (FastAPI PID 26652, Streamlit PID 11388, MySQL PID 7664) must not be terminated.
- **Zero Unapproved System Changes**: No automatic execution of `wsl.exe --install` or system driver modifications without explicit user approval.
- **Honest Status Reporting**: Never claim container runtime execution or image builds as passed when Docker Engine is absent on the host.
