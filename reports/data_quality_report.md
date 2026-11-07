# NOVANEST — COMPREHENSIVE DATA QUALITY & INTEGRITY REPORT
**Phase 02 Deliverable — Data Intelligence, Integrity Audits & Anomaly Investigation**

---

## 1. Executive Summary & Data Quality Scorecard

This report provides an exhaustive, multi-dimensional data quality evaluation across all 10 relational entities in the **NovaNest Food Delivery Ecosystem** (totaling **304,405 records**).

### Data Health Scorecard
| Metric | Result | Target Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Total Datasets Analyzed** | 10 Relational CSVs | 10 Datasets | **100% Complete** |
| **Total Records Audited** | 304,405 Records | 300,000+ Records | **Verified** |
| **Missing / Null Values** | 0 Nulls (0.00%) | < 0.01% | **PASSED (Clean)** |
| **Duplicate Records** | 0 Duplicates (0.00%) | 0.00% | **PASSED (Clean)** |
| **Referential Integrity (FK-to-PK)** | 100% Match (0 Orphan Records) | 100.0% | **PASSED (Perfect)** |
| **Price Consistency (`quantity * price`)** | 100% Exact across 49,971 rows | 100.0% | **PASSED (Exact)** |
| **Geo-Consistency (City Alignment)** | 22.8% Aligned / 77.2% Mismatched | 100.0% | **Flagged & Isolated** |
| **Temporal Consistency (Order >= Signup)**| 75.1% Valid / 24.9% Pre-Signup | 100.0% | **Flagged & Isolated** |

---

## 2. Table-by-Table Structural & Schema Audit

| Table Name | File Name | Records | Columns | Primary Key | Missing / Nulls | Duplicate PKs |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Customers** | `customers.csv` | 5,000 | 10 | `customer_id` | 0 | 0 |
| **Restaurants** | `restaurants.csv` | 1,500 | 9 | `restaurant_id` | 0 | 0 |
| **Menu Items** | `menu_items.csv` | 15,000 | 6 | `item_id` | 0 | 0 |
| **Riders** | `riders.csv` | 4,000 | 7 | `rider_id` | 0 | 0 |
| **Orders** | `orders.csv` | 49,971 | 12 | `order_id` | 0 | 0 |
| **Payments** | `payments.csv` | 49,971 | 4 | `payment_id` | 0 | 0 |
| **Deliveries** | `deliveries.csv` | 49,971 | 5 | `delivery_id` | 0 | 0 |
| **Ratings & Reviews**| `ratings_reviews.csv`| 28,792 | 5 | `review_id` | 0 | 0 |
| **Promotions** | `promotions.csv` | 200 | 5 | `promo_id` | 0 | 0 |
| **App Events** | `app_events.csv` | 100,000 | 3 | `event_id` | 0 | 0 |

---

## 3. Referential Integrity & Foreign Key Validation

Every foreign key relationship across the entire schema was systematically cross-checked against parent tables:

| Foreign Key Relationship | Child Table Column | Parent Table Column | Total Child Keys | Orphan Keys | Integrity Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Orders ➔ Customers** | `orders.customer_id` | `customers.customer_id` | 49,971 | **0** | **100% Valid** |
| **Orders ➔ Restaurants** | `orders.restaurant_id` | `restaurants.restaurant_id` | 49,971 | **0** | **100% Valid** |
| **Orders ➔ Menu Items** | `orders.item_id` | `menu_items.item_id` | 49,971 | **0** | **100% Valid** |
| **Orders ➔ Riders** | `orders.rider_id` | `riders.rider_id` | 49,971 | **0** | **100% Valid** |
| **Menu ➔ Restaurants** | `menu_items.restaurant_id`| `restaurants.restaurant_id`| 15,000 | **0** | **100% Valid** |
| **Deliveries ➔ Orders** | `deliveries.order_id` | `orders.order_id` | 49,971 | **0** | **100% Valid** |
| **Deliveries ➔ Riders** | `deliveries.rider_id` | `riders.rider_id` | 49,971 | **0** | **100% Valid** |
| **Payments ➔ Orders** | `payments.order_id` | `orders.order_id` | 49,971 | **0** | **100% Valid** |
| **Reviews ➔ Orders** | `ratings_reviews.order_id`| `orders.order_id` | 28,792 | **0** | **100% Valid** |
| **Reviews ➔ Customers** | `ratings_reviews.customer_id`| `customers.customer_id` | 28,792 | **0** | **100% Valid** |
| **Events ➔ Customers** | `app_events.customer_id` | `customers.customer_id` | 100,000 | **0** | **100% Valid** |

**Conclusion**: Referential integrity across all 11 relational paths is **100% flawless**. There are zero dangling or orphan foreign keys in the entire platform.

---

## 4. In-Depth Anomaly Investigations

### Anomaly 1: Cross-City Order Allocation (38,572 Mismatches)
- **Observation**:
  - In **38,572 out of 49,971 orders (77.2%)**, the ordering customer's registered city does not match the assigned restaurant's city or rider's city (e.g., a customer registered in Chennai ordering from a restaurant in Vijayawada with a rider from Bangalore).
  - Only **11,399 orders (22.8%)** are strictly intra-city (same city for customer, restaurant, and rider).
- **Root Cause**:
  - In `generate_orders.py`, the generator sampled `customer = customers_df.sample(1)` and `restaurant = restaurants_df.sample(1)` independently without applying a `city == customer['city']` filter.
- **Business & Analytical Impact**:
  - In real-world hyper-local food delivery, food cannot be delivered across inter-state distances (e.g., Chennai to Vijayawada) within 37 minutes.
- **Remediation & Solution Strategy**:
  - **Do NOT delete the 38,572 orders**, because doing so would destroy 77% of transaction volume and break existing Power BI dashboards, MySQL aggregations, and financial totals.
  - Implemented `cross_city_flag` (1 = cross-city, 0 = same-city) in `datasets/engineered/orders_engineered.csv`.
  - Machine learning models for hyper-local delivery time estimation will filter on `cross_city_flag == 0` for pure localized physics, while platform-level financial models evaluate the entire portfolio.

---

### Anomaly 2: Temporal Inconsistency — Orders Prior to Signup Date (12,418 Records)
- **Observation**:
  - In **12,418 orders (24.9%)**, `orders.order_datetime` is chronologically earlier than `customers.signup_date`.
- **Root Cause**:
  - Customer signup dates were randomly generated between **June 2024 and June 2026**, while order timestamps were randomly sampled across the 12-month period between **June 2025 and June 2026** without checking the individual customer's registration date.
- **Business & Analytical Impact**:
  - Causes negative customer tenure for first purchase in 25% of cases if unflagged.
- **Remediation & Solution Strategy**:
  - Implemented `pre_signup_order_flag` (1 = order precedes signup, 0 = order after signup) in `orders_engineered.csv`.
  - In downstream cohort analysis, we align customer cohort assignment to the customer's *actual first order month* (`first_order_date`) rather than registration timestamp.

---

### Anomaly 3: Clamped Final Amount Business Rule (67 Records)
- **Observation**:
  - In 67 orders, `final_amount` is exactly ₹50, even though `order_amount - discount_amount + delivery_fee` calculated to less than ₹50 (down to ₹13).
- **Explanation**:
  - This is a legitimate food platform business rule: a **minimum order threshold floor** of ₹50 is enforced to ensure the delivery partner subsidy is covered.
  - Verified and documented as an intended platform rule.

---

## 5. Statistical Distributions & Outlier Checks

| Metric / Field | Minimum | 25th Pct | Median (50th) | 75th Pct | Maximum | Outlier Summary |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Order Amount (₹)** | 80 | 452 | 794 | 1,365 | 2,800 | Realistic ticket range; no negative values |
| **Discount Amount (₹)** | 0 | 25 | 41 | 60 | 100 | Realistic campaign caps |
| **Delivery Fee (₹)** | 20 | 30 | 40 | 50 | 60 | Tiered distance-based fees |
| **Final Amount (₹)** | 50 | 448 | 789 | 1,362 | 2,843 | Matches platform billing |
| **Delivery Distance (km)**| 1.0 | 3.5 | 6.2 | 9.1 | 15.0 | Normal delivery radius |
| **Delivery Time (min)** | 15 | 26 | 36 | 47 | 65 | Normal distribution around 37.4 mins |
| **Restaurant Rating** | 1.0 | 4.0 | 4.0 | 5.0 | 5.0 | Positive skew typical of app ratings |

---

## 6. End-to-End Lineage & Reproducibility

```
[Raw Datasets (datasets/raw/*.csv)]
   │
   ▼
[Data Cleaning Pipeline (python/clean_data.py)]
   ├─ Strips whitespace, standardizes casing
   ├─ Casts datatypes (INT, FLOAT, ISO DATETIME)
   ├─ Enforces minimum bounds (Rating 1-5, Discount 0-100%)
   │
   ▼
[Cleaned Datasets (datasets/cleaned/*.csv)]
   │
   ▼
[Feature Engineering Pipeline (python/feature_engineering.py)]
   ├─ Adds 26 derived features (38 total columns)
   ├─ Flags temporal, financial, and geo anomalies
   │
   ▼
[Engineered Datasets (datasets/engineered/orders_engineered.csv)]
   │
   ▼
[Pipeline Orchestrator (python/pipeline_runner.py)]
   └─ Validates entire workflow in 4.19 seconds with 100% reproducibility
```

---
*Report certified for Phase 02 completion of NovaNest Autonomous Decision Intelligence Platform.*
