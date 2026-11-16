# NOVANEST — PHASE 06.0: Legacy AI Stabilization & Data Grounding Repairs
## File Changes Register

---

## 1. Modified Files

| File Path | Key Changes | Reason |
| :--- | :--- | :--- |
| `api/auth.py` | Added `principal_id` field to `AuthPrincipal`; added `_derive_principal_id(role, token)` using process-ephemeral / env-salted HMAC-SHA256. | Provide non-reversible principal identifiers for isolated session state without keeping raw tokens. |
| `api/main.py` | Updated `get_sqlite_conn()` to call `build_readonly_sqlite_connection(data)`; injected `principal: AuthPrincipal = require_scope(...)` in `POST /api/ai/ask` and `POST /api/ai/reset`; returned `cleared` flag on reset. | Achieve 9-table SQLite parity in FastAPI and enforce strict caller-principal session isolation & RBAC alignment (`401`/`403` fail-closed preserved). |
| `python/ai/analyst/data_grounding.py` | Fixed `restaurants.avg_rating` (`4.25`), fixed `rider_allocation.csv` schema (`order_city`, `recommended_rider_id`, `workload_tier`, `allocation_score`), removed hardcoded fallbacks (`4.2`, `32.4`, `94.2`, `96.2`, `50/60`, `North Hub`, `1250000`), aggregated `revenue_leakage` by `leakage_type` with `is_confirmed_loss=False`, added `business_overview` and `multi_domain` support. | Eliminate fabricated metrics, broken column lookups, and single-domain truncation. |
| `python/ai/analyst/root_cause.py` | Removed 100% of static hardcoded RCA claims (`32.4`, `5.8%`, `East Hub`, `412/8.2%`, `₹12.50L`, `18.2%`, `2.4x`, `8.9/4.3 km`, `18 kitchens`, `64/14 days`, `3.1 stars`, `78%`) and computed empirical values dynamically from CSVs + `kpi_definitions.json`, surfacing uncertainties & `ROC-AUC = 0.5161` caveat. | Replace fabricated RCA prose with verifiable multi-table evidence. |
| `python/ai/analyst/universal_router.py` | Added `_extract_router_domains()`, `domains`, and `is_multi_domain` metadata; expanded routing for business performance, churn count, financial-vs-operational comparison, delivery RCA, restaurant attention, and profitability recommendations. | Support natural executive & comparative inquiries without disturbing `GREETING`, `PROGRAMMING`, `CALCULATION`, `PROJECT_KNOWLEDGE`, or `GENERAL`. |
| `python/ai/analyst/orchestrator.py` | Wired `principal` forwarding; switched to 9-table `build_readonly_sqlite_connection`; replaced fake `RECOMMENDATIONS` (`₹12.5L`) with live `python/decision/next_best_action.py` integration + honest ML caveats; restored `CALCULATION` (`compute_calculation`) dispatch & fixed `AIProviderResult` custom-provider import; added broad/multi-domain executive cards. | Connect AI answers cleanly to certified deterministic NBA engines, 9-table RO SQLite, and isolated sessions while preserving single-agent boundaries. |
| `python/ai/analyst/sql_agent.py` | Added explicit `DATASET_TO_SQLITE_TABLE_MAP` (`9` tables), `build_readonly_sqlite_connection(data)` (with `orders` harmonization + C authorizer lock), and `verify_sqlite_table_parity()`. *(Verified `python/ai/analyst/query_executor.py` does not exist; SQL execution remains in `sql_agent.py` & `python/ai/conversational/query_executor.py`.)* | Guarantee full 9-table SQLite parity with identical AST/authorizer read-only protection. |
| `python/ai/analyst/conversation_manager.py` | Added `threading.RLock`, `OrderedDict` store with `1800s` (30m) idle TTL, `250`-session LRU cap, `12`-turn window (`4,000` chars), `redact_pii()`, HMAC-scoped principal keys, ownership-verified `reset_session(..., principal)`, zero raw `pd.DataFrame` retention. | Harden conversational memory against cross-tenant leakage, unbounded growth, race conditions, and PII storage. |
| `python/ai/analyst/__init__.py` | Re-exported `AskNovaNestOrchestrator`, `build_readonly_sqlite_connection`, `verify_sqlite_table_parity`, `DATASET_TO_SQLITE_TABLE_MAP`. | Clean package API surface. |
| `python/ai/conversational/nl_to_sql.py` | Added AST-safe SQL templates for underperforming/attention restaurants (`CASE WHEN` inside `HAVING` to avoid parser `AND()` ambiguity) and highest-revenue city queries. | Enable natural-language attention queries over SQLite under strict AST constraints. |
| `python/ai/insights/business_insights.py` | Updated `generate_business_insights` to compute certified non-cancelled GMV, Delivered Net Revenue, Net AOV, cancellation rate, and fulfilled-order delivery fee. | Align AI executive insights with Phase 04 certified KPI definitions. |
| `streamlit_app/pages/07_Ask_NovaNest.py` | Replaced deprecated `ai.conversational/*` calls, custom 5-table DB helper, and invalid `commission_rate_change` simulation keys with unified `analyze_business_inquiry` + `build_readonly_sqlite_connection`, `Reset Chat`, KPI strip, charts, simulation table, live NBAs, and explicit `STREAMLIT_DIR`/`PROJECT_ROOT` `sys.path` setup before `import bootstrap`. | Unify Streamlit Page 07 with the stabilized Phase 06.0 AI engine and enable standalone AppTest/page execution. |

---

## 2. New Files Created

| File Path | Purpose | Status |
| :--- | :--- | :--- |
| `tests/test_phase06_0_stabilization.py` | Comprehensive Phase 06.0 regression suite covering data grounding, empirical RCA, broad/multi-domain routing, live NBAs, 9-table SQLite parity & security, session isolation/TTL/LRU/PII, API RBAC, certified insights, and Streamlit Page 07/09 AppTest. | Active (`9/9 OK`) |
| `NEWCHAGES/PHASE_06/PHASE_06_0/PHASE_PLAN.md` | Phase 06.0 scope, objectives, and single-agent stabilization boundaries. | Created |
| `NEWCHAGES/PHASE_06/PHASE_06_0/IMPLEMENTATION_LOG.md` | Chronological log of empirical audit and code fixes. | Created |
| `NEWCHAGES/PHASE_06/PHASE_06_0/FILE_CHANGES.md` | Complete inventory of created and modified files. | Created |
| `NEWCHAGES/PHASE_06/PHASE_06_0/TEST_RESULTS.md` | Observed verification results across offline, live HTTP, Streamlit AppTest, React build, and MySQL probe. | Created |
| `NEWCHAGES/PHASE_06/PHASE_06_0/PHASE_SUMMARY.md` | Executive summary, before/after table, blockers, and readiness for Phase 06.1. | Created |

---

## 3. Master Ledgers Appended (Non-Destructive)
- Appended Phase 06.0 entries cleanly to `NEWCHAGES/NEW_FILES_REGISTER.md`, `NEWCHAGES/MODIFIED_FILES_REGISTER.md`, `NEWCHAGES/DECISIONS_AND_REASONS.md` (`ADR-010`), `NEWCHAGES/CHANGELOG.md`, `NEWCHAGES/IMPLEMENTATION_HISTORY.md`, `NEWCHAGES/TESTING_HISTORY.md`, `NEWCHAGES/ROADMAP_STATUS.md`, `NEWCHAGES/NEWCHAGES_MASTER.md`, `NEWCHAGES/NEWCHAGESTOTALREPORT.md`, and root `NEWCHAGESTOTALREPORT.md`.

---

## 4. Protected Assets Verified Untouched
- Zero edits or deletions in `datasets/`, `models/`, `powerbi/NovaNest.pbix`, `.env`, legacy `NEWCHAGES/PHASE_01`–`PHASE_05_3` folders, or git commit history.

