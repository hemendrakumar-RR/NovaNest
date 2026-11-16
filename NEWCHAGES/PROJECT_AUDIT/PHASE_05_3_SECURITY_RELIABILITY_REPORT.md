# NOVANEST PHASE 05.3 — SECURITY HARDENING, API CONTRACT FIXES & DASHBOARD RELIABILITY REPORT

- **Audit & Remediation Date**: 2026-11-11
- **Git Baseline**: `main` @ `21b2e2b` (zero commits or pushes made)
- **Overall Classification**: **`VERIFIED`** across Backend Security, API Contracts, Python Engines, Build/Lint, Offline Tests (`60/60` + `4/4`), Live HTTP (`35/35`), and Streamlit (`10/10`); **`PARTIALLY_VERIFIED`** on React CDP UI (core 8 views + `401` login + fault boundary verified; 2 automated click selectors for C360 modal & Chatbot UI left uncaptured in browser DOM); **`BLOCKED`** on Live MySQL (`1045` host auth).

---

## 1. Security Hardening Summary

| Control | Phase 05.2 Finding | Phase 05.3 Remediation | Verification Result |
| :--- | :--- | :--- | :--- |
| **CORS Policy** | `allow_origins=["*"]` with `allow_credentials=True` reflected arbitrary origins (`https://evil.example`). | Added [`api/auth.py::get_allowed_cors_origins`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/auth.py), stripping `*` and enforcing explicit trusted origins via `CORS_ALLOWED_ORIGINS`. | Live `OPTIONS`: `http://localhost:5173` allowed (`200`), `https://evil.example` denied (`400`, `acao: null`). |
| **Authentication & RBAC** | Zero authentication on `/api/*`. | Implemented constant-time `require_scope("read"|"operator"|"admin")` in `api/auth.py` reading env keys (`NOVANEST_VIEWER_KEY`, `NOVANEST_API_KEY`, `NOVANEST_ADMIN_KEY`), failing closed (`401`/`403`/`503`) with zero hardcoded keys. `/api/health` remains open without secrets. | `401` unauthenticated; `viewer` `200`/`403`; `operator` `200`/`403` (`/api/ai/reset`); `admin` `200`. |
| **SQL Validation & AST** | Comma-join whitelist bypass (`SELECT name FROM orders, sqlite_master LIMIT 2`) leaked `sqlite_master`. | Implemented recursive-descent SQL AST lexer/parser in [`python/ai/analyst/sql_ast.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/sql_ast.py) checking every table, CTE, subquery, JOIN, function & LIMIT (`default 25`, `max 100`). Wired into `sql_agent.py` & `conversational/sql_validator.py`. | `sqlite_master` comma-joins, multi-statements, DDL/writes, `randomblob`, `load_extension`, and `LIMIT 500 > 100` rejected both in AST unit tests & live `POST /api/ai/ask`. |
| **SQLite Execution Lock** | No C-level authorizer or `PRAGMA query_only` on SQLite sandbox. | Added `configure_readonly_sqlite` (`PRAGMA query_only = ON`, `PRAGMA trusted_schema = OFF`, `_sqlite_readonly_authorizer`) & `atexit` connection cleanup in `api/main.py`. | `test_03` confirms kernel-level `DatabaseError` on `sqlite_master`, `INSERT`, `PRAGMA table_info`. |

---

## 2. API Contracts, Domain Engines & Dashboard Parity

- **Executive Overview**: Added `avg_rating` (`4.25`) to `/api/overview`; fixed `streamlit_app/pages/01_Executive_Overview.py` crash (`KeyError ['rating']` -> `avg_rating`, `order_datetime`, certified Non-Cancelled GMV `₹465.90 L` & Delivered Net Revenue `₹464.26 L`). Fixed `app.py` to display certified `₹465.90 L` / `₹464.26 L` / dynamic rating.
- **Customer 360 & Segmentation**: Fixed `/api/customer/360/{id}` and `customer_360.py` (`customer_name`, nullable `email: None`, `Recency_Days`). Updated `02_Customer_Intelligence.py` from `CLV_Tier` to `CLV_Segment` (`2.5k` / `50.0%` High-Value) and mapped `customer_360` schema keys cleanly.
- **Restaurant Critical Risk**: Updated `/api/restaurant/overview` to read `Risk_Category`, aligning `critical_risk_count = 3` across FastAPI, React (`CRITICAL RISK MERCHANTS 3`), and Streamlit (`03_Restaurant_Intelligence.py`).
- **Decision Simulator**: Fixed empirical baseline/impact schemas (`Orders`, `Profit_Margin`, `Orders_Diff`, `Decision`, `scenario_assumptions`) across `python/decision_simulation/*.py`, `/api/decision/simulate`, React `DecisionSimulatorView.tsx` (`50,394` vs `47,994`, `22.8%` vs `22.1%`), and Streamlit `08_Decision_Simulator.py`.
- **Digital Twin & Command Center**: Removed hardcoded placeholders (`0.15`, `35.0`, `-₹125k Margin Drift`, `82.1/100`) across `python/digital_twin/*.py`, `/api/digital-twin/state`, React `CommandCenterView.tsx`, and Streamlit `09_NovaNest_Command_Center.py`. Empty DataFrames return explicit `"unavailable"` telemetry status. Verified `85/100`, `781` at-risk (`₹7.48 Cr` CLV), `3` critical merchants (`64.9/100`), `37.38m` avg transit ETA, `23.59%` margin, and `₹5.54L` risk exposure.
- **React Error Handling & Header Territory List**: Added global [`ErrorBoundary.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/ErrorBoundary.tsx) and [`ApiStatePanel.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/ApiStatePanel.tsx) across all 9 views, synced [`HeaderNav.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/HeaderNav.tsx) to `['All', 'Bangalore', 'Chennai', 'Coimbatore', 'Hyderabad', 'Vijayawada']`, and verified `RestaurantIntelligenceView` renders clean fallback UI with `0` uncaught exceptions during network failure injection.

---

## 3. MySQL Schema Standardization & Blocker
- Aligned `novanest_db` and `orders_table` across `api/loader.py`, `streamlit_app/database/connection.py`, `streamlit_app/utils/data_loader.py`, `python/system_config.py`, `mysql/08_phase3_intelligence.sql`, and `mysql/09_phase4_operations.sql`.
- Live MySQL check remains **`BLOCKED`**: local `.env` sets `DB_NAME='novanest'` / `DB_USER='root'` and `mysql.connector.connect()` fails with `ProgrammingError 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)`. No credentials or local DB users were altered.

---

## 4. Consolidated Verification Matrix
| Check Suite | Result | Timing / Details |
| :--- | :--- | :--- |
| Offline `unittest` Suite (7 modules) | **60/60 PASSED (`OK`)** | `39.512s` (`test_phase05_3_security_and_contracts.py` `8/8`, `test_api_alignment_phase05_1.py` `8/8`, `test_analytics.py` `12/12`, `test_ml_models_phase05.py` `8/8`, `test_universal_ai_suite.py` `15/15`, `test_frontend_rebuild.py` `6/6`, `run_all_tests.py` `3/3`) |
| `tests/test_digital_twin.py` | **4/4 PASSED** | Exit `0` |
| React `npm.cmd run lint` | **0 Errors (`Exit 0`)** | `85` warnings across `32` files in `42ms` |
| React `npm.cmd run build` | **Built (`Exit 0`)** | `1.37s` (`2669` modules -> `frontend/dist/`) |
| Live HTTP `unittest` Suite (`:8000`) | **35/35 PASSED (`OK`)** | `8.624s` (`test_ask_novanest_ai_suite`, `test_floating_chatbot_verification`, `test_sidebar_removal`, `test_theme_system`, `test_platform_full_suite`) |
| Edge CDP React (`:5173`) | **`PARTIALLY_VERIFIED`** | Interactive `401` unlock, 6-city dropdown + `Chennai`, 8 sidebar tabs (`56` API calls, `0` normal errors/exceptions), fault boundary (`0` unhandled exceptions); C360 modal & Chatbot DOM click selectors uncaptured in script |
| Edge CDP Streamlit (`:8501`) | **`VERIFIED` (`10/10`)** | `0` `[data-testid="stException"]` & `0` page errors across all 10 discovered routes (`2` boot console errors) |
| Protected Assets & Teardown | **`VERIFIED`** | `datasets/` untouched, `powerbi/NovaNest.pbix` `5,638,573` bytes, `0` active ports (`8000`/`5173`/`8501`) |



---

## 5. Final Closure Addendum (2026-11-11 — Independent Verification & SQL/CDP Closure)

This addendum records the final independent closure verification executed after completion of the initial Phase 05.3 report without overwriting any historical records.

### 5.1 React C360 Modal, Floating Chatbot & City Reset CDP Verification (`VERIFIED`)
Re-executed live FastAPI (`127.0.0.1:8000`) + Vite (`127.0.0.1:5173`) under headless Microsoft Edge CDP (`:9223`) using ephemeral per-run tokens, exact button selectors, and React controlled element value setters (`HTMLSelectElement.prototype.value`, `HTMLTextAreaElement.prototype.value`):
- **Executive Overview Territory Filter Reset (`All` -> `Chennai` -> `All`)**:
  - Initial `All`: `₹4.66 Cr` GMV, `49,971` orders.
  - Switched to `Chennai`: `Territory: Chennai` rendered with filtered totals (differs from `₹4.66 Cr`).
  - Restored `All`: **`₹4.66 Cr`** and **`49,971`** cleanly restored.
- **Customer 360 Modal (`Inspect 360`)**:
  - Navigated to `Customer Intelligence`, located `10` `"Inspect 360"` buttons, clicked first row button -> `GET /api/customer/360/C000001` returned HTTP **`200`**.
  - Rendered `"CUSTOMER DIGITAL TWIN C000001 Indira Aggarwal Chennai RFM SEGMENT Champions ESTIMATED CLV ₹22.8k CHURN PROBABILITY 8.6% TOTAL LIFETIME SPEND ₹11.4k AI Recommendation Trigger ... HYBRID MODEL CURATED MENU RECOMMENDATIONS ..."`, omitted nullable email without error, closed cleanly via modal close button, and rendered `"Customer 360 Profile Unavailable Failed to fetch Verify FastAPI is running on port 8000 and retry. Retry Request"` under `Fetch.failRequest` fault injection (`0` normal console errors, `0` JS page exceptions).
- **Floating Chatbot Lifecycle (`Ask NovaNest AI Assistant`)**:
  - Opened via `button[aria-label="Open Ask NovaNest AI Assistant"]`.
  - Submitted `"What is our total revenue?"` -> `POST /api/ai/ask` returned HTTP **`200`** with grounded CSV metrics (`₹4.66 Cr` GMV, `₹4.64 Cr` Net Revenue, `₹967.33` Net AOV, `23.59%` Realized Contribution Margin, provenance `"CSV File Store (Cleaned & Engineered) Read-Only Secure"`).
  - Submitted `"Analyze my business performance."` -> `POST /api/ai/ask` returned HTTP **`200`** *(Note: broad prompt routed via `universal_router` to `"General Knowledge & Reasoning Engine"` fallback rather than data-grounded CSV summary — queued as a Phase 06 router enhancement candidate)*.
  - Verified `Minimize Chat` + reopen preserved conversation history, offline fault injection rendered `"Service Notice: Unable to reach AI intelligence backend"`, `New Chat` reset history back to welcome + starter chips (`"Explain customer churn."`), and `Close Chat` unmounted dialog cleanly (`0` normal console errors during chat queries, `0` page exceptions).

### 5.2 Verbatim SQL Injection & System-Table Rejection Matrix (`VERIFIED`)
Inspected [`tests/test_phase05_3_security_and_contracts.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_phase05_3_security_and_contracts.py) (`test_01`–`test_04`) and observed that while the saved unittest file covered CORS, comma-joins (`orders, sqlite_master`), `sqlite_schema`, `main.orders`, `sqlite_temp_master`, `WITH RECURSIVE`, `; DROP TABLE`, `randomblob`, `load_extension`, `PRAGMA`, unknown table, `DELETE`, `INSERT`, `LIMIT 500`, and RBAC, it lacked explicit saved unit assertions for top-level `UNION`/`INTERSECT`, explicit `JOIN ... ON`, `UPDATE`, `CREATE`, and `ATTACH`. Executed an independent 20-probe verification matrix (`19` attack queries across all 5 categories + `1` safe CTE control) against `validate_sql_ast`, `validate_and_sanitize_sql`, `conversational.sql_validator.validate_sql`, `execute_safe_sql`, direct SQLite `configure_readonly_sqlite` kernel lock, and FastAPI `TestClient` `POST /api/ai/ask`:

| Category | Representative Attack / Query | AST / Agent / Conv / Safe Exec | Kernel SQLite Authorizer Direct | Live `POST /api/ai/ask` |
| :--- | :--- | :--- | :--- | :--- |
| **Direct System Table** | `SELECT * FROM sqlite_master LIMIT 5` | **Blocked** (`Table 'sqlite_master' is not in the approved database schema whitelist`) | **Blocked** (`DatabaseError: access to sqlite_master.type is prohibited`) | **Blocked** (`200`, `sql_valid: false`, `⚠️ SQL Security Guardrail Triggered`) |
| **Direct System Table** | `SELECT name FROM sqlite_schema` | **Blocked** (`Table 'sqlite_schema' is not in the approved database schema whitelist`) | **Blocked** (`DatabaseError: access to sqlite_master.name is prohibited`) | — |
| **Direct Schema Prefix** | `SELECT * FROM main.orders LIMIT 5` | **Blocked** (`Schema-qualified table 'main.orders' is not permitted`) | Allowed (`orders` is whitelisted table) — AST layer prevents bypass | — |
| **Join Attack** | `SELECT name FROM orders, sqlite_master LIMIT 2` | **Blocked** (`Table 'sqlite_master' is not in the approved database schema whitelist`) | **Blocked** (`DatabaseError: access to sqlite_master.name is prohibited`) | **Blocked** (`200`, `sql_valid: false`) |
| **Join Attack** | `SELECT o.order_id, s.sql FROM orders o JOIN sqlite_master s ON 1=1 LIMIT 5` | **Blocked** (`Table 'sqlite_master' is not in the approved database schema whitelist`) | **Blocked** (`DatabaseError: access to sqlite_master.sql is prohibited`) | — |
| **Subquery Attack** | `SELECT order_id FROM orders WHERE restaurant_id IN (SELECT tbl_name FROM sqlite_temp_master)` | **Blocked** (`Function 'IN()' is not permitted`) | **Blocked** (`DatabaseError: access to temp.sqlite_temp_master.tbl_name is prohibited`) | — |
| **UNION / Set Attack** | `SELECT order_id FROM orders UNION SELECT name FROM sqlite_master LIMIT 5` | **Blocked** (`Table 'sqlite_master' is not in the approved database schema whitelist`) | **Blocked** (`DatabaseError: access to sqlite_master.name is prohibited`) | **Blocked** (`200`, `sql_valid: false`) |
| **UNION ALL / INTERSECT** | `SELECT order_id FROM orders UNION ALL SELECT sql FROM sqlite_schema LIMIT 5` & `INTERSECT ... sqlite_temp_master` | **Blocked** (`Table 'sqlite_schema'` / `'sqlite_temp_master'` prohibited) | **Blocked** (`DatabaseError: access to sqlite_master.sql` / `temp.sqlite_temp_master.tbl_name is prohibited`) | — |
| **Multi-Statement** | `SELECT COUNT(*) FROM orders; DROP TABLE orders;` & `SELECT ...; SELECT name FROM sqlite_master;` | **Blocked** (`Multi-statement SQL queries are strictly prohibited.`) | **Blocked** (`ProgrammingError: You can only execute one statement at a time.`) | **Blocked** (`200`, `sql_valid: false`) |
| **Write / DDL / PRAGMA / Ext** | `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ATTACH`, `PRAGMA table_info(orders)` | **Blocked** (`Only read-only SELECT analytical queries are allowed.`) | **Blocked** (`DatabaseError: not authorized`) | **Blocked** (`200`, `sql_valid: false` on `DELETE`) |
| **Dangerous Function** | `SELECT load_extension('evil.so') FROM orders LIMIT 1` | **Blocked** (`Dangerous or restricted function 'load_extension()' is prohibited.`) | **Blocked** (`OperationalError: not authorized to use function: load_extension`) | — |
| **Safe CTE Control** | `WITH city_totals AS (...) SELECT city, cnt FROM city_totals ORDER BY cnt DESC` | **Allowed** (`LIMIT 25;` appended, `returned_df: true`, `row_count: 2`) | Executed (`[('Bangalore', 1), ('Chennai', 1)]`) | — |

### 5.3 Git Inventory, Secret Scan, MySQL & Final Regression Audit
- **Git Diff & Deleted Check (`main` @ `21b2e2b`)**: `git diff --stat` shows `17` modified tracked files (`566 insertions(+), 21 deletions(-)`: `.env.example` + `16` governance markdown files under `NEWCHAGES/` and root `NEWCHAGESTOTALREPORT.md`), **`0` deleted tracked files** (`git ls-files --deleted` empty), and `292` untracked files reflecting uncommitted Phases 01–05.3 modules/UI/ML artifacts (`api/`, `frontend/`, `models/`, `python/`, `streamlit_app/`, `reports/`, `tests/`), pre-existing repository archive files (`backup/frontend_backup_pre_reset/` 22 files from `2026-10-11`, `refactor_imports.py` legacy Capstone helper), and Phase 05.3 governance/test additions. Exactly `60` source/config/SQL/UI/test files (`5` new + `55` modified) fall inside the Phase 05.3 editing window (`2026-11-11 13:33–14:35`), matching [`NEWCHAGES/PHASE_05_3/FILE_CHANGES.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PHASE_05_3/FILE_CHANGES.md).
- **Secret & Ignore Verification**: `.gitignore` contains `.env` and `dist` (`git check-ignore .env` = `True`); regex secret scan across tracked/untracked workspace code and markdown returned `0` credential hits (`SECRET_SCAN_HITS: []`).
- **Protected Assets**: `git diff --name-only -- datasets/ powerbi/` empty; `powerbi/NovaNest.pbix` intact at **`5,638,573`** bytes.
- **MySQL Non-Destructive Recheck**: Windows service `MySQL80` is `Running` (`Automatic`); no alternate `MYSQL_PWD` / `NOVANEST_*_PASSWORD` environment variables exist; `.env` (`DB_HOST=localhost`, `DB_PORT=3306`, `DB_NAME='novanest'`, `DB_USER='root'`, `pw_set=True`) still fails with `ProgrammingError 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)` -> **`BLOCKED`**.
- **Final Regression Sweep**: `python -m unittest ... -v` across 7 modules -> **`Ran 60 tests in 44.470s — OK`**; `python tests/test_digital_twin.py` -> **`4/4 PASSED`**; `npm.cmd run lint` -> Exit `0` (`85 warnings, 0 errors`, `49ms`); `npm.cmd run build` -> Exit `0` (`✓ built in 1.04s`); `Get-NetTCPConnection` across `8000,5173,8501,9223,9224` -> `0` active LISTEN sockets.

### 5.4 Final Closure Classification Matrix
| Domain | Final Status | Notes |
| :--- | :--- | :--- |
| Security (CORS, RBAC, Recursive SQL AST, SQLite Kernel Lock) | **`VERIFIED`** | All 5 SQL attack classes & RBAC/CORS probes blocked verbatim; `0` secrets leaked |
| Backend API Contracts, Digital Twin, Decision Simulator & C360 | **`VERIFIED`** | Verified across unit/contract tests (`60/60 OK`), live HTTP (`35/35 OK`), and CDP |
| React Frontend (Build/Lint, 9 Views, City Filter Reset, C360 Modal, FloatingChatbot, Fault Boundaries) | **`VERIFIED`** | Upgraded from `PARTIALLY_VERIFIED` after full C360 modal, Chatbot & `All->Chennai->All` CDP verification (`0` JS/normal console errors) |
| Streamlit Multipage Application (`app.py` + Pages `01`–`09`) | **`VERIFIED`** | `6/6` `AppTest` + `10/10` live Edge CDP routes (`0` `stException`) |
| Git Hygiene, Protected Datasets & `NovaNest.pbix` | **`VERIFIED`** | `0` deleted files, `.env` ignored, `NovaNest.pbix` `5,638,573` bytes untouched |
| Live MySQL Execution (`MySQL80` + `.env`) | **`BLOCKED`** | Static SQL/config aligned (`novanest_db`/`orders_table`); host auth fails `1045 (28000)` |
