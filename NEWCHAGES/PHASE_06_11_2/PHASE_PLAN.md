# PHASE 06.11.2 — EXECUTION BLUEPRINT
## Docker Build and Runtime Validation

### 1. Objective & Scope
Phase 06.11.2 executes the end-to-end container build and runtime validation for the NovaNest application following the successful enablement of Docker Desktop 4.99.0 (Docker Engine 29.9.3, Compose 5.7.0, WSL2 Linux kernel). The goal is to verify that all NovaNest components build cleanly into hardened, non-root multi-stage container images, orchestrate seamlessly via Docker Compose, connect to an isolated container database restored from the verified backup (`scratch/novanest_backup_live.sql`), and deliver full analytical, multi-agent AI, and dashboard capabilities without interfering with existing active host services.

Core Workstreams:
1. **Preflight Verification**:
   - Verify Docker CLI and Compose availability in execution PATH.
   - Audit host service ports (:8000 FastAPI, :8501 Streamlit, :3306 MySQL) to prevent port binding collisions.
   - Confirm live host database `novanest_db` (304,405 records) remains untouched and isolated.
2. **Container Image Builds**:
   - Build FastAPI Backend (`docker/Dockerfile.api` -> `novanest-api:test`).
   - Build Streamlit Dashboard (`docker/Dockerfile.streamlit` -> `novanest-streamlit:test`).
   - Build React SPA with Nginx Edge Proxy (`docker/Dockerfile.frontend` -> `novanest-frontend:test`).
   - Document build timings, layer sizes, and resolve any build anomalies.
3. **Database Protection & Isolated Restore**:
   - Start containerized MySQL 8.0 on isolated named volume `novanest_mysql_data`.
   - Restore disaster recovery backup `scratch/novanest_backup_live.sql` into container database.
   - Validate 10 tables, 304,405 records, primary keys, and foreign key integrity inside the container.
4. **Incremental Runtime Validation**:
   - Start and probe `novanest-db` health.
   - Start and probe `novanest-api` health (`/api/health`, `/api/diagnostics/data-source`, `/api/overview`).
   - Start and probe `novanest-frontend` reverse proxy (`/nginx-health`, `/`, `/api/health` proxying).
   - Start and probe `novanest-streamlit` dashboard on host port :8502 (`/_stcore/health`).
   - Validate multi-agent SSE streaming (`/api/ai/stream`).
5. **Security & Vulnerability Audit**:
   - Verify non-root container users (`novanest:10001`, `nginx:101`).
   - Ensure zero hardcoded secrets in image layers and git-tracked files.
   - Confirm MySQL port 3306 remains unexposed to public host network.
   - Perform vulnerability scans (Docker Scout / Trivy where available).
6. **Governance Traceability**:
   - Produce complete records in `NEWCHAGES/PHASE_06_11_2/` and hierarchical mirror `NEWCHAGES/PHASE_06/PHASE_06_11_2/`.
   - Record ADR-029 in `DECISIONS_AND_REASONS.md` and update `CHANGELOG.md`, `ROADMAP_STATUS.md`, `TESTING_HISTORY.md`.

### 2. Safety & Governance Restrictions
- **Host Database Absolute Protection**: No DROP, TRUNCATE, ALTER, or data modification on host `novanest_db`.
- **Host Services Non-Interference**: Do not stop or terminate active host processes (FastAPI PID 26652, Streamlit PID 11388, MySQL PID 7664).
- **Port Conflict Mitigation**: Container Streamlit published on host port :8502 (internal :8501); container API published on host port :8001 (internal :8000) and through Nginx on host port :80. Host ports :8000, :8501, :3306 remain untouched.
- **Strict Evidence Reporting**: Never report unexecuted tests as passed. Explicitly distinguish static configuration checks from live container execution logs.
