# NOVANEST — PHASE 21: STREAMLIT COMMUNITY CLOUD DEPLOYMENT
## EXECUTION & COMPATIBILITY PLAN

### 1. OBJECTIVE & EXECUTIVE SUMMARY
The primary goal of Phase 21 is to prepare the existing NovaNest Streamlit application for deployment to **Streamlit Community Cloud** (`https://<app-name>.streamlit.app`).
This phase ensures that:
- The Streamlit application entry point (`streamlit_app/app.py`), bootstrap loader, and all 9 multi-page analytics dashboards compile and run seamlessly in a containerized cloud environment without local hardware dependencies.
- The UI retains 100% theme fidelity with NovaNest's official enterprise palette:
  - Background: `#F8FAFC`
  - Primary Navigation & Headers: `#2563EB`
  - Accent Buttons & Highlights: `#F97316`
  - Main Text: `#1E293B`
- Database connectivity supports hybrid cloud configurations:
  - Connects to secure cloud-hosted MySQL databases (e.g. Aiven MySQL, PlanetScale, AWS RDS, DigitalOcean Managed MySQL) via encrypted TLS credentials configured through Streamlit Secrets (`st.secrets`).
  - Seamlessly and reliably falls back to NovaNest's bundled canonical cleaned (10 tables, 304,405 records) and engineered (9 tables) CSV stores whenever no external cloud database is configured, ensuring zero application crashes, zero faked data, and zero silent data corruption.
- Multi-Agent AI Copilot integration routes cleanly:
  - Supports external HTTPS FastAPI endpoints configured via `st.secrets` (`NOVANEST_API_URL` and `NOVANEST_API_KEY`).
  - Implements in-process `TestClient` fallback and fail-closed security handling when external API services are offline or inaccessible.
- Strict security boundaries are preserved: Zero hardcoded secrets, zero tracked credentials in git, `.gitignore` hardened for secrets/dumps/binaries, and zero unauthorized git commits or pushes.

---

### 2. ARCHITECTURAL SCOPE & INVENTORY
| Component | Repository Path | Cloud Execution Strategy |
| :--- | :--- | :--- |
| **Streamlit Entrypoint** | `streamlit_app/app.py` | Primary execution target for `streamlit run streamlit_app/app.py`. |
| **Bootstrap & Config** | `streamlit_app/bootstrap.py`, `config/settings.py` | Sets page configs, wide layout, system paths, and caching directives. |
| **Theme Engine** | `.streamlit/config.toml`, `streamlit_app/styles/` | Custom CSS injected dynamically; enforces official NovaNest color scheme. |
| **Data Connector** | `streamlit_app/database/connection.py` | Dual resolution: `st.secrets` -> `os.getenv` -> Fail-safe CSV File Store. |
| **Data Loader** | `streamlit_app/utils/data_loader.py` | Cached loading (`@st.cache_data(ttl=3600)`) with strict single-source guarantee. |
| **FastAPI Client** | `streamlit_app/utils/api_client.py` | Supports remote FastAPI backend via `st.secrets` + in-process fallback. |
| **Analytics Dashboards** | `streamlit_app/pages/*.py` (9 pages) | Multi-page Streamlit architecture covering all 9 operational domains. |
| **Dependencies** | `requirements.txt` | Cloud-compliant Python requirements file without OS-specific packages. |
| **Secrets Management** | `.streamlit/secrets.toml.example` | Template for Community Cloud App Settings -> Secrets interface. |

---

### 3. DEPLOYMENT WORKFLOW STAGES
```
+-----------------------------------------------------------------------------------+
| Stage 1: Runtime Audit & Codebase Compatibility Verification                      |
| - Verify bytecode compilation of app.py and all 9 sub-pages                      |
| - Verify Python package requirements and runtime compatibility (Python 3.10-3.14) |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 2: Database Connectivity & Hybrid Failover Hardening                        |
| - Implement st.secrets reader in database/connection.py                           |
| - Verify dual support for root and [mysql] section secret formats                |
| - Validate deterministic CSV fallback parity (304,405 rows)                      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 3: AI Copilot & RBAC Integration Alignment                                  |
| - Support admin token scope for session reset in api_client.py                    |
| - Support cloud backend URL injection via st.secrets                              |
| - Verify 100% test pass on Milestone 5 Streamlit test suite                       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 4: Repository Hardening & Zero-Leak Security Audit                          |
| - Harden .gitignore (.streamlit/secrets.toml, *.sql, *.sig, backup/, bin/)        |
| - Audit repository for hardcoded secrets, plain text keys, and private IPs       |
| - Create clean .streamlit/secrets.toml.example                                    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Stage 5: Documentation & Community Cloud Deployment Guide                         |
| - Step-by-step instructions for GitHub repository linking and deployment         |
| - App Settings -> Secrets configuration guide                                     |
| - Verification checklist for post-deployment health check                         |
+-----------------------------------------------------------------------------------+
```

---

### 4. GOVERNANCE & METRICS
All actions are logged in `NEWCHAGES/PHASE21_STREAMLIT_CLOUD_DEPLOYMENT/` with verification against:
1. Streamlit Community Cloud readiness.
2. Canonical data parity.
3. Official palette enforcement.
4. Fail-closed security.
5. Zero git pushes without explicit approval.
