# NOVANEST PHASE 07 — FILE CHANGES
## Advanced Machine Learning Intelligence & Model Optimization

**Document Version:** 1.0.0  
**Phase:** 07  
**Date:** 2026-11-14  

---

### 1. New Files Created

| File Path | Description | Lines of Code |
| :--- | :--- | :--- |
| `python/ml/model_registry.py` | Production model registry, lifecycle governance, SHA-256 lineage, rollback engine, and confidence gating tiers. | ~215 |
| `python/ml/explainability.py` | Explainable AI framework: native TreeSHAP (XGBoost/LightGBM), permutation importance, local prediction explanations, prediction intervals. | ~230 |
| `python/ml/phase07_churn_optimization.py` | Customer Churn optimization pipeline: 6 benchmark models, probability calibration, TreeSHAP, retention segmentation, registry registration. | ~310 |
| `python/ml/phase07_eta_optimization.py` | Delivery ETA optimization pipeline: 6 benchmark models, stratified breakdowns (city, distance, vehicle), 90% prediction intervals, registry registration. | ~340 |
| `python/ml/phase07_demand_optimization.py` | City Demand Forecasting pipeline: 3-fold rolling-origin backtest, 6 benchmark models, WAPE/MASE evaluation, per-city breakdown, registry registration. | ~335 |
| `python/ml/phase07_restaurant_optimization.py` | Restaurant Performance multi-target pipeline: orders, revenue, ratings, expanding mean baselines, prediction intervals, city breakdowns. | ~325 |
| `python/ml/phase07_anomaly_optimization.py` | Anomaly & Fraud Detection pipeline: Dual Z-score/IQR, Isolation Forest, LOF, consensus ensemble, strict fraud policy compliance, risk triggers. | ~260 |
| `tests/test_phase07_ml_optimization.py` | Comprehensive Phase 07 automated test suite covering all 10 validation pillars. | ~310 |
| `models/registry_index.json` | Centralized registry index tracking active and historical model versions. | ~45 |
| `models/customer_churn/churn_metrics_v3.json` | Detailed v3 metrics, benchmark comparisons, retention segments, and caveats. | ~190 |
| `models/customer_churn/model_artifact_v3.joblib` | Serialized calibrated churn pipeline artifact. | Binary |
| `models/customer_churn/prediction_examples_v3.csv` | Scored validation sample predictions with probabilities. | 21 rows |
| `models/customer_churn/metadata_v3.json` | Formal ModelRegistry metadata and dataset SHA-256 hashes. | ~35 |
| `models/eta_prediction/eta_metrics_v3.json` | Detailed v3 ETA metrics, benchmark comparisons, stratified breakdowns, and intervals. | ~230 |
| `models/eta_prediction/model_artifact_v3.joblib` | Serialized HistGradientBoosting ETA pipeline artifact. | Binary |
| `models/eta_prediction/prediction_examples_v3.csv` | Sample ETA predictions with 90% confidence intervals. | 26 rows |
| `models/eta_prediction/metadata_v3.json` | Formal ModelRegistry metadata and dataset SHA-256 hashes. | ~35 |
| `models/demand_forecast/demand_metrics_v3.json` | Detailed v3 demand metrics, rolling backtest, per-city breakdown, WAPE/MASE. | ~210 |
| `models/demand_forecast/model_artifact_v3.joblib` | Serialized HistGradientBoosting demand forecast artifact. | Binary |
| `models/demand_forecast/prediction_examples_v3.csv` | Sample daily demand forecasts vs actuals. | 26 rows |
| `models/demand_forecast/metadata_v3.json` | Formal ModelRegistry metadata and dataset SHA-256 hashes. | ~35 |
| `models/restaurant_prediction/restaurant_metrics_v3.json` | Detailed v3 restaurant multi-target metrics, benchmarks, city breakdowns. | ~260 |
| `models/restaurant_prediction/model_artifact_v3.joblib` | Serialized Ridge L2 multi-target restaurant model artifact. | Binary |
| `models/restaurant_prediction/prediction_examples_v3.csv` | Sample restaurant next-month order predictions with intervals. | 26 rows |
| `models/restaurant_prediction/metadata_v3.json` | Formal ModelRegistry metadata and dataset SHA-256 hashes. | ~35 |
| `models/anomaly_detection/anomaly_metrics_v3.json` | Detailed v3 anomaly & fraud metrics, consensus ensemble, policy compliance. | ~90 |
| `models/anomaly_detection/model_artifact_v3.joblib` | Serialized Isolation Forest & consensus artifact. | Binary |
| `models/anomaly_detection/prediction_examples_v3.csv` | Sample flagged anomalous orders with explainable triggers. | 31 rows |
| `models/anomaly_detection/metadata_v3.json` | Formal ModelRegistry metadata and dataset SHA-256 hashes. | ~35 |
| `NEWCHAGES/PHASE_07/PHASE_PLAN.md` | Phase 07 master execution plan. | ~100 |
| `NEWCHAGES/PHASE_07/IMPLEMENTATION_LOG.md` | Phase 07 milestone-by-milestone implementation chronology. | ~110 |
| `NEWCHAGES/PHASE_07/FILE_CHANGES.md` | Detailed file modifications and additions register. | This file |
| `NEWCHAGES/PHASE_07/TEST_RESULTS.md` | Formal test results, empirical metric comparisons, and audit findings. | ~200 |
| `NEWCHAGES/PHASE_07/PHASE_SUMMARY.md` | High-level executive closure summary and sign-off. | ~150 |

---

### 2. Modified Existing Files

| File Path | Description of Changes |
| :--- | :--- |
| `requirements.txt` | Added pinned dependencies `xgboost>=3.0.0` and `lightgbm>=4.0.0`. |
| `python/ai/agents/base.py` | Added `load_model_active_metadata` and `make_model_caveat_from_registry` connecting agents to ModelRegistry. Exported both in `__all__`. |
| `python/ai/agents/customer_agent.py` | Updated `_build_churn_caveat` to query `make_model_caveat_from_registry("customer_churn", "customer")`. |
| `python/ai/agents/operations_agent.py` | Updated `_build_eta_caveat`, `_build_demand_caveat`, and `_build_anomaly_caveat` to query ModelRegistry dynamically. |
| `python/ai/agents/restaurant_agent.py` | Updated `_build_restaurant_caveat` to query `make_model_caveat_from_registry("restaurant_prediction", "restaurant")`. |
| `tests/run_ci_pipeline.py` | Added `tests.test_phase07_ml_optimization` to AI Platform test suite in CI pipeline. |
| `NEWCHAGES/CHANGELOG.md` | Appended Phase 07 entry documenting ML models, explainability, registry, and gating. |
| `NEWCHAGES/DECISIONS_AND_REASONS.md` | Added ADR-032: Advanced Machine Learning Optimization, Native TreeSHAP, and Honest Confidence Gating. |
| `NEWCHAGES/ROADMAP_STATUS.md` | Updated roadmap marking Phase 07 as COMPLETED. |
| `NEWCHAGES/TESTING_HISTORY.md` | Logged Phase 07 unit, regression, and CI execution results (10/10 passed). |
| `NEWCHAGES/MODIFIED_FILES_REGISTER.md` | Appended modified file entries with justification. |
| `NEWCHAGES/NEW_FILES_REGISTER.md` | Appended new file entries with hash and size tracking. |
