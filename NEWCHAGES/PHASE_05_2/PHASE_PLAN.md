# PHASE 05.2 — VERIFICATION PLAN
**Full Application Integration Verification (Post-Phase 05.1)**

- **Date**: 2026-11-11
- **Baseline Git Commit**: `main` @ `21b2e2b` (0 commits/pushes executed)
- **Role**: Independent End-to-End QA & Full-Stack Architecture Verification
- **Outcome Verdict**: **`PARTIALLY_VERIFIED`** (Core Phase 05.1 API <-> React <-> Streamlit alignment & React production build verified live; MySQL live execution `BLOCKED`; Streamlit `01_Executive_Overview.py` runtime `FAILED`; security gaps & non-Phase-05.1 consumer discrepancies documented).

---

## Verification Scope & Execution Pillars
1. **React Production Build & Lint**:
   - Inspect [`frontend/package.json`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/package.json), [`frontend/package-lock.json`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/package-lock.json), `vite.config.ts`, `tsconfig.app.json`.
   - Execute `npm run build` (`tsc -b && vite build`) and `npm run lint` (`oxlint`), inspecting `frontend/dist/` output without modifying dependencies.
2. **Live FastAPI + React Integration (Real Headless Edge CDP)**:
   - Run FastAPI (`127.0.0.1:8000`) and Vite (`127.0.0.1:5173`) concurrently.
   - Automate all 8 Sidebar tabs, Customer 360 interaction, Decision Simulator preset triggers, Header territory filter, FloatingChatbot submission, and intentional network fault injection (`Fetch.enable`) via Edge Chromium DevTools Protocol (`msedge.exe`), capturing console errors, uncaught exceptions, failed HTTP requests, and rendered KPI values.
3. **Streamlit Runtime Validation**:
   - Execute all 10 scripts (`app.py` + `pages/01..09`) through `streamlit.testing.v1.AppTest` and live server (`127.0.0.1:8501`) headless Edge verification.
4. **MySQL Live Connectivity & Analytical View Check**:
   - Inspect Windows `MySQL80` service status and verify `.env`-configured connection using `mysql.connector` (`SHOW TABLES`, `SHOW FULL TABLES`, analytical KPI parity against Phase 04 Python KPI engine), logging any exact credential/schema blockers honestly.
5. **Cross-Layer Data Consistency Audit**:
   - Compare raw CSV computations, [`python/analytics/kpi_engine.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/analytics/kpi_engine.py), FastAPI live responses (`/api/overview`, `/api/customer/*`, `/api/restaurant/overview`, `/api/operations/overview`, `/api/financial/overview`, `/api/decision/*`, `/api/digital-twin/state`), React DOM values, and Streamlit rendered values across every module.
6. **Security & Git Protection Audit**:
   - Verify CORS headers on cross-origin requests, Pydantic input validation, SQL injection / schema-whitelist boundaries in [`python/ai/analyst/sql_agent.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/sql_agent.py), `.gitignore` / source secret scan, error payload safety, and authentication coverage.
   - Confirm zero modifications to protected datasets, `powerbi/NovaNest.pbix`, and Phase 01–05.1 historical governance entries.

