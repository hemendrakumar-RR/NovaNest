# Phase 06.9 Plan — Controlled MySQL Activation & Live Application Validation

## 1. Executive Objective
Perform a fully controlled, verified activation of the local MySQL 8.0.46 database (`novanest_db`, 304,405 records across 10 tables) as the primary data source for NovaNest (`DATA_SOURCE=mysql`), replacing the baseline CSV file store while preserving zero-downtime automated fallback, zero data mixing, and complete historical KPI fidelity.

---

## 2. Scope & Core Requirements
1. **Pre-Activation Audit**:
   - Verify MySQL Windows service `MySQL80` running on `localhost:3306`.
   - Verify all 10 operational tables contain exactly 304,405 records.
   - Verify least-privilege users `novanest_app` and `novanest_loader` authenticate cleanly with 0 credentials leaked.
   - Confirm baseline `DATA_SOURCE=csv` before activation.
2. **Safe Rollback & Port Audit**:
   - Verify ports 8000 (FastAPI) and 8501 (Streamlit) are free before launch.
   - Maintain instant rollback capability to CSV.
3. **Controlled Activation**:
   - Configure `DATA_SOURCE=mysql` and API keys in `.env` without exposing secrets.
   - Launch FastAPI Uvicorn on port 8000 and Streamlit on port 8501.
4. **Live Network & Endpoint Validation**:
   - Verify `GET /api/health` and `GET /api/diagnostics/data-source` report `MySQL Database` with `fallback_active=false`.
   - Validate Executive, Financial, Customer, Operations, and Restaurant dashboards over live HTTP.
   - Verify all 5 domain AI agents (Financial, Customer, Operations, Restaurant, Decision) and Master Orchestrator.
   - Validate `POST /api/ai/ask` live conversational endpoint.
5. **Certified KPI Parity**:
   - Reconcile 5 core certified KPIs against authoritative ground truth (Total Orders: 49,971, Delivered Orders: 47,994, Delivered GMV: ₹46,590,125.00, Net Revenue: ₹46,425,992.00, Net AOV: ₹967.33).
6. **Controlled Fallback Simulation**:
   - Simulate database downtime (unreachable host).
   - Validate immediate 100% failover to CSV with diagnostic logging and zero partial data mixing.
   - Restore database connectivity and verify seamless recovery to MySQL.
7. **Production Distinctions**:
   - Explicitly document the boundary between local development activation and enterprise production readiness (TLS encryption, read-replicas, connection pool sizing, automated failover).
