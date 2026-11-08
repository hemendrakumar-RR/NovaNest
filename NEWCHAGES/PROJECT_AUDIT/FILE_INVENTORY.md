# NovaNest — Consolidated Dual-Root File Inventory & Artifact Catalog

## 1. Executive Summary
- **Total Tracked Files in Workspace (`NovaNest-main`)**: 157 files (60.74 MB).
- **Total Tracked Files in Capstone Archive (`NovaNest/NovaNest`)**: 302 project files (excluding `node_modules` [19,812 files] and `.git`).
- **Files Common to Both Roots**: 62 files (datasets, early SQL scripts, Power BI file, early reports).
- **Workspace-Only Artifacts**: 95 files (`NEWCHAGES/` change management suite, `python/analytics/`, `datasets/analytics/`, stabilized pipeline runners).
- **Archive-Only Artifacts**: 240 files (`api/` 2 files, `frontend/` 50 files, `streamlit_app/` 25 files, `python/ai/` 12 files, `python/digital_twin/` 10 files, `python/ml/` 6 files, `models/` 5 directories, `reports/` 20 files, `tests/` 12 files).

## 2. Directory Breakdown by Subsystem

### A. Core Data Storage (`datasets/`)
| Directory | File Count | Total Size | Description | Status |
|---|---|---|---|---|
| `datasets/raw/` | 10 CSVs | 23.36 MB | Original raw datasets (orders, customers, etc.) | Active Baseline |
| `datasets/cleaned/` | 10 CSVs | 23.41 MB | Cleaned, standardized, validated CSVs | Certified Gold |
| `datasets/engineered/` | 2 CSVs | 13.97 MB | `orders_engineered.csv`, `orders_geo_temporal_enriched.csv` | Certified Feature Store |
| `datasets/analytics/` | 7 Artifacts | 1.15 MB | KPI definitions, RFM, cohorts, funnel matrices | Certified Analytics Store |

### B. Python Pipelines & Backend (`python/` & `api/`)
| Path | Component | File Count | Purpose | Location |
|---|---|---|---|---|
| `python/clean_data.py` | Data Engineering | 1 file (12.4 KB) | Master cleaning script | Both (Workspace updated) |
| `python/feature_engineering.py` | Data Engineering | 1 file (9.1 KB) | Geo-temporal & feature enrichment | Both (Workspace updated) |
| `python/pipeline_runner.py` | Orchestration | 1 file (6.2 KB) | End-to-end pipeline executor | Workspace |
| `python/validate_master_data.py` | Quality Assurance | 1 file (14.8 KB) | Automated schema & anomaly checks | Workspace |
| `python/analytics/` | Business Intelligence | 6 files (32.1 KB) | RFM, cohorts, funnel, KPI cross-validation | Workspace |
| `api/main.py` | Backend Server | 1 file (38.4 KB, 894 lines) | FastAPI application with 13 endpoints | Archive |
| `api/loader.py` | Data Layer | 1 file (4.8 KB, 142 lines) | In-memory cache & MySQL fallback loader | Archive |
| `python/ai/` | Multi-Agent AI | 12 files (62.3 KB) | Universal engine, NL2SQL, providers | Archive |
| `python/digital_twin/` | Simulation Engine | 10 files (48.7 KB) | 5 domain twins, state machine, alerts | Archive |
| `python/ml/` | ML Training | 6 files (28.4 KB) | 5 training scripts (churn, ETA, demand, etc.) | Archive |

### C. Frontend & UI Platforms (`frontend/` & `streamlit_app/`)
| Directory | Platform | File Count | Key Technologies | Location |
|---|---|---|---|---|
| `frontend/src/views/` | React 18 | 9 Views | TypeScript, Tailwind, Lucide React, Charts | Archive |
| `frontend/src/components/` | React 18 | 8 Components | Hero banner, floating bot, top dock, cards | Archive |
| `frontend/` (config) | Web Tooling | 5 files | `package.json`, `vite.config.ts`, `tailwind.config.js` | Archive |
| `streamlit_app/pages/` | Streamlit | 9 Pages | Python, Streamlit, Glassmorphism CSS | Archive |
| `streamlit_app/` (core) | Streamlit | 3 files | `app.py`, `utils.py`, `database.py` | Archive |

### D. Relational Database Scripts (`mysql/`)
| Script Name | Size | Purpose | Primary Tables / Views |
|---|---|---|---|
| `01_schema.sql` | 4.8 KB | DDL Schema creation | 10 Core Tables |
| `02_indexes.sql` | 3.2 KB | Index definitions | B-Tree indexes on FKs & dates |
| `03_views.sql` | 5.1 KB | Basic reporting views | Executive KPIs, city aggregations |
| `04_stored_procedures.sql` | 6.4 KB | ETL procedures | Daily refresh, anomaly alerts |
| `05_triggers.sql` | 2.9 KB | Integrity triggers | Status timestamps, order totals |
| `06_analytics_queries.sql` | 7.8 KB | Business queries | CLV, RFM, delivery performance |
| `07_maintenance.sql` | 2.1 KB | DB maintenance | Table optimization, analyze index |
| `08_phase3_analytical_views.sql` | 8.2 KB | Workspace analytical views | 6 Enterprise views with window functions |
| `08_phase3_intelligence.sql` | 3.1 KB | Archive intelligence queries | RFM scores, cohort retention |
| `09_phase4_operations.sql` | 3.6 KB | Archive operations views | SLA ETA view, city demand forecast |

### E. Business Intelligence Dashboard (`powerbi/`)
| File Path | Size | Description | Integrity Status |
|---|---|---|---|
| `powerbi/NovaNest.pbix` | 1,327,104 bytes | Master Power BI Desktop file (5 pages, 66 visuals, 43 DAX measures) | Verified Untouched |

### F. Reports & Governance Suite (`reports/` & `NEWCHAGES/`)
- `reports/` in Workspace: 5 reports (`NOVANEST_MASTER_AUDIT.md`, `data_quality_report.md`, `kpi_cross_validation_report.md`, `PHASE4_FINAL_CERTIFICATION_REPORT.md`, `NOVANEST_COMPLETE_PROJECT_REPORT.md`).
- `reports/` in Archive: 24 reports covering UI/UX, Ask NovaNest AI, Digital Twin, and Streamlit redesigns.
- `NEWCHAGES/` in Workspace: 68 structured change management files across Phase 01 to Phase 04 and PROJECT_AUDIT.
