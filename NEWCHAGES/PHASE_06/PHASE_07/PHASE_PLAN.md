# NOVANEST PHASE 07 — PHASE PLAN
## Advanced Machine Learning Intelligence & Model Optimization

**Document Version:** 1.0.0  
**Phase:** 07  
**Status:** In Progress  
**Author:** NovaNest ML Engineering Team  
**Date:** 2026-11-14  

---

### 1. Executive Summary & Objectives
Phase 07 upgrades NovaNest's machine learning intelligence from Phase 05's initial baselines to production-grade, highly optimized, explainable ML models. It establishes rigorous data validation, leakage-free feature engineering, multi-algorithm benchmarking (Logistic Regression, Ridge, Random Forest, HistGradientBoosting, LightGBM, XGBoost, Isolation Forest), native TreeSHAP and permutation explainability, versioned model governance via a unified Model Registry, and honest confidence gating across all five domain agents and the Master Orchestrator.

### 2. Core Pillars & Deliverables

#### Pillar 1: Model Registry & Monitoring (`python/ml/model_registry.py`)
- Full lifecycle governance supporting historical v1, Phase 05 v2, and Phase 07 v3 models.
- Cryptographic SHA-256 dataset tracking preventing silent data drift or poisoning.
- Automated rollback mechanism allowing instant version pinning.
- Standardized metadata schema tracking hyperparameter configurations, evaluation metrics, and feature manifests.

#### Pillar 2: Explainable AI & Interpretability (`python/ml/explainability.py`)
- Native TreeSHAP computation utilizing XGBoost and LightGBM C++ engines for zero-overhead local and global feature attribution.
- Scikit-learn Permutation Importance for ensemble and linear models.
- Local instance explanations with baseline expectation, feature contributions, and direction of impact.
- Human-readable business translation transforming SHAP values into actionable operational recommendations.

#### Pillar 3: Model 1 — Customer Churn Prediction (`python/ml/phase07_churn_optimization.py`)
- Strict 90-day observation cutoff with 180-day lookback window preventing temporal and target leakage.
- Benchmarking: Heuristic Baseline vs. Logistic Regression vs. Random Forest vs. HistGradientBoosting vs. LightGBM vs. XGBoost.
- Evaluation metrics: ROC-AUC, PR-AUC, Accuracy, Precision, Recall, F1-Score, Brier score calibration, Confusion Matrix.
- Actionable retention segmentation: High-Value Churn Risk, Discount-Seeking Churn Risk, Low-Engagement Dormant.

#### Pillar 4: Model 2 — Delivery ETA Prediction (`python/ml/phase07_eta_optimization.py`)
- Strict dispatch-time feature boundary eliminating all post-delivery leakage.
- Benchmarking: Mean Baseline vs. Ridge vs. Random Forest vs. HistGradientBoosting vs. LightGBM vs. XGBoost.
- Evaluation metrics: MAE, Median AE, RMSE, R², MAPE, Mean Bias Error.
- Granular error stratifications: by city, distance tier (0-3km, 3-7km, 7-15km, 15km+), and vehicle type (bike, scooter, EV).
- Prediction intervals (90% confidence bounds) providing operations with realistic delivery windows.

#### Pillar 5: Model 3 — Demand Forecasting (`python/ml/phase07_demand_optimization.py`)
- 3-fold rolling-origin walk-forward cross-validation on daily city and restaurant level time series.
- Benchmarking: Seasonal Naive (lag 7) vs. 7-Day Rolling Mean vs. Ridge vs. HistGradientBoosting vs. LightGBM vs. XGBoost.
- Evaluation metrics: MAE, RMSE, WAPE (Weighted Absolute Percentage Error), MASE (Mean Absolute Scaled Error), pooled and within-city R².
- Explainability: Lag decomposition, day-of-week seasonality, and trend attribution.

#### Pillar 6: Model 4 — Restaurant Performance Prediction (`python/ml/phase07_restaurant_optimization.py`)
- Independent multi-target regression modeling: Order Volume, Average Customer Rating, and Monthly Revenue.
- Strictly chronological train/test split (first 10 months train, final 2 months test).
- Benchmarking: Expanding Mean Baseline vs. Ridge vs. HistGradientBoosting vs. LightGBM vs. XGBoost.
- City-level breakdown and prediction uncertainty bounds.

#### Pillar 7: Model 5 — Anomaly & Operational Risk Detection (`python/ml/phase07_anomaly_optimization.py`)
- Explicit taxonomy separation:
  - Statistical Outliers (Dual Z-Score + Tukey IQR, Isolation Forest, Local Outlier Factor).
  - Operational / Financial Risks (rule-based transaction validation).
- Absolute policy prohibiting labeling unverified transactions as "confirmed fraud".
- Financial exposure quantification and multi-factor risk attribution.

#### Pillar 8: Honest Confidence Gating in AI Agents
- Agents (Customer, Operations, Restaurant, Decision, Orchestrator) must query the Model Registry.
- Mandatory confidence gating: when empirical R² or ROC-AUC indicates synthetic data limitations, agents must transparently disclose model bounds and fallback to descriptive baselines rather than hallucinating high-confidence predictions.

#### Pillar 9: Automated Regression & Validation Suite (`tests/test_phase07_ml_optimization.py`)
- 10+ comprehensive automated tests covering leakage, registration, explainability, metric bounds, rollback, and agent gating.

---

### 3. Execution Schedule & Milestones
- **Step 1:** Model Registry & Versioning Infrastructure (`python/ml/model_registry.py`)
- **Step 2:** Explainable AI Framework (`python/ml/explainability.py`)
- **Step 3:** Model 1 Optimization (Customer Churn)
- **Step 4:** Model 2 Optimization (Delivery ETA)
- **Step 5:** Model 3 Optimization (Demand Forecasting)
- **Step 6:** Model 4 Optimization (Restaurant Performance)
- **Step 7:** Model 5 Optimization (Anomaly & Risk Detection)
- **Step 8:** Agent Integration & Confidence Gating
- **Step 9:** Comprehensive Test Suite & Execution
- **Step 10:** Governance Documentation & Master Registers Update
