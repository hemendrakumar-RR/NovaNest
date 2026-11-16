# Customer Churn Prediction — Phase 05 Validation Report

## 1. Leakage Diagnosis (v1 vs v2)
- **v1 Defect**: `Is_Churned = np.where(Recency > 90, 1, 0)` evaluated on full timeline, while `Recency` itself accounted for 89.4% normalized importance — causing artificial **ROC-AUC = 1.0000 / Accuracy = 0.9950**.
- **v2 Remediation**: Strict chronological observation cohorts (`train_cutoff = 2025-12-19 15:35:20`, `test_cutoff = 2026-03-19 15:35:20`). All features computed strictly from `orders <= cutoff_date`; pre-cutoff reviews matched strictly by pre-cutoff `order_id`; label defined over strictly future `(cutoff_date, cutoff_date + 90d]`.

## 2. Held-Out Chronological Test Performance (90-Day Horizon, n=4,999, Churn Rate=8.54%)
| Model | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 Score |
|---|---:|---:|---:|---:|---:|---:|
| Baseline (`Pre_Cutoff_Recency` Heuristic) | 0.5015 | 0.089 | 0.843 | 0.0876 | 0.089 | 0.0883 |
| LogisticRegression_Balanced_L2 | 0.4872 | 0.0828 | 0.4511 | 0.0831 | 0.541 | 0.1441 |
| LogisticRegression_Calibrated_L2 | 0.4856 | 0.0831 | 0.8108 | 0.0711 | 0.1007 | 0.0833 |
| RandomForest_Calibrated | 0.5161 | 0.0961 | 0.8858 | 0.1364 | 0.0632 | 0.0864 |
| HistGradientBoosting_Calibrated | 0.4847 | 0.0843 | 0.837 | 0.0855 | 0.0937 | 0.0894 |

**Selected Model**: `RandomForest_Calibrated` (Confusion Matrix: `{'TP': 27, 'TN': 4401, 'FP': 171, 'FN': 400}`).

## 3. Top Feature Importances
| Feature | Normalized Weight |
|---|---:|
| `Pre_Cutoff_Recency_Days` | 0.1069 |
| `Lookback_AOV` | 0.1008 |
| `Avg_Inter_Order_Gap_Days` | 0.0961 |
| `Lookback_Active_Span_Days` | 0.0939 |
| `Lookback_Monetary` | 0.0932 |
| `Discount_Usage_Pct_Pre` | 0.0912 |
| `Spend_Last_60d` | 0.0779 |
| `Avg_Rating_Given_Pre` | 0.0704 |

## 4. Synthetic Data Limitation Note
NovaNest's cleaned transaction history distributes customer order timestamps independently of loyalty decay patterns, limiting real out-of-time separability near ~0.50-0.55 ROC-AUC once `Recency` leakage is removed. This honest benchmark establishes a production-safe pipeline structure ready for real behavioral telemetry.
