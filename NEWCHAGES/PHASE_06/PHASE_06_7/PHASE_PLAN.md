# NOVANEST — PHASE 06.7 PHASE PLAN
## MySQL Database Integration & Connectivity Restoration

---

## 1. Executive Summary & Objective

NovaNest is an AI-powered Food Delivery Analytics and Decision Intelligence Platform. Prior to Phase 06.7, the application relied on an authoritative CSV file store (`datasets/cleaned/` and `datasets/engineered/`), while attempts to connect to local MySQL failed with:
```
mysql.connector.errors.ProgrammingError: 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)
```

The objective of **Phase 06.7** is to:
1. Conduct a rigorous, non-destructive diagnosis of the MySQL Error 1045 to isolate its exact root cause.
2. Inspect environment configuration, connection modules, API dependencies, and relational database schemas.
3. Harden database connection management across both FastAPI (`api/loader.py`) and Streamlit (`streamlit_app/database/connection.py`) with thread-safe connection pooling, connection timeouts, support for least-privilege application credentials, parameterized queries, and safe credential logging.
4. Establish an ironclad, zero-crash fail-safe mechanism where any database unreachable condition or authentication error transparently falls back to the authoritative CSV file store without data loss or downtime.
5. Perform an exhaustive schema discrepancy and referential integrity audit across all 10 core tables (294,405 records), validating column schemas, primary keys, and foreign keys.
6. Provide a complete test suite verifying both database resilience and end-to-end regression integrity.
7. Document a precise, operator-executable remediation runbook for synchronizing MySQL credentials without inventing or guessing passwords.

---

## 2. Strict Safety & Governance Boundaries

During Phase 06.7 execution, the following boundaries were strictly maintained:
1. **Zero Credential Invention**: Never guessed passwords, never fabricated secrets, and never wrote invented credentials into `.env`.
2. **Environment File Preservation**: `.env` and `.env.example` were inspected without printing secrets, and were never overwritten or deleted.
3. **Non-Destructive Database Operations**: No tables were dropped, truncated, or modified on the host MySQL instance.
4. **Authoritative CSV Protection**: Maintained the CSV dataset as the operational ground truth, ensuring 100% platform availability.
5. **Zero Git Modifications**: No commits, pushes, resets, branches, or deployments were executed.
6. **Governance Preservation**: Maintained the exact directory spelling of `NEWCHAGES/` and preserved all historical audit logs.

---

## 3. Scope of Work & Architectural Workstreams

### Workstream 1: MySQL Environment & Service Diagnosis
- Inspect Windows service `MySQL80` (status, PID, startup mode, listening ports).
- Trace `.env` configuration keys (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
- Inspect MySQL Workbench profile configuration and Windows Credential Manager storage.
- Attempt controlled connections across loopback interfaces (`localhost`, `127.0.0.1`, `::1`) and auth plugins (`caching_sha2_password`, `mysql_native_password`).
- Isolate the exact root cause of Error 1045.

### Workstream 2: Connection Hardening & Resilient Pooling
- Upgrade `api/loader.py` `get_db_connection()` to utilize `mysql.connector.pooling.MySQLConnectionPool` with a configurable pool size (`DB_POOL_SIZE=5`).
- Upgrade `streamlit_app/database/connection.py` with identical connection pooling logic.
- Implement strict connection timeouts (`connect_timeout=3` seconds) to prevent blocking during service unavailability.
- Support dedicated, least-privilege user credentials (`DB_APP_USER` / `DB_APP_PASSWORD`) with graceful fallback to `DB_USER` / `DB_PASSWORD`.
- Guarantee non-sensitive logging: log only MySQL error numbers (`errno`) and SQL state (`sqlstate`), never emitting connection strings or passwords into logs.
- Guarantee transparent fallback to the CSV file store on any connection or query failure.

### Workstream 3: Relational Schema & Discrepancy Analysis
- Parse and validate `mysql/01_schema.sql` (10 tables: `customers`, `restaurants`, `menu_items`, `riders`, `orders_table`, `payments`, `deliveries`, `app_events`, `ratings_reviews`, `promotions`).
- Audit clean CSV datasets in `datasets/cleaned/` against SQL table schemas.
- Reconcile naming discrepancies (`orders_table` in SQL vs `orders.csv` in file store; `novanest_db` in SQL scripts vs `novanest` in `.env`).
- Verify dual-table name mapping support in `api/loader.py` and `python/load_mysql.py`.

### Workstream 4: Data Quality & Referential Integrity Audit
- Audit all 294,405 records across all 10 CSV datasets.
- Verify primary key uniqueness (0 null IDs, 0 duplicates).
- Verify foreign key integrity across all parent-child relationships (`orders -> customers`, `orders -> restaurants`, `orders -> riders`, `deliveries -> orders`, `payments -> orders`).
- Verify ETL ingestion pipeline (`python/load_mysql.py`) for transactional safety, chunked execution, and idempotent insertion (`INSERT IGNORE INTO`).

### Workstream 5: Verification, Regression Testing & Documentation
- Build comprehensive Phase 06.7 integration suite (`tests/test_phase06_7_mysql_integration.py`).
- Run full 13-suite regression sweep covering all previous phases (04 through 06.6).
- Verify Vite frontend production build and Streamlit page runtime smoke tests.
- Deliver governance records under `NEWCHAGES/PHASE_06/PHASE_06_7/` and update master registers.

