# PHASE 06 — AGENT SPECIFICATIONS

- **Status**: `PROPOSED`
- **Common Base Contract**: Every agent implements `BaseDomainAgent.execute(task: AgentTask, ctx: AgentContext) -> AgentResult` (Pydantic-validated).

---

## 1. Unified Agent I/O Schema (`PROPOSED`)

### `AgentTask` (Master -> Domain Agent)
| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique span identifier linked to request trace ID |
| `target_agent` | `Literal["financial","customer","operations","restaurant","decision"]` | Target domain specialist |
| `sub_query` | `str` | Normalized task instruction scoped to agent domain |
| `entities` | `Dict[str, Any]` | Extracted filters (`city`, `customer_id`, `restaurant_id`, `metric_ids`, `simulation_params`) |
| `execution_mode` | `Literal["analytics","sql","rca","simulate","nba","hybrid"]` | Execution mode requested by planner |
| `allowed_tables` | `FrozenSet[str]` | Least-privilege table ACL subset permitted for this agent |
| `required_scopes` | `FrozenSet[str]` | Caller RBAC scopes (`read`, `operator`, `admin`) |
| `timeout_seconds` | `float` | Hard execution deadline (`default=3.0s`, Decision sim `4.0s`) |

### `AgentResult` (Domain Agent -> Master)
| Field | Type | Description |
|---|---|---|
| `agent_name` | `str` | Identifier + version |
| `status` | `Literal["success","partial","blocked","error","timeout"]` | Honest execution status |
| `facts` | `List[GroundedFact]` | Typed numeric claims (`metric_id`, `label`, `value`, `unit`, `formula_ref`, `source_dataset`, `row_count`) |
| `table_rows` | `List[Dict[str, Any]]` | Bounded rows (`<= 25` UI preview, `<= 100` SQL max) |
| `suggested_chart` | `Optional[ChartSpec]` | Standardized Recharts/Plotly bar/line/pie descriptor |
| `sql_audit` | `Optional[SqlAuditTrace]` | Sanitized SQL, AST validation flag, execution time |
| `recommendations` | `List[ActionRecommendation]` | Empirical interventions (`priority`, `evidence`, `caveat`) — NO unverified % uplift claims |
| `ml_confidence` | `List[ModelCaveat]` | Attached Phase 05 readiness badge (`NEEDS_MORE_DATA`/`BASELINE_ONLY`/`EXPERIMENTAL`, metric summary, `confidence_pct: None` unless empirically supported) |
| `limitations` | `List[str]` | Explicit missing telemetry disclosures (e.g., no promo attribution IDs, no GPS congestion) |
| `elapsed_ms` | `float` | Execution duration for trace telemetry |

---

## 2. Master Orchestrator Agent (`PROPOSED`)

- **Role**: Single coordination brain replacing `if/elif` cascade in [`python/ai/analyst/orchestrator.py`](../../python/ai/analyst/orchestrator.py).
- **Inputs**: Sanitized user query, `session_id`, `AuthPrincipal` (`role`, `scopes`), optional UI `city` filter, conversation history summary.
- **Reused Modules**:
  - [`python/ai/analyst/universal_router.py`](../../python/ai/analyst/universal_router.py) (preserved & expanded fast-path for `GREETING`, `PROGRAMMING`, `CALCULATION`, `PROJECT_KNOWLEDGE`, `GENERAL`).
  - [`python/ai/analyst/universal_engine.py`](../../python/ai/analyst/universal_engine.py) (`compute_calculation`, offline knowledge).
  - [`python/ai/provider/factory.py`](../../python/ai/provider/factory.py) (`GeminiProvider` / `MockAIProvider`).
- **Execution Pipeline**:
  1. **Security & Intent Gate**: Run `InputShield` (prompt injection scan, SQL keyword detection).
  2. **Contextual Resolution**: Expand ambiguous pronouns (*"which city?"*, *"how do we fix it?"*) against principal-scoped `AgentContext`.
  3. **Task Decomposition**:
     - If non-business (`GREETING`, `PROGRAMMING`, `CALCULATION`, `PROJECT_KNOWLEDGE`, pure `GENERAL` conceptual): bypass domain agents (`requires_business_data=False`), return zero business KPI cards.
     - If raw SQL statement: dispatch strictly to AST SQL Sandbox via `NL2SQL` path without fabricated RCA prose.
     - Otherwise extract 1..5 domain sub-tasks (`Wave 1` diagnostics parallelizable; `Wave 2` `DecisionAgent` dependent when *"why + what should we do / simulate"* appears).
  4. **Conflict & Formula Reconciliation**: Ensure all overlapping metrics across agents agree on `KPI-01`..`KPI-16` definitions (`Net Revenue != GMV`). Flag mismatches if Wave 1 partial failures occur.
  5. **Narrative Synthesis & Output Verification**: Pass ONLY structured `AgentResult` summaries to LLM (`GeminiProvider` in `narration-only` mode). `OutputVerifier` checks numeric fidelity before returning JSON.
- **Fallbacks**:
  - Gemini unavailable/timeout/429 -> deterministic markdown composer builds clean executive summary from verified `AgentResult.facts` with `provider_status="error"|"unconfigured"`.
  - Domain agent timeout (`> 3.0s`) -> degrade gracefully to surviving agents + mark timed-out agent `"timeout"` in `agent_execution_status`.

---

## 3. Financial Intelligence Agent (`PROPOSED`)

- **Purpose**: Answer GMV, Net Revenue, Net/Gross AOV, Take Rate, Operating Profit, Contribution Margin, Promotional Catalog, and Financial Leakage Screening inquiries without mixing unconfirmed screening exposure with realized cash flow.
- **Existing Assets Reused**:
  - [`python/analytics/kpi_engine.py`](../../python/analytics/kpi_engine.py) + [`datasets/analytics/kpi_definitions.json`](../../datasets/analytics/kpi_definitions.json) (`KPI-01`, `KPI-02`, `KPI-03`, `KPI-04`, `KPI-12`, `KPI-13`).
  - `_compute_certified_financials()` formula contract from [`api/main.py`](../../api/main.py).
  - [`python/intelligence/operations/revenue_leakage.py`](../../python/intelligence/operations/revenue_leakage.py) (`datasets/engineered/revenue_leakage.csv`).
- **Allowed Tables / Datasets**: `orders`, `orders_engineered`, `payments`, `promotions`, `revenue_leakage.csv`, `restaurants` (city join only).
- **Mandatory Fixes Over Current Code**:
  - Fix unaggregated `4,669`-row leakage iteration (`data_grounding.py` `L290`) by aggregating via `leakage_type` (`potential_leakage_amount`), matching `/api/financial/overview` (`₹553,946.31` total unverified exposure across `4,669` flagged orders).
  - Replace hardcoded `root_cause.py` `L101-128` (`"₹12.50 Lakhs"`, `"18.2%"`) with empirical `orders_engineered.csv` + `revenue_leakage.csv` rollups.
- **Disclosures & Fallbacks**:
  - Always label leakage totals `"Unverified Investigation Candidate (EXPERIMENTAL screening)"` (`is_confirmed_loss: False`) and surface missing promo-funding split & order-level `promo_id` attribution (`promotions.csv` lacks FK in `orders.csv`).

---

## 4. Customer Intelligence Agent (`PROPOSED`)

- **Purpose**: Answer Customer Counts, RFM Segments, Cohort Retention (`KPI-14`, `KPI-15`), Cumulative ARPU (`KPI-16`), Churn Risk Distribution, and VIP Customer 360 lookups (gated by `operator` RBAC scope for PII).
- **Existing Assets Reused**:
  - [`python/intelligence/customer/rfm.py`](../../python/intelligence/customer/rfm.py) & `datasets/analytics/{customer_rfm_segments.csv,rfm_segment_summary.csv}`.
  - [`python/intelligence/customer/cohort.py`](../../python/intelligence/customer/cohort.py) & `datasets/analytics/monthly_cohort_matrix.csv`.
  - [`python/intelligence/customer/clv.py`](../../python/intelligence/customer/clv.py), [`customer_360.py`](../../python/intelligence/customer/customer_360.py).
  - [`datasets/engineered/customer_churn_predictions.csv`](../../datasets/engineered/customer_churn_predictions.csv) (`781` = `15.62%` `High Risk` out of `5,000`).
- **Allowed Tables / Datasets**: `customers`, `orders`, `ratings_reviews`, `customer_churn_predictions.csv`, `customer_rfm_segments.csv`, `monthly_cohort_matrix.csv`.
- **RBAC PII Gate**:
  - `read` callers receive ONLY city/segment aggregates (`Champions`, `High Risk` counts).
  - `operator`/`admin` callers may query individual `customer_id` (`build_customer_360_profile`), still stripping raw contact/credential attributes if present.
- **Mandatory Fixes Over Current Code**:
  - Eliminate stale hardcoded `root_cause.py` `L134` (`"412 accounts (8.2%)"`, `"64 days"`, `"3.1 stars"`); compute empirical Recency/Frequency/Rating differences directly between `Churn_Risk == 'High Risk'` (`781`) vs low-risk cohorts.
- **Confidence Caveat**: Explicitly attach `ModelCaveat(model="customer_churn_v2", readiness="NEEDS_MORE_DATA", metrics="ROC-AUC=0.5161, Recall=0.0632, Precision=0.1364")`.

---

## 5. Operations Intelligence Agent (`PROPOSED`)

- **Purpose**: Analyze Delivery Duration (`KPI-09`: `37.38 min`), SLA Breach Rate (`KPI-08`: `32.26%`), Courier Throughput (`KPI-10`: `12.49` deliv/rider), Demand Forecasts, Demand Heatmap, Rider Allocation, and Operational Anomalies.
- **Existing Assets Reused**:
  - `datasets/engineered/{eta_predictions,demand_forecasts,demand_heatmap,rider_allocation,operational_anomalies,operational_alerts}.csv`.
  - [`python/intelligence/operations/`](../../python/intelligence/operations/) modules (`demand_heatmap.py`, `rider_allocation.py`, `operational_early_warning.py`, `anomaly_detection.py`).
- **Allowed Tables / Datasets**: `deliveries`, `riders`, `orders`, `eta_predictions.csv`, `demand_forecasts.csv`, `demand_heatmap.csv`, `rider_allocation.csv`, `operational_anomalies.csv`, `operational_alerts.csv`.
- **Mandatory Fixes Over Current Code**:
  - Fix `data_grounding.py` `L255-269` `alloc_df` column mismatch: compute actual per-city recommended dispatch allocations & workload tiers using real `rider_allocation.csv` columns (`order_city`, `recommended_rider_id`, `workload_tier`), never falling back to `50/60`.
  - Replace fabricated `root_cause.py` `L33-63` (`"32.4 minutes"`, `"5.8%"`, `"East Hub"`, `"8.9 km vs 4.3 km"`) with empirical correlations from `deliveries.csv` + `orders_engineered.csv` + `operational_anomalies.csv` (`2,184` anomalies).
- **Confidence Caveats**: Attach `eta_v2` (`BASELINE_ONLY`, `MAE=11.52 min`, `R2=-0.0002`, `r(distance,duration)=-0.0029`) and `demand_v2` (`BASELINE_ONLY`, `Pooled R2=0.7707` scale artifact, negative city-level `R2`), plus disclose absent GPS/traffic/weather telemetry.

---

## 6. Restaurant Intelligence Agent (`PROPOSED`)

- **Purpose**: Analyze Merchant Partner Network (`1,500` restaurants), Store Ratings (`avg_rating = 4.25`), Partner Health Score, Risk Categorization (`Critical`/`Watch`/`Healthy`), Cancellation Concentration, Menu & Cuisine Benchmarks, and Throughput (`KPI-11`).
- **Existing Assets Reused**:
  - [`python/intelligence/restaurant/health_score.py`](../../python/intelligence/restaurant/health_score.py), [`risk_detection.py`](../../python/intelligence/restaurant/risk_detection.py), [`benchmarking.py`](../../python/intelligence/restaurant/benchmarking.py), [`early_warning.py`](../../python/intelligence/restaurant/early_warning.py).
  - `datasets/engineered/restaurant_predictions.csv` (`Historical_Monthly_Avg`, `Predicted_Next_Month_Orders`, `Cancellation_Rate`).
- **Allowed Tables / Datasets**: `restaurants`, `menu_items`, `orders`, `ratings_reviews`, `restaurant_predictions.csv`.
- **Mandatory Fixes Over Current Code**:
  - Fix `data_grounding.py` `L201` (`restaurants["rating"]` -> `_resolve_column(restaurants, ["avg_rating", "rating"])`, returning `4.25` instead of fallback `4.2`), and filter Top 5 partner GMV on `order_status != 'Cancelled'` to match `KPI-01`.
- **Confidence Caveats**: Attach `restaurant_v2` (`NEEDS_MORE_DATA` / `RULE_BASED_HEURISTIC`, `MAE=1.3248 orders/mo`, `R2=-0.0027`); state that merchant prep downtime & item stockouts are unrecorded.

---

## 7. Decision Intelligence Agent (`PROPOSED`)

- **Purpose**: Orchestrate What-If Policy Simulations, Digital Twin Systemic Impact Chains, and Evidence-Grounded Next-Best-Actions (NBAs), synthesizing outputs from Wave 1 agents.
- **Existing Assets Reused**:
  - [`python/decision_simulation/scenario_engine.py`](../../python/decision_simulation/scenario_engine.py) + `validation.py` + 4 domain simulators (`financial`, `customer`, `restaurant`, `operations`).
  - [`python/digital_twin/twin_engine.py`](../../python/digital_twin/twin_engine.py) (`build_digital_twin_state`), [`twin_dependencies.py`](../../python/digital_twin/twin_dependencies.py) (`get_structured_impact_chain`).
  - [`python/decision/next_best_action.py`](../../python/decision/next_best_action.py) (`generate_customer_next_best_actions`, `generate_restaurant_next_best_actions`, `generate_operational_next_best_actions`).
- **Mandatory Fixes Over Current Code**:
  - Replace hardcoded `orchestrator.py` `L184-206` NBA templates (`"Preserve ₹12.5L"`, `"confidence": "High"`) with live calls to `next_best_action.py` + `build_digital_twin_state(data)`.
  - Ensure `simulation_agent.py` does NOT silently invent a `+5% demand, -3% subsidy` scenario if user omits parameters—require explicit user lever recognition OR clearly label defaults as `"Baseline Illustrative Preset"`.
  - Fix Streamlit `07_Ask_NovaNest.py` `L169-174` parameter mismatch by calling unified orchestrator using validated keys (`commission_change_pct`, `delivery_fee_change_pct`, etc.).
- **Disclosures**: Attach `scenario_assumptions` (`linear elasticity over observed cohorts`) and enforce `confidence_pct=None` where actions depend on `NEEDS_MORE_DATA` / `EXPERIMENTAL` upstream models.

