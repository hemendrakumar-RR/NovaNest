# PHASE 02 — TEST RESULTS & VERIFICATION LOG

---

## 1. Test Suite: Master Data Validation (`validate_master_data.py`)
- **Execution Command**: `python "python/data generation/validate_master_data.py" raw` & `python "python/data generation/validate_master_data.py"`
- **Result**: PASSED
- **Findings**:
  - `customers.csv`: 5,000 rows, 10 cols, 0 duplicates, 0 nulls
  - `restaurants.csv`: 1,500 rows, 9 cols, 0 duplicates, 0 nulls
  - `menu_items.csv`: 15,000 rows, 6 cols, 0 duplicates, 0 nulls
  - `riders.csv`: 4,000 rows, 7 cols, 0 duplicates, 0 nulls
  - `orders.csv`: 49,971 rows, 12 cols, 0 duplicates, 0 nulls
  - `payments.csv`: 49,971 rows, 4 cols, 0 duplicates, 0 nulls
  - `deliveries.csv`: 49,971 rows, 5 cols, 0 duplicates, 0 nulls
  - `app_events.csv`: 100,000 rows, 3 cols, 0 duplicates, 0 nulls
  - `ratings_reviews.csv`: 28,792 rows, 5 cols, 0 duplicates, 0 nulls
  - `promotions.csv`: 200 rows, 5 cols, 0 duplicates, 0 nulls
  - **Total**: 304,405 records verified.

---

## 2. Test Suite: Referential Integrity & Foreign Keys
- **Execution Command**: `python -c "import python.pipeline_runner as p; p.verify_referential_integrity(...)"`
- **Result**: 11/11 PASSED (100% Referential Parity)
- **Verified Relations**:
  1. `orders.customer_id -> customers.customer_id`: PASS (0 orphans)
  2. `orders.restaurant_id -> restaurants.restaurant_id`: PASS (0 orphans)
  3. `orders.item_id -> menu_items.item_id`: PASS (0 orphans)
  4. `orders.rider_id -> riders.rider_id`: PASS (0 orphans)
  5. `deliveries.order_id -> orders.order_id`: PASS (0 orphans)
  6. `deliveries.rider_id -> riders.rider_id`: PASS (0 orphans)
  7. `payments.order_id -> orders.order_id`: PASS (0 orphans)
  8. `ratings_reviews.order_id -> orders.order_id`: PASS (0 orphans)
  9. `ratings_reviews.customer_id -> customers.customer_id`: PASS (0 orphans)
  10. `app_events.customer_id -> customers.customer_id`: PASS (0 orphans)
  11. `menu_items.restaurant_id -> restaurants.restaurant_id`: PASS (0 orphans)

---

## 3. Test Suite: Feature Engineering Verification
- **Execution Command**: `python python/feature_engineering.py`
- **Result**: PASSED
- **Output Artifacts**:
  - `datasets/engineered/orders_engineered.csv`: 49,971 rows x 38 columns
  - `datasets/engineered/orders_geo_temporal_enriched.csv`: 49,971 rows x 38 columns
- **Engineered Metrics Verified**:
  - Mean Estimated Profit per Order: ₹228.01
  - Mean Profit Margin: 24.52%
  - Delivery Delays (>45 min): 16,119 (32.3%)
  - Peak Hour Orders: 14,610 (29.2%)
  - Weekend Orders: 14,287 (28.6%)
  - Cross-City Orders Flagged: 38,572 (77.2%)
  - Pre-Signup Orders Flagged: 12,418 (24.9%)

---

## 4. Test Suite: End-to-End Pipeline Harness
- **Execution Command**: `python python/pipeline_runner.py`
- **Result**: PASSED in 6.18 seconds.
- **Exit Code**: 0
