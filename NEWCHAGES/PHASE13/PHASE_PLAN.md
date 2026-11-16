# PHASE 13 — NOVANEST ULTIMATE EXECUTIVE DASHBOARD
## MASTER IMPLEMENTATION & ARCHITECTURE PLAN

**Document ID**: `NEWCHAGES/PHASE13/PHASE_PLAN.md`  
**Phase**: Phase 13 — Ultimate Executive Dashboard  
**Status**: APPROVED / ACTIVE  
**Timestamp**: 2026-11-15T15:27:00+05:30  
**Authors**: NovaNest Engineering Team & Master AI Architect  

---

## 1. EXECUTIVE OBJECTIVE

Transform the existing NovaNest dashboard into a premium, enterprise-grade, AI-powered Food Delivery Business Intelligence Dashboard.
The dashboard provides C-suite executives and business leaders with a complete, certified view of:
1. Executive Topline & Operational Vitals (10 Canonical KPIs with previous-period comparison, % change, trend indicators, calculation tooltips, and data freshness telemetry).
2. Financial Intelligence & Unit Economics (Gross vs. Net revenue, daily/weekly/monthly revenue aggregation, profit & contribution margin, payment method distribution, discount & subsidy audits, AOV trends, and city financial performance).
3. Customer Intelligence & Retention Analytics (Acquisition trends, new vs. repeat customer breakdown, cohort retention matrices, CLV distribution, RFM segmentation, `LOW_EMPIRICAL` churn risk tiers, and high-value VIP customer identification).
4. Restaurant Intelligence & Merchant Health (Merchant rankings, order volume vs. revenue contribution, prep duration SLAs, cancellation rates, cuisine benchmarks, and underperforming partner remediation).
5. Rider & Delivery Operations (Total vs. completed deliveries, average delivery duration, late delivery %, fleet utilization, city-wise delivery performance, delivery bottlenecks, and prominent telematics baseline caveats).
6. AI Business Intelligence Center (Dedicated multi-agent intelligence hub integrating Financial, Customer, Operations, Restaurant, and Decision Agents via the Master Orchestrator, complete with supporting evidence, relevant KPIs, data source attribution, confidence tiers, expected business impact, simulation estimates, and mandatory human approval gates).
7. Interactive Global Filters (Synchronized multi-criteria filtering across Date Range, City, Restaurant, Customer Segment, Order Status, and Payment Method with Apply, Reset, Active Badges, and strict backend authorization preservation).

---

## 2. PRE-IMPLEMENTATION AUDIT FINDINGS

### 2.1 React Frontend Architecture Audit
- **Framework**: React 18, TypeScript, Tailwind CSS, Lucide React, Recharts.
- **Application Structure**:
  - `frontend/src/App.tsx`: Main layout holding `HeaderNav`, `Sidebar`, main viewport rendering views based on `activeTab`, `BottomRightDock`, and `FloatingChatbot`.
  - **9 Core Views**:
    1. `ExecutiveOverviewView.tsx` (Executive cockpit, KPIs, hero banner, revenue trend, city breakdown, top restaurants)
    2. `CustomerIntelligenceView.tsx` (Customer KPIs, RFM segmentation, CLV tiers, churn distribution, cohort retention, Customer 360 drawer)
    3. `RestaurantIntelligenceView.tsx` (Health distribution, risk segments, cuisine benchmarks, performance matrix, early warnings)
    4. `OperationsIntelligenceView.tsx` (Deliveries vitals, demand forecasts, demand heatmap, fleet allocation, operational anomalies)
    5. `FinancialIntelligenceView.tsx` (GMV, net revenue, commission/delivery fees, subsidies, realized profit, revenue leakage candidates, promotions)
    6. `AiIntelligenceView.tsx` (Conversational interface with Master Orchestrator, agent trace telemetry, SQL execution, chart rendering)
    7. `DecisionIntelligenceView.tsx` (Prescriptive recommendation action center, lifecycle management, risk tiers, audit trail)
    8. `DecisionSimulatorView.tsx` (What-if scenario modeling, dynamic slider simulations, impact projections)
    9. `CommandCenterView.tsx` (Full-stack system health, container statuses, Prometheus/Grafana links, operational alerts)
- **Identified Frontend Gaps**:
  - Only `selectedCity` is currently in top-level state and passed to `ExecutiveOverviewView`. Other views operate independently without synchronized filters.
  - `KpiCard.tsx` accepts label, value, subtext, delta, deltaPositive, icon, accent, aiPayload, but lacks previous period comparison, % change, trend direction, calculation tooltip, and data freshness badge.
  - Financial view lacks daily/weekly/monthly revenue aggregation toggle, gross vs net comparison chart, payment method distribution pie chart, and AOV trend chart.
  - Customer view lacks visual acquisition trend line, new vs. repeat customer ratio bar, and a dedicated high-value customer identification table.
  - Restaurant view lacks interactive ranking and revenue contribution scatter/bubble chart.
  - Operations view lacks clear completed vs. cancelled deliveries ratio and rider ranking breakdown.

### 2.2 FastAPI Backend Architecture Audit
- **Framework**: FastAPI (Python 3.11/3.14), Uvicorn, Pandas, PyMySQL, SQLAlchemy.
- **Endpoints Available**:
  - `/api/overview`: Computes certified financials via `_compute_certified_financials()`, 30-day revenue trend, city breakdown, top restaurants, Digital Twin vitality score. Currently only accepts `city`.
  - `/api/financial/overview`: Financial KPIs, unit economics, leakage investigation candidates, promotions metadata.
  - `/api/customer/overview`, `/api/customer/list`, `/api/customer/360/{id}`: Customer KPIs, RFM, CLV, churn risk, cohort matrix.
  - `/api/restaurant/overview`: Restaurant KPIs, health score distribution, risk segments, cuisine benchmarks, performance matrix, early warnings.
  - `/api/operations/overview`: Delivery KPIs, demand forecast, demand heatmap, fleet allocation, operational anomalies.
  - `/api/prescriptive/financial-charts`: Contribution margin waterfall, revenue vs. cost breakdown.
  - `/api/prescriptive/recommendations`: Prescriptive recommendation catalog with lifecycle actions (`approve`, `reject`, `start-progress`, `mark-implemented`, `record-outcome`).
  - `/api/ai/ask`, `/api/ai/stream`: Natural language query dispatch through `MasterOrchestrator` across 5 domain agents.
- **Identified Backend Gaps**:
  - `/api/overview` does not return `active_riders` (currently 4,000 riders in database, 500 active in sample) or previous-period comparison metrics for the 10 KPIs.
  - Endpoints need to accept unified query parameters: `start_date`, `end_date`, `restaurant_id`, `customer_segment`, `order_status`, `payment_method`.
  - Previous-period comparison should be dynamically calculated from orders filtered by the preceding matching time interval.

### 2.3 MySQL Database Schema & Dataset Audit
- **Canonical Schema**: `novanest_db` hosted in `novanest-db` container (MySQL 8.0).
- **Canonical Table Counts**:
  - `customers`: 5,000
  - `restaurants`: 1,500
  - `menu_items`: 15,000
  - `riders`: 4,000
  - `payments`: 49,971
  - `deliveries`: 49,971
  - `app_events`: 100,000
  - `promotions`: 200
  - `ratings_reviews`: 28,792
  - `orders`: 49,971
  - **Total 10 Primary Canonical Tables**: Exactly **304,405 records**.
- **Constraint**: Zero data mutation. All source tables and records must remain 100% intact.

### 2.4 Existing AI Agents & Master Orchestrator Audit
- **Domain Agents**:
  1. `FinancialAgent` (`python/ai/agents/financial_agent.py`): P&L, take rate, margins, unit economics.
  2. `CustomerAgent` (`python/ai/agents/customer_agent.py`): RFM, CLV, churn, retention strategies. Preserves `LOW_EMPIRICAL` confidence tier.
  3. `OperationsAgent` (`python/ai/agents/operations_agent.py`): Delivery duration, rider allocation, anomalies. Preserves `BASELINE_ONLY` caveat.
  4. `RestaurantAgent` (`python/ai/agents/restaurant_agent.py`): Health scores, kitchen prep SLAs, rating drops, partner coaching.
  5. `DecisionAgent` (`python/ai/agents/decision_agent.py`): Next-best-action synthesis, multi-objective trade-offs, recommendation prioritization.
- **Orchestration**: `MasterOrchestrator` in `python/ai/agents/master_orchestrator.py` dispatches queries, queries read-only SQLite schema, validates results, generates charts, and attaches prescriptive recommendations.
- **Governance**: Simulated projections must be explicitly flagged with `is_simulation_projection: True`. High-impact business actions require human approval (`HumanApprovalRequiredError`).

---

## 3. CANONICAL KPI DEFINITIONS & FORMULAS MATRIX

| KPI # | KPI Name | Mathematical Formula | Certified Source Function / View | Tooltip Calculation Explanation |
|---|---|---|---|---|
| **KPI-01** | **Gross Merchandise Value (GMV)** | $\sum \text{order\_amount}$ for non-cancelled orders | `_compute_certified_financials()` / `orders` | Total transaction value of all placed non-cancelled orders across merchant partners. |
| **KPI-02** | **Net Revenue** | $\sum \text{final\_amount}$ for delivered orders | `_compute_certified_financials()` / `orders` | Certified net platform inflow collected from customers for successfully completed doorstep deliveries. |
| **KPI-03** | **Total Orders** | $\text{COUNT}(\text{order\_id})$ | `_compute_certified_financials()` / `orders` | Total count of all customer orders placed on the platform regardless of terminal status. |
| **KPI-04** | **Delivered Orders** | $\text{COUNT}(\text{order\_id})$ where `order_status = 'Delivered'` | `_compute_certified_financials()` / `orders` | Total count of customer orders successfully delivered to destination. |
| **KPI-05** | **Average Order Value (AOV)** | $\frac{\text{Net Revenue}}{\text{Delivered Orders}}$ | `_compute_certified_financials()` | Average net platform inflow per delivered order (Gross AOV = GMV / Total Orders). |
| **KPI-06** | **Contribution Margin %** | $\frac{\text{Realized Profit}}{\text{Net Revenue}} \times 100$ | `_compute_certified_financials()` / `orders_engineered` | Realized operating profit as a percentage of net revenue after platform commission, delivery fees, and discount subsidies. |
| **KPI-07** | **Active Customers** | $\text{COUNT}(\text{DISTINCT customer\_id})$ | `api/main.py` / `customers` | Total registered customer accounts with transaction or account activity in the selected period. |
| **KPI-08** | **Active Restaurants** | $\text{COUNT}(\text{DISTINCT restaurant\_id})$ | `api/main.py` / `restaurants` | Total licensed partner kitchens active and accepting customer orders. |
| **KPI-09** | **Active Riders** | $\text{COUNT}(\text{DISTINCT rider\_id})$ active | `api/main.py` / `riders` | Total certified delivery riders active in the platform fulfillment fleet. |
| **KPI-10** | **Delivery Success Rate** | $\frac{\text{Delivered Orders}}{\text{Total Orders}} \times 100$ | `_compute_certified_financials()` | Proportion of placed orders successfully fulfilled and delivered without cancellation. |

---

## 4. PHASE 13 MILESTONE ROADMAP & ARCHITECTURE DESIGN

```
+---------------------------------------------------------------------------------------------------------+
|                                    NOVANEST ULTIMATE EXECUTIVE DASHBOARD                                |
|                                                                                                         |
|  +---------------------------------------------------------------------------------------------------+  |
|  | GLOBAL FILTER BAR: Date Range | City | Restaurant | Customer Segment | Order Status | Payment      |  |
|  | [Apply Filters] [Reset Filters] Active Badges: [City: All] [Status: Delivered]                      |  |
|  +---------------------------------------------------------------------------------------------------+  |
|                                                                                                         |
|  +---------------------------------------------------------------------------------------------------+  |
|  | 10 CANONICAL EXECUTIVE KPI CARDS                                                                  |  |
|  | [GMV] [Net Revenue] [Total Orders] [Delivered Orders] [AOV]                                       |  |
|  | [Contribution Margin] [Active Customers] [Active Restaurants] [Active Riders] [Success Rate]       |  |
|  |  * Current Value  * Prev Period  * Delta %  * Trend (Up/Down)  * Formula Tooltip  * Data Freshness   |  |
|  +---------------------------------------------------------------------------------------------------+  |
|                                                                                                         |
|  +-------------------------------------+  +----------------------------------------------------------+  |
|  | FINANCIAL INTELLIGENCE              |  | CUSTOMER INTELLIGENCE                                    |  |
|  | - Daily/Weekly/Monthly Revenue Trend|  | - Customer Acquisition & Retention Trends                |  |
|  | - Gross vs Net Revenue Comparison   |  | - New vs Repeat Customer Ratio                           |  |
|  | - Payment Method Distribution (Pie) |  | - RFM Segmentation & CLV Tiers                           |  |
|  | - Discount & Subsidy Audit          |  | - LOW_EMPIRICAL Churn Distribution                       |  |
|  | - City Financial Performance        |  | - High-Value VIP Customer Identification Table           |  |
|  +-------------------------------------+  +----------------------------------------------------------+  |
|                                                                                                         |
|  +-------------------------------------+  +----------------------------------------------------------+  |
|  | RESTAURANT INTELLIGENCE             |  | RIDER & DELIVERY OPERATIONS                              |  |
|  | - Merchant Performance Ranking      |  | - Total vs Completed Delivery Volume                     |  |
|  | - Volume vs Revenue Contribution    |  | - Delivery Duration & Late Delivery %                    |  |
|  | - Preparation Time SLAs             |  | - Fleet Utilization by City                              |  |
|  | - Partner Early Warnings            |  | - Telematics Baseline Caveat & Bottlenecks               |  |
|  +-------------------------------------+  +----------------------------------------------------------+  |
|                                                                                                         |
|  +---------------------------------------------------------------------------------------------------+  |
|  | AI BUSINESS INTELLIGENCE CENTER (MASTER ORCHESTRATOR INTEGRATION)                                 |  |
|  | - 5 Domain Agents: Financial, Customer, Operations, Restaurant, Decision Agents                   |  |
|  | - AI-Generated Business Insights Grid (Evidence, KPIs, Data Source, Confidence, Impact, Action)  |  |
|  | - Simulation Projection Badges (is_simulation_projection: True)                                   |  |
|  | - Human Approval Governance Gates (Approve / Reject Recommendation Actions)                       |  |
|  +---------------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------------+
```

### Milestone Schedule:
1. **Milestone 1 — Pre-Implementation Audit & Master Plan** *(Current)*
   - Full audit of React, FastAPI, Streamlit, Power BI, MySQL, and AI Agents.
   - Creation of `NEWCHAGES/PHASE13/PHASE_PLAN.md`.
2. **Milestone 2 & 8 — Backend API & Global Filter Enhancements**
   - Enhance `/api/overview`, `/api/financial/overview`, `/api/customer/overview`, `/api/restaurant/overview`, `/api/operations/overview` with unified filter query parameters (`start_date`, `end_date`, `city`, `restaurant_id`, `customer_segment`, `order_status`, `payment_method`).
   - Implement dynamic previous-period calculation for all 10 KPIs returning `current`, `previous`, `change_pct`, `trend`, `formula`, and `freshness`.
3. **Milestone 2 & 9 — Frontend KPI Cards & Executive Overview Upgrades**
   - Upgrade `KpiCard.tsx` with previous value comparison, percentage change badge, trend icons, interactive formula tooltip, and data freshness telemetry indicator.
   - Build `GlobalFilterBar.tsx` supporting multi-criteria selection, apply/reset, active badge count, and synchronized state.
   - Refactor `ExecutiveOverviewView.tsx` to render all 10 certified KPI cards and integrate global filter synchronization.
4. **Milestone 3 — Financial Intelligence Upgrades**
   - Add daily/weekly/monthly revenue aggregation toggle to `FinancialIntelligenceView.tsx`.
   - Add gross vs net revenue comparison area chart.
   - Add payment method distribution donut/pie chart.
   - Add AOV trend line chart and city financial performance breakdown.
5. **Milestone 4 — Customer Intelligence Upgrades**
   - Add customer acquisition trend chart and new vs. repeat customer distribution to `CustomerIntelligenceView.tsx`.
   - Add high-value VIP customer identification table with direct Contextual AI launch integration.
   - Ensure `LOW_EMPIRICAL` churn tier is prominently badged with model caveats.
6. **Milestone 5 — Restaurant Intelligence Upgrades**
   - Add interactive merchant ranking table with revenue contribution %, order volume, prep duration, and ratings to `RestaurantIntelligenceView.tsx`.
   - Add underperforming merchant remediation action triggers.
7. **Milestone 6 — Rider Operations Upgrades**
   - Add total deliveries vs completed deliveries visual breakdown, average delivery duration trends, late delivery %, and rider fleet utilization by city to `OperationsIntelligenceView.tsx`.
   - Enforce prominent telematics baseline disclaimer (no fake live tracking).
8. **Milestone 7 — AI Business Intelligence Center Upgrades**
   - Build a dedicated AI Insights Center on the Executive Overview integrating all 5 agents (Financial, Customer, Operations, Restaurant, Decision) connected via Master Orchestrator.
   - Display actionable prescriptive recommendations with supporting evidence, relevant KPIs, data source, confidence level, expected impact, and recommended action.
   - Wire simulation projection badges and human approval workflow buttons.
9. **Milestone 10 & 11 — Build Optimization & Verification**
   - Run React production build (`npm run build`) ensuring zero TypeScript errors.
   - Validate API latency and browser rendering performance.
10. **Milestone 12 & 14 — Automated Testing & Visual Screenshots**
    - Author and execute automated test suite `tests/test_phase13_ultimate_dashboard.py` testing live running containers.
    - Capture live browser screenshots of the running dashboard across views and screen sizes.
11. **Milestone 13 — Governance Documentation**
    - Complete `IMPLEMENTATION_LOG.md`, `FILE_CHANGES.md`, `TEST_RESULTS.md`, `PHASE_SUMMARY.md`.
    - Update master registers: `ROADMAP_STATUS.md`, `TESTING_HISTORY.md`, `MODIFIED_FILES_REGISTER.md`, `NEW_FILES_REGISTER.md`, `CHANGELOG.md`, `DECISIONS_AND_REASONS.md` (ADR-039).

---

## 5. REUSABLE COMPONENT & DATA CONTRACT SPECIFICATION

### 5.1 Global Filter State (`GlobalFilterState`)
```typescript
export interface GlobalFilterState {
  dateRange: '7d' | '30d' | '90d' | '1y' | 'all' | 'custom';
  startDate?: string;
  endDate?: string;
  city: string;
  restaurantId?: string;
  customerSegment?: string;
  orderStatus?: string;
  paymentMethod?: string;
}
```

### 5.2 Enhanced KPI Card Props (`KpiCardProps`)
```typescript
export interface KpiCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  previousValue?: string | number;
  percentageChange?: number;
  trendDirection?: 'up' | 'down' | 'neutral';
  calculationTooltip?: string;
  dataFreshness?: string;
  icon?: LucideIcon;
  accent?: 'sapphire' | 'emerald' | 'amber' | 'crimson' | 'cyan';
  aiPayload?: ContextualAIPayload;
}
```

---

## 6. RISK MITIGATION & CONSTRAINTS

1. **Zero Database Mutation**:
   - Risk: Accidental write or table alterations.
   - Mitigation: All queries in data loader and analytics use `SELECT` statements. SQLite connection uses URI `mode=ro`.
2. **Scientific Honesty & Epistemic Boundaries**:
   - Risk: Presenting heuristic churn as ground truth or dispatch simulations as live GPS tracking.
   - Mitigation: Mandatory `LOW_EMPIRICAL` badge on churn predictions and `BASELINE_ONLY` caveat on operations telematics.
3. **Frontend-Backend Authorization**:
   - Risk: Client filters bypassing scope checks.
   - Mitigation: All FastAPI routes maintain strict `require_scope("read")` or `require_scope("operator")` security dependencies.
4. **Git Operations Policy**:
   - Risk: Premature or unapproved git commit/push.
   - Mitigation: Explicit rule: No git commit or push commands without explicit user instruction.
