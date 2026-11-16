# NovaNest — Phase 17 Performance Baseline Audit

**Timestamp**: 2026-11-15T19:15:00+05:30  
**Environment**: Production Docker Network (`novanest_network`)  
**Database**: MySQL 8.0.46 (`novanest_db`, 304,405 records)  

---

## 1. Executive Summary

This document establishes the pre-optimization performance, resource utilization, latency, and scalability baseline for the NovaNest platform prior to any modifications in Phase 17. All measurements were conducted on the live, un-optimized platform with all security and RBAC controls fully enabled.

---

## 2. Infrastructure & Container Baseline

| Service | Container Name | Status | Base Memory Usage | Port Binding | Health Check |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API Backend** | `novanest-api` | Healthy | ~240 MB | 8001 -> 8000 | `/api/health` |
| **Database** | `novanest-db` | Healthy | ~410 MB | 3306 -> 3306 | `mysqladmin ping` |
| **Frontend Web** | `novanest-frontend` | Healthy | ~18 MB | 80 -> 80 | Nginx port 80 |
| **Streamlit BI** | `novanest-streamlit` | Healthy | ~195 MB | 8502 -> 8501 | Streamlit healthz |
| **Metrics Collector** | `novanest-prometheus` | Healthy | ~45 MB | 9090 -> 9090 | Prometheus UP |
| **Dashboards** | `novanest-grafana` | Healthy | ~62 MB | 3001 -> 3000 | Grafana API health |

---

## 3. Canonical Database Row Count Baseline

All 10 canonical tables in `novanest_db` verified intact prior to audit:

| Table Name | Row Count | Primary Key | Foreign Keys | Status |
| :--- | :--- | :--- | :--- | :--- |
| `customers` | 5,000 | `customer_id` | 0 | Verified Canonical |
| `restaurants` | 1,500 | `restaurant_id` | 0 | Verified Canonical |
| `menu_items` | 15,000 | `item_id` | 1 (`restaurant_id`) | Verified Canonical |
| `riders` | 4,000 | `rider_id` | 0 | Verified Canonical |
| `orders_table` | 49,971 | `order_id` | 4 (`cust`, `rest`, `item`, `rider`) | Verified Canonical |
| `deliveries` | 49,971 | `delivery_id` | 2 (`order_id`, `rider_id`) | Verified Canonical |
| `payments` | 49,971 | `payment_id` | 1 (`order_id`) | Verified Canonical |
| `ratings_reviews` | 28,792 | `review_id` | 2 (`order_id`, `customer_id`) | Verified Canonical |
| `promotions` | 200 | `promo_id` | 0 | Verified Canonical |
| `app_events` | 100,000 | `event_id` | 1 (`customer_id`) | Verified Canonical |
| **TOTAL** | **304,405** | — | **11 Foreign Keys** | **100% INTACT** |

---

## 4. Frontend Asset & Bundle Size Baseline

Pre-optimization Vite production build (`dist/`):

- **Main Application Chunk**: `dist/assets/index-CE_61vtv.js` = **995.65 kB** (gzip: **266.14 kB**)
- **Visual Effects Chunk**: `dist/assets/glassParticleField-DgSq-Qn4.js` = **517.18 kB** (gzip: **128.97 kB**)
- **Retro Effects Chunk**: `dist/assets/retroPixelField-QMb3Zo4Q.js` = **5.23 kB** (gzip: **2.42 kB**)
- **Global CSS Bundle**: `dist/assets/index-C0d0ckKY.css` = **181.27 kB** (gzip: **43.65 kB**)
- **Total Initial JS Payload**: **1,518.06 kB** uncompressed
- **Vite Warning**: `(!) Some chunks are larger than 500 kB after minification.`
- **Code-Splitting Status**: 0 route-based code-splitting chunks; all 10 domain views and Copilot are bundled into the monolithic main chunk.

---

## 5. API Response Time Baseline (N=5 Iterations)

Measured using authenticated HTTP requests (`Bearer test-operator-key-phase06-8`):

| Endpoint | HTTP Method | Min Latency | p50 Latency | Max Latency | Mean Latency | Primary Bottleneck |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/health` | GET | 12.5 ms | 15.6 ms | 33.1 ms | 18.7 ms | Low (health ping) |
| `/api/overview` | GET | 1281.0 ms | 1399.0 ms | 1422.2 ms | **1373.1 ms** | Pandas dataframe scans & aggregation |
| `/api/customer/overview` | GET | 1083.9 ms | 1166.3 ms | 1289.9 ms | **1179.1 ms** | Customer order grouping & churn join |
| `/api/restaurant/overview`| GET | 812.1 ms | 902.8 ms | 942.4 ms | **886.8 ms** | Merchant aggregation & rating mean |
| `/api/operations/overview`| GET | 290.5 ms | 376.9 ms | 446.0 ms | **370.3 ms** | Delivery duration calculation |
| `/api/financial/overview` | GET | 901.1 ms | 1036.2 ms | 1323.1 ms | **1076.2 ms** | Certified KPI calculation & previous period |
| `/api/copilot/summaries`  | GET | 45.5 ms | 56.6 ms | 76.0 ms | **59.2 ms** | Summary generation |
| `/api/copilot/alerts`     | GET | 25.0 ms | 30.5 ms | 53.4 ms | **35.3 ms** | Proactive alert generator |
| `/api/copilot/query`      | POST | 777.7 ms | 947.6 ms | 2064.7 ms | **1119.7 ms** | Multi-agent orchestration & fact verifier |

---

## 6. MySQL Query Execution Plan Baseline

EXPLAIN ANALYZE results on common analytical queries:

1. **City Aggregation Query** (`orders_table` JOIN `customers` on `order_status != 'Cancelled'`):
   - Execution Time: **865.0 ms**
   - Plan: Table scan on `orders_table` (49,971 rows) -> Nested loop inner join -> Stream results (47,994 rows) -> Sort: `c.city` (795 ms) -> Group aggregate.
   - Bottleneck: Missing composite index on `(order_status, customer_id, final_amount)` causes full table scan and massive temporary sort.

2. **Date Range Aggregation** (`orders_table` WHERE `order_datetime >= '2024-01-01'` GROUP BY `order_status`):
   - Execution Time: **209.0 ms**
   - Plan: Index scan on `idx_orders_status` -> Filter on `order_datetime` (49,971 rows).
   - Bottleneck: Non-composite index requires filtering all 49,971 rows after index scan.

---

## 7. Audit Findings & Targets for Phase 17

| Area | Baseline State | Phase 17 Target | Improvement Strategy |
| :--- | :--- | :--- | :--- |
| **Frontend Bundle** | 995.65 kB main chunk | < 450 kB main chunk | `React.lazy` + `Suspense` route-based splitting + manual chunks |
| **Executive Overview API** | 1,373 ms latency | < 50 ms (cached) / < 400 ms (uncached) | High-speed memory/Redis cache layer + vector aggregation |
| **Pagination** | Unbounded (all rows into memory) | Standardized page/cursor with limit | `/api/records/{entity}` pagination engine with index utilization |
| **AI Copilot Latency** | 1,119 ms average | < 450 ms average | Parallelized agent execution + fact synthesis optimization |
| **Database Queries** | 865 ms city join | < 80 ms city join | Targeted composite index additions with verified read/write profile |
| **Concurrency (50 Users)**| High CPU spikes, queueing | Stable p95 < 250ms | Thread/async connection pooling & non-blocking cache hits |
