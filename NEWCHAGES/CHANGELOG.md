# NOVANEST — CHANGELOG

All notable changes to the NovaNest project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.1] - 2026-11-08 - Phase 04: Final KPI Audit & Certification

### Added
- Created `NEWCHAGES/PHASE_04/FINAL_KPI_AUDIT.md`: comprehensive before/after KPI comparison, mathematical proofs, and methodological boundaries.
- Created `datasets/analytics/app_event_overlap_matrix.csv`: pairwise co-occurrence matrix measuring user presence across the 6 app events.

### Changed
- Re-engineered `python/analytics/kpi_engine.py`:
  - Disentangled Net AOV (₹967.33 = Net Revenue / Completed Orders) from Gross AOV (₹970.75 = GMV / Completed Orders).
  - Reconciled Contribution Margin to Realized Margin on Delivered Orders (23.59% = ₹10.95M profit / ₹46.43M net revenue) and gross booking margin (23.60% = ₹11.39M / ₹48.28M).
  - Renamed `Customer Lifetime Value` to `Historical Realized Spend per Customer (Cumulative ARPU)` (₹9,285.20 realized / ₹9,656.33 gross).
  - Renamed `Rider Utilization` to `Delivered Orders per Active Rider` (12.49 deliveries/rider; 12.00 completed deliveries/rider).
  - Separated `Restaurant Performance` into 5 distinct dimensions (Gross Throughput ₹30,950.66, Food GMV ₹31,060.08, Net Food Payout ₹24,077.85).
  - Added 5 distinct status tiers for each KPI (Python execution, SQL static, SQL live, DAX review, Power BI runtime).
- Re-engineered `python/analytics/funnel_analysis.py`:
  - Documented lack of timestamps in `app_events.csv` and uniform random generator behavior (`random.choice`).
  - Switched focus to unique-user stage reach and event co-occurrence overlap, disabling chronological drop-off claims.
- Re-engineered `python/analytics/validate_kpis.py`:
  - Updated validation logic to reflect audited formulas and generated multi-layer status matrix.
- Expanded `tests/test_analytics.py`:
  - Expanded from 7 to 12 automated unit and integration tests (added dual AOV checks, margin filter reconciliation, terminology governance, empty dataset handling, zero denominators, and idempotency).
  - All 12/12 tests passing in 2.880s.

---

## [0.4.0] - 2026-11-07 - Phase 04: Advanced Business Analytics & KPI Framework

### Added
- Created `python/analytics/` modular package with full export conventions.
- Created `python/analytics/rfm_segmentation.py`: calculates R, F, M scores and segments 5,000 customers into 10 behavioral tiers.
- Created `python/analytics/cohort_analysis.py`: constructs Month 0 to Month 12 monthly cohort retention matrices.
- Created `python/analytics/funnel_analysis.py`: evaluates clickstream marketing funnels across 100,000 events and 6 stages.
- Created `python/analytics/kpi_engine.py`: implements 16 core business metrics with formulas, SQL equivalents, and DAX measures.
- Created `python/analytics/validate_kpis.py`: automated cross-validation reconciling Python, SQL, and DAX layers within 0.05 tolerance.
- Created `tests/test_analytics.py`: unit and integration test suite (7/7 tests passed).
- Created `NEWCHAGES/PHASE_03/FINAL_ACCEPTANCE_REVIEW.md`: diagnostic error review, dataset parity certification, and repeat rate vs cohort retention distinction.
- Created `reports/kpi_cross_validation_report.md` and 8 analytical data artifacts in `datasets/analytics/`.

---

## [0.3.0] - 2026-11-07 - Phase 03: MySQL & Database Optimization


### Added
- Created `mysql/08_optimized_views.sql` with 7 production-grade analytical views (`vw_customer_rfm`, `vw_monthly_cohort_retention`, `vw_unit_economics`, `vw_rider_efficiency`, `vw_restaurant_performance`, `vw_monthly_revenue`, `vw_customer_lifetime_value`).
- Created `python/load_mysql.py` automated CSV-to-MySQL data ingestion pipeline supporting batch loading, FK-safe order, and transaction control.
- Created `NEWCHAGES/PHASE_02/FINAL_VERIFICATION.md` certifying Phase 02 completion with independent Python calculations.
- Created `NEWCHAGES/GITHUB_READINESS_FINAL_CHECK.md` auditing pre-push security, file sizes, and push governance.
- Created `NEWCHAGES/PHASE_03/SQL_VALIDATION_REPORT.md` certifying static syntax validation across 8 SQL files (103 statements).

### Changed
- Sanitized SQL files `03_level2_business.sql`, `04_level3_intermediate.sql`, `05_level4_advanced.sql`, and `06_level5_executive.sql`, converting all prose headers into standardized SQL comments.
- Refactored `07_level6_strategy_analytics.sql` Query 2 to use a modern CTE for repeat customer retention calculation (verified at 99.94%).

---

## [0.2.0] - 2026-11-07 - Phase 02: Data Intelligence & Pipeline Stabilization


### Added
- Created `python/pipeline_runner.py` automating data cleaning, referential checks, and feature engineering in 6.18 seconds.
- Created `reports/data_quality_report.md` documenting comprehensive data health, 0 nulls, 0 duplicates, and 11/11 verified foreign keys.
- Created `docs/GITHUB_SETUP_AND_PUSH_READINESS.md` detailing security audit, file size checks, and GitHub setup guide.
- Created `datasets/engineered/orders_geo_temporal_enriched.csv` providing machine learning models with `cross_city_flag` and `pre_signup_order_flag`.
- Created `NEWCHAGES/` change management infrastructure with 8 root tracking registers, 9 phase folders, and phase sub-files.
- Created `NEWCHAGESTOTALREPORT.md` executive master report.

### Changed
- Overhauled `python/feature_engineering.py` into a 38-feature engine joining restaurants, customers, riders, and deliveries with unit economics and anomaly flags.
- Refactored `python/clean_data.py` with granular dataset cleaning, whitespace trimming, and ISO formatting.
- Updated `.gitignore` to explicitly exclude `*.zip` archives (`datasets.zip` 8.7 MB).
- Updated `python/data generation/validate_master_data.py` with dual-target support (`raw` / `cleaned`) and dynamic root discovery.


---

## [0.1.0] - 2026-11-07 - Phase 01: Complete System Audit

### Added
- Completed comprehensive file-by-file audit of all 6 workspace folders.
- Generated `reports/NOVANEST_MASTER_AUDIT.md` documenting architecture, technical gaps, and 10-phase master roadmap.
- Initialized local Git repository on branch `main`.
