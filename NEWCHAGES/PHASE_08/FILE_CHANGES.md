# NOVANEST PHASE 08 — FILE CHANGES REGISTER
## Prescriptive Business Intelligence & AI Decision Optimization

**Governance ID:** `NOVANEST-PHASE-08-FILES`  
**Phase:** 08  
**Date:** 2026-11-15  

---

### 1. New Production & Intelligence Files Created

| File Path | Component / Purpose | Lines of Code |
| :--- | :--- | :--- |
| `python/decision/prescriptive_contracts.py` | Prescriptive contracts, enums, financial breakdown models, lifecycle state models | 165 |
| `python/decision/customer_retention_intelligence.py` | Multi-factor risk segmentation, discount caps, MOV, customer diagnostic explanation | 320 |
| `python/decision/revenue_optimization.py` | Order-level contribution margin engine, subsidy leakage diagnosis, fee restructuring simulation | 260 |
| `python/decision/restaurant_optimization.py` | Partner performance diagnosis, bottleneck identification, partner-specific action plans | 265 |
| `python/decision/rider_operations_optimization.py` | Fleet workload, order-to-rider ratio, SLA breach mitigation, live telemetry disclaimer | 210 |
| `python/decision/scenario_simulation_engine.py` | Controlled What-If simulation engine across 5 scenarios with projection disclaimers | 230 |
| `python/decision/financial_impact_engine.py` | Standardized financial calculations (ROI, payback period, audited variance) | 85 |
| `python/decision/recommendation_lifecycle.py` | 6-state recommendation lifecycle manager with Human Approval safety enforcement | 230 |
| `python/decision/prescriptive_engine.py` | Unified master prescriptive engine coordinating all recommendation pipelines | 115 |
| `tests/test_phase08_prescriptive_intelligence.py` | Comprehensive 10-point test suite for Phase 08 verification | 435 |

### 2. Modified Existing Files

| File Path | Modifications Made |
| :--- | :--- |
| `python/ai/agents/contracts.py` | Enhanced `ActionRecommendation` with 14 additive fields (`recommendation_id`, `business_problem`, `proposed_action`, `expected_benefit`, `implementation_cost`, `net_financial_impact`, `risk_and_uncertainty`, `confidence_tier`, `measurement_period`, `success_metric`, `lifecycle_status`, `human_approval_required`, `is_simulation_projection`, `realized_outcome`) with field sanitization. |
| `python/decision/next_best_action.py` | Enriched `generate_next_best_actions`, `generate_customer_next_best_actions`, `generate_restaurant_next_best_actions`, and `generate_operational_next_best_actions` with Phase 08 financial calculations and confidence tiers while preserving 100% backward compatibility. |
| `python/ai/agents/decision_agent.py` | Updated `_generate_grounded_nbas` to populate Phase 08 prescriptive fields on `ActionRecommendation`. |
| `python/ai/agents/customer_agent.py` | Updated `ActionRecommendation` generation to populate prescriptive fields and explicit `LOW_EMPIRICAL` churn gating. |
| `python/ai/agents/financial_agent.py` | Updated `ActionRecommendation` generation to populate prescriptive fields and subsidy leakage audit details. |
| `python/ai/agents/operations_agent.py` | Updated `ActionRecommendation` generation to populate prescriptive fields and zone dispatch balancing details. |
| `python/ai/agents/restaurant_agent.py` | Updated `ActionRecommendation` generation to populate prescriptive fields and partner remediation details. |
| `tests/run_ci_pipeline.py` | Added `tests.test_phase08_prescriptive_intelligence` to Stage 2 (AI Platform CI). |
| `NEWCHAGES/CHANGELOG.md` | Recorded Phase 08 implementation and certification. |
| `NEWCHAGES/DECISIONS_AND_REASONS.md` | Added ADR-033: Prescriptive Business Intelligence & Human-in-the-Loop Lifecycle Governance. |
| `NEWCHAGES/ROADMAP_STATUS.md` | Updated Phase 08 status to COMPLETED. |
| `NEWCHAGES/TESTING_HISTORY.md` | Appended Phase 08 test run results (10/10 passed, 35/35 regression passed). |
| `NEWCHAGES/MODIFIED_FILES_REGISTER.md` | Registered all modified files. |
| `NEWCHAGES/NEW_FILES_REGISTER.md` | Registered all new files. |

### 3. Preserved Unmodified Files
- All datasets in `datasets/cleaned/` (`orders.csv`, `customers.csv`, `restaurants.csv`, `riders.csv`, `deliveries.csv`, `menu_items.csv`, `promotions.csv`).
- All MySQL database tables and records (all 304,405 records preserved intact).
- All Phase 07 model artifacts in `models/` (`registry_index.json`, `*_metrics_v3.json`, `model_artifact_v3.joblib`).
- All active host services (FastAPI on :8000, Streamlit on :8501, MySQL on :3306) and Docker containers.
