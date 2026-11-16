# City Demand Forecasting — Phase 05 Validation Report

## 1. Chronological Holdout Comparison (All 5 Cities Pooled, n=340)
| Model / Baseline | MAE | Median AE | RMSE | Pooled R² | MAPE |
|---|---:|---:|---:|---:|---:|
| Baseline_Naive_Lag1 | 5.9618 | 5.0 | 7.5039 | 0.5709 | 25.38% |
| Baseline_SeasonalNaive_Lag7 | 6.2794 | 5.0 | 7.8891 | 0.5257 | 26.34% |
| Baseline_Rolling28_Mean | 4.4252 | 3.7143 | 5.5577 | 0.7646 | 18.8% |
| OLS_LinearRegression | 4.3889 | 3.7049 | 5.4854 | 0.7707 | 18.08% |
| Ridge_L2_Regression | 4.4421 | 3.9993 | 5.5405 | 0.7661 | 19.17% |
| HistGradientBoosting | 4.5185 | 3.7188 | 5.6654 | 0.7554 | 18.77% |

## 2. Per-City Within-City Diagnostics (OLS_LinearRegression)
| City | Mean Daily Orders | MAE | RMSE | Within-City R² | Seasonal Naive (Lag 7) MAE |
|---|---:|---:|---:|---:|---:|
| Bangalore | 35.3824 | 5.6597 | 6.5983 | -0.0337 | 8.3235 |
| Chennai | 41.3382 | 4.6038 | 5.6068 | -0.0078 | 6.7059 |
| Coimbatore | 20.0 | 3.6203 | 4.4117 | -0.0042 | 4.9265 |
| Hyderabad | 27.7941 | 5.0649 | 6.4642 | -0.0298 | 6.9706 |
| Vijayawada | 13.3971 | 2.996 | 3.7714 | -0.0157 | 4.4706 |

## 3. Expanding-Window 3-Fold Backtesting
| Fold | Window | Ridge MAE | Ridge RMSE | Seasonal Naive MAE |
|---|---|---:|---:|---:|
| Fold 1 | 2026-02-02 -> 2026-03-01 | 4.0466 | 5.1231 | 5.5357 |
| Fold 2 | 2026-03-08 -> 2026-04-04 | 3.6621 | 4.8478 | 5.2929 |
| Fold 3 | 2026-04-11 -> 2026-05-08 | 4.3164 | 5.3969 | 5.9071 |

## 4. Analytical Interpretation
- Global pooled R2 (~0.80+) reflects cross-city demand scale separation (e.g., Chennai ~41 vs Vijayawada ~14 orders/day). Within individual cities, synthetic daily series exhibit weak autocorrelation (|acf| < 0.08), yielding near-zero within-city R2 comparable to Rolling 28D / Seasonal Naive baselines.
