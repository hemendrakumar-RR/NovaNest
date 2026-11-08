# NovaNest — Artificial Intelligence & Digital Twin Architecture Audit

## 1. Multi-Agent AI Architecture (`python/ai/`)
NovaNest implements a hierarchical multi-agent decision support system:

```
User Query (Natural Language)
             │
             ▼
    [UniversalRouter]
             │
   ┌─────────┼─────────┬─────────┐
   ▼         ▼         ▼         ▼
[SQLAgent] [SimAgent] [RootCause] [UniversalEngine]
   │         │         │         │
   └─────────┼─────────┴─────────┘
             ▼
    [ProviderFactory]
             │
   ┌─────────┴─────────┐
   ▼                   ▼
[Gemini 1.5]     [MockProvider (Fallback)]
```

### A. Core Agent Roles
1. `UniversalRouter`: Intent classification via regex and semantic keyword clustering. Directs queries to the appropriate agent.
2. `SQLAgent` (`conversational/nl_to_sql.py`): Converts natural language questions into executable MySQL queries.
3. `SQLValidator` (`conversational/sql_validator.py`): AST-based syntax and security validator. Rejects non-SELECT queries.
4. `SimulationAgent` (`analyst/simulation_agent.py`): Translates what-if queries into parameter adjustments for the decision simulator.
5. `RootCauseAgent` (`analyst/root_cause.py`): Investigates KPI dips (e.g., "Why did revenue drop in Hyderabad?") by analyzing cancellation rates and delivery delays.
6. `UniversalEngine` (`analyst/universal_engine.py`): High-level conversational synthesizer combining responses into executive summaries.

### B. LLM Provider Layer (`python/ai/provider/`)
- `BaseProvider`: Abstract base class specifying `generate_text()`, `generate_sql()`, and `chat()`.
- `GeminiProvider`: Google GenAI SDK integration (`google-generativeai`) targeting `gemini-1.5-pro` and `gemini-1.5-flash`.
- `MockProvider`: Pure deterministic fallback engine containing 150+ pre-mapped query templates and rule-based heuristics. Guarantees 100% offline availability without an API key.

## 2. Recommendation Engines (`python/ai/recommendations/`)
- `CollaborativeFilteringRecommender`: Item-item and user-user cosine similarity matrix computed across 49,971 order histories.
- `ContentBasedRecommender`: Cuisine, price point, and dietary preference vector matching.
- `HybridRecommender`: Weighted ensemble combining collaborative interaction weights (60%) with content attributes (40%).

## 3. Digital Twin Architecture (`python/digital_twin/`)
The NovaNest Digital Twin emulates the interconnected food delivery platform:

| Twin Component | Managed State Attributes | Primary Risk Triggers |
|---|---|---|
| `CustomerTwin` | Churn risk index, order frequency, price sensitivity | Inactivity > 30 days, high cancellation rate |
| `RestaurantTwin` | Kitchen queue depth, prep delay, cancellation rate | Prep time > 25 mins, order backlog > 15 |
| `OperationsTwin` | Active rider density, delivery SLA adherence, fuel burn | Available riders < 5 per zone, SLA breach > 15% |
| `FinancialTwin` | Real-time burn rate, commission yield, margin health | Contribution margin < 20%, high refund spikes |
| `PlatformTwin` | Master orchestrator harmonizing cross-twin state | Systemic operational bottlenecks |

- **State Propagation (`twin_dependencies.py`)**: Models ripple effects—a rainstorm delay in `OperationsTwin` increases customer churn probability in `CustomerTwin` and dampens commission revenue in `FinancialTwin`.
- **Alert Generation (`twin_alerts.py`)**: Automatically fires operational alerts when metrics exceed 2 standard deviations.
