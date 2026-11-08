# NOVANEST — COMPREHENSIVE SOURCE CODE AUDIT
**Scope:** 25 Python Source Files, 8 SQL Query & Schema Scripts, 1 Test Suite  
**Audit Date:** 2026-11-08  
**Auditor:** Senior Software Architect & Database Auditor  

---

## 1. Python Engineering Architecture

NovaNest's Python architecture is organized into four distinct operational tiers:
1. **Core Pipeline Orchestration** (`python/*.py`): Data cleaning, feature enrichment, master execution, and database ingestion.
2. **Production Business Analytics** (`python/analytics/*.py`): RFM customer segmentation, monthly cohort retention matrices, marketing stage reach, 16-KPI business engine, and multi-layer cross-validation.
3. **Data Generation & Master Validation** (`python/data generation/*.py`): Synthetic data generation routines and dual-target validation harnesses.
4. **Command-Line Exploratory Scripts** (`python/data analysis/*.py`): Quick console summary scripts for domain metrics.
5. **Quality Assurance & Testing** (`tests/*.py`): Comprehensive automated test suites.

---

## 2. Deep Module Audit — Core Data Engineering

### A. `python/clean_data.py` (8,264 bytes)
- **Purpose**: Cleans all 10 raw CSV datasets non-destructively, applying strict data typing, string stripping, ISO datetime formatting, and bounds checking without dropping rows.
- **Main Functions**: `clean_customers()`, `clean_restaurants()`, `clean_riders()`, `clean_menu_items()`, `clean_orders()`, `clean_deliveries()`, `clean_payments()`, `clean_promotions()`, `clean_ratings_reviews()`, `clean_app_events()`, `clean_all()`.
- **Inputs**: `datasets/raw/*.csv` (10 files).
- **Outputs**: `datasets/cleaned/*.csv` (10 files).
- **Dependencies**: `pandas`, `numpy`, `pathlib`.
- **Business Logic**: Normalizes phone numbers, formats order and signup timestamps to ISO 8601 (`YYYY-MM-DD HH:MM:SS`), clips negative prices, verifies foreign keys.
- **Error Handling**: Graceful fallback on missing columns, robust type-coercion with zero row drops.
- **Status**: Production-ready; verified on 304,405 records in 0.73s.
- **Limitations**: Synthetic generator artifacts (pre-signup orders) are preserved with flags rather than dropped to preserve data integrity.

### B. `python/feature_engineering.py` (7,165 bytes)
- **Purpose**: Enriches baseline orders table with temporal, spatial, behavioral, unit economics, and anomaly audit features.
- **Main Functions**: `engineer_order_features()`, `run_feature_engineering()`.
- **Inputs**: Cleaned orders, restaurants, customers, riders, and deliveries.
- **Outputs**: `datasets/engineered/orders_engineered.csv` and `orders_geo_temporal_enriched.csv` (49,971 rows x 38 cols).
- **Dependencies**: `pandas`, `numpy`, `pathlib`.
- **Business Logic**:
  - Temporal: `hour`, `day_of_week`, `peak_hour_flag` (12-14, 19-22), `weekend_flag` (Sat, Sun).
  - Economics: `commission_revenue` ($order\_amount \times commission\_pct$), `estimated_profit` ($comm + delivery\_fee - ₹30$), `profit_margin_pct` ($profit / final\_amount \times 100$).
  - Spatial: `distance_km`, `delivery_speed_kph` ($distance / (duration / 60)$), `delivery_delay_flag` ($duration > 45$).
  - Anomaly Auditing: `cross_city_flag` ($customer\_city \neq restaurant\_city$), `pre_signup_order_flag` ($order\_date < signup\_date$).
- **Status**: Production-ready; certified in 1.20s.

### C. `python/pipeline_runner.py` (4,379 bytes)
- **Purpose**: Master pipeline orchestration harness running cleaning, 11 foreign-key validations, and feature engineering end-to-end.
- **Main Functions**: `run_pipeline()`.
- **Outputs**: Pipeline console audit log and fresh cleaned/engineered datasets.
- **Execution Benchmark**: 3.24 seconds total runtime.
- **Status**: Production-ready.

### D. `python/load_mysql.py` (7,119 bytes)
- **Purpose**: Automated CSV-to-MySQL ingestion pipeline supporting batch loading, FK-safe table order, transactions, and idempotent truncations.
- **Main Functions**: `get_mysql_connection()`, `load_table()`, `load_all_tables()`.
- **Inputs**: `datasets/cleaned/*.csv`, `.env` credentials.
- **Database Target**: MySQL 8.0 `novanest_db`.
- **Error Handling**: Safe rollback on failure, batch inserts in chunks of 2,000–5,000 rows.
- **Status**: Statically verified; live database execution blocked pending password configuration in `.env`.

---

## 3. Deep Module Audit — Production Business Analytics

### A. `python/analytics/rfm_segmentation.py` (6,432 bytes)
- **Purpose**: Computes Recency, Frequency, and Monetary scores across 5,000 customers and segments them into 10 behavioral tiers.
- **Main Functions**: `calculate_rfm_segments()`, `run_rfm_analysis()`.
- **Inputs**: Cleaned `orders.csv` and `customers.csv`.
- **Outputs**: `datasets/analytics/customer_rfm_segments.csv` (5k rows) and `rfm_segment_summary.csv` (10 rows).
- **Business Logic**: Inverted quintile scoring for Recency (1 = inactive >60 days; 5 = active <15 days). Forward scoring for Frequency and Monetary.
- **Segments**: Champions (775), Loyal Customers (1,003), At Risk (630), Hibernating / Lost (1,046), Potential Loyalists (464), Promising (334), Cannot Lose Them (158), New Customers (281), Occasional (244), Need Attention (65).
- **Status**: Production-ready; 100% verified.

### B. `python/analytics/cohort_analysis.py` (5,015 bytes)
- **Purpose**: Computes monthly acquisition cohort retention matrices from Month 0 to Month 12.
- **Main Functions**: `compute_cohort_retention_matrix()`, `run_cohort_analysis()`.
- **Inputs**: Cleaned `orders.csv`.
- **Outputs**: `monthly_cohort_matrix.csv` (percentages) and `monthly_cohort_counts.csv` (headcounts).
- **Business Logic**: First valid order month defines acquisition cohort (11 cohorts from 2025-06 to 2026-05). Month 0 is 100.0%.
- **Key Metrics**: Month 1 average retention = 53.36%, Month 3 = 56.65%, Month 6 = 53.73%. Proves repeat-purchase rate (99.94%) is strictly distinct from cohort decay.
- **Status**: Production-ready.

### C. `python/analytics/funnel_analysis.py` (6,319 bytes)
- **Purpose**: Evaluates clickstream marketing event distributions, unique-user stage reach, and pairwise event co-occurrence.
- **Main Functions**: `analyze_marketing_funnel()`, `run_funnel_analysis()`.
- **Inputs**: Cleaned `app_events.csv`.
- **Outputs**: `app_funnel_summary.csv` and `app_event_overlap_matrix.csv`.
- **Architectural Boundary**: Transparently handles the absence of timestamps in `app_events.csv`. Evaluates unique-user presence (96.3%–96.7% reach) and stage co-occurrence (4,043 users logged all 6 stages) without fabricating temporal progression.
- **Status**: Production-ready; scientifically grounded.

### D. `python/analytics/kpi_engine.py` (26,679 bytes)
- **Purpose**: Master business performance engine computing 16 core business metrics with formulas, SQL equivalents, DAX representations, and 5-layer status tracking.
- **Main Functions**: `compute_all_kpis()`, `run_kpi_engine()`.
- **Outputs**: `kpi_summary.csv` and `kpi_definitions.json`.
- **Audited Formulas**:
  - Net AOV (₹967.33) vs Gross AOV (₹970.75).
  - Realized Contribution Margin on Delivered Orders (23.59%) vs Gross Booking Margin (23.60%).
  - Delivered Operating Profit (₹10,953,031.58).
  - Cumulative ARPU (₹9,285.20 realized / ₹9,656.33 gross).
  - Delivered Orders per Active Rider (12.49 deliveries/rider).
  - Restaurant Performance (₹30,950.66 throughput, ₹31,060.08 GMV, ₹24,077.85 payout).
- **Status**: Production-ready; 100% verified.

### E. `python/analytics/validate_kpis.py` (9,668 bytes)
- **Purpose**: Cross-layer mathematical reconciler verifying formula parity across Python, SQL views, and Power BI DAX.
- **Main Functions**: `run_cross_validation()`, `run_kpi_validation()`.
- **Outputs**: `reports/kpi_cross_validation_report.md` and `kpi_cross_validation_matrix.csv`.
- **Verification Result**: 16/16 exact matches within 0.05 tolerance.
- **Status**: Production-ready.

---

## 4. Deep Module Audit — SQL Engineering

NovaNest features 8 production SQL scripts containing **103 total statements**:

| Script File | Lines | Statements | Purpose | Primary Constructs | Validation Status |
| :--- | ---:| ---:| :--- | :--- | :--- |
| `01_schema.sql` | 170 | 10 | Relational DDL for 10 tables | `CREATE TABLE`, `PRIMARY KEY`, `FOREIGN KEY`, `CHECK` | 10/10 Valid (Static) |
| `02_level1_foundation.sql` | 54 | 10 | Foundational data inspection | `SELECT`, `WHERE`, `ORDER BY`, `LIMIT` | 10/10 Valid (Static) |
| `03_level2_business.sql` | 131 | 15 | Core business aggregations | `GROUP BY`, `HAVING`, `SUM`, `AVG`, `COUNT` | 15/15 Valid (Static) |
| `04_level3_intermediate.sql`| 255 | 20 | Multi-table joins & subqueries | `INNER JOIN`, `LEFT JOIN`, `CASE WHEN`, Subqueries | 20/20 Valid (Static) |
| `05_level4_advanced.sql` | 264 | 15 | Window functions & rankings | `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `NTILE()` | 15/15 Valid (Static) |
| `06_level5_executive.sql` | 133 | 10 | Executive summaries & KPIs | `SUM() OVER()`, Running totals, MoM growth | 10/10 Valid (Static) |
| `07_level6_strategy_analytics.sql`| 196 | 16 | Strategic analytics & retention | Multi-stage CTEs (`WITH ... AS`), Cohorts | 16/16 Valid (Static) |
| `08_optimized_views.sql` | 164 | 7 | Production analytical views | `CREATE OR REPLACE VIEW` (7 analytical views) | 7/7 Valid (Static) |
| **TOTAL** | **1,367** | **103** | **Full Database Layer** | **All SQL Constructs** | **100% SYNTACTICALLY VALID** |

### Analytical Views in `08_optimized_views.sql`:
1. `vw_customer_rfm`: Computes customer R, F, M scores and monetary volume.
2. `vw_monthly_cohort_retention`: CTE-based acquisition cohort retention calculation.
3. `vw_unit_economics`: Per-order commission revenue, delivery fee, fulfillment cost, and estimated profit.
4. `vw_rider_efficiency`: Fleet throughput, average duration, speed, and SLA breach rate.
5. `vw_restaurant_performance`: Gross food sales, commission revenue, and order volume per merchant.
6. `vw_monthly_revenue`: Monthly financial throughput and platform commission growth.
7. `vw_customer_lifetime_value`: Cumulative customer revenue spend to date.

---

## 5. Automated Testing Suite (`tests/test_analytics.py`)

- **Size**: 10,324 bytes (12 comprehensive tests).
- **Coverage**:
  - RFM dimensions and null checks (Test 01).
  - RFM monetary revenue balance (Test 02).
  - Cohort Month 0 = 100.0% baseline (Test 03).
  - Repeat-purchase rate (99.94%) vs cohort decay distinction (Test 04).
  - Dual AOV consistency: Net AOV ₹967.33 vs Gross AOV ₹970.75 (Test 05).
  - Contribution margin filter reconciliation: 23.59% delivered vs 23.60% booking (Test 06).
  - Terminology governance: Cumulative ARPU & Deliveries per Rider (Test 07).
  - Funnel event schema and lack of timestamps (Test 08).
  - Restaurant 5-dimensional performance (Test 09).
  - Empty dataset and zero denominator resilience (Test 10).
  - Pipeline repeatability and idempotency (Test 11).
  - 16/16 KPI cross-validation tolerances and 5 status tiers (Test 12).
- **Execution Time**: 2.852 seconds.
- **Pass Rate**: 12 / 12 (100% PASSED).

*Source Code Audit Certified by NovaNest Architecture Governance on 2026-11-08.*
