# NOVANEST — COMPLETE REPOSITORY DATASET AUDIT
**Scope:** 31 Datasets (10 Raw, 10 Cleaned, 2 Engineered, 9 Analytics)  
**Total Records Analyzed:** 304,405 Base Records + 49,971 Engineered Records + Analytics Matrices  
**Audit Date:** 2026-11-08  
**Auditor:** Senior Data Engineer & Data Quality Lead  

---

## 1. Executive Summary & Quality Certification

A full programmatic audit was conducted on every dataset in the repository using automated Python scripts. All 10 cleaned datasets maintain **100% row preservation** (zero rows dropped from raw data), **zero nulls**, **zero duplicate rows**, and **100% referential integrity** across 11 foreign-key relationships.

---

## 2. Master Dataset Profile Table

| Category | Dataset Name | Rows | Cols | File Size | Primary Key | PK Unique | Nulls | Dups | Operational Role |
| :--- | :--- | ---:| ---:| ---:| :--- | :---: | ---:| ---:| :--- |
| **Raw** | `raw/customers.csv` | 5,000 | 10 | 449,023 B | `customer_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/restaurants.csv` | 1,500 | 9 | 111,890 B | `restaurant_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/riders.csv` | 4,000 | 7 | 206,759 B | `rider_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/menu_items.csv` | 15,000 | 6 | 663,727 B | `item_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/orders.csv` | 49,971 | 12 | 4,284,433 B | `order_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/deliveries.csv` | 49,971 | 5 | 1,658,158 B | `delivery_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/payments.csv` | 49,971 | 4 | 1,616,181 B | `payment_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/promotions.csv` | 200 | 5 | 8,620 B | `promo_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/ratings_reviews.csv` | 28,792 | 5 | 892,617 B | `review_id` | Yes | 0 | 0 | Immutable baseline |
| **Raw** | `raw/app_events.csv` | 100,000 | 3 | 2,882,096 B | `event_id` | Yes | 0 | 0 | Immutable baseline |
| **Cleaned**| `cleaned/customers.csv` | 5,000 | 10 | 454,024 B | `customer_id` | Yes | 0 | 0 | Production profiles |
| **Cleaned**| `cleaned/restaurants.csv` | 1,500 | 9 | 113,391 B | `restaurant_id` | Yes | 0 | 0 | Production merchants |
| **Cleaned**| `cleaned/riders.csv` | 4,000 | 7 | 210,760 B | `rider_id` | Yes | 0 | 0 | Production fleet |
| **Cleaned**| `cleaned/menu_items.csv` | 15,000 | 6 | 678,728 B | `item_id` | Yes | 0 | 0 | Production catalog |
| **Cleaned**| `cleaned/orders.csv` | 49,971 | 12 | 4,334,405 B | `order_id` | Yes | 0 | 0 | Production orders |
| **Cleaned**| `cleaned/deliveries.csv` | 49,971 | 5 | 1,708,130 B | `delivery_id` | Yes | 0 | 0 | Production deliveries |
| **Cleaned**| `cleaned/payments.csv` | 49,971 | 4 | 1,666,153 B | `payment_id` | Yes | 0 | 0 | Production payments |
| **Cleaned**| `cleaned/promotions.csv` | 200 | 5 | 8,821 B | `promo_id` | Yes | 0 | 0 | Production campaigns |
| **Cleaned**| `cleaned/ratings_reviews.csv`| 28,792 | 5 | 921,410 B | `review_id` | Yes | 0 | 0 | Production reviews |
| **Cleaned**| `cleaned/app_events.csv` | 100,000 | 3 | 2,982,097 B | `event_id` | Yes | 0 | 0 | Production clickstream |
| **Engineered**| `orders_engineered.csv`| 49,971 | 38 | 11,233,541 B | `order_id` | Yes | 0 | 0 | BI reporting layer |
| **Engineered**| `orders_geo_temporal.csv`| 49,971| 38 | 11,233,541 B | `order_id` | Yes | 0 | 0 | ML training twin |
| **Analytics**| `customer_rfm_segments.csv`| 5,000 | 15 | 552,190 B | `customer_id` | Yes | 0 | 0 | RFM customer tiers |
| **Analytics**| `rfm_segment_summary.csv` | 10 | 8 | 651 B | `segment` | Yes | 0 | 0 | Segment metrics |
| **Analytics**| `monthly_cohort_matrix.csv`| 11 | 14 | 774 B | `cohort_month` | Yes | 57*| 0 | Retention % matrix |
| **Analytics**| `monthly_cohort_counts.csv`| 11 | 14 | 753 B | `cohort_month` | Yes | 57*| 0 | Headcount matrix |
| **Analytics**| `app_funnel_summary.csv` | 6 | 6 | 304 B | `stage_order` | Yes | 0 | 0 | Stage reach summary |
| **Analytics**| `app_event_overlap_matrix.csv`| 6 | 7 | 340 B | `event_type` | Yes | 0 | 0 | Event overlap matrix |
| **Analytics**| `kpi_summary.csv` | 16 | 16 | 9,972 B | `kpi_id` | Yes | 6* | 0 | Core KPI summary |
| **Analytics**| `kpi_definitions.json` | N/A | N/A | 16,333 B | `kpi_id` (JSON) | Yes | 0 | 0 | Structured JSON dict |
| **Analytics**| `kpi_cross_validation_matrix.csv`| 16 | 14 | 3,257 B | `kpi_id` | Yes | 0 | 0 | Verification matrix |

*\*Note: Nulls in cohort matrices represent future un-elapsed cohort months ($M_{t} > M_{now}$), which are mathematically expected triangles. Nulls in `kpi_summary.csv` notes column are empty optional commentary fields.*

---

## 3. Referential Integrity Audit (11 Foreign Keys)

| # | Relationship | Child Table.Column | Parent Table.Column | Orphan Records | Status |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **1** | Customer Orders | `orders.customer_id` | `customers.customer_id` | 0 | **PASS ✅ (100%)** |
| **2** | Restaurant Orders | `orders.restaurant_id` | `restaurants.restaurant_id` | 0 | **PASS ✅ (100%)** |
| **3** | Menu Item Orders | `orders.item_id` | `menu_items.item_id` | 0 | **PASS ✅ (100%)** |
| **4** | Rider Assignments | `orders.rider_id` | `riders.rider_id` | 0 | **PASS ✅ (100%)** |
| **5** | Menu Item Catalog | `menu_items.restaurant_id`| `restaurants.restaurant_id` | 0 | **PASS ✅ (100%)** |
| **6** | Delivery Tracking | `deliveries.order_id` | `orders.order_id` | 0 | **PASS ✅ (100%)** |
| **7** | Delivery Courier | `deliveries.rider_id` | `riders.rider_id` | 0 | **PASS ✅ (100%)** |
| **8** | Order Payments | `payments.order_id` | `orders.order_id` | 0 | **PASS ✅ (100%)** |
| **9** | Order Reviews | `ratings_reviews.order_id`| `orders.order_id` | 0 | **PASS ✅ (100%)** |
| **10**| Customer Reviews | `ratings_reviews.customer_id`| `customers.customer_id` | 0 | **PASS ✅ (100%)** |
| **11**| Clickstream User | `app_events.customer_id` | `customers.customer_id` | 0 | **PASS ✅ (100%)** |

---

## 4. Raw versus Cleaned Comparison Audit

| Metric | Raw Datasets (10 files) | Cleaned Datasets (10 files) | Transformation Details |
| :--- | :--- | :--- | :--- |
| **Total Rows** | 304,405 | 304,405 | Exactly 0 rows dropped (100% preservation) |
| **Total Columns** | 66 across 10 files | 66 across 10 files | Schemas preserved exactly |
| **Whitespace** | Trailing spaces in city, name strings | 100% trimmed and stripped | String cleanliness enforced |
| **Date Formats** | Mixed formats (`YYYY-MM-DD`, slashed dates) | Standardized ISO 8601 (`YYYY-MM-DD HH:MM:SS`) | Date parser compatibility |
| **Phone Numbers** | Variable lengths and prefixes | Cleaned 10-digit Indian MSISDN format | Verified valid format |
| **Bounds Checks** | Raw float prices and fees | Clipped non-negative bounds | Financial integrity preserved |

---

## 5. Cleaned versus Engineered Comparison Audit

`orders.csv` (12 columns) was enriched into `orders_engineered.csv` (38 columns) by joining 4 parent entities:
- **Base Columns (12)**: `order_id`, `customer_id`, `restaurant_id`, `item_id`, `rider_id`, `order_datetime`, `quantity`, `order_amount`, `discount_amount`, `delivery_fee`, `final_amount`, `order_status`.
- **Newly Engineered Features (26)**:
  1. `order_date`: Date component (`YYYY-MM-DD`).
  2. `order_year`: Integer year (`2025` or `2026`).
  3. `order_month`: Integer month (`1` to `12`).
  4. `order_month_name`: Month string name (`June`, etc.).
  5. `hour`: Hour of order placement (`0` to `23`).
  6. `day_of_week`: Day name (`Monday`, etc.).
  7. `peak_hour_flag`: Binary indicator (1 if hour in 12–14 or 19–22).
  8. `weekend_flag`: Binary indicator (1 if Saturday or Sunday).
  9. `cancellation_flag`: Binary indicator (1 if `order_status == 'Cancelled'`).
  10. `net_order_value`: `order_amount - discount_amount`.
  11. `discount_percentage`: `(discount_amount / order_amount) * 100`.
  12. `commission_percentage`: Merchant commission rate from `restaurants.csv`.
  13. `restaurant_city`: Merchant city.
  14. `commission_revenue`: Platform food commission earned.
  15. `estimated_profit`: Platform net unit profit ($commission + delivery\_fee - 30$).
  16. `profit_margin_pct`: Platform margin percentage ($profit / final\_amount \times 100$).
  17. `order_size`: Categorical bucket (`Small` < ₹500, `Medium` ₹500–₹1200, `Large` > ₹1200).
  18. `distance_km`: Trip delivery distance.
  19. `delivery_duration`: Trip transit minutes.
  20. `delivery_speed_kph`: Rider transit speed in km/h.
  21. `delivery_delay_flag`: Binary indicator (1 if `delivery_duration > 45`).
  22. `customer_city`: Registered customer city.
  23. `signup_date`: Registered customer signup timestamp.
  24. `rider_city`: Registered fleet courier city.
  25. `cross_city_flag`: Non-destructive operational audit flag.
  26. `pre_signup_order_flag`: Non-destructive chronological audit flag.
- **Engineered Dataset Twin Parity**: `orders_engineered.csv` and `orders_geo_temporal_enriched.csv` are 100% bit-for-bit identical (exact hash match).

---

## 6. Investigation of Data Generation Anomalies

1. **Cross-City Order Flag (`cross_city_flag`)**:
   - Occurrence: **38,572 orders (77.19%)** have mismatched cities between customer, restaurant, or rider.
   - Root Cause: In `python/data generation/generate_orders.py`, order sampling selected `customer`, `restaurant`, and `rider` independently at random without enforcing a geographic constraint.
   - Treatment: Preserved intact; flagged with `cross_city_flag` to enable machine learning models to either condition on or filter geographic cross-city friction.
2. **Pre-Signup Order Flag (`pre_signup_order_flag`)**:
   - Occurrence: **12,418 orders (24.85%)** have `order_datetime < customer.signup_date`.
   - Root Cause: Customer signup dates span `2024-06-16` to `2026-06-16` (24 months), whereas order dates span `2025-06-17` to `2026-06-17` (12 months), and order generation did not filter customers by `order_date >= signup_date`.
   - Treatment: Non-destructively flagged with `pre_signup_order_flag`. In analytical cohort retention, cohorts are anchored on **First Order Month** rather than signup date, cleanly isolating retention mechanics.
3. **App Events Missing Timestamps**:
   - Occurrence: All 100,000 rows in `app_events.csv` lack `timestamp` and `session_id`.
   - Root Cause: Synthetic generator used `random.choice(event_types)` for 100k iterations.
   - Treatment: Handled via unique-user stage reach and event co-occurrence overlap, removing unsupported sequential progression claims.

*Dataset Audit Certified by NovaNest Architecture Governance on 2026-11-08.*
