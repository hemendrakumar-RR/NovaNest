# NOVANEST — PHASE 06.1: Core Multi-Agent Foundation & Shared Contracts
## Phase Plan

- **Phase**: `Phase 06.1` (Shared Contracts, Context, Registry, OutputVerifier & Execution Tracing Foundation)
- **Date**: `2026-11-11`
- **Status**: `VERIFIED` (Foundation Implemented & Tested; Legacy Phase 06.0 Intact; Live MySQL Runtime `BLOCKED` by Host Auth `1045 (28000)`)
- **Prerequisite**: [`Phase 06.0 Legacy AI Stabilization`](../PHASE_06_0/PHASE_SUMMARY.md) (`VERIFIED`)
- **Scope**: Build the foundational Multi-Agent infrastructure under `python/ai/agents/` prior to implementing the five domain agents or `MasterOrchestrator`.

---

## 1. Objectives & Deliverables

| Task ID | Workstream | Module | Exit Criterion |
| :--- | :--- | :--- | :--- |
| **T1** | Pre-Implementation Audit | Existing AI/Auth/SQL/Tests | Audit `api/auth.py`, `conversation_manager.py`, `sql_ast.py`, `sql_agent.py`, `orchestrator.py`, `data_grounding.py`, `kpi_definitions.json`, `models/*`, and baseline test counts without modifying legacy code. |
| **T2** | Typed Agent Contracts | `python/ai/agents/contracts.py` | Implement Pydantic v2 schemas (`AgentMessage`, `AgentRequest`, `AgentResult`, `AgentStatus`, `AgentError`, `DataProvenance`, `AgentExecutionMetadata`, `GroundedFact`, `ModelCaveat`, `SqlAuditTrace`, `ChartSpec`, `ActionRecommendation`) forbidding raw DataFrames and secrets. |
| **T3** | Shared Principal-Isolated Context | `python/ai/agents/context.py` | Implement thread-safe `AgentContext` & `AgentContextManager` with strict `principal_id` isolation, `session_id`, `user_query`, bounded turn/history/metadata caps, `kpi_definitions.json` loader, deadlines, cooperative cancellation, and safe JSON serialization. |
| **T4** | Deterministic Output Verification | `python/ai/agents/output_verifier.py` | Implement `OutputVerifier` verifying INR/`Cr`/`Lakhs`/percentage claims within rounding tolerances against grounded facts and KPIs, catching fabricated claims, cross-agent conflicts, missing-data gaps, and unconfirmed-loss framing (`is_confirmed_loss=False`). |
| **T5** | Capability & ACL Agent Registry | `python/ai/agents/registry.py` | Implement `AgentRegistry` supporting registration, discovery, Pydantic I/O contract checks, RBAC scope + `ALLOWED_TABLES` checks, and strict gating preventing unfinished domain agents from being marked `OPERATIONAL`. |
| **T6** | Secret-Redacted Execution Tracing | `python/ai/agents/tracing.py` | Implement `ExecutionTrace` & `ExecutionTracer` with `RLock` concurrency, LRU bounding, `elapsed_ms` span timings, error/source tracking, principal isolation, and secret/PII redaction. |
| **T7** | Package Exports & Verification | `python/ai/agents/__init__.py`, `tests/test_phase06_1_foundation.py` | Export clean public APIs and pass comprehensive unit, concurrency, security, and regression tests while leaving `python/ai/analyst/orchestrator.py` undisturbed. |
| **T8** | Governance Traceability | `NEWCHAGES/PHASE_06/PHASE_06_1/*` + Master Registers | Document all Phase 06.1 decisions, new files, and test outcomes non-destructively. |

---

## 2. Explicit Scope Boundaries
- **In Scope**: Shared typed contracts, shared principal-isolated context, agent capability/ACL registry (`0` unfinished domain agents operational), deterministic output verifier, execution tracing, foundation unit tests, regression runs, and Phase 06.1 governance records.
- **Out of Scope (Deferred to Phase 06.2–06.8)**: Implementing `FinancialAgent`, `CustomerAgent`, `OperationsAgent`, `RestaurantAgent`, `DecisionAgent`, implementing `MasterOrchestrator`, modifying `python/ai/analyst/orchestrator.py`, modifying datasets/models/Power BI/``.env``, or performing git commits/pushes.

