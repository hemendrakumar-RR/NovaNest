# PHASE 06.11 — PHASE EXECUTION PLAN
## Docker Containerization & Deployment Foundation

### 1. Objectives & Scope
The objective of Phase 06.11 is to prepare the complete NovaNest analytical and multi-agent AI platform for reproducible, secure, and production-grade containerized deployment across multi-tier environments without altering existing application business logic or corrupting data.

Core deliverables:
1. **Multi-Stage Dockerfiles**:
   - `docker/Dockerfile.api`: Hardened Python 3.11 FastAPI backend running Uvicorn under non-root system user `novanest` (UID 10001).
   - `docker/Dockerfile.streamlit`: Multipage executive dashboard under non-root system user `novanest`.
   - `docker/Dockerfile.frontend`: Multi-stage build compiling React TypeScript SPA with Node 20 and serving via production Nginx 1.27 Alpine.
2. **Dependency Separation & Pinning**:
   - `docker/requirements-api.txt`: Pinned FastAPI backend dependencies.
   - `docker/requirements-streamlit.txt`: Pinned Streamlit dashboard dependencies.
   - Root `requirements.txt`: Preserved shared backward compatibility.
3. **Nginx Reverse Proxy & Real-Time SSE**:
   - `docker/nginx.conf`: Upstream routing to `api:8000`, client caching, security headers (`X-Frame-Options`, `X-Content-Type-Options`), SPA client-side routing fallback, and unbuffered streaming for Server-Sent Events (`/api/ai/ask/stream`, `/api/ai/stream`).
4. **Multi-Service Docker Compose**:
   - `docker-compose.yml`: Development/testing orchestration defining `db` (MySQL 8.0.46 with persistent volumes and healthchecks; port 3306 not exposed publicly), `api`, `frontend`, and `streamlit` with healthcheck conditions and CPU/memory limits.
   - `docker-compose.prod.yml`: Production override utilizing Docker Secrets, log rotation (`json-file`), and strict restart policies.
5. **Secret Sanitization & Build Isolation**:
   - `.dockerignore`: Comprehensive exclusion preventing `.env`, Git history, Python caches, and heavy analytics scratch files from entering build contexts.
   - `.env.docker.example`: Sanitized container environment configuration template.
6. **Continuous Integration Pipeline**:
   - `.github/workflows/ci.yml`: GitHub Actions pipeline covering backend tests, AST security audit, frontend build, Docker buildx image builds, and Trivy container vulnerability scanning.
7. **Disaster Recovery & Backup Validation**:
   - `scratch/test_backup_and_recovery.py`: Verified non-destructive `mysqldump` generation (15.10 MB) capturing all 10 tables and 304,405 records without touching `novanest_db`.

### 2. Safety & Governance Boundaries
- **Zero Destructive Operations**: Zero `DROP`, `TRUNCATE`, `ALTER`, or `DELETE` executed on `novanest_db`.
- **Zero Secret Exposure**: Passwords, tokens, and credentials strictly excluded from Dockerfiles, git registers, and logs.
- **Zero Premature Deployment**: Container configuration certified syntactically and structurally; host environment limitations (Docker CLI / daemon absent on local Windows) documented transparently.
- **Preservation of Working Local State**: Local Uvicorn (`:8000`), Streamlit (`:8501`), and MySQL (`:3306`) remain fully operational throughout.
