# Restaurant Next-Month Order Prediction — Phase 05 Validation Report

## 1. Synthetic Target Leakage Removal (v1 vs v2)
- **v1 Defect**: `performance_prediction.py` synthesized `Predicted_Next_Month_Orders = Total_Orders * uniform(0.9, 1.15)` and passed `Total_Orders` as a feature (fake R² = `0.8559`).
- **v2 Remediation**: Evaluated on real observed monthly restaurant counts across complete calendar months (`2025-07 -> 2026-05`), holding out `2026-05` (n=1,500 restaurants) using strictly prior (`< 2026-05`) lag & metadata features.

## 2. Holdout Month Performance (`2026-05`, n=1,500)
| Model / Baseline | MAE (orders/mo) | Median AE | RMSE | R² Score |
|---|---:|---:|---:|---:|
| Baseline_GlobalTrainMean | 1.3351 | 1.256 | 1.6894 | -0.0106 |
| Baseline_RestaurantExpandingMean | 1.3795 | 1.1 | 1.7541 | -0.0894 |
| Baseline_PreviousMonth_Orders | 1.8067 | 1.5 | 2.3321 | -0.9256 |
| Ridge_L2_Regression | 1.3248 | 1.1069 | 1.6829 | -0.0027 |
| RandomForest_Regularized | 1.3317 | 1.1759 | 1.6878 | -0.0086 |
| HistGradientBoosting | 1.3312 | 1.1535 | 1.6871 | -0.0078 |

**Selected Model**: `Ridge_L2_Regression` (Baseline Train Mean MAE = `1.3351`, Selected MAE = `1.3248`, RMSE = `1.6829`).

## 3. Rolling Expanding-Window Backtest
| Target Month | Prior Train Months | Restaurants | MAE | RMSE | R² |
|---|---:|---:|---:|---:|---:|
| 2026-03 | 5 | 1500 | 1.3702 | 1.7276 | -0.0688 |
| 2026-04 | 6 | 1500 | 1.3116 | 1.6338 | -0.0044 |
| 2026-05 | 7 | 1500 | 1.3248 | 1.6829 | -0.0027 |

## 4. Synthetic Data Limitation
Adjacent monthly restaurant order volumes in `datasets/cleaned/orders.csv` exhibit near-zero autocorrelation (`|r| <= 0.02`), bounding any honest leak-free predictor near the Poisson mean (~2.7–2.9 orders/month per restaurant, RMSE ~1.67 orders).
