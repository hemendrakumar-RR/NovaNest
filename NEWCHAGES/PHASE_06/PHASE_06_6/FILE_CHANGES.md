# NOVANEST — PHASE 06.6 FILE CHANGES
## Detailed Line-Level Diff Summary of Modified Files

### 1. `api/auth.py`
- **Imports Added**: `threading`, `time`, `Dict`, `StreamTicket`, `StreamTicketManager`, `authenticate_stream_principal`.
- **`_extract_token`**: Removed lines extracting `token` from `request.query_params`. Only headers `X-API-Key` and `Authorization: Bearer` are inspected.
- **`StreamTicket`**: New dataclass storing `ticket_id`, `principal`, `session_id`, `created_at`, `expires_at`, `consumed`.
- **`StreamTicketManager`**: New thread-safe ticket manager class with `create_ticket`, `consume_ticket`, `_purge_expired_locked`, and `clear`.
- **`stream_ticket_manager`**: Exported shared singleton instance.
- **`authenticate_stream_principal`**: New security gate for SSE endpoints:
  - If `request.query_params.get("token")` is present -> raises HTTP 401 Unauthorized.
  - If `ticket` is provided -> validates ticket, expiration, session matching, and role scopes. Atomically consumes ticket.
  - If no ticket -> inspects Bearer / X-API-Key request headers.
- **`require_scope`**: Added check rejecting requests where `request.query_params.get("token")` is present.

---

### 2. `api/main.py`
- **Imports**: Added `authenticate_stream_principal` and `stream_ticket_manager` from `api.auth`.
- **`POST /api/ai/stream-ticket`**: New endpoint requiring `require_scope("operator")`. Issues a single-use 60s stream ticket bound to caller principal and session ID.
- **`GET /api/ai/ask/stream` & `GET /api/ai/stream`**:
  - Added `ticket: Optional[str] = Query(None)`.
  - Added `token: Optional[str] = Query(None)` (deprecated, triggers security rejection).
  - Authenticates via `authenticate_stream_principal(...)`.
  - Atomically consumes ticket on connection.
  - Preserves client cancellation / disconnect handling (`asyncio.CancelledError`).

---

### 3. `frontend/vite.config.ts`
- **`threeEncodingPolyfillPlugin`**: Added build-time code transform plugin:
  - Intercepts imports of `@designcodeio/threeui` and transforms legacy Three.js properties:
    - `.sRGBEncoding` -> `3001`
    - `.LinearEncoding` -> `3000`
  - Eliminates `[IMPORT_IS_UNDEFINED]` warnings in Rolldown / Vite 8 without modifying `node_modules` or altering visual shader rendering.

---

### 4. `frontend/src/services/api.ts`
- **`getStreamTicket`**: Added method calling `POST /api/ai/stream-ticket` with `{ session_id }`, returning `{ ticket, expires_in, session_id, created_at }`.

---

### 5. `streamlit_app/utils/api_client.py`
- **`get_stream_ticket`**: Added method to `StreamlitAiClient` requesting a stream ticket via HTTP `POST /api/ai/stream-ticket` (with seamless in-process fallback support).

---

### 6. Streamlit Pages & Components (Deprecation Fixes: `use_container_width=True` -> `width="stretch"`)
- `streamlit_app/app.py`: Replaced 1 occurrence.
- `streamlit_app/components/chart_components.py`: Replaced 2 occurrences.
- `streamlit_app/components/contextual_ai.py`: Replaced 1 occurrence.
- `streamlit_app/components/kpi_components.py`: Replaced 4 occurrences.
- `streamlit_app/components/status_components.py`: Replaced 3 occurrences.
- `streamlit_app/pages/02_Customer_Intelligence.py`: Replaced 2 occurrences.
- `streamlit_app/pages/04_Operations_Intelligence.py`: Replaced 1 occurrence.
- `streamlit_app/pages/07_Ask_NovaNest.py`: Replaced 6 occurrences.
- **Total occurrences migrated**: 20.

---

### 7. `tests/test_phase06_5_integration.py`
- **`test_18`**: Updated to request a stream ticket via `POST /api/ai/stream-ticket` before connecting to `GET /api/ai/ask/stream?ticket=...`. Added assertion verifying that passing `?token=...` query parameter returns HTTP 401 Unauthorized.

---

### 8. `tests/test_phase06_6_security_and_hardening.py`
- **New File**: 16 dedicated unit and integration tests verifying stream ticket lifecycle, anti-replay, TTL enforcement, session binding, credential exposure rejection, and Streamlit client integration.

