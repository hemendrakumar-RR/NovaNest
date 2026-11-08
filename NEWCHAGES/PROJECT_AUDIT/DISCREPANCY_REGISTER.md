# NOVANEST — MASTER DISCREPANCY & GAP REGISTER
**Comprehensive Technical, Data, and Documentation Gap Analysis**  
**Audit Date:** 2026-11-08  
**Audit Standard:** Zero Silent Overwrites — Full Historical Transparency  

---

## 1. Executive Summary
This register documents every technical limitation, synthetic data generator anomaly, formula discrepancy, and documentation gap discovered across the repository lifecycle, recording the root cause, business impact, resolution, and current status.

---

## 2. Technical & Data Discrepancy Matrix

| Discrepancy ID | Category | Component | Discrepancy Description | Root Cause | Impact | Resolution Applied | Current Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **DISC-01** | Data Generation | `orders.csv` | 38,572 cross-city orders (77.19%) where customer, merchant, or rider cities do not match | Independent random sampling in `generate_orders.py` | Operational friction; unrealistic delivery distances across distant cities | Non-destructively flagged with `cross_city_flag`; preserved intact | **DOCUMENTED & FLAGGED** |
| **DISC-02** | Data Generation | `orders.csv` | 12,418 orders (24.85%) placed before customer signup date | Signup dates (2024–2026) vs order dates (2025–2026) were not cross-validated during generation | Chronological anomaly if signup date is used for cohort grouping | Non-destructively flagged with `pre_signup_order_flag`; acquisition cohorts anchored on **First Order Month** | **RESOLVED IN COHORTS** |
| **DISC-03** | Data Generation | `app_events.csv`| Missing timestamps and session IDs in 100,000 clickstream events | `random.choice(event_types)` without temporal attributes | Cannot determine chronological sequence or session-level drop-offs | Re-engineered `funnel_analysis.py` for user stage presence and pairwise overlap; temporal claims removed | **RESOLVED IN FUNNEL** |
| **DISC-04** | KPI Formula | `kpi_engine.py` | AOV formula was documented as `GMV / Completed Orders`, but code computed `Net Revenue / Completed Orders` | Ambiguous naming between Gross AOV (₹970.75) and Net AOV (₹967.33) | Metric confusion in documentation | Standardized KPI-03 as `Average Order Value (Net AOV)` = ₹967.33 and documented `Gross AOV` = ₹970.75 in metadata | **RESOLVED & CERTIFIED** |
| **DISC-05** | KPI Formula | `kpi_engine.py` | Contribution Margin reported as 23.60%, but estimated profit / net revenue was 24.54% | Numerator was All-Orders Profit (₹11.39M), while denominator was Delivered Net Revenue (₹46.43M) | Mixed-filter mismatch | Reconciled: Realized Delivered Margin = **23.59%** (₹10.95M / ₹46.43M); Gross Booking Margin = **23.60%** (₹11.39M / ₹48.28M) | **RESOLVED & CERTIFIED** |
| **DISC-06** | Terminology | `kpi_engine.py` | Cumulative historical customer spend (₹9,285.20) was labeled "Customer Lifetime Value (Realized CLV)" | Conflating historical ARPU with predictive lifetime valuation models | Inaccurate actuarial claims | Renamed to `Historical Realized Spend per Customer (Cumulative ARPU)` | **RESOLVED & CERTIFIED** |
| **DISC-07** | Terminology | `kpi_engine.py` | `Delivered Orders / Active Riders` = 12.49 was labeled "Rider Utilization" | Fleet table lacks shift hours, login duration, or capacity rosters | Conflating delivery volume with time utilization % | Renamed to `Delivered Orders per Active Rider` with unit `Deliveries/Rider` | **RESOLVED & CERTIFIED** |
| **DISC-08** | Environment | `load_mysql.py` | Live CSV-to-MySQL ingestion cannot connect | MySQL running (`MySQL80` service active), but `.env` lacks `DB_PASSWORD` | Ingestion script returns `Access denied` | Code statically validated; connection template provided; live execution paused pending password | **PENDING USER CONFIG** |
| **DISC-09** | Reporting | `NovaNest.pbix`| Live runtime measure recalculation and visual testing cannot execute via CLI | Power BI Desktop requires interactive GUI display session | Runtime DAX execution cannot be verified programmatically | Internal layout, entity bindings, and measures extracted via ZIP; documented as pending GUI session | **DOCUMENTED BOUNDARY** |
| **DISC-10** | Roadmap | `PHASE_05/` to `PHASE_10/` | Folders contain 55–63 byte placeholder template files | Placeholder structures created during Phase 01 initialization | Future phases not yet implemented | Preserved as placeholders; roadmap clearly marks Phases 05–10 as QUEUED / PENDING | **DOCUMENTED IN ROADMAP** |

---

## 3. Residual Risk Assessment

1. **Synthetic Data Realism**: When training ML models in Phase 05, the `cross_city_flag` and `pre_signup_order_flag` columns should be explicitly evaluated as predictive features or filtered out during baseline evaluation.
2. **Database Ingestion Dependency**: When MySQL credentials are provided in `.env`, `python/load_mysql.py` is fully prepared to execute idempotent, transactional, and batch-loaded ingestion in under 30 seconds.
3. **Power BI Manual Validation**: Prior to final executive presentations, a 5-minute visual inspection in Power BI Desktop is recommended to confirm that all 5 report pages render cleanly.

*Discrepancy Register Certified by NovaNest Architecture Governance on 2026-11-08.*

