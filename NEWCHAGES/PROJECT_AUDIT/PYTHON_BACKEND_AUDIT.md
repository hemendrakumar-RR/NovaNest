# NovaNest — Python Backend & Intelligence Subsystem Deep Audit

## 1. Backend Module Architecture
The NovaNest Python backend is organized into specialized domain packages:
```
python/
├── clean_data.py                   # Master Data Sanitizer (Phase 2)
├── feature_engineering.py          # Geo-temporal & Behavioral Features (Phase 2)
├── pipeline_runner.py              # Automated Pipeline Orchestrator (Phase 2)
├── validate_master_data.py         # Automated QA & Schema Inspector (Phase 2)
├── load_mysql.py                   # MySQL Batch Ingestion Utility (Phase 3)
├── analytics/                      # Phase 4 Business KPI Framework
│   ├── kpi_engine.py               # Master KPI Calculation Engine
│   ├── rfm_analysis.py             # Customer RFM Segmentation
│   ├── cohort_analysis.py          # Monthly Retention Matrix
│   ├── funnel_analysis.py          # 5-Stage User Conversion Funnel
│   └── unit_economics.py          # Contribution Margin & Cost Breakdown
├── ai/                             # Artificial Intelligence & Multi-Agent Subsystem
│   ├── analyst/                    # Universal AI Engine, Router, SQL Agent, Sim Agent
│   ├── conversational/             # NL2SQL Generator, Validator, Answer Formatter
│   ├── provider/                   # Google Gemini & MockProvider Factory
│   ├── insights/                   # Automated Business Insights Synthesizer
│   └── recommendations/            # Collaborative, Content & Hybrid Recommenders
├── digital_twin/                   # Digital Twin Simulation Infrastructure
│   ├── platform_twin.py            # Master Platform Orchestrator
│   ├── customer_twin.py            # Customer Behavior & Churn State
│   ├── restaurant_twin.py          # Kitchen SLA & Capacity State
│   ├── operations_twin.py          # Rider Fleet & Delivery State
│   ├── financial_twin.py           # Revenue, Margin & Burn State
│   ├── twin_state.py               # Central State Machine
│   ├── twin_dependencies.py        # Directed Acyclic Graph (DAG) of Twin Impacts
│   └── twin_alerts.py              # Operational Anomaly & SLA Alert Generator
└── ml/                             # Machine Learning Training Pipelines
    ├── train_customer_churn.py     # Logistic Regression Churn Model
    ├── train_demand_forecast.py    # NumPy Ridge Demand Regressor
    ├── train_eta_model.py          # Delivery Duration Predictor
    ├── train_restaurant_prediction.py # Restaurant Revenue & Rating Regressor
    └── train_anomaly_model.py      # Statistical Z-Score & Rule-Based Anomaly Detector
```

## 2. In-Depth Subsystem Evaluations

### A. Data Engineering & Validation (`python/*.py`)
- Standardizes 49,971 records across 10 tables.
- Handles temporal parsing, time-zone alignment (IST UTC+05:30), and geodetic distance calculations via the Haversine formula.
- `validate_master_data.py` performs 11 automated foreign-key relationship checks and verifies 0 orphan records.

### B. Business Analytics Engine (`python/analytics/`)
- Mathematically certified KPI engine producing standardized financial metrics.
- Reconciles GMV (₹46,590,125) vs Net Revenue (₹46,425,992).
- Computes true Contribution Margin (24.54%) across 47,994 completed orders.
- Segments 5,000 customers into 8 RFM tiers ('Champions', 'Loyal', 'At Risk', etc.).
- Computes monthly cohort retention across 12 distinct signup cohorts.

### C. Multi-Agent AI Subsystem (`python/ai/`)
- Features the `UniversalRouter` which classifies incoming natural language queries into 4 intent categories:
  1. `DATA_QUERY`: Dispatched to `SQLAgent` for NL2SQL conversion.
  2. `SIMULATION`: Dispatched to `SimulationAgent` for what-if scenarios.
  3. `ROOT_CAUSE`: Dispatched to `RootCauseAgent` for diagnostic anomaly investigation.
  4. `GENERAL`: Dispatched to `UniversalEngine` for domain intelligence.
- `ProviderFactory` cleanly abstracts LLM backends: dynamically instantiates `GeminiProvider` if `GEMINI_API_KEY` is present, or gracefully falls back to `MockProvider`.

### D. Digital Twin Simulation Engine (`python/digital_twin/`)
- Emulates the end-to-end food delivery operational ecosystem in real time.
- Maintains interconnected state: simulated changes in rider availability immediately impact restaurant dispatch delay and platform-wide delivery SLA compliance.
- Emits real-time alerts when capacity thresholds or ETA boundaries are breached.
