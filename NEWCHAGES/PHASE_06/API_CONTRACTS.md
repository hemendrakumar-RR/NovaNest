# PHASE 06 — API, REACT & STREAMLIT INTEGRATION CONTRACTS

- **Status**: `PROPOSED`

---

## 1. FastAPI Endpoints & Backward Compatibility (`PROPOSED`)

Existing [`POST /api/ai/ask`](../../api/main.py#L1123) and [`POST /api/ai/reset`](../../api/main.py#L1152) MUST remain backward compatible with `ChatResponse` in [`frontend/src/services/api.ts`](../../frontend/src/services/api.ts) (`tests/test_universal_ai_suite.py` and `tests/test_ask_novanest_ai_suite.py`).

### 1.1 RBAC Scope Remediation on Session Reset (`CRITICAL FIX`)
- **Current Defect**: `POST /api/ai/ask` requires `operator`, but `POST /api/ai/reset` requires `admin` (`api/main.py` `L1123`, `L1152`). When an `operator`-role user clicks **New Chat** (`FloatingChatbot.tsx` / `AiIntelligenceView.tsx`), the UI logs `HTTP 403`.
- **Proposed Fix**: Allow `operator` (and `admin`) to reset ONLY sessions owned by their own `ScopedSessionKey` (`principal + token_hash`), reserving `admin`-only scope for a future global/cross-principal flush (`POST /api/ai/admin/purge-sessions`).

### 1.2 Additive Fields on `POST /api/ai/ask` (`200 OK`)
Preserve all existing keys (`question, resolved_query, intent, route, category, requires_business_data, answer, provider_status, verified_metrics, suggested_chart, sql, sql_query, sql_valid, validation_message, data_rows, root_cause_analysis, simulation_results, recommendations, follow_up_suggestions, provenance, insights, timestamp`) and append additive Multi-Agent observability fields:

| Field (`PROPOSED`) | Type | UI / Consumer Purpose |
|---|---|---|
| `trace_id` | `str` | Unique request audit ID (correlates API logs, agent spans, SQL sandbox audits) |
| `orchestration_mode` | `Literal["single_fast_path","multi_agent_parallel","multi_agent_sequential","sql_sandbox"]` | Shows whether fast-path or multi-agent collaboration ran |
| `agents_invoked` | `List[AgentTraceSummary]` | Ordered list `{ agent_name, status, elapsed_ms, domain_scope }` rendered as live agent status pills |
| `calculation_steps` | `List[CalculationStep]` | Formula transparency `{ metric_id, formula, filter_applied, source_table, computed_value }` |
| `ml_confidence_warnings` | `List[ModelCaveat]` | Surfaces Phase 05 readiness tags (`NEEDS_MORE_DATA`, `BASELINE_ONLY`, `EXPERIMENTAL`) cleanly |
| `limitations` | `List[str]` | Explicit data/telemetry gaps encountered across agents |
| `data_source_badges` | `List[str]` | Exact datasets/tables consulted (e.g., `orders.csv`, `orders_engineered.csv`, `RO SQLite Sandbox`) |
| `grounding_verified` | `bool` | Result of `OutputVerifier` numeric reconciliation check |

### 1.3 Proposed Additive Multi-Agent Endpoints (`Optional v2 Surface`)
| Endpoint | Auth Scope | Purpose |
|---|---|---|
| `GET /api/ai/agents/status` | `read` | Returns registered agents, LLM provider health (`Gemini`/`Mock`/`Unconfigured`), MySQL vs CSV tier status, and loaded `kpi_definitions.json` + ML readiness inventory |
| `POST /api/ai/ask` | `operator` | Enhanced multi-agent orchestrator preserving full backwards compatibility; accepts optional `city_filter?: string` matching `HeaderNav` city selector! |
| `POST /api/ai/reset` | `operator` | Principal-scoped session reset (`session_id` isolated by caller token digest) |

---

## 2. Frontend & Dashboard Integration Blueprint (`PROPOSED`)

### 2.1 React [`AiIntelligenceView.tsx`](../../frontend/src/views/AiIntelligenceView.tsx) & [`FloatingChatbot.tsx`](../../frontend/src/components/FloatingChatbot.tsx)
1. **City Filter Alignment**: Pass React's active `selectedCity` (`All | Bengaluru | Chennai | Coimbatore | Hyderabad | Vijayawada`) into `api.askAi(question, sessionId, selectedCity)` so AI responses respect the user's selected city scope (or explicitly note when answering platform-wide).
2. **Agent Collaboration Strip**: Inside assistant message cards (`AiIntelligenceView.tsx` below header pill `L521`), render compact `agents_invoked` pills (`Financial ✓ 18ms`, `Operations ✓ 24ms`, `Decision ✓ 41ms`, or amber `Partial/Timeout` badge).
3. **Calculation Transparency & Data Source Popover**: Add an expandable **"How this was calculated"** accordion displaying `calculation_steps` (`KPI-01` formula + filter + source table) alongside existing `verified_metrics` cards (`L563`) and `provenance` footer (`L814`).
4. **Honest ML Confidence & Limitations Banner**: Whenever `ml_confidence_warnings` or `limitations` is non-empty, render an amber warning box distinguishing verified historical metrics from `EXPERIMENTAL` screening or `NEEDS_MORE_DATA` predictions (`confidence_pct = None` shown as `Heuristic / Uncalibrated`).
5. **Graceful Error / Timeout States**: Wire `ApiErrorState` on `HTTP 401/403` token prompts and `HTTP 503` timeouts cleanly in both `AiIntelligenceView` and `FloatingChatbot` (never silently swallowing `resetAiSession` 403/500 errors).

### 2.2 Streamlit Unification ([`07_Ask_NovaNest.py`](../../streamlit_app/pages/07_Ask_NovaNest.py) & [`09_NovaNest_Command_Center.py`](../../streamlit_app/pages/09_NovaNest_Command_Center.py))
- **Retire Disconnected Page 07 Pipeline**: Replace direct calls to legacy `python/ai/conversational/*` (`L21-27`) and unhardened 5-table SQLite DB (`L56-65`) with unified calls to `MasterOrchestrator.process_query(..., data=data, sqlite_conn=hardened_9table_conn)`.
- **Synchronized UI Sections on Page 07**: Render agent execution badges, calculation formulas, `ml_confidence_warnings` callouts (`render_callout(..., level="warning")`), validated SQL audit badge (`sql_ast.py`), and verified data table.
- **Executive & Command Center (`ExecutiveOverviewView.tsx`, `09_NovaNest_Command_Center.py`)**: Add optional read-only **"Explain Twin Alerts"** quick link forwarding active systemic alert slugs (`operations_delay`, `merchant_churn`) straight into `Ask NovaNest` multi-agent investigation with pre-populated trace context.

