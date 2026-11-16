# PHASE 05.1 — IMPLEMENTATION PLAN
**API Data Contract & Business Logic Alignment**

- **Date**: 2026-11-11
- **Status**: Completed & Validated (Offline + Live HTTP)
- **Prerequisite Audit**: [`NEWCHAGES/PROJECT_AUDIT/PHASE_05_FINAL_CLOSURE_AUDIT.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PROJECT_AUDIT/PHASE_05_FINAL_CLOSURE_AUDIT.md)

---

## Scope & Remediation Objectives
1. **Loader Resilience ([`api/loader.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/loader.py))**:
   - Guard CSV reads against missing or 0-byte empty CSV files (`_safe_read_csv`), and guard `_harmonize_data` against missing base columns.
2. **Backend REST API Contract Alignment ([`api/main.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/main.py))**:
   - Extract shared helpers `_resolve_column`, `_is_high_risk_label`, `_load_model_readiness_summary`, and `_compute_certified_financials`.
   - Reconcile `/api/overview` and `/api/financial/overview` to Phase 04 certified KPIs (`KPI-01` GMV = `₹46,590,125`, `KPI-02` Net Revenue = `₹46,425,992`, `KPI-03` Net AOV = `₹967.33`, `KPI-12` Realized Contribution Margin = `23.59%`, Realized Profit = `₹10,953,031.58`), eliminating non-existent `"commission_amount"` lookups and mixed-denominator per-order ratios.
   - Reconcile `/api/customer/overview` and `/api/customer/list` with `Churn_Risk`, `Churn_Probability`, and `customer_name`, removing `0.15` / `"Low"` / `"Bangalore"` fallbacks.
   - Reconcile `/api/operations/overview` with `demand_forecasts.csv` (`actual_orders`, `predicted_orders`, explicit `has_actual` + `missing_actual_reason` on future horizon), `demand_heatmap.csv`, `riders.csv` + `rider_allocation.csv` (`deficit: None`), and `operational_anomalies.csv` (`Entity_ID`, `Metric`, `Explanation`, removing `"ANM-01"` / `"Delay Spike"` / `"East Hub"`).
   - Remove fabricated `redemptions = 1500` / `roi_multiple = 3.2` on `promotions.csv`, aggregate `revenue_leakage.csv` honestly as `"Investigation Candidate"` (`is_confirmed_loss: False`), and remove hardcoded `92`/`88`/`95` `confidence_pct` from `/api/decision/actions`.
3. **Grounded AI, Streamlit & React UI Consumer Alignment**:
   - Align `python/ai/analyst/data_grounding.py` churn count/rate from stale `412` (`8.2%`) fallback to verified `781` (`15.62%`) from `Churn_Risk`.
   - Align `streamlit_app/pages/01_Executive_Overview.py`, `04_Operations_Intelligence.py`, `05_Financial_Intelligence.py`, `06_Decision_Intelligence.py`, `frontend/src/services/api.ts`, and React view components (`ExecutiveOverviewView.tsx`, `CustomerIntelligenceView.tsx`, `OperationsIntelligenceView.tsx`, `FinancialIntelligenceView.tsx`, `DecisionIntelligenceView.tsx`).
4. **Automated & Live HTTP Regression Coverage**:
   - Update outdated `"4.90"` string checks in `test_floating_chatbot_verification.py`, `test_sidebar_removal.py`, and `test_theme_system.py` to certified `4.66` / `4.64`.
   - Author [`tests/test_api_alignment_phase05_1.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_api_alignment_phase05_1.py) and execute both live HTTP (`http://127.0.0.1:8000`) and full offline regression checks.

