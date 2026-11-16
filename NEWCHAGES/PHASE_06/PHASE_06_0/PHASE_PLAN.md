# NOVANEST — PHASE 06.0: Legacy AI Stabilization & Data Grounding Repairs
## Phase Plan

- **Phase**: `Phase 06.0` (Mandatory Stabilization Prerequisite Prior to Multi-Agent Phase 06.1–06.8)
- **Date**: `2026-11-11`
- **Status**: `VERIFIED` (Offline + Live HTTP + Streamlit AppTest + React Build Verified; Live MySQL Runtime `BLOCKED` by Host Auth `1045 (28000)`)
- **Scope**: Stabilize verified bugs in the existing single-agent conversational AI architecture without creating the 5 Phase 06.2 domain agents yet.

---

## 1. Objectives & Task Breakdown

| Task ID | Workstream | Target Modules | Exit Criterion |
| :--- | :--- | :--- | :--- |
| **T1** | Data Grounding & Schema Repair | `python/ai/analyst/data_grounding.py` | Fix `restaurants.avg_rating`, `rider_allocation.csv` columns (`order_city`, `recommended_rider_id`, `workload_tier`, `allocation_score`), remove fake fallbacks (`4.2`, `32.4`, `94.2`, `96.2`, `50`/`60`, `North Hub`, `1250000`), aggregate `revenue_leakage` by `leakage_type` with `is_confirmed_loss=False`, support multi-domain synthesis. |
| **T2** | Empirical Root-Cause Analysis | `python/ai/analyst/root_cause.py` | Eliminate all hardcoded strings (`32.4`, `5.8%`, `East Hub`, `412`, `8.2%`, `₹12.50L`, `18.2%`, `2.4x`, `8.9/4.3 km`, `18 kitchens`, `64%/22%`, `64/14 days`, `3.1/4.4 stars`, `78%`) and compute dynamically from CSVs + `kpi_definitions.json`, including real uncertainties and `ROC-AUC = 0.5161` caveat. |
| **T3** | Orchestrator & Live NBA Integration | `python/ai/analyst/orchestrator.py`, `python/ai/analyst/__init__.py` | Handle broad performance & multi-domain queries cleanly, wire 9-table RO SQLite builder, replace fake `RECOMMENDATIONS` with live `python/decision/next_best_action.py`, preserve single-agent Phase 06.0 boundary and calculation routing. |
| **T4** | 9-Table SQLite Data Parity | `python/ai/analyst/sql_agent.py`, `python/ai/conversational/nl_to_sql.py`, `api/main.py` | Expose explicit `DATASET_TO_SQLITE_TABLE_MAP` (`9` approved `ALLOWED_TABLES`), harmonize `orders` columns, verify row parity, add safe underperforming-restaurant SQL template, keep SQL AST & SQLite C authorizer intact. |
| **T5** | Universal Intent Router Upgrade | `python/ai/analyst/universal_router.py` | Support natural-language business performance, churn count, financial-vs-operational comparison, delivery RCA, restaurant attention, and profitability recommendations while preserving `GREETING`, `PROGRAMMING`, `CALCULATION`, `PROJECT_KNOWLEDGE`, and `GENERAL`. |
| **T6** | Session Memory Hardening | `python/ai/analyst/conversation_manager.py` | Enforce `threading.RLock`, HMAC-scoped caller principal isolation (zero raw tokens), `1800s` (30m) idle TTL, `250`-session LRU cap, `12`-turn window, regex PII/secret redaction preserving currency numbers, and zero raw DataFrame retention. |
| **T7** | API RBAC & Principal Ownership | `api/auth.py`, `api/main.py` | Derive opaque `principal_id` on `AuthPrincipal`, enforce caller-principal isolation in `POST /api/ai/ask` (`operator`) and `POST /api/ai/reset` (`admin`, preserving `viewer=403` and `operator=403` when `NOVANEST_ADMIN_KEY` is configured). |
| **T8** | Streamlit & Insights Parity | `python/ai/insights/business_insights.py`, `streamlit_app/pages/07_Ask_NovaNest.py` | Align insights with certified non-cancelled GMV & Delivered Net Revenue/AOV; migrate Page 07 onto `analyze_business_inquiry` + `build_readonly_sqlite_connection`; remove bogus `commission_rate_change` keys & deprecated `ai.conversational` calls. |
| **T9** | Comprehensive Verification | `tests/test_phase06_0_stabilization.py` + Existing Suites | Achieve green offline unit suites, live FastAPI HTTP suites, isolated Streamlit AppTest (`Page 07` + `Page 09`), and React production build. |
| **T10** | Governance Traceability | `NEWCHAGES/PHASE_06/PHASE_06_0/*` + Master Registers | Record full plan, changes, execution logs, verified numbers, and non-destructive appends across master registers. |

---

## 2. Explicit Scope Boundaries
- **In Scope**: Repairing legacy AI data grounding, dynamic RCA, router coverage, live NBA wiring, 9-table RO SQLite parity, principal-isolated session store, FastAPI RBAC ownership alignment, Streamlit Page 07 unification, and verification.
- **Out of Scope (Deferred to Phase 06.1–06.8)**: Implementing the 5 new domain agent classes, `MasterOrchestrator` parallel wave scheduler, or modifying `datasets/`, `models/`, `powerbi/NovaNest.pbix`, or `.env`.

