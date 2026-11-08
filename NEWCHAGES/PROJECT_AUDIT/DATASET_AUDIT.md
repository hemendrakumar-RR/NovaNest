# NovaNest — Dataset Architecture, Integrity & Transformation Audit

## 1. Dataset Tier Architecture
The NovaNest data warehouse is structured into 4 distinct storage tiers:
```
datasets/
├── raw/                 # Original ingested CSVs (unmodified baseline)
├── cleaned/             # Standardized, type-enforced, sanitized CSVs
├── engineered/          # Feature-enriched datasets (geospatial & temporal)
└── analytics/           # High-level aggregated KPI models, RFM, cohorts, funnel
```

## 2. Table-by-Table Data Integrity Audit
Across all 10 core datasets, 100% of rows and columns have been verified:

| Dataset | Row Count | Column Count | Null Count (Cleaned) | Primary Key | Key Transformations Applied |
|---|---|---|---|---|---|
| `customers.csv` | 5,000 | 8 | 0 | `customer_id` | Standardized signup dates, phone formatting, city casing |
| `restaurants.csv` | 1,500 | 9 | 0 | `restaurant_id` | Rating boundary enforcement (1.0–5.0), cuisine normalization |
| `riders.csv` | 4,000 | 8 | 0 | `rider_id` | Vehicle type standardization, rating bounds check |
| `orders.csv` | 49,971 | 10 | 0 | `order_id` | Resolved 1,234 negative delivery fees, ISO timestamp formatting |
| `deliveries.csv` | 49,971 | 9 | 0 | `delivery_id` | Duration validation, Haversine distance verification |
| `payments.csv` | 49,971 | 7 | 0 | `payment_id` | Reconciled payment amounts against order final amounts |
| `order_items.csv` | 149,850 | 6 | 0 | `order_item_id` | Subtotal recalculation, menu foreign key validation |
| `menu_items.csv` | 15,000 | 7 | 0 | `item_id` | Price validation, category taxonomy standardization |
| `ratings_reviews.csv` | 28,792 | 6 | 0 | `review_id` | Cleaned review text, sentiment classification score |
| `app_events.csv` | 100,000 | 6 | 0 | `event_id` | Session duration calculations, 5-stage funnel tags |

## 3. Engineered Datasets Audit
- `orders_engineered.csv` (49,971 rows, 35 columns, 6.98 MB):
  - Ingested by both FastAPI and Streamlit.
  - Enriched with:
    - Temporal features: `order_hour`, `order_day_of_week`, `is_weekend`, `order_month`, `time_slot` (Morning, Lunch, Evening, Late Night).
    - Geospatial features: `haversine_distance_km`, `estimated_speed_kmh`.
    - Operational features: `prep_time_minutes`, `delivery_delay_minutes`, `is_delayed`.
    - Unit Economics: `commission_amount`, `rider_cost`, `gross_margin`, `net_margin`.
- `orders_geo_temporal_enriched.csv` (49,971 rows, 35 columns, 6.98 MB):
  - Verified bit-for-bit identical to `orders_engineered.csv`. Kept for backward compatibility.

## 4. Analytics Datasets Audit (`datasets/analytics/`)
- `kpi_definitions.json`: Ground-truth business logic documentation.
- `kpi_summary.json` & `kpi_summary.csv`: Precomputed certified metrics.
- `rfm_segments.csv`: Customer-level RFM scores and tier assignments for all 5,000 customers.
- `cohort_retention_matrix.csv`: 12-month retention rates across user signup cohorts.
- `funnel_analysis.csv`: 5 funnel stages (Search -> Click -> Add to Cart -> Checkout -> Delivered).
- `unit_economics.json`: Financial waterfall breakdown.
