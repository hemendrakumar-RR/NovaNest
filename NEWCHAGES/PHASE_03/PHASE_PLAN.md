# PHASE 03 — MYSQL & DATABASE OPTIMIZATION PLAN

---

## 1. Objectives & Scope
1. **SQL Syntax Sanitization**:
   - Inspect files `01_schema.sql` through `07_level6_strategy_analytics.sql`.
   - Convert all un-commented emoji titles, markdown notes, and prose descriptions into valid SQL comments (`--`).
   - Preserve original query logic intact.
2. **Retention Query Refactor**:
   - Refactor Query 2 in `07_level6_strategy_analytics.sql` using a modern Common Table Expression (CTE) grouping by `customer_id`.
   - Cross-validate retention calculation against an independent Python result.
3. **Automated MySQL Ingestion Pipeline**:
   - Develop `python/load_mysql.py` supporting environment-based configuration, table verification, batch loading, foreign-key safe execution order, and transaction control.
4. **Optimized Analytical Views**:
   - Create `mysql/08_optimized_views.sql` with 7 production-grade analytical views (`vw_customer_rfm`, `vw_monthly_cohort_retention`, `vw_unit_economics`, `vw_rider_efficiency`, `vw_restaurant_performance`, `vw_monthly_revenue`, `vw_customer_lifetime_value`).
5. **Static & Dynamic SQL Validation**:
   - Statically validate all 8 SQL files for syntax errors, balanced clauses, and schema consistency.
   - Document live MySQL service and credential status clearly without inventing credentials.

---

## 2. Key Deliverables
- Sanitized `mysql/03_level2_business.sql` (15 queries)
- Sanitized `mysql/04_level3_intermediate.sql` (20 queries)
- Sanitized `mysql/05_level4_advanced.sql` (15 queries)
- Sanitized `mysql/06_level5_executive.sql` (10 queries)
- Corrected `mysql/07_level6_strategy_analytics.sql` (16 queries)
- New file: `mysql/08_optimized_views.sql` (7 analytical views)
- New file: `python/load_mysql.py` (Automated data loader)
- Validation report: `NEWCHAGES/PHASE_03/SQL_VALIDATION_REPORT.md`
