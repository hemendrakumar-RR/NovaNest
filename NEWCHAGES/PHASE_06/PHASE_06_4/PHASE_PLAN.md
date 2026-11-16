# NOVANEST PHASE 06.4 — ADVANCED MULTI-AGENT SECURITY, RELIABILITY & AI EVALUATION
## PHASE PLAN

- **Phase**: `06.4`
- **Date**: `2026-11-12`
- **Objective**: Harden the verified Phase 06.0–06.3 NovaNest Multi-Agent AI system through comprehensive security testing, prompt-injection defense, fault-tolerance & reliability engineering, `OutputVerifier` adversarial hardening, repeatable 9-category AI quality evaluation, performance/memory benchmarking, and API/Frontend resilience verification.
- **Status**: `VERIFIED_COMPLETE` (`CSV File Store` primary runtime; MySQL DB parity remains `BLOCKED` / `PARTIALLY_VERIFIED`)

---

## Scope & Task Breakdown

| Task | Title | Primary Targets | Acceptance Criteria |
|---|---|---|---|
| Task 1 | Agent Security Audit | `context.py`, `registry.py`, `master_orchestrator.py`, `tracing.py`, `base.py` | Viewer RBAC & scope downgrade blocked; cross-principal context/trace isolated; SQL/dataset ACLs enforced; `registry.lock()` prevents runtime mutation; secrets/PII scrubbed. |
| Task 2 | Prompt Injection Defense | `contracts.py`, `base.py`, `master_orchestrator.py`, `__init__.py` | `detect_prompt_injection`, `neutralize_untrusted_text`, `sanitize_user_query`, `sanitize_scalar` on CSV entity/review text, `AgentMessage` & Stage-2 `upstream_findings` sanitization. |
| Task 3 | Reliability Engineering | `context.py`, `master_orchestrator.py` | Parent->child cancellation propagation + isolated child timeouts; GET/read-only bounded retry with exponential backoff (never unsafe writes/security blocks); `BoundedSemaphore` concurrency limit; `CLOSED`/`OPEN`/`HALF_OPEN` `_AgentCircuitBreaker`; partial degradation fallbacks. |
| Task 4 | Output Verification Hardening | `output_verifier.py` | Reject wrong financial values, wrong percentages, `KPI_DEFINITION_MISMATCH`, `UNSUPPORTED_RECOMMENDATION`, fabricated provenance, conflicting agent values, unconfirmed losses, and experimental ML overclaims while preserving valid rounding. |
| Task 5 | AI Evaluation Framework | `python/ai/agents/evaluation.py` | Repeatable 18-case suite across all 9 required categories (`financial`, `customer`, `operations`, `restaurant`, `decision`, `multi_domain`, `ambiguous`, `unsupported_data`, `prompt_injection`) + partial failure recovery checks. |
| Task 6 | Performance Benchmarking | `python/ai/agents/evaluation.py` | Real measurements on idle host: single-agent, 5-agent parallel, parallel vs sequential speedup, 4-worker concurrency, `tracemalloc` peak MB, timeout cutoff, retry recovery elapsed ms, plus hardware profile. |
| Task 7 | API & Frontend Reliability | `api/main.py`, `frontend/src/services/api.ts`, `frontend/src/views/AiIntelligenceView.tsx` | `/api/ai/ask` bounds validation (`400`), safe error handling, React `AbortController` timeouts (`20s` / `68s`), GET-only bounded retries (`maxRetries=1`), `lastFailedQuery` Retry button re-submission, Chrome CDP verified. |
| Task 8 | Full Regression & Live Suite | All 11 unittest modules + `run_all_tests` + `test_digital_twin` + Chrome CDP | Zero test failures (`137/137` + `3/3` + `4/4`), clean `py_compile`, `tsc --noEmit`, `vite build`, live server + CDP clean with ports `8000/5173/9222` closed. |
| Task 9 | Governance & Master Ledgers | `NEWCHAGES/PHASE_06/PHASE_06_4/` (8 docs) + 11 ledgers | Complete accurate reporting using strictly observed outputs; non-destructive appends (`ADR-014`); no git commit/push/reset. |

---

## Guardrails Preserved
- Phase 06.0–06.3 implementations and shared contracts preserved without breaking signatures.
- Existing Phase 05.3 AST SQL validator, CORS allowlist, and HMAC RBAC intact.
- Experimental Phase 05 ML caveats (`customer_churn`, `eta_prediction`, `demand_forecast`, `restaurant_prediction`) and `is_confirmed_loss=False` revenue leakage flags preserved.
- `.env` and source CSV datasets (`datasets/`) completely untouched.

