# NOVANEST — PHASE 06.8 PHASE PLAN
## MySQL Application Integration and Full-Stack End-to-End Validation

---

## 1. Executive Summary & Objective

With the completion of Phase 06.7, the NovaNest platform has achieved live MySQL database connectivity, least-privilege user isolation (`novanest_loader` and `novanest_app`), and 100% successful ingestion of all 10 datasets (304,405 records, 11 foreign keys, 19 secondary indexes) into `novanest_db`.

The objective of **Phase 06.8** is to:
1. Conduct a comprehensive full-stack integration audit of all data access paths across FastAPI, Streamlit, and React.
2. Establish a unified, configurable data-source routing mechanism supporting seamless switching between `DATA_SOURCE=mysql` and `DATA_SOURCE=csv` with automated fallbacks.
3. Validate MySQL read paths across all 10 relational tables, verifying schema integrity, non-empty records, representative queries, and multi-table relational joins.
4. Execute mathematical and financial KPI reconciliation comparing all 16 certified business metrics between CSV and MySQL, targeting 100.00% parity with 0.0% variance.
5. Validate all 5 AI Domain Agents (`FinancialAgent`, `CustomerAgent`, `OperationsAgent`, `RestaurantAgent`, `DecisionAgent`) running directly on live MySQL data, verifying provenance, calculation accuracy, and zero schema regressions.
6. Verify all frontend entry points (React dashboard build, FastAPI REST endpoints, and Streamlit analytics pages) operate stably against MySQL.
7. Provide production-ready operational procedures for controlled runtime switching and instant zero-downtime rollback to CSV.

---

## 2. Strict Safety & Governance Boundaries

During Phase 06.8 execution, the following boundaries were strictly enforced:
1. **Database Immutability**: Preserved all 304,405 MySQL records in `novanest_db`; zero tables dropped, altered, or truncated.
2. **Authoritative CSV Protection**: Source CSV datasets remained untouched as permanent disaster-recovery fallbacks.
3. **Zero Plaintext Credential Exposure**: Passwords and secrets were never printed, logged, or emitted in telemetry.
4. **Least-Privilege Enforcement**: Application queries strictly executed under `novanest_app@localhost` credentials.
5. **Zero Git Modifications**: No commits, pushes, resets, branches, or deployments executed.
6. **Default Safety Mode**: Kept `DATA_SOURCE=csv` as the safe default in configuration, enabling `DATA_SOURCE=mysql` via explicit environment override.
7. **Governance Preservation**: Maintained the exact directory spelling of `NEWCHAGES/` and updated all historical registers.

---

## 3. Workstream Breakdown & Deliverables

### Workstream 1: Data Source Architecture Harmonization
- Audit `api/loader.py`, `streamlit_app/utils/data_loader.py`, and `streamlit_app/database/connection.py`.
- Implement dynamic data source resolution: if `DATA_SOURCE=mysql`, inspect connectivity and verify table population (`SELECT COUNT(*) FROM customers > 0`).
- Implement dynamic connection pool invalidation keyed by `(db_host, db_port, db_user, db_name)`.
- Ensure zero-crash fallback to CSV if MySQL is unreachable, timed out, or unpopulated.

### Workstream 2: MySQL Read-Path & Relational Join Validation
- Query all 10 tables through application DB abstraction.
- Verify exact row counts: `customers` (5,000), `restaurants` (1,500), `riders` (4,000), `promotions` (200), `menu_items` (15,000), `orders_table` (49,971), `payments` (49,971), `deliveries` (49,971), `ratings_reviews` (28,792), `app_events` (100,000). Total: 304,405 records.
- Verify relational join integrity across `orders_table`, `customers`, `restaurants`, `menu_items`, `deliveries`, and `payments`.

### Workstream 3: Certified KPI Reconciliation
- Compare 16 certified metrics calculated from CSV against MySQL:
  - Total Orders, Delivered Orders, Cancelled Orders, Fulfillment Rate
  - Total GMV, Delivered GMV, Net Revenue, AOV, Net AOV
  - Customer Count, Active Restaurants, Active Delivering Riders
  - Avg Delivery Duration, Avg Distance KM, Repeat Order Rate, Average Rating.
- Confirm 0.00% variance across all metrics.

### Workstream 4: AI Domain Agents MySQL Execution
- Run all 5 domain agents against live MySQL in-memory and relational queries.
- Verify `AgentStatus.SUCCESS`, execution trace telemetry, and data provenance.

### Workstream 5: Frontend & Endpoint Verification
- Validate React frontend production build (`npm run build`).
- Verify FastAPI authenticated REST endpoints under MySQL data.
- Verify Streamlit dashboard runtime execution and page compatibility.

### Workstream 6: Integration Testing & Verification Runbook
- Author automated integration test suite `tests/test_phase06_8_application_integration.py` (14 comprehensive test cases).
- Execute full platform regression sweep (190+ tests across 14 suites).
- Document switchover and rollback procedures.

