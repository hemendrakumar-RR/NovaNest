# NOVANEST PHASE 06.2 — TEST RESULTS REPORT

**Execution Date**: 2026-11-11  
**Environment**: Windows / Python 3.14 / Certified CSV File Store + 9-Table RO SQLite Sandbox (`MySQL80` live host auth `BLOCKED` `1045 (28000)`)

---

## 1. Phase 06.2 Dedicated Verification Suite (`tests.test_phase06_2_domain_agents`)
- **Command**: `python -m unittest tests.test_phase06_2_domain_agents -v`
- **Result**: **`PASSED — Ran 22 tests in 20.345s — OK`** (`0` failures, `0` errors, `0` skipped)
- **Verified Behaviors**:
  - **Registry & Boundary (`4/4`)**: `create_default_domain_registry()` promotes all 5 domain agents to `OPERATIONAL` with callable handlers while `AgentRegistry(preload_planned_blueprints=True)` stays `PLANNED` by default; `MasterOrchestrator` absent; RBAC/table authorization enforced.
  - **FinancialAgent (`4/4`)**: Exact parity with `KPI-01` (`₹46,590,125.00`), `KPI-02` (`₹46,425,992.00`), `KPI-03` (`₹967.33`), `KPI-04` (`22.48%`), `KPI-12` (`23.59%`), `KPI-13` (`₹10,953,031.58`), `is_confirmed_loss=False`, city filter `"Chennai"`, allowed SQL on `orders` vs `SQL_PERMISSION_DENIED` on `customers` & `sqlite_master`, `TABLE_ACL_DENIED`, `BLOCKED`/`PARTIAL`/`ERROR` missing/bad datasets.
  - **CustomerAgent (`4/4`)**: Strictly blocks `viewer`/`read` scope (`RBAC_SCOPE_DENIED`), operator metrics (`5,000` customers, `99.94%` repeat, `53.36%` M1 cohort, `₹9,285.20` ARPU, `781` High Risk = `15.62%`), non-production `NEEDS_MORE_DATA` churn caveat (`ROC-AUC=0.5161`), C360 lookup & cohort matrix, `PARTIAL` mode without churn predictions (no fabricated probabilities), `riders` SQL denied.
  - **OperationsAgent (`2/2`)**: Exact SLA (`32.26%`, `16,119/49,971 > 45m`), latency (`37.38 mins`), rider efficiency (`12.49`), anomalies (`2,184`), all 3 ML caveats flagged `is_production_ready=False` (`BASELINE_ONLY` ETA/Demand, `EXPERIMENTAL` Anomaly), intents (`rider_performance`, `demand_forecasting`, `operational_anomalies`), `customers` SQL denied, empty data `BLOCKED`.
  - **RestaurantAgent (`2/2`)**: Verified `1,500` partners, `KPI-11` (`₹30,950.66`), `avg_rating` (`4.25`), `3` Critical & `397` At Risk, `NEEDS_MORE_DATA` caveat (`MAE=1.3248`, `R2=-0.0027`), intents (`restaurant_risk`, `ratings_and_menu`, `restaurant_benchmarks`, `restaurant_demand`), `deliveries` SQL denied, degraded `PARTIAL`/`BLOCKED`.
  - **DecisionAgent (`3/3`)**: Strictly blocks `viewer`/`read` (`RBAC_SCOPE_DENIED`), verifies `decision_synthesis`, `root_cause`, `what_if_simulation` (`sim_revenue_diff_inr`), `systemic_risk`, `next_best_action`, `is_confirmed_loss=False`, `HEURISTIC_SIMULATION` non-production caveat, missing-data `BLOCKED`, `payments` SQL denied.
  - **Cross-Agent, Concurrency, Security & Tracing (`3/3`)**: 5-thread concurrent `ThreadPoolExecutor` run (`5/5 SUCCESS`), cross-agent `OutputVerifier.verify(..., agent_results=results)` -> `VERIFIED` (`0` conflicts, `0` unsupported claims, `unconfirmed_loss_preserved=True`), synthetic conflict & hallucinated `"confirmed loss"` caught (`REJECTED`), cross-principal block (`PRINCIPAL_ISOLATION_VIOLATION`), cooperative cancellation (`CANCELLED`), timeout (`TIMEOUT`), JWT/Bearer secret redaction.

---

## 2. Full Offline Regression Matrix
- **9-Module Combined Unittest Sweep**:
  - `python -m unittest tests.test_phase06_2_domain_agents tests.test_phase06_1_foundation tests.test_phase06_0_stabilization tests.test_universal_ai_suite tests.test_phase05_3_security_and_contracts tests.test_analytics tests.test_api_alignment_phase05_1 tests.test_ml_models_phase05 tests.test_frontend_rebuild -v`
  - **Result**: **`PASSED — Ran 102 tests in 49.120s — OK`** (`22 + 14 + 9 + 15 + 8 + 12 + 8 + 8 + 6 = 102` tests; `0` failures, `0` errors).
- **Standalone Verification Scripts**:
  - `python -m tests.run_all_tests` -> **`PASSED — Ran 3 tests in 0.001s — OK`**.
  - `python tests/test_digital_twin.py` -> **`PASSED — 4/4 PASSED`**.

---

## 3. Ephemeral Live Uvicorn HTTP Check (`127.0.0.1:8000`)
- **Command**: Launched temporary `uvicorn api.main:app --host 127.0.0.1 --port 8000` (`SERVER_READY=True`) against legacy Phase 3/4 HTTP suites (`test_ask_novanest_ai_suite`, `test_floating_chatbot_verification`, `test_animated_top_dock`, `test_cinematic_effects`, `test_sidebar_removal`, `test_theme_system`).
- **Observed Result**: **`37 passed, 15 failed` out of `52` tests (`6.940s`)**:
  - `14` failures returned `401 != 200` on unauthenticated `/api/ai/...` HTTP requests because Phase 05.3 enforced mandatory `X-API-Key` authentication (expected security posture, not a Phase 06.2 defect; authenticated API tests pass inside `test_phase05_3_security_and_contracts` and `test_phase06_0_stabilization`).
  - `1` failure (`test_cinematic_effects.test_08_live_service_connectivity`) timed out/refused connecting to frontend Vite dev server `http://localhost:5173/` (not started).
- **Teardown Verification**: Verified post-cleanup `netstat -ano | Select-String ":8000 "` showed zero `LISTENING` sockets (only closed `TIME_WAIT 0` remnants).

