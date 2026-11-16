# PHASE 05.3 — EXECUTION PLAN
**Security Hardening, API Contract Fixes & Dashboard Reliability**

- **Date**: 2026-11-11
- **Baseline Preceding Phase**: Phase 05.2 (`PARTIALLY_VERIFIED`) — Git `main` @ `21b2e2b` (uncommitted working tree preserved; zero commits/pushes executed)
- **Objective**: Remediate every security vulnerability, runtime crash, API/UI contract mismatch, Digital Twin / Simulator divergence, MySQL configuration drift, and unhandled frontend fetch failure identified during Phase 05.2 prior to Phase 06 agentic expansion.

---

## Planned Remediation Workstreams

1. **Application Security Hardening (`api/auth.py`, `api/main.py`, `python/ai/analyst/`, `python/ai/conversational/`, `.env.example`)**
   - Remove wildcard CORS (`allow_origins=["*"]`) when `allow_credentials=True`; enforce explicit trusted frontend origins via `CORS_ALLOWED_ORIGINS`.
   - Replace comma-join SQL whitelist bypasses with a recursive-descent SQL AST lexer/parser (`python/ai/analyst/sql_ast.py`) validating all tables, CTEs, subqueries, JOINs, and functions against a read-only whitelist while explicitly blocking `sqlite_master`, `sqlite_schema`, system tables, multi-statements, write/DDL ops, and dangerous functions.
   - Lock in-memory SQLite execution with C-level authorizer (`set_authorizer`), `PRAGMA query_only = ON`, `PRAGMA trusted_schema = OFF`, and `atexit` connection cleanup.
   - Enforce fail-closed bearer/`X-API-Key` authentication & RBAC scopes (`read`, `operator`, `admin`) across all `/api/*` endpoints while keeping `/api/health` open without leaking credentials.

2. **Backend API Contract & Domain Engine Fixes (`api/main.py`, `python/digital_twin/`, `python/decision_simulation/`, `python/intelligence/customer/`)**
   - Reconcile `/api/overview` (`kpis.avg_rating`), `/api/customer/360/{id}` (`customer_name`, nullable email, `Recency_Days`), `/api/restaurant/overview` (`Risk_Category` -> `critical_risk_count: 3`), `/api/decision/simulate` (full empirical baseline `Orders`/`Profit_Margin`), and `/api/digital-twin/state` (empirical pillar telemetry, structured ripple chains, explicit `unavailable` state on missing data).
   - Remove hardcoded placeholder constants in Digital Twin & Decision Simulation modules (`python/digital_twin/*.py`, `python/decision_simulation/*.py`) and return explicit `unavailable` / `scenario_assumptions` metadata when inputs are absent.

3. **Streamlit Runtime & Schema Fixes (`streamlit_app/`)**
   - Eliminate `KeyError: ['rating']` crash on `01_Executive_Overview.py` (`avg_rating`, `order_datetime`, non-cancelled GMV / delivered Net Revenue).
   - Fix `app.py`, `02_Customer_Intelligence.py` (`CLV_Segment`, `customer_360` keys), `08_Decision_Simulator.py` (`Profit_Margin`, `Orders`, `Orders_Diff`), and `09_NovaNest_Command_Center.py` (`unavailable` status & `Signal`/`Business_Impact` alert formatting).

4. **React Resilience & UI Contract Sync (`frontend/src/`)**
   - Implement global `ErrorBoundary.tsx` and standardized `ApiStatePanel.tsx` (`ApiErrorState` with interactive `HTTP 401/403` `sessionStorage` token prompt + `EmptyStateCard`).
   - Add API token injection (`Authorization: Bearer` + `X-API-Key`) in `frontend/src/services/api.ts`, nullable formatters in `formatters.ts`, full 5-city list in `HeaderNav.tsx` (`All`, `Bangalore`, `Chennai`, `Coimbatore`, `Hyderabad`, `Vijayawada`), and error/empty handling across all 9 views + `FloatingChatbot.tsx`.
   - Fix modal/KPI mismatches in `CustomerIntelligenceView.tsx`, `RestaurantIntelligenceView.tsx`, `DecisionSimulatorView.tsx`, and `CommandCenterView.tsx`.

5. **MySQL Canonical Schema Alignment & Read-Only Check**
   - Align `api/loader.py`, `streamlit_app/database/connection.py`, `streamlit_app/utils/data_loader.py`, `python/system_config.py`, `mysql/08_phase3_intelligence.sql`, and `mysql/09_phase4_operations.sql` on canonical `novanest_db` and `orders_table` (with fallback reads where needed).
   - Verify `.env` connectivity non-destructively without altering local DB credentials or schemas.

6. **Verification, Protected Asset Integrity & Governance Closure**
   - Execute full offline regression tests (`tests/test_phase05_3_security_and_contracts.py` + prior suites), live HTTP RBAC/CORS/SQL security checks, live unittest HTTP suites, headless Edge CDP browser checks across React & Streamlit, and React production `lint` + `build`.
   - Confirm zero modifications to protected `datasets/` and `powerbi/NovaNest.pbix` (`5,638,573` bytes), zero lingering server listeners, and complete Phase 05.3 documentation under `NEWCHAGES/`.

