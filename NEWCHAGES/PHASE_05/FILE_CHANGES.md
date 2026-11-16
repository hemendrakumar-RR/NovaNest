# PHASE 05 — FILE CHANGES REGISTER
**Exact Inventory of Created, Modified & Preserved Assets**

---

## 1. Newly Created Code, Tests & Model Artifacts

| File Path | Category | Purpose |
|---|---|---|
| `python/ml/validation_framework.py` | Core ML Framework | Shared schema auditing, chronological & leakage assertions, deterministic seeding (`42`), regression/classification metrics (`Median AE` included), and versioned artifact saving. |
| `tests/test_ml_models_phase05.py` | Automated Tests | 8-test unit & integration suite covering leakage guards, temporal cutoffs, gap calendar reindexing, untruncated anomaly detection, reproducibility, v1 preservation, and FastAPI `TestClient` parity. |
| `models/customer_churn/` (`churn_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`, `model_artifact.joblib`) | Model 1 Artifacts | Leak-free out-of-time churn evaluation, feature metadata, sample predictions, and serialized `RandomForest_Calibrated` pipeline. |
| `models/eta_prediction/` (`eta_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`, `model_artifact.joblib`) | Model 2 Artifacts | Chronological ETA evaluation, 3-fold CV & city/vehicle error breakdown, and serialized `HistGradientBoosting` pipeline. |
| `models/demand_forecast/` (`demand_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`, `model_artifact.joblib`) | Model 3 Artifacts | Contiguous daily demand backtests, per-city vs pooled metrics, baseline comparisons, and serialized forecaster. |
| `models/restaurant_prediction/` (`restaurant_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`, `model_artifact.joblib`) | Model 4 Artifacts | Real next-month panel evaluation (`2026-05` holdout), 3-month rolling backtest, and serialized `Ridge_L2_Regression` pipeline. |
| `models/anomaly_detection/` (`anomaly_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`) | Model 5 Artifacts | Full-population Z-Score & Tukey IQR bounds, separated statistical vs business-rule audit KPIs, and false-positive attribution summary. |
| `NEWCHAGES/PROJECT_AUDIT/PHASE_05_ML_VALIDATION_REPORT.md` | Master Audit Report | Consolidated enterprise ML validation report comparing v1 leaked metrics vs Phase 05 certified metrics across all 5 models. |
| `NEWCHAGES/PROJECT_AUDIT/PHASE_05_FINAL_CLOSURE_AUDIT.md` | Closure Audit Report | Independent QA & ML readiness closure audit classifying all 5 models (`NEEDS_MORE_DATA` / `BASELINE_ONLY` / `EXPERIMENTAL`), documenting live HTTP payload schema drift, and recording `IMPLEMENTATION_COMPLETE_VALIDATION_PENDING` status. |

## 2. Modified ML Modules & Serving / Grounding Fixes

| File Path | Change Summary | Backward Compatibility |
|---|---|---|
| `python/ai/analyst/data_grounding.py` | Aligned GMV (`order_status != 'Cancelled'`, `₹4.66 Cr`), Net Revenue (`Delivered` `final_amount`, `₹4.64 Cr`), Net AOV (`₹967.33`), Realized Contribution Margin (`23.59%`), non-cancelled city GMV breakdown, and dynamic order count provenance (`49,971 Orders`) with certified Phase 04 KPI definitions. | Preserves `retrieve_grounded_business_context()` contract & AI response schema. |
| `tests/test_universal_ai_suite.py` | Replaced outdated `4.90 Cr` (`49,002,112`) legacy assertion in `test_07_grounded_total_revenue` with dynamic verification against `datasets/cleaned/orders.csv` and `datasets/analytics/kpi_definitions.json` (`KPI-01` & `KPI-02`). | Strengthened test (`15/15` passing); zero weakening. |
| `python/intelligence/customer/churn.py` | Replaced full-timeline `Recency > 90` target with strict pre-cutoff feature extraction + forward inactivity labels; filtered ratings by pre-cutoff `order_id`. | `extract_churn_features()` signature preserved. |
| `python/ml/train_customer_churn.py` | Implemented chronological cohort split (`T_train`, `T_test`), model comparison, calibrated probability scoring, and v2 artifact export. | Preserves `churn_metrics.json` & API/Streamlit CSV columns. |
| `python/intelligence/operations/eta_prediction.py` | Added chronological sort, `vehicle_type`, cyclical time/peak features, restaurant joins, baseline/model comparisons, 3-fold `TimeSeriesSplit`, and residual analysis. | `train_and_predict_eta()` default 2-tuple return preserved. |
| `python/ml/train_eta_model.py` | Updated wrapper passing `restaurants_df` + saving v2 artifacts without overwriting v1 `eta_metrics.json`. | Preserves `eta_metrics.json` & `eta_predictions.csv` contract. |
| `python/intelligence/operations/demand_forecasting.py` | Contiguous calendar grid reindexing, `rolling_std_7` + lags 14/28, baseline comparisons (`lag_1`, `lag_7`, `rolling_28`), expanding backtests, per-city metrics. | `prepare_demand_time_series` & `train_and_forecast_demand` contracts preserved. |
| `python/ml/train_demand_forecast.py` | Updated wrapper saving v2 artifacts without overwriting `demand_metrics.json`. | Preserves `demand_metrics.json` & `demand_forecasts.csv` columns. |
| `python/intelligence/restaurant/performance_prediction.py` | Removed `Predicted_Next_Month_Orders = Total_Orders * uniform(0.9, 1.15)` target leakage; added `build_restaurant_monthly_panel()`. | `extract_restaurant_features()` preserved cleanly without random target leakage. |
| `python/ml/train_restaurant_prediction.py` | Replaced OLS on synthetic target with chronological monthly panel training/backtesting (`Ridge_L2_Regression`). | Preserves `restaurant_metrics.json` & `restaurant_predictions.csv` columns. |
| `python/intelligence/operations/anomaly_detection.py` | Implemented full-population Z-Score & Tukey IQR (`1.5x`/`3.0x`) without `.head(50)`/`.head(100)` truncation or duplicate keys. | `detect_operational_anomalies()` wrapper preserved. |
| `python/intelligence/operations/revenue_leakage.py` | Vectorized 4-rule + statistical hybrid audit with per-restaurant `commission_percentage`, `detection_category`, `false_positive_risk`, `severity`, `record_preserved`. | Preserves `(flagged_df, kpis)` return + API/Streamlit columns (`leakage_amount`, `potential_leakage_amount`, `risk_level`). |
| `python/ml/train_anomaly_model.py` | Updated runner saving `anomaly_metrics_v2.json` & full untruncated operational/financial outputs while preserving historical `anomaly_metrics.json`. | Preserves all 5 operational CSV outputs. |
| `datasets/engineered/` (`customer_churn_predictions.csv`, `eta_predictions.csv`, `demand_forecasts.csv`, `restaurant_predictions.csv`, `operational_anomalies.csv`, `revenue_leakage.csv`, `rider_allocation.csv`, `demand_heatmap.csv`, `operational_alerts.csv`) | Regenerated against certified `49,971`-order cleaned dataset (`2025-06-17..2026-06-17`) replacing stale 50,000-row legacy outputs. | Preserves schemas expected by `api/` and `streamlit_app/`. |

## 3. Strictly Preserved / Untouched Components
- **Datasets**: `datasets/raw/*`, `datasets/cleaned/*`, `datasets/analytics/*`, `datasets/engineered/orders_engineered.csv`, `datasets/engineered/orders_geo_temporal_enriched.csv`
- **Historical ML Baseline Files**: `models/customer_churn/churn_metrics.json`, `models/eta_prediction/eta_metrics.json`, `models/demand_forecast/demand_metrics.json`, `models/restaurant_prediction/restaurant_metrics.json`, `models/anomaly_detection/anomaly_metrics.json`
- **BI & Database**: `powerbi/NovaNest.pbix`, `mysql/*.sql`
- **Historical Governance**: `NEWCHAGES/PHASE_02/`, `NEWCHAGES/PHASE_03/`, `NEWCHAGES/PHASE_04/`, all prior `NEWCHAGES/PROJECT_AUDIT/` reports
