# PHASE 04 — ADVANCED BUSINESS ANALYTICS & KPI FRAMEWORK PLAN

---

## 1. Objectives & Scope
1. **RFM Customer Segmentation Engine**:
   - Calculate Recency, Frequency, and Monetary scores across all 5,000 customers.
   - Assign evidence-based behavioral marketing segments (Champions, Loyal Customers, Potential Loyalists, At Risk, Cannot Lose Them, Hibernating, etc.).
   - Export customer-level and segment-level summary artifacts.
2. **Monthly Cohort Retention Matrix Engine**:
   - Establish customer acquisition cohort based on first order month.
   - Build monthly retention matrices (counts and percentages) spanning Month 0 to Month 12.
   - Strictly delineate lifetime repeat-purchase rate (99.94%) from monthly cohort retention (decay across time).
3. **Marketing Funnel Analysis Engine**:
   - Inspect and align with actual `app_events.csv` 3-column schema (`event_id`, `customer_id`, `event_type`).
   - Quantify conversion rates, drop-off rates, and identify largest leakage stages across the 6 supported event types.
4. **Core Business KPI Engine (16 KPIs)**:
   - Compute GMV, Net Revenue, AOV, Take Rate, Total Orders, Completed Orders, Cancellation Rate, SLA Breach Rate, Average Delivery Time, Rider Utilization, Restaurant Revenue, Contribution Margin, Estimated Profit, Repeat Rate, Cohort Retention, and Realized CLV.
   - Provide business definitions, formulas, source tables, filters, SQL equivalents, and DAX equivalents.
5. **Cross-Layer Validation Framework**:
   - Reconcile KPI outputs across Python, SQL analytical views, and Power BI DAX definitions within a 0.05 tolerance.
   - Distinguish verified static formulas from live MySQL execution.
6. **Automated Unit & Integration Test Suite**:
   - Create `tests/test_analytics.py` verifying mathematical integrity, null handling, and idempotency.

---

## 2. Key Deliverables
- `python/analytics/__init__.py`
- `python/analytics/rfm_segmentation.py`
- `python/analytics/cohort_analysis.py`
- `python/analytics/funnel_analysis.py`
- `python/analytics/kpi_engine.py`
- `python/analytics/validate_kpis.py`
- `tests/test_analytics.py`
- Data Artifacts in `datasets/analytics/` (`customer_rfm_segments.csv`, `rfm_segment_summary.csv`, `monthly_cohort_matrix.csv`, `monthly_cohort_counts.csv`, `app_funnel_summary.csv`, `kpi_summary.csv`, `kpi_definitions.json`, `kpi_cross_validation_matrix.csv`)
- Report: `reports/kpi_cross_validation_report.md`
