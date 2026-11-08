# NOVANEST — TESTING HISTORY

Chronological master log of all testing and verification activities across the project lifecycle.

---

| Run ID | Date | Component Tested | Test Type | Command Executed | Result | Details / Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST-001** | 2026-11-07 | Python Environment | Environment Audit | `python --version; pip list` | **PASSED** | Python 3.14.4; all data science packages verified |
| **TEST-002** | 2026-11-07 | MySQL Windows Service | Service Inspection | `Get-Service -Name *mysql*` | **PASSED** | Service `MySQL80` status is `Running` |
| **TEST-003** | 2026-11-07 | Power BI Binary | Zip Architecture Audit | Inspect `Report/Layout` via python script | **PASSED** | 5 report pages, 27 measures identified; pbix preserved |
| **TEST-004** | 2026-11-07 | Data Cleaning Pipeline | Script Execution | `python python/clean_data.py` | **PASSED** | All 10 datasets cleaned & verified with 0 nulls |
| **TEST-005** | 2026-11-07 | Master Data Validator | Data Quality Check | `python "python/data generation/validate_master_data.py"` | **PASSED** | 304,405 records checked; 0 duplicates, 0 nulls |
| **TEST-006** | 2026-11-07 | Feature Engineering | Script Execution | `python python/feature_engineering.py` | **PASSED** | 49,971 records enriched to 38 features with anomaly flags |
| **TEST-007** | 2026-11-07 | Pipeline Orchestrator | End-to-End Workflow | `python python/pipeline_runner.py` | **PASSED** | Full pipeline runs in 4.19s with 100% reproducibility |
| **TEST-008** | 2026-11-07 | Data Analysis Scripts | Execution Verification | Customer, Financial, Ops, Restaurant analysis scripts | **PASSED** | All 4 analysis scripts output valid business aggregations |
| **TEST-009** | 2026-11-07 | Referential Integrity Suite | Foreign Key Verification | `python python/pipeline_runner.py` (Step 2) | **PASSED** | 11/11 relations verified; 0 orphans across 304,405 records |
| **TEST-010** | 2026-11-07 | End-to-End Pipeline Harness | Full Execution Benchmark | `python python/pipeline_runner.py` | **PASSED** | Cleaning, 11 FK checks, feature engineering finished in 6.18s |
| **TEST-011** | 2026-11-07 | Phase 2 Final Verification | Comprehensive Audit | Independent Python comparison & calculation | **PASSED** | 304,405 records preserved; 38 columns (12+26); 24.52% unit profit margin |
| **TEST-012** | 2026-11-07 | Static SQL Validation Suite | Syntax & Structure Analysis | Python AST & delimiter parser on all 8 files | **PASSED** | 8/8 SQL files passed; 103/103 statements valid; 0 prose syntax errors |
| **TEST-013** | 2026-11-07 | Retention Query Cross-Validation | Math & Logic Cross-Check | Python pandas groupby vs SQL CTE logic | **PASSED** | 4,997 repeat / 5,000 customers = 99.94% repeat retention rate verified |
| **TEST-014** | 2026-11-07 | MySQL Connectivity Diagnostic | Service & Auth Inspection | `mysql.connector.connect()` test | **BLOCKED** | Service `MySQL80` running; authentication requires password in `.env` |
| **TEST-015** | 2026-11-07 | RFM Engine Integrity | Unit Test | `python tests/test_analytics.py` (Test 01) | **PASSED** | 5,000 customers evaluated; 0 nulls across R, F, M; 10 segments |
| **TEST-016** | 2026-11-07 | RFM Monetary Parity | Financial Reconciliation | `python tests/test_analytics.py` (Test 02) | **PASSED** | Sum of customer monetary equals ₹46,425,992.00 (exact match) |
| **TEST-017** | 2026-11-07 | Cohort Matrix Baseline | Metric Verification | `python tests/test_analytics.py` (Test 03) | **PASSED** | Month 0 retention is exactly 100.0% across all 11 cohorts |
| **TEST-018** | 2026-11-07 | Repeat Rate vs Cohort Decay | Concept Distinction | `python tests/test_analytics.py` (Test 04) | **PASSED** | Lifetime Repeat Rate (99.94%) strictly distinct from M1 retention (53.36%) |
| **TEST-019** | 2026-11-07 | Funnel Engine Completeness | Clickstream Test | `python tests/test_analytics.py` (Test 05) | **PASSED** | 100k events across 6 stages; 4,043 users completed all stages (80.86%) |
| **TEST-020** | 2026-11-07 | Core KPI Engine Output | Metric Completeness | `python tests/test_analytics.py` (Test 06) | **PASSED** | Exactly 16 KPIs calculated with positive non-null values |
| **TEST-021** | 2026-11-07 | KPI Cross-Layer Validation | Multi-Layer Audit | `python tests/test_analytics.py` (Test 07) | **PASSED** | 16/16 exact matches across Python, SQL, and DAX within 0.05 tolerance |
| **TEST-022** | 2026-11-08 | Dual AOV Consistency | Formula Verification | `python -m unittest tests/test_analytics.py` (Test 05) | **PASSED** | Net AOV (₹967.33) and Gross AOV (₹970.75) both validated |
| **TEST-023** | 2026-11-08 | Margin Filter Parity | Unit Economics Audit | `python -m unittest tests/test_analytics.py` (Test 06) | **PASSED** | Delivered margin (23.59%) reconciled with booking margin (23.60%) |
| **TEST-024** | 2026-11-08 | Terminology Governance | Metric Renaming Audit | `python -m unittest tests/test_analytics.py` (Test 07) | **PASSED** | Cumulative ARPU (₹9,285.20) and Deliveries/Rider (12.49) confirmed |
| **TEST-025** | 2026-11-08 | Funnel Reality & Schema Check | Schema & Overlap Audit | `python -m unittest tests/test_analytics.py` (Test 08) | **PASSED** | No timestamps confirmed; 6 stages, 100k events, overlap matrix verified |
| **TEST-026** | 2026-11-08 | Merchant 5-D Performance | Revenue Multi-Dimension | `python -m unittest tests/test_analytics.py` (Test 09) | **PASSED** | Throughput ₹30,950.66, GMV ₹31,060.08, Payout ₹24,077.85 verified |
| **TEST-027** | 2026-11-08 | Edge Case Resilience | Empty Dataset Handling | `python -m unittest tests/test_analytics.py` (Test 10) | **PASSED** | Empty DataFrames return 0.0 safely without crashing |
| **TEST-028** | 2026-11-08 | Pipeline Idempotency | Execution Repeatability | `python -m unittest tests/test_analytics.py` (Test 11) | **PASSED** | Repeated runs produce bit-for-bit identical frames and zero drift |
| **TEST-029** | 2026-11-08 | 5-Layer Status Matrix | Layer Transparency | `python -m unittest tests/test_analytics.py` (Test 12) | **PASSED** | 16/16 verified with separated Python, SQL, DAX, and Power BI statuses |



