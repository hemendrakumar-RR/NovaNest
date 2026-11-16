# PHASE 05 — TEST & VALIDATION RESULTS
**Executed Commands, Pass/Fail Evidence, Live HTTP Validation & Closure Audit**

- **Final Closure Verification Date**: 2026-11-11
- **Environment**: Python 3.14.4 (`pandas 3.0.5`, `numpy 2.5.2`, `scikit-learn 1.9.1`, `scipy 1.18.1`, `joblib 1.6.0`, `fastapi 0.143.0`, `uvicorn 0.53.0`)

---

## 1. Phase 05 Training Pipeline Runs (Certified Cleaned Dataset: 49,971 Orders)

| Command Executed | Exit Code | Key Verified Outputs |
|---|---:|---|
| `python python/ml/train_customer_churn.py` | `0` | Selected `RandomForest_Calibrated`: `ROC-AUC = 0.5161`, `PR-AUC = 0.0961`, `Accuracy = 0.8858`, `Precision = 0.1364`, `Recall = 0.0632`, `F1 = 0.0864`, `Brier = 0.0781` (`n = 4,999`, positive = `8.54%`); Baseline heuristic `ROC-AUC = 0.5015`. Saved `5,000` scored customers. |
| `python python/ml/train_eta_model.py` | `0` | Selected `HistGradientBoosting`: Holdout `MAE = 11.5186m`, `MedAE = 11.4689m`, `RMSE = 13.3158m`, `R2 = -0.0002` (`n = 9,995`); 3-Fold CV `MAE = 11.5103m`; Mean Baseline `MAE = 11.5162m`. Saved `49,971` ETA predictions. |
| `python python/ml/train_demand_forecast.py` | `0` | Selected `OLS_LinearRegression`: Pooled Holdout `MAE = 4.3889`, `MedAE = 3.7049`, `RMSE = 5.4854`, `MAPE = 18.08%`, `Pooled R2 = 0.7707` (`n = 340`) vs Seasonal Naive `lag_7` (`MAE = 6.2794`, `RMSE = 7.8891`). Within-city `R2`: `-0.0042` to `-0.0337`. Saved `1,760` rows across `5` cities (`14`-day forecast included). |
| `python python/ml/train_restaurant_prediction.py` | `0` | Selected `Ridge_L2_Regression`: `2026-05` Holdout (`n = 1,500`) `MAE = 1.3248`, `MedAE = 1.1069`, `RMSE = 1.6829`, `R2 = -0.0027` vs Global Train Mean `MAE = 1.3351` & Prev Month `MAE = 1.8067`. Saved `1,500` forward restaurant predictions. |
| `python python/ml/train_anomaly_model.py` | `0` | Detected `2,184` deduplicated statistical anomalies (`4.371%`, `0` duplicates, `0` source deletions) + `4,669` financial leakage flags (`₹553,946.31` potential risk, `9.34%`, `0` duplicate `order_id`s, `49,971` preserved). |

---

## 2. Automated Offline Unit & Integration Suites (Verified After Final Edit)

| Suite | Command | Passed | Total | Status | Notes |
|---|---|---:|---:|---|---|
| **Phase 05 ML Suite** | `python tests/test_ml_models_phase05.py` | `8` | `8` | **PASSED (`5.787s`)** | Verifies validation guards, pre-cutoff isolation, ETA chronological sorting/fallbacks, gap calendar reindexing, restaurant non-leakage, untruncated anomaly detection, v1 preservation, and FastAPI `TestClient` endpoints. |
| **Universal AI Suite** | `python tests/test_universal_ai_suite.py` | `15` | `15` | **PASSED (`1.297s`)** | Resolved prior `test_07_grounded_total_revenue` failure after aligning `python/ai/analyst/data_grounding.py` to certified Phase 04 `KPI-01` GMV (`₹4.66 Cr`), `KPI-02` Net Revenue (`₹4.64 Cr`), `KPI-03` Net AOV (`₹967.33`), and `KPI-12` Margin (`23.59%`), and updating `test_07` to assert dynamic CSV/KPI parity. |
| **Phase 04 Analytics Suite** | `python tests/test_analytics.py` | `12` | `12` | **PASSED (`2.801s`)** | Zero regressions in RFM, cohorts, funnel, and KPI cross-validation. |
| **Platform Core Suite** | `python tests/run_all_tests.py` | `3` | `3` | **PASSED (`0.001s`)** | SQL safety validator + empty/missing DataFrame digital twin resilience verified. |
| **Digital Twin Suite** | `python tests/test_digital_twin.py` | `4` | `4` | **PASSED** | `test_twin_state_creation`, `test_health_score`, `test_alert_generation`, `test_dependencies` all passed. |
| **Frontend Core Architecture Suite** | `python tests/test_frontend_rebuild.py` | `6` | `6` | **PASSED (`2.545s`)** | Streamlit config, data loader, SQL safety, recommender, scenario engine, digital twin imports & logic verified. |

---

## 3. Live FastAPI HTTP Validation (`http://127.0.0.1:8000` — Server Started & Stopped)

- **Server Startup**: `python -m uvicorn api.main:app --host 127.0.0.1 --port 8000` (started cleanly, verified, and terminated after tests; `netstat` confirmed zero listener remaining on `:8000`).

| Check | Result | Findings |
|---|---|---|
| `python tests/test_ask_novanest_ai_suite.py` | **14 / 14 PASSED (`3.817s`)** | Live HTTP `/api/ai/ask`, `/api/ai/reset`, `/api/health`, `/api/overview`, `/api/customer/overview`, `/api/restaurant/overview`, `/api/operations/overview`, `/api/financial/overview`, `/api/digital-twin/state`, `/api/decision/actions` all returned HTTP `200`. |
| `tests/test_platform_full_suite.py::test_api_endpoints` | **12 / 12 PASSED** | All 12 FastAPI REST endpoints returned HTTP `200` and required top-level schema keys. |
| Invalid Request & Error Matrix (`7` cases) | **7 / 7 Correct Statuses** | Empty AI question -> `400`; missing `question` JSON field -> `422`; missing customer `/api/customer/360/INVALID_CUST_999` -> `404`; nonexistent route -> `404`; invalid integer query `limit=abc` -> `422`; `DELETE /api/health` -> `405`; invalid simulator float -> `422`. |
| **Semantic Payload Audit Findings** | **Action Needed Before Production** | Inspected JSON payloads exposed API-to-CSV column drift: `/api/customer/overview` returns `churn_distribution: []` (`high_churn_rate_pct: 0.0`) because `api/main.py` expects `churn_risk_level` rather than `Churn_Risk`; `/api/operations/overview` returns `actual: 0.0, forecast: 0.0` (`actual_demand` vs `actual_orders`) and placeholder `"ANM-01" / "Significant delivery delay in East Hub"`; `/api/decision/actions` hardcodes `confidence_pct: 92`. |
