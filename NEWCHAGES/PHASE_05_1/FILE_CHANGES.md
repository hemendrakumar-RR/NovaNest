# PHASE 05.1 — FILE CHANGES REGISTER

## 1. Newly Created Files
| File Path | Purpose | Status |
|---|---|---|
| [`tests/test_api_alignment_phase05_1.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_api_alignment_phase05_1.py) | 8-test API data contract, CSV parity, empty CSV resilience & invalid HTTP test suite | Passed (`8/8`) |
| [`NEWCHAGES/PHASE_05_1/PHASE_PLAN.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PHASE_05_1/PHASE_PLAN.md) | Phase 05.1 implementation plan | Created |
| [`NEWCHAGES/PHASE_05_1/IMPLEMENTATION_LOG.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PHASE_05_1/IMPLEMENTATION_LOG.md) | Step-by-step execution log | Created |
| [`NEWCHAGES/PHASE_05_1/FILE_CHANGES.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PHASE_05_1/FILE_CHANGES.md) | File modification & creation manifest | Created |
| [`NEWCHAGES/PHASE_05_1/TEST_RESULTS.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PHASE_05_1/TEST_RESULTS.md) | Complete offline & live HTTP verification output record | Created |
| [`NEWCHAGES/PHASE_05_1/PHASE_SUMMARY.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PHASE_05_1/PHASE_SUMMARY.md) | Phase 05.1 executive closure summary | Created |
| [`NEWCHAGES/PROJECT_AUDIT/PHASE_05_1_API_ALIGNMENT_REPORT.md`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/NEWCHAGES/PROJECT_AUDIT/PHASE_05_1_API_ALIGNMENT_REPORT.md) | Detailed Phase 05.1 technical audit & reconciliation report | Created |

## 2. Modified Existing Files
| File Path | Summary of Changes | Verification |
|---|---|---|
| [`api/loader.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/loader.py) | Added `_safe_read_csv` for 0-byte/missing CSV safety & column existence guard in `_harmonize_data` | `py_compile` + `test_api_alignment_phase05_1.py` |
| [`api/main.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/main.py) | Added certified KPI & column helpers; fixed `/api/overview`, `/api/customer/overview`, `/api/customer/list`, `/api/customer/360/{id}`, `/api/operations/overview`, `/api/financial/overview`, `/api/decision/actions` | Live HTTP + `test_api_alignment_phase05_1.py` (`8/8`) + `test_ml_models_phase05.py` (`8/8`) |
| [`python/ai/analyst/data_grounding.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/data_grounding.py) | Updated churn section to resolve `Churn_Risk` (`781`, `15.62%`) instead of falling back to stale `412` (`8.2%`) | `test_universal_ai_suite.py` (`15/15`) + Live `/api/ai/ask` |
| [`streamlit_app/pages/01_Executive_Overview.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/01_Executive_Overview.py) | Aligned GMV (`!= 'Cancelled'`) & Net AOV (`Delivered`) calculation | `py_compile` |
| [`streamlit_app/pages/04_Operations_Intelligence.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/04_Operations_Intelligence.py) | Corrected demand model description (OLS without weather), `order_city` chart, and unverified statistical anomaly caveat | `py_compile` |
| [`streamlit_app/pages/05_Financial_Intelligence.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/05_Financial_Intelligence.py) | Aligned KPI-01/02/03/12 formulas (`commission_revenue`, `estimated_profit`, Delivered filter), labeled leakage as potential risk candidates, noted promo linkage gap | `py_compile` |
| [`streamlit_app/pages/06_Decision_Intelligence.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/streamlit_app/pages/06_Decision_Intelligence.py) | Added experimental Churn ROC-AUC & promo funding audit caveats in strategic briefing | `py_compile` |
| [`frontend/src/services/api.ts`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/services/api.ts) | Updated TypeScript interfaces for nullable/honest fields & added aligned KPI/readiness properties | `npx tsc --noEmit` (exit `0`) |
| [`frontend/src/views/ExecutiveOverviewView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/ExecutiveOverviewView.tsx) | Aligned executive KPI card labels/subtext with certified KPI-02/03 | `npx tsc --noEmit` (exit `0`) |
| [`frontend/src/views/CustomerIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/CustomerIntelligenceView.tsx) | Supported `"High Risk"`/`"Medium Risk"` labels & replaced `0.12` fallback with `'Unavailable'` | `npx tsc --noEmit` (exit `0`) |
| [`frontend/src/views/OperationsIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/OperationsIntelligenceView.tsx) | Removed hardcoded `50,000` / Prophet-weather claims & safely rendered nullable dispatch deficit fields | `npx tsc --noEmit` (exit `0`) |
| [`frontend/src/views/FinancialIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/FinancialIntelligenceView.tsx) | Aligned waterfall profit pillar, unit economics caption, Potential Risk Exposure label & nullable promotions table | `npx tsc --noEmit` (exit `0`) |
| [`frontend/src/views/DecisionIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/DecisionIntelligenceView.tsx) | Safely displayed unavailable confidence + model readiness status instead of `% Empirical Confidence` | `npx tsc --noEmit` (exit `0`) |
| [`tests/test_floating_chatbot_verification.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_floating_chatbot_verification.py) | Updated obsolete `"4.90"` assertion to certified `"4.66"` & `"4.64"` | Live HTTP (`9/9`) |
| [`tests/test_sidebar_removal.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_sidebar_removal.py) | Updated obsolete `"4.90"` assertion to certified `"4.66"` & `"4.64"` | Live HTTP (`4/4`) |
| [`tests/test_theme_system.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_theme_system.py) | Updated obsolete `"4.90"` assertion to certified `"4.66"` & `"4.64"` | Live HTTP (`8/8`) |

## 3. Protected Assets Verification
- `datasets/raw/*`, `datasets/cleaned/*`, `datasets/analytics/*`, `datasets/engineered/orders_engineered.csv`, `datasets/engineered/orders_geo_temporal_enriched.csv`, `powerbi/NovaNest.pbix`, `mysql/*`, `models/*/*_metrics*.json`, and `NEWCHAGES/PHASE_02..PHASE_05/` remain unmodified.

