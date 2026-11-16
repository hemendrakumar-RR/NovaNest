# NOVANEST PHASE 06.3 — PHASE PLAN
## Master Orchestrator and Multi-Agent Intelligence Integration

**Date**: 2026-11-12  
**Status**: `COMPLETED_VERIFIED`  
**Scope**: Implement the central `MasterOrchestrator`, cross-agent `synthesizer`, intent routing, concurrent + sequential safe execution, `OutputVerifier` verification, FastAPI endpoint wiring, React UI orchestration telemetry wiring, and comprehensive testing without modifying preserved Phase 06.0, 06.1, or 06.2 core implementations.

---

## Objectives & Deliverables

1. **Master Orchestrator (`python/ai/agents/master_orchestrator.py`)**
   - Implement `OrchestrationMode`, `RoutingPlan`, `IntentRouter`, `OrchestrationOutcome`, `MasterOrchestrator`, and `_slice_isolated_data()`.
   - Preserve exact Phase 06.0, 06.1, and 06.2 implementations while exporting Phase 06.3 classes in `python/ai/agents/__init__.py`.
   - Perform hybrid routing across:
     - Single-agent domain queries (`financial_agent`, `customer_agent`, `operations_agent`, `restaurant_agent`, `decision_agent`)
     - Multi-agent cross-domain synthesis (Stage 1 parallel data/domain agents -> Stage 2 sequential dependent `DecisionAgent` receiving `upstream_findings`)
     - SQL AST sandbox path (`validate_sql_ast` + read-only 9-table SQLite executor), while guarding English `"Analyze ..."` prompts with `_NL_ANALYZE_PHRASE_RE` so natural-language analytical queries do not misroute as bare SQL `ANALYZE` commands
     - General assistant / math / offline knowledge / topic-switch fast path (`general_assistant`) with business-context reset isolation.
   - Enforce per-worker DataFrame slice isolation (`.copy(deep=True)` on `ALLOWED_DATASETS`), cooperative timeouts (`default_timeout_seconds=65.0`, `per_agent_timeout_seconds=35.0`, `shutdown(wait=False, cancel_futures=True)`), principal-isolated `AgentContext` + `ExecutionTracer` spans, and `.to_chat_response()`.

2. **Cross-Agent Synthesizer (`python/ai/agents/synthesizer.py`)**
   - Implement `SynthesisOutput`, `synthesize_agent_results`, provenance/caveat/recommendation/calculation-step collectors, deterministic cancellation rate derivation (`cancelled_orders / total_orders`), and fail-closed `_build_rejected_limitation_response` stripping unverified numeric prose when `OutputVerifier` rejects a draft.
   - Preserve `is_confirmed_loss=False`, experimental Phase 05 ML `ModelCaveat` tags, and explicit partial/timeout/RBAC/error limitations.

3. **FastAPI Multi-Agent API Integration (`api/main.py`)**
   - Preserve `require_scope("operator")` on `POST /api/ai/ask` and `require_scope("admin")` on `POST /api/ai/reset`, while preserving SQL AST & table ACL protections.
   - Add thread-safe `get_master_orchestrator()`, optional `city_filter` on `ChatInquiry`, `GET /api/ai/agents/status` (`require_scope("read")`), and principal-isolated `GET /api/ai/traces/{request_id}` (`require_scope("operator")`).
   - Synchronize `POST /api/ai/reset` across legacy conversation sessions, orchestrator sessions (`reset_orchestrator_session`), and `AgentContextManager`.

4. **Frontend React Integration & Bundle Verification (`frontend/`)**
   - Extend TypeScript contracts and client (`frontend/src/services/api.ts`) with `InvokedAgentSummary`, `CalculationStep`, `AiAgentsStatusResponse`, orchestration telemetry fields on `ChatResponse`, optional `city_filter` parameter on `api.askAi()`, and `api.getAiAgentsStatus()`.
   - Render orchestration mode, verification status, `trace_id`, Stage 1 / Stage 2 agent badges, data source badges, collapsible calculation steps, ML caveats, and limitations inside `AiIntelligenceView.tsx` and `FloatingChatbot.tsx`.
   - Rebuild React Vite production bundle (`tsc -b && vite build`).

5. **Verification & Governance (`tests/test_phase06_3_orchestrator.py` + `NEWCHAGES/`)**
   - Build a dedicated 15-test Phase 06.3 verification suite alongside full offline regression suites, live authenticated Uvicorn HTTP checks, non-destructive MySQL probe, Streamlit Page 07/09 compatibility, and complete `NEWCHAGES` documentation + **ADR-013**.

