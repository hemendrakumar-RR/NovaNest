# NovaNest — Relational Database Architecture & SQL Audit

## 1. Relational Database Schema Design
- **Database Engine**: MySQL 8.0+ (InnoDB Engine).
- **Schema Model**: Constellation / Multi-Fact Star Schema centered on `orders` and `deliveries`.
- **Core Entity Tables (10 Tables)**:
  1. `customers`: 5,000 records. Customer demographics, signup dates, cities.
  2. `restaurants`: 1,500 records. Partner metadata, cuisine types, ratings, commission tiers.
  3. `riders`: 4,000 records. Delivery fleet details, vehicle types, ratings.
  4. `orders`: 49,971 records. Primary transactional fact table with financial amounts and status.
  5. `deliveries`: 49,971 records. Operational fact table with pickup/delivery timestamps, distance, and duration.
  6. `payments`: 49,971 records. Payment methods, transaction status, discount codes.
  7. `order_items`: ~150,000 records. Line-item details linking orders to menu items.
  8. `menu_items`: 15,000 records. Product catalog with categories, base prices, preparation times.
  9. `ratings_reviews`: 28,792 records. Customer review scores, feedback text, sentiment.
  10. `app_events`: 100,000 records. User behavioral stream (searches, clicks, cart adds, checkouts).

## 2. SQL Scripts Inventory & Quality Review (`mysql/`)
| Script | Lines | Core Objectives | Quality & Safety Assessment |
|---|---|---|---|
| `01_schema.sql` | 145 | DDL Table creation, primary keys, foreign keys | Fully normalized, InnoDB, UTF8MB4. |
| `02_indexes.sql` | 82 | Secondary composite indexes | B-Tree indexes on FKs, dates, and status codes. |
| `03_views.sql` | 115 | Standard reporting views | Daily sales, restaurant ratings, city volume. |
| `04_stored_procedures.sql` | 160 | ETL maintenance & alerts | `sp_refresh_daily_kpis`, `sp_flag_sla_breaches`. |
| `05_triggers.sql` | 74 | Data integrity triggers | Validates status transitions and timestamp sequencing. |
| `06_analytics_queries.sql` | 195 | Complex analytical SQL | Customer RFM, CLV, Rider earnings. |
| `07_maintenance.sql` | 55 | Optimization routines | `OPTIMIZE TABLE`, index statistics rebuild. |
| `08_phase3_analytical_views.sql` | 210 | Workspace analytical views | 6 Enterprise views with window functions (`ROW_NUMBER`, `DENSE_RANK`, `SUM OVER`). |
| `08_phase3_intelligence.sql` | 67 | Archive intelligence queries | Analytical CLV, RFM base CTEs, cohort retention. |
| `09_phase4_operations.sql` | 88 | Archive operations views | `view_daily_city_demand`, `view_delivery_sla_performance`. |

## 3. Workspace vs Archive SQL Discrepancies
- **Discrepancy**: In the Capstone archive, `08_phase3_intelligence.sql` contains raw `SELECT` queries rather than permanent database views.
- **Workspace Enhancement**: In `NovaNest-main`, `08_phase3_analytical_views.sql` replaces these with 6 production-grade `CREATE OR REPLACE VIEW` statements, adding formal database views:
  1. `view_customer_rfm_segments`
  2. `view_restaurant_performance_matrix`
  3. `view_rider_efficiency_and_sla`
  4. `view_daily_financial_unit_economics`
  5. `view_monthly_cohort_retention`
  6. `view_app_funnel_conversion_dropoff`

## 4. Query Performance & Indexing Strategy
- Composite indexes established on `orders(customer_id, order_datetime)` and `orders(restaurant_id, order_datetime)`.
- Operational lookups on `deliveries(rider_id, delivery_status)` achieve index seek with $O(\log N)$ complexity.
- Zero Cartesian product joins identified in analytical views.
