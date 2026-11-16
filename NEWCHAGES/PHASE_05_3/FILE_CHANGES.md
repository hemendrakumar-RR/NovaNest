# PHASE 05.3 — FILE CHANGES REGISTER

## 1. Newly Created Files (`5` Source / Test Files + `6` Governance Docs)
| File Path | Category | Purpose |
| :--- | :--- | :--- |
| [`api/auth.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/auth.py) | Security / Auth | Explicit CORS allowlist parser + fail-closed RBAC scope authentication (`read`/`operator`/`admin`) |
| [`python/ai/analyst/sql_ast.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/sql_ast.py) | SQL Security | Recursive-descent SQL AST parser/validator blocking system tables, multi-statements, write ops, and unsafe functions |
| [`frontend/src/components/ErrorBoundary.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/ErrorBoundary.tsx) | React Reliability | Global view error boundary with recover/reload actions |
| [`frontend/src/components/ApiStatePanel.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/ApiStatePanel.tsx) | React UI / Auth | Standardized `ApiErrorState` (HTTP `401`/`403` `sessionStorage` token input + retry) & `EmptyStateCard` |
| [`tests/test_phase05_3_security_and_contracts.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_phase05_3_security_and_contracts.py) | Verification | 8 comprehensive tests covering CORS, AST/SQLite lock, RBAC, API contracts, Streamlit AppTest & MySQL config |
| `NEWCHAGES/PHASE_05_3/{PHASE_PLAN,IMPLEMENTATION_LOG,FILE_CHANGES,TEST_RESULTS,PHASE_SUMMARY}.md` | Governance | Phase 05.3 lifecycle plans, execution logs, file manifest, empirical tests & closure summary |
| [`NEWCHAGES/PROJECT_AUDIT/PHASE_05_3_SECURITY_RELIABILITY_REPORT.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PROJECT_AUDIT/PHASE_05_3_SECURITY_RELIABILITY_REPORT.md) | Audit Report | Consolidated Phase 05.3 security hardening, contract parity & dashboard verification report |

---

## 2. Modified Existing Files (`55` Source / Config / SQL / UI / Test Files + Rebuilt `frontend/dist/`)

### Backend & Security Configuration
- [`.env.example`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/.env.example) — Documented `NOVANEST_API_KEY`, `NOVANEST_ADMIN_KEY`, `NOVANEST_VIEWER_KEY`, and `CORS_ALLOWED_ORIGINS`.
- [`api/main.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/main.py) — Enforced CORS allowlist + fail-closed RBAC scopes, added `atexit` SQLite cleanup, `avg_rating` in `/api/overview`, fixed `/api/customer/360/{id}`, `/api/restaurant/overview`, `/api/decision/simulate`, and `/api/digital-twin/state`.
- [`api/loader.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/loader.py) — Loaded `.env`, defaulted DB to `novanest_db`, updated MySQL query to `orders_table` with `orders` fallback.

### AI & SQL Sandboxing
- [`python/ai/analyst/sql_agent.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/sql_agent.py) — Wired `validate_sql_ast` and added `configure_readonly_sqlite` C-level authorizer + `PRAGMA query_only = ON`.
- [`python/ai/analyst/orchestrator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/orchestrator.py), [`universal_router.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/universal_router.py), [`simulation_agent.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/simulation_agent.py) — Enforced read-only SQLite lock and aligned empirical routing/simulation payloads.
- [`python/ai/conversational/nl_to_sql.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/conversational/nl_to_sql.py), [`sql_validator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/conversational/sql_validator.py), [`query_executor.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/conversational/query_executor.py) — Delegated SQL validation to AST validator and executed safely under read-only constraints.

### Digital Twin, Decision Simulation & Customer 360
- [`python/digital_twin/customer_twin.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/customer_twin.py), [`restaurant_twin.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/restaurant_twin.py), [`operations_twin.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/operations_twin.py), [`financial_twin.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/financial_twin.py), [`twin_alerts.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/twin_alerts.py), [`twin_dependencies.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/twin_dependencies.py), [`twin_engine.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/digital_twin/twin_engine.py) — Replaced hardcoded placeholders with empirical metrics, structured ripple objects, and explicit `"unavailable"` data status.
- [`python/decision_simulation/customer_simulator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/decision_simulation/customer_simulator.py), [`restaurant_simulator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/decision_simulation/restaurant_simulator.py), [`operations_simulator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/decision_simulation/operations_simulator.py), [`financial_simulator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/decision_simulation/financial_simulator.py), [`scenario_engine.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/decision_simulation/scenario_engine.py) — Empirical baselines, explicit `scenario_assumptions`, and consistent `Orders`/`Profit_Margin`/`Orders_Diff` schema.
- [`python/intelligence/customer/customer_360.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/intelligence/customer/customer_360.py), [`cust_twin.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/intelligence/customer/cust_twin.py) — Returned `customer_name`, nullable email, and accurate `Recency_Days`.

### MySQL Canonical Alignment
- [`python/system_config.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/system_config.py), [`streamlit_app/database/connection.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/database/connection.py), [`streamlit_app/utils/data_loader.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/utils/data_loader.py), [`mysql/08_phase3_intelligence.sql`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/mysql/08_phase3_intelligence.sql), [`mysql/09_phase4_operations.sql`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/mysql/09_phase4_operations.sql) — Aligned DB name `novanest_db` and table `orders_table`.

### Streamlit Application
- [`streamlit_app/app.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/app.py), [`pages/01_Executive_Overview.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/01_Executive_Overview.py), [`pages/02_Customer_Intelligence.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/02_Customer_Intelligence.py), [`pages/08_Decision_Simulator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/08_Decision_Simulator.py), [`pages/09_NovaNest_Command_Center.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/09_NovaNest_Command_Center.py).

### React Frontend (`frontend/src/` + Rebuilt `frontend/dist/`)
- [`frontend/src/App.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/App.tsx), [`services/api.ts`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/services/api.ts), [`utils/formatters.ts`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/utils/formatters.ts), [`components/HeaderNav.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/HeaderNav.tsx), [`components/FloatingChatbot.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/FloatingChatbot.tsx), and all 9 view components (`ExecutiveOverviewView.tsx`, `CustomerIntelligenceView.tsx`, `RestaurantIntelligenceView.tsx`, `OperationsIntelligenceView.tsx`, `FinancialIntelligenceView.tsx`, `AiIntelligenceView.tsx`, `DecisionIntelligenceView.tsx`, `DecisionSimulatorView.tsx`, `CommandCenterView.tsx`).

### Updated Regression Suites (`7` Files)
- [`tests/test_api_alignment_phase05_1.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_api_alignment_phase05_1.py), [`tests/test_ml_models_phase05.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_ml_models_phase05.py), [`tests/test_ask_novanest_ai_suite.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_ask_novanest_ai_suite.py), [`tests/test_floating_chatbot_verification.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_floating_chatbot_verification.py), [`tests/test_platform_full_suite.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_platform_full_suite.py), [`tests/test_sidebar_removal.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_sidebar_removal.py), [`tests/test_theme_system.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_theme_system.py).

---

## 3. Protected Assets Verified Untouched
- `git diff --name-only -- datasets/ powerbi/` returned empty (zero tracked edits).
- [`powerbi/NovaNest.pbix`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/powerbi/NovaNest.pbix) verified intact at exact **`5,638,573`** bytes.
- Historical Phase 02 – 05.2 governance folders preserved cleanly without overwriting.

