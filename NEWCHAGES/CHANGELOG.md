# NOVANEST — CHANGELOG

All notable changes to the NovaNest project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
