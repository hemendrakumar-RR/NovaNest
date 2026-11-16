# Delivery ETA Prediction — Phase 05 Validation Report

## 1. Chronological Validation Setup
- **Split**: Strict time-ordered 80/20 split (`Train = 39,976`, `Test = 9,995`).
- **3-Fold TimeSeriesSplit CV**: Mean MAE = `11.5103 min`, Mean RMSE = `13.2987 min`.

## 2. Model Comparison (Held-Out Chronological Test Set)
| Model | MAE (min) | Median AE (min) | RMSE (min) | R² Score | MAPE |
|---|---:|---:|---:|---:|---:|
| Baseline_HistoricalMean | 11.5162 | 11.3928 | 13.3146 | -0.0 | 38.92% |
| OLS_LinearRegression | 11.5208 | 11.4596 | 13.3196 | -0.0008 | 38.93% |
| Ridge_L2_Regression | 11.5208 | 11.4596 | 13.3196 | -0.0008 | 38.93% |
| HistGradientBoosting | 11.5186 | 11.4689 | 13.3158 | -0.0002 | 38.9% |

**Selected Model**: `HistGradientBoosting` (Holdout SLA: <=5m `21.8%`, 5-15m `43.3%`, >15m `34.9%`).

## 3. Residual Error Breakdown
### By City
| City | Test Deliveries | MAE (min) | Median AE (min) |
|---|---:|---:|---:|
| Bangalore | 2565 | 11.751 | 11.718 |
| Chennai | 2945 | 11.469 | 11.423 |
| Coimbatore | 1380 | 11.411 | 11.376 |
| Hyderabad | 2090 | 11.535 | 11.57 |
| Vijayawada | 1015 | 11.188 | 10.76 |

### By Rider Vehicle Type
| Vehicle Type | Test Deliveries | MAE (min) | Median AE (min) |
|---|---:|---:|---:|
| Bike | 4915 | 11.548 | 11.581 |
| Scooter | 5080 | 11.49 | 11.418 |

## 4. Known Data & Domain Limitations
- Live GPS routes, real-time traffic congestion, weather, and kitchen prep durations are absent from the synthetic dataset; cleaned delivery_duration exhibits near-zero bivariate correlation with distance_km (r ~ -0.003), bounding true R2 near 0.
