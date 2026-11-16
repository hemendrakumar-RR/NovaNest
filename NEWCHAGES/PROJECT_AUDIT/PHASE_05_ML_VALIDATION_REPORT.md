# NOVANEST — PHASE 05 ML VALIDATION REPORT
**Enterprise Technical Audit & Comparison Across All 5 Predictive & Risk Models**

- **Report Date**: 2026-11-11
- **Data Basis**: Certified `datasets/cleaned/` (`49,971` orders spanning `2025-06-17` to `2026-06-17`; `5,000` customers; `1,500` restaurants; `4,000` riders; `28,792` reviews)
- **Random Seed**: `42`

---

## 1. Executive Comparison: Legacy v1 vs Phase 05 Certified v2

| Model | Legacy v1 Claim | v1 Defect Diagnosed | Phase 05 Validation Setup | Phase 05 Certified Metrics | Baseline Comparison |
|---|---|---|---|---|---|
| **1. Customer Churn** | `ROC-AUC = 1.0000`, `Acc = 0.9950` (`churn_metrics.json`) | Full-timeline `Is_Churned = (Recency > 90)` + `Recency` input (`0.894` weight) + future ratings leak | Chronological cohorts (`T_train = 2025-12-19`, `T_test = 2026-03-19`, future 90d label, `n = 4,999`, `8.54%` churn) | `RandomForest_Calibrated`: `ROC-AUC = 0.5161`, `PR-AUC = 0.0961`, `Acc = 0.8858`, `Prec = 0.1364`, `Recall = 0.0632`, `Brier = 0.0781` | Pre-cutoff Recency heuristic: `ROC-AUC = 0.5015`, `Acc = 0.8430`, `Brier = 0.1191` |
| **2. Delivery ETA** | `MAE = 10.06m`, `RMSE = 12.13m`, `R2 = 0.3796` (on legacy 50k snapshot) | Omitted `vehicle_type`, unsorted split, missing restaurant features; stale 50k snapshot vs cleaned 49,971 rows (`r = -0.0029`) | Strict time-ordered 80/20 (`Train = 39,976`, `Test = 9,995`) + 3-fold `TimeSeriesSplit` CV | `HistGradientBoosting`: `MAE = 11.5186m`, `MedAE = 11.4689m`, `RMSE = 13.3158m`, `R2 = -0.0002`, `CV MAE = 11.5103m` | Mean Baseline: `MAE = 11.5162m`, `MedAE = 11.3928m`, `RMSE = 13.3146m`; Ridge: `MAE = 11.5208m` |
| **3. Demand Forecast** | `MAE = 4.14`, `RMSE = 5.26`, `R2 = 0.8123` (`demand_metrics.json`) | Labeled OLS `pinv` as Ridge; omitted `rolling_std_7`; no calendar reindex, baselines, or per-city R² split | Contiguous `366`-day city grids, holdout (`2026-04-11..2026-06-17`, `n = 340`) + 3-fold expanding backtest | `OLS_LinearRegression`: `MAE = 4.3889`, `MedAE = 3.7049`, `RMSE = 5.4854`, `MAPE = 18.08%`, `Pooled R2 = 0.7707` (Within-city `R2 = -0.004..-0.034`) | Seasonal Naive (`lag_7`): `MAE = 6.2794`, `RMSE = 7.8891`; Rolling 28D: `MAE = 4.4252`, `RMSE = 5.5577` |
| **4. Restaurant Orders** | `MAE = 2.1534`, `RMSE = 2.5250`, `R2 = 0.8559` (`restaurant_metrics.json`) | Synthesized fake target `Total_Orders * uniform(0.9, 1.15)` and passed `Total_Orders` as feature | Real full-month panel (`2025-07..2026-05`, train `10,500`, holdout `2026-05` `n = 1,500`) + 3-month rolling backtest | `Ridge_L2_Regression`: `MAE = 1.3248`, `MedAE = 1.1069`, `RMSE = 1.6829`, `R2 = -0.0027` | Global Mean Baseline: `MAE = 1.3351`, `RMSE = 1.6894`; Expanding Mean: `MAE = 1.3795`; Prev Month: `MAE = 1.8067` |
| **5. Anomaly & Financial Risk** | `10` anomalies, `14,699` leakage orders (`₹6.22M`) (`anomaly_metrics.json`) | Computed zero IQR bounds; `.head(50)`/`.head(100)` truncation; slow `iterrows()`; 18% flat commission error | Vectorized dual Z-Score + Tukey IQR (`1.5x`/`3.0x`) on all `49,971` orders separated from business rules | `2,184` statistical anomalies (`4.371%`, `0` dups); `4,669` financial risk orders (`₹553,946.31`, `9.34%`, `0` dups, `49,971` preserved) | False-positive risk separated (`Business Rule: 3,035`, `Hybrid: 1,407`, `Statistical: 227`) |

---

## 2. Empirical Data Reality & Honest Limitations
1. **Synthetic Independence Ceiling**: Quantitative audits across `datasets/cleaned/` demonstrate independent random sampling across cleaned tables:
   - Pre-cutoff customer RFM features correlate at `|r| < 0.03` with future 90-day inactivity.
   - `delivery_duration` (`[15, 60]` min Uniform) has `r = -0.0029` with `distance_km` (`[1, 12]` km) and `0` statistical latency anomalies above `Z > 2.5`.
   - Daily city demand autocorrelation is near zero (`|acf(1)| <= 0.04`, `|acf(7)| <= 0.08`), explaining why pooled cross-city `R² = 0.7707` stems from static city volume scale (`Chennai ~41/day` vs `Vijayawada ~14/day`) rather than predictable temporal waves.
   - Adjacent-month restaurant order volume correlations range from `-0.027` to `+0.014`, proving real month-to-month prediction matches a Poisson dispersion limit (`RMSE ~ 1.68` on mean `2.92` orders).
2. **Telemetry Absences Preserved Honestly**: Live traffic delays, road GPS polylines, weather conditions, kitchen prep timestamps, and promo funding split (platform vs merchant funded) are absent from source tables and were intentionally never fabricated.

## 3. Shared Engineering Infrastructure & Reproducibility
- All pipelines execute deterministically (`RANDOM_SEED = 42`) through `python/ml/validation_framework.py`.
- All 5 models store preserved v1 JSON alongside updated `*_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`, and serialized `.joblib` pipelines (Models 1–4).
- Phase 05 automated test suite (`tests/test_ml_models_phase05.py`) passes 8/8 checks covering leakage guards, temporal boundaries, untruncated detection, determinism, and FastAPI endpoint compatibility.

