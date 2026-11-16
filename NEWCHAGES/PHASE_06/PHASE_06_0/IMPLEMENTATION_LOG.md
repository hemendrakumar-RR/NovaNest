# NOVANEST — PHASE 06.0: Legacy AI Stabilization & Data Grounding Repairs
## Implementation Log

- **Execution Date**: `2026-11-11`
- **Safety Backups**: Pre-edit copies of modified source modules archived outside workspace tree under artifact path `backup_phase06_0_20261111/`.

---

## Chronological Execution Steps

1. **Empirical Baseline Audit**:
   - Audited `datasets/cleaned/` and `datasets/engineered/` alongside `datasets/analytics/kpi_definitions.json` and `models/*/*_v2.json`.
   - Verified baseline numbers: GMV (`!= 'Cancelled'`) = `₹46,590,125.00` (`₹4.66 Cr`); Delivered Net Revenue = `₹46,425,992.00` (`₹4.64 Cr`); Net AOV = `₹967.33`; Contribution Margin = `23.59%` (`₹10,953,031.58` realized profit); Mean `avg_rating` = `4.25` (`246` merchants `<3.8`); Mean delivery duration = `37.38 mins`; Strict SLA breaches (`>45m`) = `16,119` (`32.26%`, vs `1,067` boundary orders at `==45m`); Cancellation rate = `3.96%` (`1,977 / 49,971`, Coimbatore highest at `4.27%`); Sub-`3.8` rated partner cancellation ratio = `4.46%` vs `3.86%` (`1.16x`); High Churn Risk = `781` (`15.62%`, Churn v2 `ROC-AUC = 0.5161`, `NEEDS_MORE_DATA`); Unverified Potential Revenue Leakage = `₹553,946.31` across `4,669` flagged rows (`Cancelled Commission Loss` `1,977` / `₹502,452.12`, `Post-Discount Margin Deficit` `2,465` / `₹51,494.19`, `Promotional & Delivery Subsidies` `227` / `₹0.00`).
2. **Task 7 Prep (`api/auth.py`)**:
   - Added opaque HMAC-SHA256 `principal_id` derivation (`_derive_principal_id(role, token)`) to `AuthPrincipal` using `NOVANEST_SESSION_SALT` or process-ephemeral `secrets.token_bytes(32)`, avoiding raw token retention.
3. **Task 6 (`python/ai/analyst/conversation_manager.py`)**:
   - Implemented thread-safe `_SESSION_LOCK` (`threading.RLock()`), `OrderedDict` session store (`_SESSIONS`) with `1800s` (30m) idle TTL, `250`-session LRU eviction cap, `12`-turn window (`4,000`-char turn bound), `redact_pii()` (email, bearer token, API key, PAN, phone context — preserving currency numbers), caller-principal scoping (`make_scoped_session_key`), ownership checks on `reset_session(..., principal)`, zero raw `pd.DataFrame` retention, and expanded topic follow-up templates.
4. **Task 4 (`python/ai/analyst/sql_agent.py` & `python/ai/conversational/nl_to_sql.py`)**:
   - Added explicit `DATASET_TO_SQLITE_TABLE_MAP` (`9` tables: `customers`, `restaurants`, `menu_items`, `riders`, `orders` [mapped to MySQL `orders_table`], `payments`, `deliveries`, `ratings_reviews`, `promotions`), `build_readonly_sqlite_connection(data)` (with `order_datetime`/`final_amount` harmonization + `configure_readonly_sqlite`), and `verify_sqlite_table_parity()`. Note: confirmed `python/ai/analyst/query_executor.py` does not exist in repository; SQL execution operates via `sql_agent.py` and `python/ai/conversational/query_executor.py`.
   - Added AST-safe SQL templates in `nl_to_sql.py` for `"Which restaurants need attention?"` and `"city.*highest revenue"`; replaced `HAVING ... AND (...)` with `AND CASE WHEN ... END = 1` after catching an AST `"Function 'AND()' is not permitted"` block during initial test verification.
5. **Task 1 (`python/ai/analyst/data_grounding.py`)**:
   - Replaced `restaurants["rating"]` (`4.2`) with `_resolve_column(..., ["avg_rating", "rating"])` (`4.25`), replaced broken `rider_allocation` columns (`city`/`current_riders:50`/`recommended_riders:60`) with `order_city`/`recommended_rider_id`/`workload_tier`/`allocation_score`, eliminated all fabricated fallbacks (`32.4`, `94.2`, `96.2`, `North Hub`, `1250000.0`), aggregated `revenue_leakage` by `leakage_type` (`is_confirmed_loss=False`, `classification="Investigation Candidate"`), and added `business_overview` + `multi_domain` aggregation with aligned city financial/operational scorecards.
6. **Task 2 (`python/ai/analyst/root_cause.py`)**:
   - Replaced all 4 fabricated narrative branches (+ added `_rca_restaurants`) with dynamic multi-table empirical analytics across `deliveries`, `orders`, `orders_engineered`, `restaurants`, `ratings_reviews`, `customer_churn_predictions`, `revenue_leakage`, `rider_allocation`, `operational_anomalies`, and `datasets/analytics/kpi_definitions.json`, including real Pearson distance correlation (`r = -0.0029`), ETA v2 `R2 = -0.0002`, Churn v2 `ROC-AUC = 0.5161`, and unconfirmed leakage caveats.
7. **Task 5 (`python/ai/analyst/universal_router.py`)**:
   - Implemented `_extract_router_domains()` and broadened routing to classify `"Analyze my business performance."`, `"How many high churn customers do we have?"`, `"Compare financial and operational performance."`, `"Why is delivery performance declining?"`, `"Which restaurants need attention?"`, and `"Recommend actions to improve profitability."` while keeping non-business routes (`GREETING`, `PROGRAMMING`, `CALCULATION`, `PROJECT_KNOWLEDGE`, `GENERAL`) accurate.
8. **Task 3 (`python/ai/analyst/orchestrator.py` & `__init__.py`)**:
   - Passed caller `principal` into `resolve_follow_up_query`, `get_session_history`, and `record_turn`; built 9-table RO SQLite connections on demand; replaced static `RECOMMENDATIONS` (`"Preserve ₹12.5L"`) with `_generate_grounded_recommendations()` invoking `python/decision/next_best_action.py` (`generate_customer_next_best_actions`, `generate_restaurant_next_best_actions`, `generate_operational_next_best_actions`) and empirical intelligence helpers (with exact argument order `(restaurants, orders, ratings)` verified via `inspect.signature`). Fixed `CALCULATION` (`compute_calculation`) dispatch and `AIProviderResult` custom-provider bug discovered during regression testing.
9. **Task 7 (`api/main.py`)**:
   - Switched `get_sqlite_conn()` to `build_readonly_sqlite_connection(data)`.
   - Injected `principal: AuthPrincipal = require_scope("operator")` on `POST /api/ai/ask` and `principal: AuthPrincipal = require_scope("admin")` on `POST /api/ai/reset`, forwarding `principal` so caller sessions stay isolated while preserving `viewer=403` and `operator=403` (when `NOVANEST_ADMIN_KEY` is configured) RBAC rules.
10. **Task 8 (`python/ai/insights/business_insights.py` & `streamlit_app/pages/07_Ask_NovaNest.py`)**:
    - Aligned `generate_business_insights` with non-cancelled GMV, Delivered Net Revenue, Net AOV, cancellation rate, and fulfilled-order delivery fee.
    - Rebuilt Page 07 on unified `analyze_business_inquiry` + `build_readonly_sqlite_connection`, removing direct `ai.conversational/*` calls and wrong `commission_rate_change` keys, adding `Reset Chat`, Verified KPIs, SQL barrier card, charts, simulation table, live NBAs, and explicit `STREAMLIT_DIR`/`PROJECT_ROOT` `sys.path` bootstrapping so Page 07 runs cleanly in standalone execution as well as inside the multipage app.
11. **Task 9 & Task 10 (`tests/test_phase06_0_stabilization.py` & `NEWCHAGES/`)**:
    - Authored `test_phase06_0_stabilization.py`, verified all offline suites (`52/52`), standalone `run_all_tests`, live FastAPI HTTP suites (`35/35`), React Vite production build (`0.999s`), isolated Streamlit Page 07 + Page 09 `AppTest`, and MySQL read-only fallback status (`BLOCKED` `1045`). Recorded full Phase 06.0 documentation under `NEWCHAGES/PHASE_06/PHASE_06_0/` and appended master ledgers.

