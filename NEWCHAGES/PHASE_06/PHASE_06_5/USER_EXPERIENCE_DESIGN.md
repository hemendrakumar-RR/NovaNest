# NOVANEST PHASE 06.5 — USER EXPERIENCE DESIGN
## UNIFIED BUSINESS INTELLIGENCE USER EXPERIENCE & MULTI-AGENT VISUALIZATION

- **Phase**: `06.5 — User Experience Design`
- **Date**: `2026-11-13`
- **Status**: `PROPOSED` (Designed for NovaNest Dark Obsidian Design System)

---

## 1. Design System Foundations & Principles

The NovaNest UI adheres to a high-density, command-center aesthetic optimized for enterprise food delivery operations. The design principles for Phase 06.5 are:

1. **Non-Disruptive Contextual Intelligence**: AI is not isolated in a silo; it is woven into every dashboard view as contextual investigation triggers, instant explanations, and deep-dive shortcuts.
2. **Transparent Execution Without Cognitive Clutter**: Surface orchestration stages, selected agents, execution times, and verification outcomes cleanly without exposing internal system prompts or private reasoning.
3. **Rigorous Evidence Grounding**: Visual badges clearly distinguish:
   - **Certified Historical Metrics** (e.g., `KPI-01 GMV ₹4.66 Cr` with emerald verification badge)
   - **Potential Risk Signals** (e.g., `is_confirmed_loss=False` with amber warning indicator)
   - **Experimental ML Baselines** (e.g., ETA / Churn predictions with explicit `ModelCaveat` pill tags)
4. **Resilient Feedback & Recovery**: Informative empty, loading, error, and partial-failure states with instant, one-click `Retry` re-submitting failed prompts.

---

## 2. Multi-Agent Execution Visualization Architecture

To provide executive transparency during complex multi-agent reasoning, the UI introduces a standardized **Multi-Agent Orchestration Telemetry Banner** rendered in both `AiIntelligenceView` and `FloatingChatbot`.

```
+---------------------------------------------------------------------------------------------------------+
| [ORCHESTRATION PIPELINE] Mode: MULTI_AGENT | Status: COMPLETED | Verification: VERIFIED [v]             |
|                                                                                                         |
| Stage 1: Domain Analysis (Parallel)                         Stage 2: Strategic Synthesis                |
| [*] financial_agent   [SUCCESS • 408ms] (orders, payments)  [*] decision_agent [SUCCESS • 1816ms]       |
| [*] operations_agent  [SUCCESS • 46ms]  (deliveries, riders)    • Root-Cause Synthesis: Complete        |
| [*] restaurant_agent  [SUCCESS • 958ms] (restaurants, orders)   • Digital Twin Impact Chain: Computed   |
| [*] customer_agent    [SUCCESS • 497ms] (customers, churn)      • Grounded Next-Best Actions: 4 Emitted |
|                                                                                                         |
| Provenance: CSV File Store (orders: 50,000, deliveries: 50,000, customers: 10,000, restaurants: 1,000) |
+---------------------------------------------------------------------------------------------------------+
```

### Component Specification: `AgentTelemetryCard`
- **Orchestration Status Pill**:
  - `Routing`: Blue pulse (`#38bdf8`) — parsing query semantics and selecting domain experts.
  - `Dispatched (Stage 1)`: Violet pulse (`#a855f7`) — executing parallel domain workers.
  - `Synthesizing (Stage 2)`: Amber pulse (`#f59e0b`) — running DecisionAgent root-cause & simulation.
  - `Verifying`: Cyan pulse (`#06b6d4`) — validating numbers against certified KPI catalog.
  - `Verified / Complete`: Emerald glow (`#10b981`) — all facts verified.
  - `Partial`: Amber border (`#f59e0b`) — some domain agents completed; others degraded cleanly.
  - `Rejected / Blocked`: Crimson border (`#ef4444`) — unbacked claims or prompt injection blocked.
- **Agent Domain Badges**:
  - `financial_agent`: Emerald badge (`bg-emerald-950/60 text-emerald-300 border-emerald-700/40`)
  - `customer_agent`: Sapphire badge (`bg-sky-950/60 text-sky-300 border-sky-700/40`)
  - `operations_agent`: Amber badge (`bg-amber-950/60 text-amber-300 border-amber-700/40`)
  - `restaurant_agent`: Rose badge (`bg-rose-950/60 text-rose-300 border-rose-700/40`)
  - `decision_agent`: Purple badge (`bg-purple-950/60 text-purple-300 border-purple-700/40`)
- **Data Provenance Drawer**:
  - Expandable accordion displaying data sources, table names, row counts, and active filters (e.g., `city='Bengaluru'`).
- **Privacy & Safety Perimeter**:
  - **Forbidden**: Raw system prompts, private chain-of-thought scratchpads, API keys/tokens, unhandled Python tracebacks.
  - **Permitted**: Agent ID, domain, execution time (`elapsed_ms`), execution stage (`Stage 1` vs `Stage 2`), public summary sentence, verified fact count, and provenance badges.

---

## 3. Executive AI Assistant (`AiIntelligenceView`) Design

[`frontend/src/views/AiIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/AiIntelligenceView.tsx) serves as the primary conversational command cockpit.

```
+----------------------------------------------------------------------------------------------------+
| Ask NovaNest AI v2.5 Universal   [Multi-Agent Operational] [CSV Store Active]  [Reset Context]     |
+----------------------------------------------------------------------------------------------------+
| Suggestion Prompts:                                                                                |
| [Analyze my business performance] [Why is profitability declining?] [Which areas need attention?]  |
+----------------------------------------------------------------------------------------------------+
| User: Why is profitability declining?                                                             |
|                                                                                                    |
| NovaNest AI:                                                                                       |
| +------------------------------------------------------------------------------------------------+ |
| | [TELEMETRY] Multi-Agent (4 Agents Invoked • Verified • 2.96s)                      [Details v] | |
| +------------------------------------------------------------------------------------------------+ |
| Executive Briefing:                                                                                |
| Profitability compression is driven primarily by a high delivery SLA breach rate (32.26%) in       |
| Bengaluru, coupled with unconfirmed promotional discount leakage of ₹18.42 L across high-volume   |
| partner restaurants. Gross merchandise value remains strong at ₹4.66 Cr.                           |
|                                                                                                    |
| +------------------------------------------------------------------------------------------------+ |
| | Verified Business Metrics:                                                                     | |
| | [ GMV (KPI-01) ]   [ Net Revenue (KPI-02) ]  [ SLA Breach Rate (KPI-08) ] [ Repeat Rate (14) ]| |
| |   ₹4.66 Cr                ₹4.64 Cr                      32.26%                    67.89%       | |
| |   Source: orders          Source: orders                Source: deliveries        Source: cust | |
| +------------------------------------------------------------------------------------------------+ |
|                                                                                                    |
| [Root-Cause Analysis Accordion] (Observed Facts • Contributing Drivers • Uncertainties)           |
|                                                                                                    |
| [Next Best Actions Priority List]:                                                                 |
| 1. [CRITICAL] Rebalance Rider Zone Allocation in South Corridor (Target: Operations SLA)           |
| 2. [HIGH] Audit Promotional Discount Tiers for 14 Flagged Restaurants (Target: Revenue Leakage)    |
|                                                                                                    |
| [Follow-Up Inquiries]:                                                                             |
| [Which city has highest breach rate?] [Simulate 10% delivery speedup] [Show at-risk restaurants]   |
+----------------------------------------------------------------------------------------------------+
| [ Input Prompt: Type your business question...                                           ] [Send]  |
+----------------------------------------------------------------------------------------------------+
```

### Key UI Features:
1. **Interactive KPI Pill Row**: Emits clickable verified business metrics with KaTeX formatting (`₹4.66 Cr`), delta indicators, and provenance tags.
2. **Interactive Recharts Visualizer**: Dynamically renders `bar`, `line`, `area`, or `pie` charts provided by `ChatResponse.suggested_chart`.
3. **Structured Root-Cause Breakdown**: Tabular division into Observed Empirical Facts, Contributing Factors, and Stated Uncertainties.
4. **Action Recommendation Cards**: Prioritized action cards (Critical, High, Medium) with explicit rationale and backing evidence.
5. **Follow-Up Suggestion Chips**: Context-aware one-click prompt pills that preserve conversational flow.

---

## 4. Global Floating Chatbot Widget (`FloatingChatbot`) Design

[`frontend/src/components/FloatingChatbot.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/FloatingChatbot.tsx) provides instant AI intelligence across all views.

### UX Specifications:
- **Floating Trigger Pill**: Fixed in bottom-right (`z-50`). Shows NovaNest AI avatar, pulsing emerald status dot ("AI Ready"), and subtle tooltip shortcut (`Ctrl + Space`).
- **Collapsible Dialogue Window**:
  - Compact dimensions (`w-[420px] max-h-[620px]`), glassmorphism styling (`bg-obsidian-950/95 backdrop-blur-xl border-slate-800`).
  - Header with current territory indicator (`Territory: Bengaluru`), status badge, minimize button, and "Open Full View" shortcut.
- **Message Stream & Telemetry**:
  - Streamlined `AgentTelemetryBar` showing invoked agent pills (`financial_agent`, `customer_agent`) and verification tag.
  - Formatted markdown response with syntax-highlighted code/SQL and clickable follow-up chips.
  - "Expand in AI View" button transferring active conversation history to `AiIntelligenceView`.

---

## 5. Domain Dashboard Cross-Integration Blueprints

To eliminate Gap 1 (isolated intelligence), all existing domain dashboards receive contextual AI touchpoints that preserve their existing layouts:

### A. Executive Overview (`ExecutiveOverviewView.tsx`)
- **Embedded AI Briefing Accordion**: Positioned below the Hero banner. Auto-generates a 3-bullet executive health summary grounded in current KPIs.
- **KPI Card "Ask AI" Action**: Small sparkle icon on each KPI card (`GMV`, `Net Revenue`, `Total Orders`) launching a pre-populated query (e.g., `"Analyze GMV trends and city contributions"`).

### B. Customer Intelligence (`CustomerIntelligenceView.tsx`)
- **Contextual Action Bar**: Added above RFM segments:
  - Button: `[Sparkle] Investigate Churn with AI` -> Queries: `"Why are customers churning and which segments are at risk?"`
  - Button: `[Users] Analyze VIP Retention Trends` -> Queries: `"Analyze cohort retention and repeat purchase behavior"`
- **Customer 360 Modal Integration**: Inside customer profile modal, add `[AI] Generate Customer Account Briefing` button.

### C. Restaurant Intelligence (`RestaurantIntelligenceView.tsx`)
- **Merchant Risk AI Launcher**:
  - Button: `[Store] Audit High-Risk Restaurants` -> Queries: `"Which restaurants have critical health scores and high cancellation rates?"`
  - Button: `[TrendingUp] Explain Partner Health Scores` -> Queries: `"Explain restaurant health score distribution and benchmark percentiles"`

### D. Operations Intelligence (`OperationsIntelligenceView.tsx`)
- **Logistics Bottleneck AI Launcher**:
  - Button: `[Truck] Diagnose Delivery SLA Breaches` -> Queries: `"Why is delivery SLA breach rate at 32.26% and which zones are worst?"`
  - Button: `[Map] Explain Zone Dispatch Heatmap` -> Queries: `"Analyze rider utilization and zone dispatch bottlenecks"`

### E. Financial Intelligence (`FinancialIntelligenceView.tsx`)
- **P&L Economics AI Launcher**:
  - Button: `[IndianRupee] Screen Promotional Leakage` -> Queries: `"Show promotional discount exposure and potential leakage risk"`
  - Button: `[DollarSign] Compare City Profitability` -> Queries: `"Compare revenue, net AOV, and margin economics across top cities"`

### F. Decision Intelligence (`DecisionIntelligenceView.tsx`)
- **What-If Simulation Launcher**: Direct launch into conversational what-if scenarios (e.g., `"Simulate impact of 5% discount reduction and 2-minute delivery speedup"`).
- **Next-Best-Action Prioritization Assistant**: Explains rationale and empirical data backing each action card.

---

## 6. Truthful Answering & Verification Visual Hierarchy

Every business response must visually enforce the boundary between certified reality and statistical conjecture:

```
[VERIFIED FACT]          --> Emerald Pill: Verified by KPI Engine (e.g., "Net Revenue: ₹4.64 Cr")
[UNCONFIRMED RISK]       --> Amber Pill: Unconfirmed Signal (is_confirmed_loss=False) (e.g., "Leakage Risk: ₹18.42 L")
[EXPERIMENTAL ML MODEL]  --> Slate Pill: Baseline Heuristic (ModelCaveat) (e.g., "ETA Model: Baseline MAE 11.5m")
[STATISTICAL SIMULATION] --> Purple Pill: Projected Scenario (is_confirmed=False) (e.g., "Projected Delta: +₹2.4 L")
```

Under this hierarchy:
- Confirmed metrics display certified KPI IDs (`KPI-01` through `KPI-16`).
- Unconfirmed leakage or churn figures display explicit disclaimer badges: *"Unconfirmed empirical signal; not verified as realized financial loss."*
- Predictive ML outputs display holdout test error metrics directly in a hover tooltip.

