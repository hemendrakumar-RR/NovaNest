# PHASE 05 — ML MODEL RELIABILITY, VALIDATION & PERFORMANCE IMPROVEMENT
**Execution Plan & Leakage Remediation Charter**

- **Execution Date**: 2026-11-11
- **Status**: Completed & Validated
- **Baseline Anchor Commit**: `21b2e2b` (`main`)

---

## 1. Phase Objectives
Audit, remediate, validate, and document all five existing NovaNest ML subsystems without compromising certified Phase 01–04 components (`datasets/raw/`, `datasets/cleaned/`, `datasets/analytics/`, `orders_engineered.csv`, `orders_geo_temporal_enriched.csv`, `powerbi/NovaNest.pbix`, certified SQL scripts, historical v1 `models/*/*_metrics.json`).

## 2. Identified v1 Audit Deficiencies & Planned Fixes
| Model | v1 Audit Finding | Phase 05 Remediation Plan |
|---|---|---|
| **1. Customer Churn** | `Is_Churned = (Recency > 90)` full-timeline target leakage + direct `Recency` input (`weight 0.894`) produced artificial `ROC-AUC = 1.0000`. | Implement chronological observation cutoffs (`train_cutoff = 2025-12-19`, `test_cutoff = 2026-03-19`), filter orders/ratings strictly `<= cutoff_date`, exclude `Recency` via leakage guard, compare calibrated Logistic Regression / RF / HGBR against Recency heuristic baseline. |
| **2. Delivery ETA** | `vehicle_type` ignored in features; linear hour encoding; missing restaurant/order context; unsorted 80/20 split; legacy `eta_metrics.json` built on older 50k snapshot. | Chronological sort by `order_datetime`, merge riders + restaurants (`vehicle_type`, `shift_type`, cyclical sin/cos hour & weekday, meal peaks, distance-to-radius, `cross_city_flag`) with zero fabricated traffic/GPS, 3-fold `TimeSeriesSplit` + 80/20 holdout comparing Mean Baseline / OLS / Ridge / HGBR. |
| **3. Demand Forecast** | Unregularized `pinv` OLS labeled as Ridge; `rolling_std_7` computed but omitted from features; no calendar reindex before shifting; no per-city or baseline comparison. | Contiguous daily calendar grid per city (`0`-fill gaps), include `rolling_std_7`, `lag_14`, `lag_28`, `rolling_14/28`, cyclical sin/cos, compare Seasonal Naive (`lag_7`), Naive `lag_1`, Rolling 28D Mean vs OLS / L2 Ridge / HGBR with 3-fold expanding backtesting and per-city error decomposition. |
| **4. Restaurant Prediction** | Synthetic target leakage: `Predicted_Next_Month_Orders = Total_Orders * uniform(0.9, 1.15)` trained directly on `Total_Orders` (`R2 = 0.8559`). | Build complete monthly panel across full calendar months (`2025-07` to `2026-05`), predict real observed `Actual_Next_Month_Orders` strictly from prior months `< M_t` (`2026-05` holdout + 3-month rolling backtest), excluding lifetime `Total_Orders`. |
| **5. Anomaly & Revenue Risk** | Claimed Z-Score & IQR while computing zero IQR bounds (`0` delivery latency flags); `.head(50)` / `.head(100)` truncation; slow `iterrows()`; 18% flat commission assumption; high false-positive conflation. | Vectorized Z-Score & Tukey IQR (`1.5x` & `3.0x`) without truncation or source deletions; separate Statistical Anomalies from Business Rule cost checks; add false-positive risk, severity, Z-scores, and uniqueness guarantees. |

## 3. Shared Governance & Verification Criteria
1. Reusable validation harness `python/ml/validation_framework.py` (`RANDOM_SEED = 42`, leakage/chronology assertions, unified classification/regression metrics incl. Median AE).
2. Preserve all legacy `models/*/*_metrics.json` v1 reports untouched; record v2 metrics, metadata, feature documentation, prediction examples, validation reports, and serialized artifacts separately.
3. Preserve API and Streamlit column contracts while updating `datasets/engineered/` prediction CSVs to align with `datasets/cleaned/` (`49,971` orders).
4. Add `tests/test_ml_models_phase05.py` verifying zero leakage, determinism, missing-value resilience, no truncation/duplicates, and API endpoint parity.
