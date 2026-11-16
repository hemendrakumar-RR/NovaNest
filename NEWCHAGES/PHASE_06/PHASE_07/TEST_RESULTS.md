# NOVANEST PHASE 07 — TEST RESULTS & EMPIRICAL METRICS AUDIT
## Advanced Machine Learning Intelligence & Model Optimization

**Document Version:** 1.0.0  
**Phase:** 07  
**Date:** 2026-11-14  
**Test Suite:** `tests/test_phase07_ml_optimization.py`  
**Execution Result:** 10/10 PASSED (100.0% Pass Rate in 11.787s)  

---

### 1. Executive Test Summary

| Test ID | Test Name | Target Pillar | Status | Duration |
| :--- | :--- | :--- | :--- | :--- |
| `test_01` | `test_model_registry_lifecycle_and_rollback` | Model Registry & Versioning | PASS | 0.082s |
| `test_02` | `test_explainability_engine_treeshap_and_local` | Explainable AI & TreeSHAP | PASS | 0.415s |
| `test_03` | `test_customer_churn_leakage_and_metrics` | Model 1: Customer Churn | PASS | 0.045s |
| `test_04` | `test_delivery_eta_dispatch_boundaries_and_breakdowns` | Model 2: Delivery ETA | PASS | 0.038s |
| `test_05` | `test_demand_forecasting_rolling_origin_and_mase` | Model 3: Demand Forecast | PASS | 0.041s |
| `test_06` | `test_restaurant_performance_multitarget` | Model 4: Restaurant Perf | PASS | 0.039s |
| `test_07` | `test_anomaly_detection_fraud_policy_and_consensus` | Model 5: Anomaly & Fraud | PASS | 0.035s |
| `test_08` | `test_agent_confidence_gating` | AI Agent Integration | PASS | 3.250s |
| `test_09` | `test_model_artifact_serialization_and_backward_compatibility` | Artifact Governance | PASS | 0.120s |
| `test_10` | `test_dataset_lineage_and_record_count_integrity` | Data Safety (304,405 rows) | PASS | 7.722s |

---

### 2. Empirical Benchmark Comparisons Across All 5 Models

#### Model 1: Customer Churn Prediction (Holdout N = 4,999)
- **Problem Formulation:** Binary classification predicting whether an active customer places zero orders in the 90 days following observation cutoff.
- **Base Rate:** 8.54% (427 churned out of 4,999 customers).
- **Leakage Audit:** PASS. Strictly zero post-cutoff orders, reviews, or full-timeline recency used in features.

| Candidate Algorithm | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1-Score | Brier Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Heuristic Baseline (Recency > 90d)** | 0.5015 | 0.0869 | 84.32% | 0.0858 | 0.0867 | 0.0862 | 0.1299 |
| **Logistic Regression (L2)** | 0.4887 | 0.0842 | 91.46% | 0.0000 | 0.0000 | 0.0000 | 0.0782 |
| **Random Forest (Calibrated)** | **0.5062** | **0.0950** | 91.46% | 0.0000 | 0.0000 | 0.0000 | **0.0781** |
| **HistGradientBoosting (Calibrated)** | 0.4911 | 0.0825 | 91.46% | 0.0000 | 0.0000 | 0.0000 | 0.0782 |
| **LightGBM (Calibrated)** | 0.4775 | 0.0806 | 91.46% | 0.0000 | 0.0000 | 0.0000 | 0.0782 |
| **XGBoost (Calibrated)** | 0.4861 | 0.0832 | 91.46% | 0.0000 | 0.0000 | 0.0000 | 0.0781 |

*Empirical Finding & Confidence Gating:* When post-cutoff leakages are eliminated, the uniform synthetic customer arrival process yields near-chance discriminative power (ROC-AUC ~ 0.50-0.51). Assigned `LOW_EMPIRICAL` confidence tier. Automated campaigns must use validated RFM rules rather than treating ML probabilities as ground truth.

---

#### Model 2: Delivery ETA Prediction (Holdout N = 9,995)
- **Problem Formulation:** Regression predicting `delivery_duration` (minutes) at order dispatch time.
- **Target Statistics:** Mean = 37.33 minutes, Std = 13.31 minutes.
- **Leakage Audit:** PASS. All post-dispatch features (actual arrival time, delivered status, ratings) eliminated.

| Candidate Algorithm | MAE (min) | Median AE (min) | RMSE (min) | $R^2$ Score | MAPE (%) | Mean Bias (min) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline Mean** | **11.5123** | **11.0000** | 13.3186 | -0.0006 | 38.50% | -0.3325 |
| **Ridge Regression (L2)** | 11.5208 | 11.4596 | 13.3196 | -0.0008 | 38.93% | 0.0544 |
| **Random Forest** | 11.5254 | 11.4614 | 13.3245 | -0.0015 | 38.93% | 0.0435 |
| **HistGradientBoosting** | **11.5158** | 11.4930 | **13.3159** | **-0.0002** | 38.89% | **0.0365** |
| **LightGBM** | 11.5281 | 11.4743 | 13.3346 | -0.0030 | 38.95% | 0.0640 |
| **XGBoost** | 11.5222 | 11.4743 | 13.3314 | -0.0025 | 38.94 | 0.0695 |

*Stratified Error Breakdown:*
- **By City:** Bangalore (MAE 11.75m), Chennai (MAE 11.47m), Coimbatore (MAE 11.41m), Hyderabad (MAE 11.53m), Vijayawada (MAE 11.18m).
- **By Distance Tier:** 0-3km Hyperlocal (MAE 11.35m), 3-7km Mid-range (MAE 11.49m), 7-15km Long-range (MAE 11.61m).
- **By Vehicle Type:** Bike (MAE 11.55m, N=4,915), Scooter (MAE 11.48m, N=5,080).
- **Uncertainty Bounds:** 90% Empirical Prediction Interval = $\text{predicted} \pm 21.9\text{ minutes}$.

---

#### Model 3: City Demand Forecasting (Holdout N = 70 city-days)
- **Problem Formulation:** Daily order volume forecasting per city on a contiguous calendar grid.
- **Validation Methodology:** 3-fold rolling-origin backtest (14-day evaluation windows).

| Model / Benchmark | MAE (orders) | Median AE | RMSE | Pooled $R^2$ | WAPE (%) | MASE | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Seasonal Naive ($lag_7$)** | 7.1714 | 6.0000 | 8.5973 | 0.3730 | 26.31% | 1.000 | Baseline |
| **Rolling Mean (7-day)** | 5.0735 | 4.2857 | 6.2318 | 0.6705 | 18.61% | 0.707 | Rolling Baseline |
| **Ridge Regression (L2)** | 4.6943 | 4.4243 | **5.7168** | **0.7227** | 17.22% | 0.655 | Regularized OLS |
| **HistGradientBoosting** | **4.6878** | **4.1245** | 6.1350 | 0.6807 | **17.20%** | **0.654** | **Selected Best** |
| **LightGBM** | 4.7447 | 4.3969 | 6.2085 | 0.6730 | 17.41% | 0.662 | Tree Ensemble |
| **XGBoost** | 4.8654 | 4.7444 | 6.2687 | 0.6666 | 17.85% | 0.678 | Tree Ensemble |

*Rolling Origin Backtest Folds:*
- **Fold 1:** Model MAE 4.51 vs Seasonal Naive 6.26 (28.0% improvement)
- **Fold 2:** Model MAE 4.31 vs Seasonal Naive 6.24 (31.0% improvement)
- **Fold 3:** Model MAE 4.69 vs Seasonal Naive 7.17 (34.6% improvement)

---

#### Model 4: Restaurant Performance Multi-Target (Holdout N = 1,500 restaurants)
- **Problem Formulation:** Multi-target regression for Next-Month Orders, Next-Month Revenue, Customer Rating.
- **Target 1 Orders:** Mean = 2.92 orders/month, Std = 1.68 orders.

| Algorithm / Baseline | Target | MAE | Median AE | RMSE | $R^2$ Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline Global Mean** | Orders | 1.3351 | 1.2560 | 1.6894 | -0.0106 |
| **Baseline Expanding Mean** | Orders | 1.3795 | 1.1000 | 1.7541 | -0.0894 |
| **Baseline Prev-Month** | Orders | 1.8067 | 1.5000 | 2.3321 | -0.9256 |
| **Ridge Regression (L2)** | **Orders** | **1.3248** | **1.1069** | **1.6829** | **-0.0027** |
| **HistGradientBoosting** | Orders | 1.3326 | 1.1467 | 1.6870 | -0.0076 |
| **XGBoost** | Orders | 1.3305 | 1.1211 | 1.6890 | -0.0101 |
| **Ridge Regression (L2)** | **Revenue** | **₹1,546.93** | **₹1,302.86** | **₹1,983.65** | **0.0142** |
| **Baseline Mean Revenue** | Revenue | ₹1,552.02 | ₹1,302.89 | ₹2,005.00 | -0.0071 |

---

#### Model 5: Anomaly & Fraud Detection (N = 49,971 Orders Audited)
- **Platform GMV Audited:** ₹48,451,925.00
- **Policy Compliance:** Absolute 0 "confirmed fraud" labels. 100% compliant with enterprise risk governance.

| Detection Method | Flagged Orders | Flagged Rate | Risk Category Assigned | Exposure Quantified |
| :--- | :--- | :--- | :--- | :--- |
| **Dual Z-Score / Tukey IQR** | 945 | 1.89% | `STATISTICAL_OUTLIER` | ₹918,204.00 |
| **Isolation Forest (Contamination=3%)** | 1,500 | 3.00% | `STATISTICAL_OUTLIER` | ₹1,453,558.00 |
| **Local Outlier Factor (Sample 10k)** | 300 | 3.00% | `STATISTICAL_OUTLIER` | Subsample check |
| **Consensus Ensemble (Agreement >= 2)** | **628** | **1.26%** | `SUSPECTED_OPERATIONAL_RISK` | **₹519,596.00** |

---

### 3. Verification Sign-Off
- All 10 Phase 07 tests passed cleanly.
- Phase 06.13 regression suite (25 tests) passed with zero defects.
- All 304,405 records preserved without modification.
- All 4 active host and Docker service instances continue uninterrupted.
