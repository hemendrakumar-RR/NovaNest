# PHASE 06 — SHARED CONTEXT, MEMORY & DATA GROUNDING DESIGN

- **Status**: `PROPOSED`

---

## 1. Shared `AgentContext` & Conversation Memory Architecture (`PROPOSED`)

Replaces un-scoped, unbounded `_SESSIONS` dict in [`python/ai/analyst/conversation_manager.py`](../../python/ai/analyst/conversation_manager.py).

### 1.1 Structure of `AgentContext` (Per Request + Session Store)
```text
ScopedSessionKey = "{principal.role}:{hmac_sha256(token_fingerprint)[:12]}:{sanitized_session_id}"
```
- **Session Isolation**: Two different API keys or roles passing `"session_id": "default"` NEVER share or overwrite conversation memory. When auth uses anonymous dev only? Auth in `api/auth.py` is already fail-closed (`401`/`503`); key scoping derives strictly from verified `AuthPrincipal` + HMAC token digest (raw secret is NEVER stored).
- **Stored Artifacts Inside Bounded `SessionState`**:
  1. `turns`: bounded deque (`max_turns = 12`, `max_chars_per_turn = 4000`, raw PII redacted if caller is `read`-only).
  2. `entity_memory`: active business filter state (`last_city`, `last_domain`, `last_customer_id` — `operator`/`admin` only, `last_restaurant_id`, `last_kpi_ids`).
  3. `last_agent_outputs`: compact structured summary (metric IDs, values, SQL query hash, NO large raw DataFrames kept in session RAM).
  4. `business_glossary`: read-only reference to canonical terms (`GMV != Net Revenue`, `Leakage = Investigation Candidate`, `Avg Delivery Time = 37.38m`).
  5. `metadata`: `created_at`, `last_accessed_at`, `turn_count`.

### 1.2 Lifecycle, Concurrency, TTL & Retention (`PROPOSED`)
| Policy Dimension | Proposed Standard | Enforcement Mechanism |
|---|---|---|
| **Thread / Async Safety** | Safe concurrent `/api/ai/ask` requests | `threading.RLock()` around `_SESSION_STORE` read/write/evict |
| **Idle TTL Expiration** | **30 minutes** (`1800s`) | Lazy sweep on read + periodic prune when store size exceeds threshold |
| **Max Session Cap** | **250 active sessions** (LRU eviction) | `collections.OrderedDict` moving accessed key to tail, evicting oldest on overflow |
| **Raw Payload Retention** | Zero raw SQL `data_rows` persisted across turns | Store only metadata/KPI summary (`<= 2 KB` per turn) in RAM; no unencrypted disk persistence of user prompts or customer PII |
| **Sensitive Storage Rule** | Zero passwords, tokens, raw phone/email strings stored in `AgentContext` | Redact email/phone regex patterns prior to recording turn logs |

---

## 2. Authoritative Data Grounding Architecture (`PROPOSED`)

### 2.1 `DatasetMetadataRegistry` (`PROPOSED`, derived from verified CSV inspection)
Provides agents with exact column names, row counts, null-handling rules, and join keys—eliminating silent schema drift bugs like `restaurants["rating"]` vs `avg_rating` and `rider_allocation.csv` `current_riders` vs `recommended_rider_id`.

| Dataset Key (`api/loader.py`) | Source Directory | Verified Rows | Key Columns / Schema Facts (`VERIFIED`) | Grounding Caveats |
|---|---|---|---|---|
| `orders` | `datasets/cleaned/` | `49,971` | `order_id, customer_id, restaurant_id, item_id, rider_id, order_datetime, order_amount, final_amount, order_status` | Filter `!= 'Cancelled'` (`47,994` Delivered; `1,977` Cancelled) per metric rule |
| `orders_engineered` | `datasets/engineered/` | `49,971` (`38 cols`) | `commission_revenue, estimated_profit, profit_margin_pct, discount_percentage, delivery_delay_flag, pre_signup_order_flag` | Canonical source for `KPI-04`, `KPI-12`, `KPI-13` |
| `customers` | `datasets/cleaned/` | `5,000` | `customer_id, customer_name, city, persona, occupation, signup_date` | PII masked/omitted for `read`-only role |
| `restaurants` | `datasets/cleaned/` | `1,500` | `restaurant_id, restaurant_name, city, cuisine_type, avg_rating, delivery_radius_km` | Use `avg_rating` (NEVER legacy `rating`) |
| `deliveries` | `datasets/cleaned/` | `49,971` | `delivery_id, order_id, rider_id, distance_km, delivery_duration` | Mean `37.38m`; `32.26%` (`16,120`) `> 45m`; uncorrelated with distance (`r=-0.0029`) |
| `riders`, `menu_items`, `payments`, `promotions`, `ratings_reviews` | `datasets/cleaned/` | `4k / 15k / 50k / 200 / 28.8k` | Complete relational tables (`promotions` lacks FK in `orders`; `ratings_reviews` has `restaurant_rating, delivery_rating`) | `app_events` (`100k`) lacks timestamps -> excluded from SQL sandbox / survival modeling |
| `customer_churn_predictions` | `datasets/engineered/` | `5,000` | `Churn_Probability, Churn_Risk` (`781` `High Risk` = `15.62%`) | `NEEDS_MORE_DATA` (`ROC-AUC=0.5161`) |
| `demand_forecasts` / `demand_heatmap` | `datasets/engineered/` | `1,760` / `5` | `date, city, actual_orders, predicted_orders, lower_bound, upper_bound` | `BASELINE_ONLY` (`Pooled R2=0.7707` scale artifact; city `R2 < 0`) |
| `eta_predictions` / `rider_allocation` | `datasets/engineered/` | `49,971` / `2,000` | ETA: `predicted_eta, eta_error`; Alloc: `order_city, recommended_rider_id, workload_tier` | ETA `BASELINE_ONLY` (`MAE=11.52m`); Alloc has NO `current_riders` column |
| `restaurant_predictions` | `datasets/engineered/` | `1,500` | `Total_Orders, Total_Revenue, Cancellation_Rate, Predicted_Next_Month_Orders` | `NEEDS_MORE_DATA` (`R2=-0.0027`, `MAE=1.3248`) |
| `revenue_leakage` / `operational_anomalies` / `operational_alerts` | `datasets/engineered/` | `4,669` / `2,184` / `2` | `leakage_type, potential_leakage_amount` (`₹553,946.31`), `false_positive_risk`; Anomalies: `Entity_ID, Metric, Deviation_Pct, Severity` | **`EXPERIMENTAL`**: unverified candidates; NEVER label `"Confirmed Loss"` |

### 2.2 Certified Metric & Formula Registry (`kpi_definitions.json`)
`kpi_registry.py` (`PROPOSED`) loads [`datasets/analytics/kpi_definitions.json`](../../datasets/analytics/kpi_definitions.json) at startup and binds every domain agent's metric lookup to the `16` audited definitions:
- `KPI-01` GMV = `SUM(order_amount) WHERE order_status != 'Cancelled'` (`₹46,590,125.00`)
- `KPI-02` Net Revenue = `SUM(final_amount) WHERE order_status = 'Delivered'` (`₹46,425,992.00`)
- `KPI-03` Net AOV = `₹967.33` (Gross AOV = `₹970.75`)
- `KPI-04` Take Rate = `22.48%`
- `KPI-07` Cancellation Rate = `3.96%` (`1,977 / 49,971`)
- `KPI-08` SLA Breach Rate (`> 45m`) = `32.26%` (`16,120 / 49,971`)
- `KPI-09` Avg Delivery Time = `37.38 mins`
- `KPI-12` / `KPI-13` Contribution Margin = `23.59%` (`₹10,953,031.58` realized profit)
- `KPI-14`..`KPI-16`: Repeat Purchase (`99.94%`), M1 Cohort Retention (`53.36%`), Cumulative ARPU (`₹9,285.20`)

### 2.3 Storage & Execution Path Strategy (CSV + SQLite Sandbox + Optional MySQL)
1. **Tier-1 Primary Analytical Store (`VERIFIED`)**: `api/loader.py` singleton CSV store + unified `9`-table in-memory Read-Only SQLite sandbox (`orders, customers, restaurants, deliveries, riders, promotions, ratings_reviews, menu_items, payments`), ensuring `orchestrator.py` and `api/main.py` both load all `9` tables rather than `orchestrator.py`'s current `6`-table subset (`L134`).
2. **Dynamic Cache Freshness**: `loader.py` checks file `mtime_ns` signature before serving cached DataFrames (no stale cache if engineered CSVs regenerate).
3. **Live MySQL Mode (`BLOCKED` Currently)**: Remains gated behind [`streamlit_app/database/connection.py`](../../streamlit_app/database/connection.py) / `api/loader.py::get_db_connection()` using `.env` credentials (`novanest_db`, `orders_table`) with `SET SESSION TRANSACTION READ ONLY` and `max_execution_time = 2000`, falling back automatically to Tier-1 CSV/SQLite while `1045 (28000)` persists.
4. **No Invented Facts Rule**: If a user asks about uncollected data (e.g., *"customer support chat transcripts"*, *"real-time GPS traffic"*, *"promo_id ROI attribution"*), agents return explicit `limitations` stating the dataset gap—NEVER invoking general LLM knowledge to fabricate platform figures.

