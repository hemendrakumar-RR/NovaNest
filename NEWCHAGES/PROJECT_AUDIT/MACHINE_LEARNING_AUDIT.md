# NovaNest — Machine Learning Infrastructure & Model Catalog Audit

## 1. Machine Learning Portfolio Overview
NovaNest incorporates 5 specialized predictive and statistical models in `models/` trained via `python/ml/`:
1. Customer Churn Prediction
2. Delivery ETA Prediction
3. Demand Forecasting
4. Restaurant Revenue & Rating Prediction
5. Operational & Financial Anomaly Detection

## 2. Model-by-Model Technical Evaluation

### A. Customer Churn Prediction (`models/customer_churn/`)
- **Algorithm**: Logistic Regression (NumPy Engine with gradient descent optimization).
- **Reported Metrics**:
  - Accuracy: 0.9950 (earlier report claimed 0.9997)
  - Precision: 1.0000
  - Recall: 0.9419
  - F1 Score: 0.9701
  - ROC-AUC: 1.0000
- **Feature Weights & Importances**:
  - `Recency`: 0.894 (Dominant feature)
  - `Frequency`: 0.029
  - `Tenure_Days`: 0.017
  - `AOV`: 0.0108
  - `Cancellation_Rate`: 0.009
- **Critical Feature Leakage Analysis**:
  - An ROC-AUC score of 1.0000 indicates severe feature leakage or synthetic label determinism.
  - In the synthetic data generator, churn was deterministically defined if `days_since_last_order > 60`. Because `Recency` directly measures `days_since_last_order`, the model is merely learning the exact threshold rule rather than latent predictive behavioral patterns.
  - **Remediation**: Re-train with historical window cutoff (exclude the last 60 days of activity from features).

### B. Delivery ETA Prediction (`models/eta_prediction/`)
- **Algorithm**: Linear Regression (NumPy OLS).
- **Actual Evaluated Metrics**:
  - MAE: 10.06 minutes
  - RMSE: 12.13 minutes
  - $R^2$ Score: 0.3796
  - Deliveries Evaluated: 50,000
- **Discrepancy Investigation**:
  - Historical reports claimed an $R^2$ of 0.9946 and RMSE of 0.74 minutes.
  - **Root Cause**: The synthetic generator calculated delivery time as $\text{prep\_time} + (\text{distance} / 30 \times 60)$. When an early model was trained purely on distance and prep time, it achieved artificial perfection ($R^2 > 0.99$). When evaluated against realistic variations and noise without live traffic telemetry, the realistic $R^2$ is 0.3796 with 10.06 min MAE. The documentation has been corrected.

### C. City Demand Forecasting (`models/demand_forecast/`)
- **Algorithm**: Pure NumPy OLS Ridge / Linear Regressor with L2 regularization.
- **Evaluated Metrics**:
  - MAE: 4.14 orders/day
  - RMSE: 5.26 orders/day
  - MAPE: 18.06%
  - $R^2$ Score: 0.8123 (Strong predictive power)
- **Features**: Lagged demand (Lag 1, 7, 14, 30 days), rolling 7-day average, day of week indicators.

### D. Restaurant Rating & Revenue Prediction (`models/restaurant_prediction/`)
- **Algorithm**: Multiple Linear Regression (NumPy Engine).
- **Evaluated Metrics**:
  - MAE: 2.15
  - RMSE: 2.52
  - $R^2$ Score: 0.8559
- **Feature Importances**: `Total_Orders` (5.18), `Total_Revenue` (0.65), `AOV` (0.47), `commission_percentage` (0.19).

### E. Financial & Operational Anomaly Detection (`models/anomaly_detection/`)
- **Algorithm**: Statistical Z-Score & Interquartile Range (IQR) bounds combined with multi-factor rule scoring.
- **Detection Results**:
  - Total Flagged Orders: 14,699 (29.4% audit rate).
  - Potential Revenue Leakage Identified: ₹6,216,183.31.
  - Critical Risk Transactions: 7,818.
  - High Risk Transactions: 4,137.
