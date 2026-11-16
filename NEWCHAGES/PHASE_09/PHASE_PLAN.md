# NOVANEST PHASE 09 — PHASE PLAN
## Executive UI, Recommendation Action Center & Multi-Platform Experience

**Document Reference:** `NEWCHAGES/PHASE_09/PHASE_PLAN.md`  
**Execution Date:** 2026-11-15  
**Author:** Principal AI Systems & UI Architect  
**Status:** COMPLETED & AUDITED  

---

### 1. Phase Objective & Executive Scope

Phase 09 elevates the NovaNest platform from analytical and machine-learning intelligence into an **interactive executive decision-support system**. The objective is to expose the Prescriptive Business Intelligence backend built in Phase 08 across both the **React TypeScript Frontend** and the **Streamlit Operations Console** with 100% mathematical parity, rigorous human-in-the-loop authorization gating, and audited financial tracking.

Zero financial calculations or domain heuristics are duplicated in frontend code; all decision engines, what-if simulations, and lifecycle states flow through unified backend APIs and shared Python decision packages.

---

### 2. Implementation Workstreams

```
+----------------------------------------------------------------------------------------------------+
|                                    NOVANEST PHASE 09 ARCHITECTURE                                  |
+----------------------------------------------------------------------------------------------------+
                                                  │
                 ┌────────────────────────────────┴────────────────────────────────┐
                 ▼                                                                 ▼
      [ React Executive Webapp ]                                      [ Streamlit Operations Portal ]
       - Executive Recommendation Center                               - Executive Recommendation Center
       - Multi-Criteria Filtering                                      - Full Lifecycle Form Controls
       - Contribution Margin Waterfall                                 - Plotly Waterfall & Bar Charts
       - What-If Decision Lab (5 Scenarios)                            - Interactive Sensitivity Sliders
       - Customer 360 Action Cards                                     - Customer 360 & LOW_EMPIRICAL
       - Restaurant 360 Action Plans                                   - Restaurant 360 Partner Plans
       - Rider Fleet Workload Radar                                    - Rider Fleet & Live GPS Caveat
                 │                                                                 │
                 └────────────────────────────────┬────────────────────────────────┘
                                                  ▼
                                     [ FastAPI REST Gateway ]
                         - GET  /api/prescriptive/summary
                         - GET  /api/prescriptive/recommendations
                         - POST /api/prescriptive/recommendations/{id}/approve
                         - POST /api/prescriptive/recommendations/{id}/reject
                         - POST /api/prescriptive/recommendations/{id}/start-progress
                         - POST /api/prescriptive/recommendations/{id}/mark-implemented
                         - POST /api/prescriptive/recommendations/{id}/record-outcome
                         - POST /api/prescriptive/simulate
                         - GET  /api/prescriptive/customer-profile/{id}
                         - GET  /api/prescriptive/restaurant-profile/{id}
                         - GET  /api/prescriptive/rider-fleet-workload
                         - GET  /api/prescriptive/financial-charts
                                                  │
                                                  ▼
                                    [ Shared Decision Kernel ]
                     - RecommendationLifecycleManager (Thread-safe, RBAC Gated)
                     - ScenarioSimulationEngine (5 Controlled Scenarios, is_simulation_projection=True)
                     - CustomerRetentionIntelligence (RFM Segments, Capped Subsidies)
                     - RestaurantOptimizationEngine (Prep Time, Cancel Reduction)
                     - RiderOperationsOptimization (SLA Breaches >45m, Density Balancing)
                     - RevenueOptimizationEngine (Audited Waterfall & Discount Reconciliation)
                                                  │
                                                  ▼
                                 [ MySQL Database (novanest_db) ]
                                   All 304,405 records preserved
```

#### Workstream 1: Financial Reconciliation & Ground-Truth Baseline
- Investigate and document discrepancies identified in Phase 08:
  - **VIP GMV Projections**: Empirical VIP champion cohort size (344 accounts with spend $\ge$ ₹10,000, mean spend ₹12,424.09, mean AOV ₹1,112.08, mean recency 71.8 days).
  - **Promotional Subsidy Totals**: Distinct split between heavy discount orders (>25% discount, 2,449 orders, ₹166,477.00 discounts) and platform-wide delivered discount volume (47,994 orders, ₹2,082,585.00 discounts, platform 60% share ₹1,249,551.00).
  - **Restaurant Cancellations**: Critical partner cohort with >5.0% cancellation rate (511 partners, 1,338 cancellations; 50% recovery yields 669 orders vs 720 orders in macro scenario).
  - **Recommendation ID Consistency**: Enforce canonical deterministic IDs across both web applications and test harnesses (`REC-RET-VIP-001`, `REC-RET-LOY-001`, `REC-REV-DISC-001`, `REC-REV-AOV-001`, `REC-RES-CAN-001`, `REC-RES-QAL-001`, `REC-OPS-SLA-001`, `REC-OPS-FLT-001`).

#### Workstream 2: FastAPI Gateway REST Contracts
- Expose 13 prescriptive REST endpoints in `api/main.py` with fail-closed token authorization and scope enforcement (`read` for inspect endpoints, `operator` or `admin` for lifecycle mutations).
- Implement Pydantic schema validation for approval, rejection, progress, implementation, outcome recording, and controlled what-if simulations.

#### Workstream 3: React Executive UI Upgrade
- `frontend/src/services/api.ts`: Add TypeScript definitions and API client functions matching FastAPI schemas.
- `frontend/src/views/DecisionIntelligenceView.tsx`: Build unified Executive Recommendation Center with KPI summary bar, multi-criteria filtering, lifecycle action modals, and contribution margin waterfall.
- `frontend/src/views/DecisionSimulatorView.tsx`: Upgrade Decision Simulator with 5 canonical scenario archetypes, parameter sensitivity sliders, baseline vs projected comparison tables, Recharts visual comparison, and mandatory projection disclaimers.
- `frontend/src/views/CustomerIntelligenceView.tsx`: Embed Customer 360 Prescriptive Action Card with RFM recency, discount ceiling, minimum order value (MOV), subsidy budget, and explicit `LOW_EMPIRICAL` ML caveats.
- `frontend/src/views/RestaurantIntelligenceView.tsx`: Embed Restaurant 360 Partner Action Plan modal with performance diagnosis, prep buffer benchmarks, and monthly recovered GMV.
- `frontend/src/views/OperationsIntelligenceView.tsx`: Embed Rider Operations Action Center with SLA breach tail analysis (>45m), metro zone workload densities, and explicit live GPS availability caveats.

#### Workstream 4: Streamlit Operations Parity
- `streamlit_app/pages/06_Decision_Intelligence.py`: Transform into Executive Recommendation Center with interactive lifecycle approval, rejection, progress, implementation, and outcome measurement forms connecting to `RecommendationLifecycleManager`.
- `streamlit_app/pages/08_Decision_Simulator.py`: Implement interactive sensitivity sliders and Plotly baseline vs projected bar charts for all 5 canonical scenarios.
- `streamlit_app/pages/02_Customer_Intelligence.py`: Embed Customer 360 prescriptive action card and `LOW_EMPIRICAL` churn warning banner.
- `streamlit_app/pages/03_Restaurant_Intelligence.py`: Embed Restaurant 360 partner diagnosis and actionable directives.
- `streamlit_app/pages/04_Operations_Intelligence.py`: Embed Rider Operations Action Center and live GPS telematics warning callout.

#### Workstream 5: Testing, Safety & Governance
- Build automated test suite `tests/test_phase09_executive_ui_and_parity.py` with 15 granular tests.
- Verify 100% pass rate across regression suites (Phase 08, Phase 07, Phase 06).
- Zero modifications to MySQL database records (all 304,405 records preserved).
- Complete governance documentation in `NEWCHAGES/PHASE_09/` and update master registers.

---

### 3. Deliverables Checklist

| Deliverable | Target File | Status |
| :--- | :--- | :--- |
| Canonical Deterministic IDs | `python/decision/*.py` | Completed |
| 13 Prescriptive REST Endpoints | `api/main.py` | Completed |
| React TypeScript Interfaces & Client | `frontend/src/services/api.ts` | Completed |
| React Executive Recommendation Center | `frontend/src/views/DecisionIntelligenceView.tsx` | Completed |
| React What-If Scenario Simulator | `frontend/src/views/DecisionSimulatorView.tsx` | Completed |
| React Customer 360 Action Card | `frontend/src/views/CustomerIntelligenceView.tsx` | Completed |
| React Restaurant 360 Diagnosis | `frontend/src/views/RestaurantIntelligenceView.tsx` | Completed |
| React Rider Operations Action Center | `frontend/src/views/OperationsIntelligenceView.tsx` | Completed |
| Streamlit Executive Decision Center | `streamlit_app/pages/06_Decision_Intelligence.py` | Completed |
| Streamlit What-If Scenario Simulator | `streamlit_app/pages/08_Decision_Simulator.py` | Completed |
| Streamlit Customer 360 Prescriptive Card | `streamlit_app/pages/02_Customer_Intelligence.py` | Completed |
| Streamlit Restaurant 360 Plan | `streamlit_app/pages/03_Restaurant_Intelligence.py` | Completed |
| Streamlit Rider Telematics Caveat | `streamlit_app/pages/04_Operations_Intelligence.py` | Completed |
| Phase 09 Automated Test Suite | `tests/test_phase09_executive_ui_and_parity.py` | Completed (15/15 Pass) |
| Governance Records & Master Registers | `NEWCHAGES/PHASE_09/`, `NEWCHAGES/*.md` | Completed |
