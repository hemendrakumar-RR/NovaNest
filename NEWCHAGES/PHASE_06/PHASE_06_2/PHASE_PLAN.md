# NOVANEST PHASE 06.2 — PHASE PLAN
## Domain Intelligence Agents Implementation

**Date**: 2026-11-11  
**Status**: `COMPLETED_VERIFIED`  
**Scope**: Implement the five specialized NovaNest business intelligence domain agents over the Phase 06.1 foundation (`python/ai/agents/`), reusing existing analytics, ML metadata, Digital Twin, simulation, and Next Best Action engines without implementing `MasterOrchestrator` or modifying legacy routes/UI.

---

## Objectives & Deliverables

1. **Shared Domain Agent Infrastructure (`python/ai/agents/base.py` + `python/ai/agents/__init__.py`)**
   - Provide abstract `BaseDomainAgent` enforcing:
     - `AgentRequest` -> `AgentResult` Pydantic v2 contract adherence
     - Principal isolation (`context.assert_principal(request.principal_id)`)
     - RBAC scope authorization (`REQUIRED_SCOPES` vs `context.principal_scopes` / `principal_scopes`)
     - Narrow per-agent SQL table ACLs (`validate_sql_ast` + ephemeral C-level read-only SQLite sandbox)
     - Least-privilege dataset slicing per agent
     - Cooperative cancellation and deadline enforcement
     - Automatic `OutputVerifier` verification over generated `summary` & `narrative`
     - Complete `ExecutionTracer` spans + bounded `AgentContext` history
   - Provide `build_domain_agents()` and `create_default_domain_registry()` registering all 5 agents cleanly into `AgentRegistry` (`OPERATIONAL`, `is_implemented=True`, callable `.execute` handlers).

2. **Task 1 — Financial Intelligence Agent (`python/ai/agents/financial_agent.py`)**
   - GMV (`KPI-01`), Net Revenue (`KPI-02`), Net & Gross AOV (`KPI-03`), Take Rate (`KPI-04`), Contribution Margin (`KPI-12`), Realized Operating Profit (`KPI-13`), monthly revenue trends, city comparisons, payments/promotions context, and unconfirmed revenue leakage screening (`is_confirmed_loss=False`).

3. **Task 2 — Customer Intelligence Agent (`python/ai/agents/customer_agent.py`)**
   - Operator+ RBAC gated RFM segmentation, CLV estimation, Repeat Purchase Rate (`KPI-14`), Month 1 Cohort Retention (`KPI-15`), Historical Realized ARPU (`KPI-16`), scoped Customer 360 lookup (`customer_id` filter), and churn risk indicators paired with mandatory Phase 05 v2 `NEEDS_MORE_DATA` caveat (`ROC-AUC = 0.5161`).

4. **Task 3 — Operations Intelligence Agent (`python/ai/agents/operations_agent.py`)**
   - Delivery latency (`KPI-09`), SLA Breach Rate (`KPI-08`), Rider Efficiency (`KPI-10`) + workload allocation, demand heatmap/hotspots, operational anomaly audit (`2,184`), city comparisons, and explicit `BASELINE_ONLY` / `EXPERIMENTAL` caveats for ETA (`R2 = -0.0002`) and Demand Forecast (`per-city R2 < 0`).

5. **Task 4 — Restaurant Intelligence Agent (`python/ai/agents/restaurant_agent.py`)**
   - Partner throughput (`KPI-11`), verified `avg_rating` (`4.25`) and `ratings_reviews` analysis, revenue contribution, city/cuisine benchmarking, menu mix analysis, risk classification (`Healthy` / `Watch` / `At Risk` / `Critical`), and `NEEDS_MORE_DATA` disclosure for `restaurant_prediction` v2 (`MAE = 1.3248`, `R2 = -0.0027`).

6. **Task 5 — Decision Intelligence Agent (`python/ai/agents/decision_agent.py`)**
   - Operator+ RBAC gated cross-domain synthesis combining `perform_root_cause_analysis`, `execute_conversational_simulation` (`run_scenario`), `build_digital_twin_state` + `get_structured_impact_chain`, and live `next_best_action` generators without fabricating savings or recommendations (`is_confirmed_loss=False`, `HEURISTIC_SIMULATION`).

7. **Independent, Cross-Agent & Security Verification (`tests/test_phase06_2_domain_agents.py`)**
   - Independent tests across all 5 agents plus cross-agent consistency, RBAC, SQL ACLs, missing/empty/bad schemas, concurrency (`ThreadPoolExecutor`), `ExecutionTracer` spans, and full offline/HTTP regression sweeps.

