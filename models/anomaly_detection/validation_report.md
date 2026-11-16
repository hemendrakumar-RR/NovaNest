# Operational Anomaly & Financial Risk Audit — Phase 05 Validation Report

## 1. Key Remediation Summary (v1 vs v2)
- Implemented true **Z-Score + Tukey IQR (1.5x & 3.0x)** checks on `49,971` orders without `.head(50)` / `.head(100)` truncation (`duplicate_anomaly_keys = 0`, zero source deletions).
- Separated **Statistical Anomalies** (`2,184` unique entity/metric flags, `4.371%` of audited orders) from **Business Rule Cost Audits** (`4,669` orders, `9.34%`, duplicate order flags = `0`).

## 2. Full-Population Statistical Bounds Audit
| Metric | Mean | Std | Tukey 1.5x IQR Bounds | Z > 3.0 Count | IQR 1.5x Outliers |
|---|---:|---:|---|---:|---:|
| `delivery_duration` | 37.3807 | 13.2728 | [-8.5, 83.5] | 0 | 0 |
| `distance_km` | 6.4602 | 3.1732 | [-4.55, 17.45] | 0 | 0 |
| `discount_percentage` | 7.9225 | 9.7996 | [-8.4973, 20.5606] | 1079 | 3769 |
| `delivery_speed_kph` | 12.0861 | 8.2678 | [-8.8065, 30.6774] | 774 | 2018 |
| `order_amount` | 969.6009 | 649.6284 | [-917.5, 2734.5] | 0 | 304 |
| `restaurant_cancellation_rate_pct` | 3.9546 | 3.4571 | [-9.0909, 15.1515] | 6 | 4 |

Note: `delivery_duration` and `distance_km` follow bounded Uniform distributions in the cleaned data (`z > 2.5 count = 0`), whereas `discount_percentage` (up to `123.5%`) and `delivery_speed_kph` (up to `48.0 km/h`) contain genuine heavy-tail anomalies.

## 3. Detected Statistical Anomalies by Metric
| Metric | Flagged Count |
|---|---:|
| Discount Percentage (%) | 1,079 |
| Delivery Speed (km/h) | 774 |
| Gross Order Amount (INR) | 304 |
| Cancellation Rate (%) | 27 |

## 4. Revenue Risk Audit — False-Positive Attribution
| False-Positive Risk Bucket | Orders |
|---|---:|
| Moderate - Negative only if discount is 100% platform-funded | 2,542 |
| Low - Verified cancelled order lost commission | 1,874 |
| High - Likely intentional marketing promo or free-delivery waiver | 227 |
| Low - Discount meets/exceeds gross order value | 26 |
