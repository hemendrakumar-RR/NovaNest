# NOVANEST — PHASE 06.6 PHASE PLAN
## Critical Error Resolution & Application Hardening

### 1. Objective & Scope
The objective of Phase 06.6 is to resolve confirmed critical, high, and medium-severity issues identified during the independent Phase 06.5 closure audit, harden authentication and streaming mechanisms, ensure strict parameter compatibility across frameworks, and verify zero regressions across the NovaNest platform.

### 2. Confirmed Audit Findings & Remediation Strategy

| Issue ID | Severity | Area | Finding Summary | Remediation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | CRITICAL | SSE Streaming Security | `GET /api/ai/ask/stream?token=<key>` exposed static API tokens in URL query strings, leaking credentials to access logs, browser history, and referers. | Implement cryptographically secure, short-lived (60s), single-use stream ticket service (`POST /api/ai/stream-ticket`). Consume atomically upon connection establishment (`GET /api/ai/ask/stream?ticket=<id>`). Strictly reject `?token=<key>` query parameters with HTTP 401 Unauthorized across all endpoints. Update React and Streamlit clients. |
| **DB-01** | HIGH | MySQL Connectivity | `1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)` logged when attempting MySQL80 connection. | Perform non-destructive diagnostics. Confirm MySQL service state on port 3306. Verify credentials without guessing, inventing, or modifying `.env`. Confirm graceful degradation to authoritative CSV File Store. Classify status as `BLOCKED (Requires User Credential Action)` and document exact user resolution commands. |
| **DEP-01** | MEDIUM | Streamlit 1.54.0 Deprecations | `use_container_width=True` emitted deprecation warnings on `st.button`, `st.plotly_chart`, and `st.dataframe`. | Migrate all occurrences across `streamlit_app/` from `use_container_width=True` to modern `width="stretch"` while preserving layout, responsive styling, and widget state. Verify with page runtime smoke tests. |
| **BUILD-01** | MEDIUM | Three.js / Vite 8 Build | `[IMPORT_IS_UNDEFINED] LinearEncoding / sRGBEncoding` emitted during Rolldown build of `@designcodeio/threeui`. | Three.js r152+ removed legacy encoding constants in favor of `ColorSpace`. Implement a non-destructive Vite AST transform build plugin (`threeEncodingPolyfillPlugin`) in `frontend/vite.config.ts` replacing property references with integer constants (3001, 3000) during build. Avoid mutating `node_modules` or runtime prototypes. |

### 3. Strict Safety Protocol
1. Zero Git commits, pushes, deployments, resets, or discards.
2. Zero modification of untracked files, datasets, backups, or existing reports.
3. No invention or exposure of credentials or passwords; no overwriting of `.env`.
4. Creation of isolated pre-hardening backups in `backup/phase06_6_pre_hardening/`.
5. Exact directory naming preservation: `NEWCHAGES/`.
6. 100% regression verification across all 12 platform test suites.

