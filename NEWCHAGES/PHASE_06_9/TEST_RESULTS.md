# Phase 06.9 Test Results — Controlled MySQL Activation

## Test Execution Summary

| Test Suite / Probe | Component Under Test | Tests Executed | Status | Execution Time |
| :--- | :--- | :--- | :--- | :--- |
| `scratch/test_live_http_mysql.py` | Live HTTP Endpoints & Streamlit Socket (`:8000`, `:8501`) | 9 network checks | **9/9 PASSED (100%)** | 5.8s |
| `scratch/test_phase06_9_live_validation.py` | MySQL Endpoints, Dashboards, 5 AI Agents, Orchestrator, KPIs | 11 unit tests | **11/11 PASSED (100%)** | 6.742s |
| `scratch/test_phase06_9_controlled_fallback.py` | Unavailability Injection, Failover, Mixing Check, Recovery | 1 lifecycle test | **1/1 PASSED (100%)** | 12.568s |
| `tests/test_phase06_8_application_integration.py` | MySQL Read Paths, Joins, KPI Parity, Agents, Endpoints | 15 unit tests | **15/15 PASSED (100%)** | 25.416s |
| `tests/test_phase06_7_mysql_integration.py` | MySQL Connectivity, Schema, Topological Dry Run, Security | 17 unit tests | **17/17 PASSED (100%)** | 10.493s |
| `tests/run_all_tests.py` | Core Project Verification Runner | 3 unit tests | **3/3 PASSED (100%)** | 0.001s |
| `tests/validate_pages_runtime.py` | Streamlit Multi-Page Runtime Deprecation Validator | 2 unit tests | **2/2 PASSED (100%)** | 0.016s |
| `npm run build` | Frontend TypeScript & Vite Production Bundle | 2,673 modules | **RC=0 (0 errors, 0 warnings)** | 1.17s |

---

## Detailed Failure, Root Cause, and Fix Registry

### 1. Endpoint Key Mismatch on `/api/overview`
- **Observed Failure**: `KeyError: 'gmv'` in initial test script.
- **Root Cause**: The executive overview endpoint in `api/main.py` names the gross merchandise key `total_gmv` (referencing `fin["gmv"]`), not `gmv`.
- **Fix Applied**: Updated test assertions to access `payload["kpis"]["total_gmv"]`.
- **Retest Result**: **PASS (HTTP 200, ₹46,590,125.00)**.

### 2. Metric Hierarchy on `/api/financial/overview`
- **Observed Failure**: `KeyError: 'net_aov'` under `payload["kpis"]`.
- **Root Cause**: In `/api/financial/overview`, average order value is structured under `payload["unit_economics"]["aov"]`, and margin is under `payload["kpis"]["profit_margin_pct"]`.
- **Fix Applied**: Updated test assertion to query `unit_economics["aov"]`.
- **Retest Result**: **PASS (HTTP 200, ₹967.33)**.

### 3. Fleet Size Key on `/api/operations/overview`
- **Observed Failure**: `KeyError: 'fleet_size'` under `payload["kpis"]`.
- **Root Cause**: The operations endpoint exposes total active riders as `kpis["active_riders"]` (representing `len(riders) == 4000`), not `fleet_size`.
- **Fix Applied**: Updated assertion to check `kpis["active_riders"] == 4000`.
- **Retest Result**: **PASS (HTTP 200, 4,000 riders)**.

### 4. Review Rating Column Resolution
- **Observed Failure**: `KeyError: 'rating_food'` on `ratings_reviews` DataFrame.
- **Root Cause**: The database schema in `mysql/01_schema.sql` and `load_mysql.py` defines `restaurant_rating` and `delivery_rating`, not `rating_food`.
- **Fix Applied**: Queried `reviews["restaurant_rating"].mean()`.
- **Retest Result**: **PASS (Mean = 3.99 / 5.00)**.

### 5. Master Orchestrator Outcome Subscripting
- **Observed Failure**: `TypeError: 'OrchestrationOutcome' object is not subscriptable`.
- **Root Cause**: `OrchestrationOutcome` is a Pydantic model (`BaseModel`), whose synthesis is accessed via attribute `outcome.synthesis.consolidated_summary` rather than dictionary subscripting.
- **Fix Applied**: Updated test to access `outcome.synthesis.consolidated_summary` and `outcome.agent_result.status`.
- **Retest Result**: **PASS (Status = SUCCESS, synthesis length > 0)**.

### 6. Chatbot API Response Contract
- **Observed Failure**: `AssertionError: 'response' not found` in `/api/ai/ask` JSON.
- **Root Cause**: The chat endpoint returns `{"question": ..., "answer": ..., "verified_metrics": ...}`, using `"answer"` for the primary synthesized response.
- **Fix Applied**: Updated test to verify `"answer"` and `"verified_metrics"` presence.
- **Retest Result**: **PASS (HTTP 200, grounded response verified)**.

### 7. Auth Key Gateway Configuration
- **Observed Failure**: `HTTP 503 Service Unavailable: Server API authentication keys are not configured in environment.`
- **Root Cause**: The local `.env` did not specify `NOVANEST_API_KEY`, causing `api/auth.py`'s `has_configured_auth_keys()` to refuse scoped endpoint execution for security.
- **Fix Applied**: Configured explicit API keys in `.env` and restarted application processes.
- **Retest Result**: **PASS (HTTP 200 across all scoped endpoints)**.

---

## Ground Truth KPI Reconciliation

| Certified Metric | Verified Database Ground Truth | Live MySQL API Output | Variance | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Total Orders** | 49,971 | 49,971 | 0 (0.00%) | **EXACT MATCH** |
| **Delivered Orders** | 47,994 | 47,994 | 0 (0.00%) | **EXACT MATCH** |
| **Delivered GMV** | ₹46,590,125.00 | ₹46,590,125.00 | ₹0.00 (0.00%) | **EXACT MATCH** |
| **Net Revenue** | ₹46,425,992.00 | ₹46,425,992.00 | ₹0.00 (0.00%) | **EXACT MATCH** |
| **Net AOV** | ₹967.33 | ₹967.33 | ₹0.00 (0.00%) | **EXACT MATCH** |
