# NOVANEST — DECISIONS AND REASONS
**Architectural Decision Records (ADR)**

---

### ADR-001: Preservation of Raw Datasets
- **Status**: Accepted
- **Context**: The raw datasets in `datasets/raw/` represent the simulated ground truth for the 5-city food delivery marketplace.
- **Decision**: Never perform in-place modification or destructive cleaning on `datasets/raw/*.csv`. All transformations must read from `datasets/raw/` and write to `datasets/cleaned/` or `datasets/engineered/`.
- **Reason**: Maintains 100% pipeline reproducibility and prevents accidental data loss.

---

### ADR-002: Dynamic Path Resolution using `pathlib.Path`
- **Status**: Accepted
- **Context**: Legacy scripts contained hardcoded relative paths like `Path(__file__).resolve().parent.parent` which resolved differently depending on the folder depth (`python/` vs `python/data generation/`).
- **Decision**: Standardize dynamic project-root discovery using `Path(__file__).resolve().parents[N]` or root-anchoring, ensuring scripts execute identically from terminal root or subdirectories.
- **Reason**: Eliminates `FileNotFoundError` across all Python runners.

---

### ADR-003: Non-Destructive Handling of Cross-City and Temporal Anomalies
- **Status**: Accepted
- **Context**: Audit revealed 38,572 orders where customer city != restaurant/rider city, and 12,418 orders occurring before customer signup date.
- **Decision**: Do not arbitrarily drop or delete these records from `datasets/cleaned/orders.csv`, as dropping them would destroy 77% of the order dataset and break referential integrity with `payments.csv` and `deliveries.csv`. Instead:
  1. Document the anomalies in `reports/data_quality_report.md`.
  2. Maintain `datasets/cleaned/` with referential consistency intact.
  3. Create an enriched feature-engineered dataset `datasets/engineered/orders_geo_temporal_enriched.csv` with explicit anomaly flags (`cross_city_flag`, `pre_signup_order_flag`) so downstream ML models can either filter or train on verified subsets.
- **Reason**: Preserves existing metrics, avoids downstream join breakage, and maintains mathematical honesty without fabricating data.

---

### ADR-004: Preservation of Power BI Report (`powerbi/NovaNest.pbix`)
- **Status**: Accepted
- **Context**: `NovaNest.pbix` is a 5.6 MB binary file containing 5 dashboards and 27 DAX measures.
- **Decision**: Strictly treat `powerbi/NovaNest.pbix` as a protected read-only asset. Inspect internal schema and visual layouts via safe zip extraction. Never overwrite or re-save without explicit backup and user consent.
- **Reason**: Protects against binary corruption.


---

### ADR-005: Chronological Observation Cutoffs & Non-Destructive Historical Model Preservation (Phase 05)
- **Status**: Accepted
- **Context**: Legacy `models/customer_churn/churn_metrics.json` reported `ROC-AUC = 1.0000` due to full-timeline `Recency > 90` target definition, and `models/restaurant_prediction/restaurant_metrics.json` reported `R2 = 0.8559` by predicting synthetic uniform noise over `Total_Orders`. Moreover, legacy prediction CSVs corresponded to an older `50,000`-row dataset rather than the Phase 02 certified `49,971`-order tables.
- **Decision**:
  1. Never overwrite historical `models/*/*_metrics.json` baseline reports; store all validated Phase 05 outputs alongside them as `*_metrics_v2.json`, `model_metadata.json`, `feature_documentation.json`, `validation_report.md`, `prediction_examples.csv`, and `.joblib` artifacts.
  2. Enforce strict temporal cutoffs (`<= cutoff_date`) and forbidden-feature assertions (`Recency`, `Total_Orders`, targets) via `python/ml/validation_framework.py`, without fabricating GPS/traffic data or artificially inflating synthetic performance.
  3. Refresh serving prediction CSVs under `datasets/engineered/` against the certified `49,971`-order dataset while keeping original API and Streamlit column schemas intact.
- **Reason**: Eliminates data leakage, guarantees scientific honesty around synthetic data entropy limits, and maintains 100% historical auditability and runtime platform compatibility.

### ADR-006: Strict Schema Alignment, Certified KPI Single Source of Truth & Honest Unavailability Contracts (Phase 05.1)
- **Date**: 2026-11-11
- **Context**: `PHASE_05_FINAL_CLOSURE_AUDIT.md` identified systemic API-to-CSV column mismatches (`churn_risk_level` vs `Churn_Risk`, `actual_demand` vs `actual_orders`, nonexistent `"commission_amount"`), mixed-denominator financial calculations in `/api/overview` and `/api/financial/overview`, unverified `"ANM-01"` / `SAVE20` / `92%` confidence placeholders, and outdated `"4.90"` GMV assertions.
- **Decision**: Centralize Phase 04 financial KPI computation in `_compute_certified_financials`, resolve actual disk CSV column names via `_resolve_column` in [`api/main.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/main.py) and [`python/ai/analyst/data_grounding.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/analyst/data_grounding.py), return explicit `None` + status/caveat fields (`confidence_pct: null`, `redemptions: null`, `deficit: null`, `is_confirmed_loss: false`, `is_confirmed_incident: false`) whenever empirical evidence or schema linkage is absent, and update React/Streamlit consumers and UI tests to handle those contracts safely.
- **Reason**: Prevents silent fallback fabrication in dashboards and API responses, guarantees numerical parity between FastAPI, Streamlit, React, Ask NovaNest AI, and certified Phase 04 KPI definitions, and establishes an honest baseline before Phase 06 agentic integration.

### ADR-007: Independent Phase 05.2 Classification (`PARTIALLY_VERIFIED`) & Remediation Gate Before Phase 06
- **Date**: 2026-11-11
- **Context**: Phase 05.1 certified API contract alignment across targeted endpoints, but end-to-end browser, Streamlit multipage, MySQL, cross-layer parity, and security runtime tests revealed non-trivial regressions and drift outside Phase 05.1 unit coverage.
- **Decision**: Assign Phase 05.2 an honest `PARTIALLY_VERIFIED` classification (`VERIFIED` build/lint, `FAILED` on Streamlit Page `01`, `BLOCKED` on MySQL `1045`, `PARTIALLY_VERIFIED` elsewhere) without weakening checks or mutating code mid-audit, and mandate fixing the logged crash, dict-key mismatches, CORS wildcard credentials, and `sql_agent.py` comma-join bypass prior to Phase 06 sign-off.


### ADR-008: Explicit CORS Allowlist, AST SQL Validation, Fail-Closed RBAC & React Fault Boundaries (Phase 05.3)
- **Date**: 2026-11-11
- **Context**: Phase 05.2 exposed wildcard CORS reflection with credentials enabled, unauthenticated `/api/*` endpoints, comma-join SQL bypasses disclosing `sqlite_master`, React uncaught `Failed to fetch` rejections on `RestaurantIntelligenceView`, Streamlit Page `01` `KeyError ['rating']`, and hardcoded Digital Twin / Simulator fallbacks.
- **Decision**:
  1. Enforce explicit `CORS_ALLOWED_ORIGINS` allowlist and constant-time RBAC tokens (`read`/`operator`/`admin`) in `api/auth.py` with zero embedded credentials, interactive UI `sessionStorage` token prompting on HTTP `401`/`403`, and `<ErrorBoundary>` + `<ApiErrorState>` across every React view.
  2. Replace regex/split SQL filtering with recursive-descent AST validation (`sql_ast.py`), bounded row limits (`default 25`, `max 100`), `PRAGMA query_only = ON`, and a C-level SQLite read-only authorizer.
  3. Eliminate hardcoded telemetry fallbacks in Digital Twin, Simulator, Customer 360, and Streamlit pages, surfacing `"unavailable"` explicitly when empirical inputs are absent, while aligning loaders/SQL on canonical `novanest_db` / `orders_table`.
- **Reason**: Eliminates arbitrary-origin credential exposure, injection bypasses, UI crashes, and misleading placeholder telemetry cleanly before Phase 06 agentic workflows.

---

## ADR-009: Phase 06 In-Process Hub-and-Spoke Multi-Agent AI Architecture & Stabilization-First Roadmap
- **Date**: 2026-11-11
- **Status**: `PROPOSED` (**Architecture Blueprint Only — Implementation Not Started**)
- **Context**: Existing Phase 05.3 conversational AI ([`orchestrator.py`](../python/ai/analyst/orchestrator.py), [`universal_router.py`](../python/ai/analyst/universal_router.py), [`data_grounding.py`](../python/ai/analyst/data_grounding.py), [`root_cause.py`](../python/ai/analyst/root_cause.py)) operates via single-intent `if/elif` dispatch, suffers residual schema/hardcoding bugs (`restaurants["rating"]`, `rider_allocation` columns, unaggregated `4,669`-row leakage, hardcoded `root_cause.py` prose & fake `RECOMMENDATIONS`), omits `3/9` SQLite tables in fallback mode, lacks principal-scoped session isolation, enforces `admin` RBAC on `/api/ai/reset` (`403` on operator New Chat), and leaves Streamlit `07_Ask_NovaNest.py` on the deprecated `python/ai/conversational/` fork.
- **Decision**:
  1. Adopt an **in-process Python/FastAPI Hub-and-Spoke Multi-Agent Engine** (`Master Orchestrator` + `Financial`, `Customer`, `Operations`, `Restaurant`, `Decision` agents) with 2-wave bounded parallel/sequential `ThreadPoolExecutor` execution over typed Pydantic `AgentTask`/`AgentResult` schemas — avoiding heavyweight distributed frameworks (Kafka/Celery/external vector clusters).
  2. Reuse certified `python/analytics/*`, `python/intelligence/*`, `python/digital_twin/*`, `python/decision_simulation/*`, `python/decision/next_best_action.py`, `api/auth.py`, `api/loader.py`, and `sql_ast.py` as deterministic tool backends; restrict LLM synthesis (`GeminiProvider`/`MockAIProvider`) strictly to narration validated by a numeric `OutputVerifier`.
  3. Mandate **Phase 06.0 (Stabilize Existing AI Bugs & 9-Table SQLite)** prior to agent implementation (`Phase 06.2`–`06.6`).
- **Reason**: Maximizes determinism, ground-truth financial/KPI fidelity (`KPI-01`..`KPI-16`), honest Phase 05 ML caveat disclosure (`0/5` production-ready), security isolation, and UI consistency across React and Streamlit with minimal operational complexity.

---

## ADR-010: Phase 06.0 Legacy AI Stabilization, Unconfirmed Leakage Framing & Principal Session Isolation
- **Date**: 2026-11-11
- **Status**: `IMPLEMENTED_VERIFIED` (**Phase 06.0 Stabilization Only — Multi-Agent Build Deferred to Phase 06.1+**)
- **Context**: Empirical verification confirmed legacy defects in [`data_grounding.py`](../python/ai/analyst/data_grounding.py), [`root_cause.py`](../python/ai/analyst/root_cause.py), [`orchestrator.py`](../python/ai/analyst/orchestrator.py), [`conversation_manager.py`](../python/ai/analyst/conversation_manager.py), `sql_agent.py` (only `5/9` tables loaded cleanly in API/UI), `api/main.py` unscoped sessions, and `streamlit_app/pages/07_Ask_NovaNest.py`. In addition, Phase 05.3 security regression tests (`test_phase05_3_security_and_contracts.py::test_04`) require `operator` tokens to receive HTTP `403` on `/api/ai/reset` when `NOVANEST_ADMIN_KEY` is separately configured.
- **Decision**:
  1. Replace all hardcoded KPIs/narratives with live multi-table computations over CSVs and `kpi_definitions.json`, explicitly surfacing `is_confirmed_loss=False` (`₹553,946.31` aggregated across 3 leakage types) and Phase 05 `ROC-AUC = 0.5161` / `ETA R2 = -0.0002` uncertainties rather than inventing causal prose.
  2. Expose `DATASET_TO_SQLITE_TABLE_MAP` covering all `9` approved `ALLOWED_TABLES` via `build_readonly_sqlite_connection`, wire live `next_best_action.py` engines into `orchestrator.py` + Page 07, and preserve single-agent Phase 06.0 boundaries.
  3. Enforce `threading.RLock`, `1800s` idle TTL, `250`-session LRU eviction, `12`-turn window, regex PII/secret redaction, zero DataFrame storage, and HMAC-hashed caller `principal_id` isolation across both `POST /api/ai/ask` and `POST /api/ai/reset` while keeping `admin` scope enforcement on `/api/ai/reset` (`viewer=403`, `operator=403` when `NOVANEST_ADMIN_KEY` is set) and cross-principal reset isolation.
- **Reason**: Eliminates hallucinated/hardcoded analytics, multi-tenant session collisions, and UI fork drift while keeping every Phase 05.3 fail-closed security guarantee strictly intact.


---

## ADR-011: Phase 06.1 Standalone Multi-Agent Foundation (`python/ai/agents/`) Without Premature Agent Registration
- **Date**: 2026-11-11
- **Status**: `IMPLEMENTED_VERIFIED` (**Phase 06.1 Foundation Only — Domain Agents & MasterOrchestrator Deferred to Phase 06.2+**)
- **Context**: Before building the 5 Phase 06.2 Domain Agents and Phase 06.3 `MasterOrchestrator`, NovaNest requires hardened, framework-light foundational abstractions over existing `pydantic 2.14.0`, `api/auth.py` `AuthPrincipal`, `conversation_manager.py` PII redaction, `sql_ast.py` `ALLOWED_TABLES`, and `kpi_definitions.json`, without breaking or coupling into stabilized Phase 06.0 `python/ai/analyst/orchestrator.py`.
- **Decision**:
  1. Build `python/ai/agents/` (`contracts.py`, `context.py`, `registry.py`, `output_verifier.py`, `tracing.py`, `__init__.py`) natively with Pydantic v2 (`extra="forbid"`, `model_dump(mode="json")`), `threading.RLock`, monotonic deadlines/cancellation, and zero heavyweight external orchestration frameworks.
  2. Enforce hard fail-closed invariants across boundaries: reject `pd.DataFrame`/callables and raw `Bearer`/`API` keys in contracts and contexts; isolate `AgentContext` and `ExecutionTracer` strictly by `principal_id`; allow legitimate rounding tolerances (`₹4.66 Cr` <-> `₹46,590,125.00`) in `OutputVerifier` while blocking unconfirmed screening losses (`is_confirmed_loss=False`) framed as confirmed losses.
  3. Require both `is_implemented=True` and a verified callable handler before `AgentRegistry` allows `AgentAvailability.OPERATIONAL`, ensuring the 5 blueprint domain agents remain strictly non-operational (`PLANNED`) during Phase 06.1.
- **Reason**: Establishes clean, concurrency-safe, verifiable contracts and guardrails first while keeping Phase 06.0 conversational AI and FastAPI routes 100% undisturbed.


## ADR-012 — Phase 06.2 Shared BaseDomainAgent Wrapper & Strict Pre-Execution Guards
- **Date**: 2026-11-11
- **Status**: `IMPLEMENTED_VERIFIED` (**Phase 06.2 Domain Agents Complete — `MasterOrchestrator` Deferred to Phase 06.3**)
- **Context**: Implementing five specialized domain agents over the Phase 06.1 foundation requires zero duplication of RBAC/ACL/lifecycle logic across domains, strict conformance to existing analytics/decision/Digital Twin engines, and protection against Phase 05 experimental ML overclaiming (`customer_churn`, `eta_prediction`, `demand_forecast`, `restaurant_prediction`) or unconfirmed leakage losses (`is_confirmed_loss=False`).
- **Decision**:
  1. Introduce [`BaseDomainAgent`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/agents/base.py) to uniformly execute principal isolation (`assert_principal`), deadline/cancellation checks, RBAC scope verification (`operator` required on `customer_agent` & `decision_agent`), narrow per-agent SQL table ACLs (`validate_sql_ast` + ephemeral RO SQLite scoped strictly to permitted tables), least-privilege dataset slicing, `OutputVerifier` self-audit, and `ExecutionTracer` spans before/after `_run_domain`.
  2. Reuse existing analytics, Digital Twin (`twin_engine.py`, `twin_dependencies.py`), RCA (`root_cause.py`), simulation (`simulation_agent.py` / `scenario_engine.py`), and `next_best_action.py` modules with explicit `ensure_python_path()` bootstrap and direct CSV-verified counts (`16,119` SLA breaches out of `49,971` deliveries = `32.26%`, `avg_rating = 4.25`), avoiding `api/main.py` top-level imports.
  3. Preserve Phase 06.1 `AgentRegistry(preload_planned_blueprints=True)` planned-by-default invariant while exposing `create_default_domain_registry()` in `python/ai/agents/__init__.py` to register all 5 operational agents cleanly ahead of Phase 06.3 `MasterOrchestrator`.
- **Reason**: Guarantees uniform security, zero numeric drift across agents (`0` conflicts in `OutputVerifier`), clean degraded handling (`PARTIAL`/`BLOCKED`) on missing data, and zero impact on existing Phase 06.0 API/UI surfaces.



## ADR-013 — Phase 06.3 Two-Stage MasterOrchestrator, Fail-Closed Synthesis & UI Telemetry Integration
- **Date**: 2026-11-12
- **Status**: `IMPLEMENTED_VERIFIED` (`MasterOrchestrator` + Cross-Agent `synthesizer.py` + FastAPI + React UI Integration)
- **Context**: Coordinating all five verified Phase 06.2 domain intelligence agents requires deterministic intent routing across single-agent, multi-agent, AST-validated SQL, and general assistant paths; preventing `sql_ast.starts_like_sql_statement` from misclassifying natural-language `"Analyze ..."` queries as SQL `ANALYZE` statements; isolating concurrent DataFrame slices across worker threads; synchronizing `python.ai.*` module paths between `api/main.py` and `MasterOrchestrator`; and failing closed without echoing unverified numbers if `OutputVerifier` rejects a synthesized draft.
- **Decision**:
  1. Implement `IntentRouter` (with `_NL_ANALYZE_PHRASE_RE` natural-language guard and SQL syntax cue detection) plus two-stage `MasterOrchestrator`: Stage 1 concurrent domain execution via `ThreadPoolExecutor` (`_slice_isolated_data` deep-copying `ALLOWED_DATASETS`, `shutdown(wait=False, cancel_futures=True)`, `default_timeout_seconds=65.0`, `per_agent_timeout_seconds=35.0`) followed by Stage 2 sequential `DecisionAgent` execution injected with `upstream_findings` in shared `AgentContext`.
  2. Implement `synthesize_agent_results` and `_build_rejected_limitation_response` in [`synthesizer.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/agents/synthesizer.py) to aggregate provenance, caveats, recommendations, calculation steps, and deterministic cancellation rates while stripping unverified raw numeric prose on `VerificationOutcome.REJECTED` and preserving `is_confirmed_loss=False`.
  3. Wire [`api/main.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/main.py) (`PROJECT_ROOT` prior to `python/` on `sys.path` to avoid `_SESSIONS` split-brain) with `get_master_orchestrator()`, `POST /api/ai/ask` (`operator`), `GET /api/ai/agents/status` (`read`), principal-isolated `GET /api/ai/traces/{request_id}` (`operator`), and multi-store `POST /api/ai/reset` (`admin`), surfaced in React via [`api.ts`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/services/api.ts), [`AiIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/AiIntelligenceView.tsx), and [`FloatingChatbot.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/components/FloatingChatbot.tsx).
  4. Preserve Phase 06.2 `tests/test_phase06_2_domain_agents.py` unmodified (leaving historical boundary check `test_master_orchestrator_not_implemented_in_phase06_2` transparently documented as superseded by Phase 06.3).
- **Reason**: Enables concurrent, trace-audited, provenance-grounded multi-agent intelligence across FastAPI and React without weakening RBAC, SQL AST security, session isolation, or experimental ML transparency.


### ADR-013 Final Closure Addendum (2026-11-12)
- Updated [`tests/test_phase06_2_domain_agents.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_phase06_2_domain_agents.py) (explicitly authorized Phase 06.3 regression cleanup) to replace the obsolete `test_master_orchestrator_not_implemented_in_phase06_2` check with explicit verification that all 5 Phase 06.2 domain agents remain `OPERATIONAL` and that `MasterOrchestrator`, `IntentRouter`, and `synthesize_agent_results` are exported and callable (`23/23` OK; `118/118` OK across all 10 unittest suites in `57.704s`).
- Updated `_handle_sql_sandbox` in [`master_orchestrator.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/agents/master_orchestrator.py) so `OutputVerifier` verifies prose summary statements while `table_rows` & `sql_audit` hold structured row data, ensuring valid AST-approved SQL queries return `grounding_verified=True` & `verification_outcome="verified"`.
- Supersedes the earlier pre-cleanup probe note (`MYSQL_CONN_IS_NONE=False` from inspecting the `(conn, source)` tuple rather than `conn`): proper unpacking confirms `conn is None` and `mysql.connector.connect` raises `1045 (28000): Access denied` (`PARTIALLY_VERIFIED` / live DB parity `BLOCKED`).


## ADR-014 — Phase 06.4 Multi-Agent Security Hardening, Reliability Controls & Repeatable Evaluation
- **Date**: 2026-11-12
- **Status**: `IMPLEMENTED_VERIFIED` (`CSV File Store` authoritative runtime; MySQL DB parity remains `BLOCKED` / `PARTIALLY_VERIFIED`)
- **Context**: Moving from functional multi-agent orchestration (Phase 06.3) to production-grade reliability and safety requires fail-closed defense against indirect prompt injection via CSV text fields and inter-agent messages, runtime immutability for registered agents, isolated per-agent cancellation/timeouts, bounded retries that never re-execute unsafe operations, adversarial `OutputVerifier` coverage, repeatable quality/performance benchmarking, and resilient FastAPI/React timeout & retry UX.
- **Decision**:
  1. Neutralize untrusted text at three boundaries — entry query (`sanitize_user_query`), CSV/SQL row scalars (`sanitize_scalar` -> `neutralize_untrusted_text`), and inter-agent payloads (`AgentMessage` validators + Stage-2 `upstream_findings`) — while stripping injection clauses rather than dropping legitimate hybrid business questions, and extending `IntentRouter`'s `nl_analyze_prefix` guard for benign English `"Explain ..."` questions without weakening `sql_ast.py`.
  2. Enforce runtime safety via `AgentRegistry.lock()`, `filters.get("requested_tables")` ACL merging, `AgentContext.fork_for_agent` (parent->child cancellation propagation without peer blast radius), `_AgentCircuitBreaker` (`CLOSED`/`OPEN`/`HALF_OPEN`), `BoundedSemaphore` concurrency capping, and GET/read-only-only bounded retries (`_NON_RETRYABLE_ERROR_CODES` forbidding write/security retries).
  3. Tighten `OutputVerifier` across provenance, experimental ML overclaims (respecting negated disclosures), KPI definition inversions, and evidence-less recommendations while keeping legitimate rounding (`±0.5%` / step rounding) intact.
  4. Provide repeatable 9-category (`18`-case) AI evaluation + `tracemalloc`/concurrency/timeout benchmark suite in [`python/ai/agents/evaluation.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/agents/evaluation.py), plus `AbortController` timeouts (`20s`/`68s`), GET-only retries in [`api.ts`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/services/api.ts), and `lastFailedQuery` Retry recovery in [`AiIntelligenceView.tsx`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/frontend/src/views/AiIntelligenceView.tsx).
- **Reason**: Verified `137/137 OK` across all 11 unittest modules, `100.0%` eval accuracy with `0.0%` unsupported claim rate, `51.408 MB` peak traced memory, and clean live Uvicorn + Chrome CDP Retry recovery with zero leaked console/page/HTTP errors.


## ADR-015 — Phase 06.5 Production Integration, Executive Experience & Latency Optimization Architecture
- **Date**: 2026-11-13
- **Status**: `PROPOSED` (Architecture & Planning Blueprint Completed)
- **Context**: Phases 06.0–06.4 delivered a verified 5-domain autonomous multi-agent backend with strict RBAC, AST SQL validation, and anti-fabrication verification. However, production deployment requires: (1) breaking out of an isolated AI chat tab into contextual triggers across all 6 domain dashboards; (2) upgrading Streamlit from legacy single-agent to `MasterOrchestrator`; (3) replacing static regex follow-up rewrites with structured entity/topic memory; and (4) resolving the multi-agent memory churn and GIL allocation bottleneck.
- **Decision**:
  1. Design a zero-copy DataFrame data layer using pandas Copy-on-Write and non-writeable NumPy buffers, cutting memory churn and reducing multi-agent sweep latency while maintaining absolute thread isolation.
  2. Inject pre-computed Stage-1 metrics directly into Stage-2 `DecisionAgent` via `upstream_findings`, eliminating redundant 50k-row scans.
  3. Introduce `ConversationState` in `AgentContext` with entity extraction and pronoun resolution to resolve multi-turn dialogue trees cleanly without dropping geographic or entity context.
  4. Design `AgentTelemetryCard` and an optional SSE streaming progress endpoint (`/api/ai/ask/progress/{request_id}`) to provide real-time orchestration transparency without exposing sensitive internal chain-of-thought.
  5. Weave contextual AI launchers into `Executive`, `Customer`, `Operations`, `Restaurant`, `Financial`, and `Decision` views, and plan Streamlit `07_Ask_NovaNest.py` migration to `MasterOrchestrator`.
- **Reason**: Establishes a complete, verified architectural blueprint for Phase 06.5 with zero application code modification, zero version control mutation, and complete rollback procedures.


## ADR-016 — Phase 06.5 Milestone 1 Zero-Copy Engine & Stage-2 Metric Reuse Architecture
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`MasterOrchestrator` + `DecisionAgent` + `tests/test_phase06_5_integration.py`)
- **Context**: Prior to Milestone 1, `MasterOrchestrator._slice_isolated_data` executed `df.copy(deep=True)` across all permitted datasets for every dispatched agent, consuming 40.27 ms in data slicing alone and triggering 51.41 MB peak memory churn. Simultaneously, `DecisionAgent` in Stage 2 re-scanned the 50,000-row `orders` and `deliveries` tables from scratch to compute GMV, Net Revenue, Total Orders, and SLA Breach Rate, even though Stage 1 domain agents had already computed certified values for these identical metrics.
- **Decision**:
  1. Leverage Pandas 3.0.5 native Copy-on-Write (CoW) to replace deep buffer copies with zero-copy shallow slices (`df.copy(deep=False)`) in `_slice_isolated_data`. CoW guarantees that any column assignment in an agent automatically triggers an unshared copy of only the affected column buffer, leaving shared DataFrames 100% bit-for-bit immutable.
  2. Enrich `_execute_stage2_sequential` in `MasterOrchestrator` to inject structured `metrics` and `facts` from successful Stage-1 results into `request.metadata["upstream_findings"]`.
  3. Enhance `DecisionAgent._run_domain` to reuse certified metrics (`KPI-01`, `KPI-02`, `KPI-05`, `KPI-08`, `KPI-09`) directly when overall platform telemetry is evaluated, falling back to raw table scanning when called standalone or with narrowing city filters.
- **Reason**: Eliminates memory duplication and redundant scans: slicing latency dropped from 40.27 ms to 2.74 ms (14.7x speedup), peak memory consumption fell by 48.0% (51.41 MB -> 26.71 MB), input DataFrame SHA-256 hashes remained 100% identical across all 10 datasets, and all 137 unit tests across 11 modules passed with zero regressions.


## ADR-017 — Phase 06.5 Milestone 2 Conversational Memory & Context Persistence Architecture
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`conversation_manager.py` + `context.py` + `master_orchestrator.py` + `tests/test_phase06_5_integration.py`)
- **Context**: Prior to Milestone 2, conversational context in `conversation_manager.py` used simple topic/intent rewrites without structured entity tracking. Follow-up inquiries (e.g., asking about revenue in Bangalore, then asking *"How many orders were placed?"*) lost city, customer segment, and restaurant entities, reverting to platform-wide metrics unless the user repeated their filters. Furthermore, memory needed to support explicit filter replacement, nationwide filter resets, principal/session isolation, idle TTL eviction, prompt injection filtering, and provenance-backed fact persistence without treating assistant prose as unquestioned data.
- **Decision**:
  1. Implement `extract_conversational_entities` in `conversation_manager.py` with support for canonical cities (`Bangalore`, `Chennai`, `Hyderabad`, `Coimbatore`, `Vijayawada`, `Mumbai`, `Delhi`, etc.), reset triggers (`all cities`, `nationwide`, `platform-wide`), customer segments (`Champions`, `Loyal Customers`, `At Risk`, `VIP`, `Hibernating`), restaurants (quoted or prefixed by `restaurant/outlet/merchant/partner`), date ranges (`last_quarter`, `last_month`, `annual`), and business domains.
  2. Implement `resolve_follow_up_query_and_context` returning `(augmented_query, resolved_intent, context_topic, effective_filters, remembered_entities)` while preserving backward-compatible 3-tuple `resolve_follow_up_query`.
  3. Store active filters, remembered entities, and recent verified facts (with dataset provenance, label, value, unit) in principal-scoped session memory (`principal_key::session_id`) bounded by 30-minute idle TTL and 250 LRU cap.
  4. Expand `AgentContext` and `ConversationTurnSummary` to serialize `filters` and `remembered_entities`, and wire `MasterOrchestrator._orchestrate_within_slot` to propagate `effective_filters` to all Stage 1 and Stage 2 domain worker requests (`request.filters = effective_filters`).
  5. Add `active_filters` and `remembered_entities` to `OrchestrationOutcome` and `to_chat_response()`.
  6. Add order volume and order count keywords to `universal_router.py` to ensure order-related follow-ups route to `BUSINESS_DATA`.
- **Reason**: Enables seamless multi-turn executive conversational analysis: follow-up inquiries inherit active filters accurately (e.g. Bangalore total orders = 12,695), explicit city changes replace active filters (Hyderabad = 10,193), nationwide queries reset filters, cross-user and cross-session isolation guarantees 0% filter bleed, malicious overrides are neutralized, and 147/147 regression tests pass with zero regressions.


## ADR-018 — Phase 06.5 Milestone 3 Server-Sent Events (SSE) Streaming Telemetry & Real-Time Agent Execution Observability
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`telemetry_events.py` + `master_orchestrator.py` + `api/main.py` + `api/auth.py` + `AgentTelemetryCard.tsx` + `api.ts` + `FloatingChatbot.tsx` + `AiIntelligenceView.tsx`)
- **Context**: In multi-agent orchestration involving up to 5 concurrent domain agents and cross-agent synthesis, queries require 1.5s to 3s of compute time. Previously, frontend interfaces displayed an all-or-nothing spinner, providing zero real-time visibility into agent dispatch, stage progression, verification outcomes, or execution bottlenecks. Moreover, streaming telemetry must strictly prevent secret leakage (API keys, tokens, JWTs), stack traces, raw SQL, or unconfirmed loss metrics.
- **Decision**:
  1. Define a typed, validated contract in `python/ai/agents/telemetry_events.py` (`OrchestratorTelemetryEvent`) supporting 10 lifecycle events (`query_received`, `intent_classified`, `agent_started`, `agent_progress`, `agent_completed`, `agent_failed`, `synthesis_started`, `verification_completed`, `response_completed`, `execution_failed`) + `heartbeat`, with `extra="forbid"`, automatic secret/token scrubbing (`[REDACTED_SECRET]`), stack trace redaction (`[EXECUTION_FAULT]`), internal path masking (`[PATH]`), and W3C SSE standard string serialization (`to_sse()`).
  2. Enhance `MasterOrchestrator` (`orchestrate()`, `_orchestrate_within_slot()`, `_execute_stage1_parallel()`, `_execute_stage2_sequential()`) to accept `event_callback` and emit lifecycle events across all execution stages without adding lock contention or overhead.
  3. Implement authenticated SSE endpoints in `api/main.py`: `POST /api/ai/ask/stream` (and alias `/api/ai/stream`) and `GET /api/ai/ask/stream` (and alias `/api/ai/stream`) requiring `require_scope("operator")`, supporting browser `EventSource` with query parameter `token` authentication in `api/auth.py`.
  4. Design async event stream generator with `asyncio.Queue(maxsize=100)`, 3-second idle heartbeat emission, background orchestration thread, and client disconnect handling (`request.is_disconnected()`) cancelling active `AgentContext`.
  5. Implement `frontend/src/components/AgentTelemetryCard.tsx` rendering real-time execution status, 5 domain agent cards with stage badges (S1/S2), execution duration, status pills, verification badges, and live ticker.
  6. Implement resilient `askAiStream(...)` in `frontend/src/services/api.ts` with SSE chunk decoding, SSE block parsing, and automatic fallback to synchronous `askAi(...)` on connection failure.
  7. Integrate live telemetry streaming into `FloatingChatbot.tsx` and `AiIntelligenceView.tsx`.
- **Reason**: Delivers trustworthy, sub-second visibility into multi-agent operations with 100% fail-closed security. Zero token or stack trace leaks, strict principal isolation, 100% backward compatibility with synchronous `/api/ai/ask`, clean client cancellation handling, 21/21 integration tests passing, and 152/152 full regression tests passing with zero regressions.


## ADR-019 — Phase 06.5 Milestone 4 Contextual AI Launchers Across NovaNest Dashboards & Strict Metric Grounding Principle
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`contextualAi.ts` + `ContextualAIButton.tsx` + `ContextualAIAction.tsx` + `KpiCard.tsx` + `FloatingChatbot.tsx` + `api.ts` + 5 Dashboard Views + `api/main.py` + `restaurant_agent.py` + `operations_agent.py` + `conversation_manager.py` + `sql_ast.py` + `master_orchestrator.py` + `tests/test_phase06_5_integration.py`)
- **Context**: In Phase 06.5 Milestone 4, users required the ability to trigger AI analysis directly from any dashboard KPI card, chart, table row, or business entity drawer across the 5 core dashboard views (Executive Overview, Financial Intelligence, Customer Intelligence, Restaurant Intelligence, Operations Intelligence), while preserving context (active filters, city, metric, entity ID/name) across follow-up queries. Crucially, the system must enforce the **Untrusted Client Metric Principle**: client-provided metric values must NEVER be accepted as authoritative or injected into calculation models; the backend must recalculate and ground all metrics from verified raw DataFrames. Additionally, natural language questions starting with conversational phrases like *"Analyze GMV..."* must not be misclassified as raw SQL `ANALYZE` commands, and entity extraction regexes must not falsely extract generic business terms (such as *"churn"* from *"customer churn"*) as entity IDs.
- **Decision**:
  1. Define typed `ContextualAIPayload` contract in `frontend/src/types/contextualAi.ts` specifying `dashboardName`, `kpiOrChartId`, `selectedMetric`, `metricValue`, `activeFilters`, `city`, `dateRange`, `entityType`, `entityId`, `entityName`, `sourceComponent`, `suggestedPrompt`, and `autoSubmit`.
  2. Implement decoupled custom event dispatch `launchContextualAI(payload)` dispatching `novanest-launch-contextual-ai`, and build reusable `ContextualAIButton` (4 visual variants: `icon`, `badge`, `button`, `compact`) and `ContextualAIAction` (for table rows and drawer headers).
  3. Wire `KpiCard.tsx` with optional `aiPayload`, and outfit all 5 core dashboard views:
     - **Executive Overview**: 8 KPI cards, Revenue Velocity chart, Territory Distribution chart, Top Partners table.
     - **Financial Intelligence**: 4 KPI cards, P&L Waterfall chart, Risk Screening chart, Promotions catalog table.
     - **Customer Intelligence**: 4 KPI cards, RFM Segment chart, CLV Distribution chart, Cohort Retention heatmap, Customer List table rows, Customer 360 drawer header.
     - **Restaurant Intelligence**: 4 KPI cards, Composite Health Index Distribution, Merchant Performance Matrix, Cuisine Benchmarks, Early Warning Alert signals, Partner Directory table rows.
     - **Operations Intelligence**: 4 KPI cards, 14-Day Demand Forecast chart, Fleet Dispatch table, Statistical Anomaly candidates, city allocation rows.
  4. Enhance `FloatingChatbot.tsx` to listen for the event, automatically open with preloaded context, render a Context Preload Banner with dismiss capability, and transmit `contextualData` to streaming client `api.askAiStream(...)`.
  5. Enforce **Untrusted Client Metric Principle** in `api/main.py`: `_apply_contextual_data_to_filters` maps entity IDs (`customer_id`, `restaurant_name`, `rider_id`) and territory filters (`city`) into `filters`, while client `metric_value` is explicitly ignored for calculations. Calculation engines and `OutputVerifier` independently recompute ground truths directly from raw datasets.
  6. Enhance `restaurant_agent.py` and `operations_agent.py` with contextual entity lookups, calculating entity-specific metrics (health scores, cancellation rates, delivery counts, SLA breaches) and generating dedicated `GroundedFact` and remediation `ActionRecommendation` records.
  7. Refine `conversation_manager.py` entity extraction regexes (`cust[_-]?\d+`, `rest[_-]?\d+`, `rider[_-]?\d+`, `customer id <id>`) to prevent false-positive extraction of business terms like "churn" as IDs.
  8. Refine `sql_ast.py` (`starts_like_sql_statement`) and `master_orchestrator.py` (`nl_analyze_prefix`) to cleanly distinguish conversational inquiries starting with "Analyze ..." from raw SQLite `ANALYZE [table];` commands.
- **Reason**: Enables seamless, zero-friction AI analysis from any dashboard component while maintaining ironclad data integrity, anti-fabrication controls, and PII protection. Tested with 29 integration tests and 172 full regression tests passing with 0 failures and 0 regressions; frontend builds cleanly in 529ms with 0 TypeScript errors.

---

## ADR-020 — Phase 06.5 Milestone 5 Streamlit MasterOrchestrator Hybrid Parity & Unified API Boundary
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`api_client.py` + `telemetry_components.py` + `contextual_ai.py` + `kpi_components.py` + `07_Ask_NovaNest.py` + 6 Dashboard Pages + `tests/test_phase06_5_milestone5_streamlit.py`)
- **Context**: In Phase 06.5 Milestone 5, NovaNest's Streamlit application needed to be brought into full architectural and functional parity with the React SPA's unified Multi-Agent AI system. Prior to this, Streamlit's `07_Ask_NovaNest.py` directly called legacy single-agent `orchestrator.py` functions, bypassing `MasterOrchestrator`, the 5 domain agents, zero-copy optimizations, conversational memory, output verification, and live telemetry streaming. Furthermore, dashboard KPI cards and analytics charts in Streamlit lacked contextual AI launchers. To maintain architectural integrity, Streamlit must consume the authenticated FastAPI backend gateway rather than duplicating business logic or agent orchestration locally, while ensuring tests can execute reliably in headless mode.
- **Decision**:
  1. Build `streamlit_app/utils/api_client.py` (`StreamlitAiClient`) providing authenticated synchronous (`ask_ai`) and SSE streaming (`ask_ai_stream`) methods, fail-closed auth handling (`401`/`403`/`503`), timeout/retry resilience, and a built-in headless testing fallback executing through FastAPI's `TestClient(app)` to ensure identical middleware, route dependencies, and RBAC authentication run even in automated test harnesses.
  2. Implement `streamlit_app/components/telemetry_components.py` (`render_agent_telemetry_card`) providing visual and functional parity with React's `AgentTelemetryCard.tsx`, displaying all 5 domain intelligence agents across Stage 1 (Parallel) and Stage 2 (Synthesis), with per-agent execution timers, live/completed badges, and `OutputVerifier` ground-truth verification badges.
  3. Implement `streamlit_app/components/contextual_ai.py` (`build_contextual_payload`, `render_contextual_ai_button`, `render_contextual_ai_inline`) supporting one-click context preloading and page switching to `07_Ask_NovaNest.py` using `st.switch_page`.
  4. Extend `streamlit_app/components/kpi_components.py` (`render_kpi_row`) with optional `ai_payload` support on KPI cards.
  5. Completely refactor `streamlit_app/pages/07_Ask_NovaNest.py` to route all queries through `StreamlitAiClient.ask_ai` (invoking `MasterOrchestrator`), display a dismissible Context Preload Banner, render the 5-domain agent telemetry card, maintain multi-turn chat history with active filters, and include inline markdown summary badges to ensure backward compatibility with test runners.
  6. Outfit all 6 core Streamlit analytics pages (`01_Executive_Overview.py` through `06_Decision_Intelligence.py`) with KPI contextual AI buttons and expandable inline multi-agent launchers.
- **Reason**: Eliminates architectural divergence between React and Streamlit; establishes a single, secure, authenticated API boundary for all AI intelligence inquiries; guarantees 100% data grounding and anti-fabrication via `OutputVerifier`; verified with 12 new automated tests in `tests/test_phase06_5_milestone5_streamlit.py` (100% passing) and a full 184-test regression sweep with zero failures and zero regressions.


## ADR-021 — Phase 06.6 Short-Lived Single-Use Streaming Tickets for SSE Authentication
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`api/auth.py` + `api/main.py` + `frontend/src/services/api.ts` + `streamlit_app/utils/api_client.py` + `tests/test_phase06_6_security_and_hardening.py`)
- **Context**: In Phase 06.5 Milestone 3, GET SSE streaming permitted passing static API tokens in URL query strings (`GET /api/ai/ask/stream?token=<key>`). This presented a critical security finding during the Phase 06.5 closure audit because static tokens passed in query strings are leaked into reverse proxy access logs, browser history, and HTTP `Referer` headers. Browsers opening `EventSource` connections cannot natively pass custom authorization headers. A secure, credential-safe mechanism was required to authenticate GET SSE streams without exposing static secrets in URLs.
- **Decision**:
  1. Implement a thread-safe `StreamTicketManager` in `api/auth.py` issuing cryptographically secure, high-entropy tickets (`st_<token_urlsafe(32)>`).
  2. Bind tickets to the caller's verified `AuthPrincipal`, `session_id`, and a strict 60.0-second TTL.
  3. Create an authenticated endpoint `POST /api/ai/stream-ticket` requiring `operator` scope via standard Bearer or `X-API-Key` headers.
  4. Enforce strict single-use consumption in `consume_ticket`: atomically remove and invalidate the ticket upon first connection establishment in `GET /api/ai/ask/stream?ticket=<id>`, defending against replay attacks.
  5. Strictly reject any request containing `token` in query parameters with HTTP 401 Unauthorized across all endpoints, providing an informative message explaining the ticket exchange mechanism.
  6. Update React and Streamlit clients to provide `getStreamTicket(sessionId)` methods.
- **Reason**: Eliminates static credential exposure in query parameters and logs, satisfies zero-trust transport requirements, and passes all 16 security tests in `tests/test_phase06_6_security_and_hardening.py` with zero regressions.


## ADR-022 — Phase 06.6 Three.js Color Space Migration via Bundler AST Transform & Streamlit 1.54 Modernization
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`frontend/vite.config.ts` + `streamlit_app/` components and pages + `tests/validate_pages_runtime.py`)
- **Context**: During the Phase 06.5 audit, two non-functional warnings were identified: (1) Three.js r152+ removed `sRGBEncoding` and `LinearEncoding` in favor of `SRGBColorSpace` / `LinearSRGBColorSpace`, causing Vite 8 / Rolldown to emit `[IMPORT_IS_UNDEFINED]` warnings for third-party library `@designcodeio/threeui`; (2) Streamlit 1.54.0 deprecated `use_container_width=True` on buttons, charts, and dataframes in favor of `width="stretch"`.
- **Decision**:
  1. In `frontend/vite.config.ts`, implement a clean build-time AST transform plugin `threeEncodingPolyfillPlugin()` that intercepts `@designcodeio/threeui` module code during compilation and substitutes `.sRGBEncoding` with numeric literal `3001` and `.LinearEncoding` with `3000`. This resolves the warning without modifying `node_modules` or altering runtime prototype chains.
  2. In `streamlit_app/`, replace all 20 occurrences of `use_container_width=True` with `width="stretch"` across 8 component and page files, preserving layout fidelity and eliminating all deprecation warnings.
- **Reason**: Preserves zero-warning build hygiene, eliminates deprecation debt, and ensures forward compatibility with future Vite, Three.js, and Streamlit releases. Verified with a 591ms React build and 2/2 passing Streamlit page runtime smoke tests.


## ADR-023 — Phase 06.7 Resilient MySQL Connection Pooling, Least-Privilege Support & Transparent CSV Failover
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`api/loader.py` + `streamlit_app/database/connection.py` + `tests/test_phase06_7_mysql_integration.py`)
- **Context**: In Phase 06.7, NovaNest needed to diagnose MySQL `Error 1045 (28000): Access denied for user 'root'@'localhost'` while ensuring the application never crashes, leaks credentials, or suffers downtime if MySQL is unavailable. The diagnostic revealed that while Windows service `MySQL80` is healthy and listening on port 3306, the password in `.env` does not match the actual root password stored securely in Windows Credential Manager from MySQL Workbench. Under strict security boundaries, AI agents must never guess passwords, fabricate credentials, or overwrite `.env`. Additionally, opening unpooled single database connections per HTTP request in FastAPI and per render cycle in Streamlit introduces connection leaks, latency spikes, and socket exhaustion under load.
- **Decision**:
  1. Implement thread-safe connection pooling using `mysql.connector.pooling.MySQLConnectionPool` with double-checked locking (`_pool_lock`) across both `api/loader.py` and `streamlit_app/database/connection.py`.
  2. Enforce a 3-second connection timeout (`connect_timeout=3`) to ensure threads never hang on database connection attempts if the database host is unreachable.
  3. Support dedicated least-privilege service account credentials via `DB_APP_USER` and `DB_APP_PASSWORD`, falling back gracefully to `DB_USER` / `DB_PASSWORD`.
  4. Redact sensitive credentials in exception handlers: log only the MySQL error number (`errno`) and SQL state (`sqlstate`), never printing connection strings, usernames, or passwords.
  5. Enforce transparent, fail-safe degradation: when a database connection fails (due to Error 1045, timeout, or missing schema), catch the exception cleanly and return `(None, "csv")` in FastAPI and `None` in Streamlit, seamlessly serving all analytics and multi-agent AI features from the authoritative CSV file store (`datasets/cleaned/`).
  6. Document clear, operator-executable SQL scripts for creating a dedicated `novanest_app` user with least-privilege DML grants (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) without requiring administrative `root` privileges.
- **Reason**: Protects system availability and stability under credential mismatches or network failures, enforces security best practices (connection pooling, least privilege, zero credential leaks), and maintains 100% platform uptime. Verified with 11 automated integration tests in `tests/test_phase06_7_mysql_integration.py` (100% passing) and a full 184-test platform regression sweep with zero failures.


## ADR-024 — Phase 06.8 Dynamic Dual-Source Routing, Population Verification & Safe Failover
- **Date**: 2026-11-13
- **Status**: `IMPLEMENTED_VERIFIED` (`api/loader.py` + `streamlit_app/utils/data_loader.py` + `streamlit_app/database/connection.py` + `tests/test_phase06_8_application_integration.py`)
- **Context**: In Phase 06.8, NovaNest needed to validate that all application components (FastAPI backend, Streamlit dashboard, React frontend, and AI Domain Agents) could operate against the live MySQL database (`novanest_db`, 304,405 records) while retaining 100% backward compatibility and instantaneous rollback to the authoritative CSV file store. If `DATA_SOURCE=mysql` is configured but the database is empty, unreachable, or in maintenance, the platform must not return empty or corrupt data.
- **Decision**:
  1. Introduce dynamic data-source routing controlled by `os.getenv("DATA_SOURCE", "csv")` across both `api/loader.py` and `streamlit_app/utils/data_loader.py`.
  2. Implement an active data verification probe: when `DATA_SOURCE=mysql`, execute `SELECT COUNT(*) FROM customers` before serving data. If the table is empty or an error occurs, automatically and transparently revert to the authoritative CSV store.
  3. Introduce connection pool cache invalidation: store `_pool_config = (db_host, db_port, db_user, db_name)` and rebuild the connection pool when configuration parameters change, preventing stale sockets across mock environments or host switching.
  4. Preserve `DATA_SOURCE=csv` as the out-of-the-box safe default, requiring explicit operator enablement of `DATA_SOURCE=mysql`.
- **Reason**: Guarantees zero risk of data loss, application crashes, or silent partial ingestion failures; enables seamless toggling between live MySQL analytics and offline CSV testing; certified by 14 integration tests in `tests/test_phase06_8_application_integration.py`.


## ADR-025 — Phase 06.9 Controlled MySQL Activation, Single-Source Isolation & Observable Diagnostics
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`.env` + `api/loader.py` + `streamlit_app/utils/data_loader.py` + `api/main.py` + `scratch/test_live_http_mysql.py` + `scratch/test_phase06_9_live_validation.py` + `scratch/test_phase06_9_controlled_fallback.py`)
- **Context**: Prior to Phase 06.9, MySQL data ingestion was complete (304,405 records in `novanest_db`), but `DATA_SOURCE=csv` remained active. Activating `DATA_SOURCE=mysql` requires strict guarantees against partial data mixing (e.g. some tables from CSV and others from MySQL), observable diagnostics for health probes and operators, fail-closed auth handling, and certified 100% KPI parity against historical delivered-order baselines (47,994 delivered orders, ₹46,590,125.00 delivered GMV).
- **Decision**:
  1. Set `DATA_SOURCE=mysql` in local `.env` and configure explicit API tokens (`NOVANEST_API_KEY`, `NOVANEST_ADMIN_KEY`, `NOVANEST_VIEWER_KEY`) to ensure scoped endpoints operate securely without 503 auth gateway errors.
  2. Implement single-source isolation in `api/loader.py` and `streamlit_app/utils/data_loader.py`: call `data.clear()` before any fallback reload to guarantee zero mixing of CSV and MySQL DataFrames in memory.
  3. Implement observable diagnostic instrumentation: expose `get_data_source_diagnostics()` via `GET /api/diagnostics/data-source` and embed it in `GET /api/health`, returning `configured_data_source`, `active_data_source`, `fallback_active`, `fallback_reason`, `last_db_error`, `consistent_source`, and `mixed_sources_detected`.
  4. Author live network verification harness (`scratch/test_live_http_mysql.py`) testing actual HTTP responses from Uvicorn (`:8000`) and Streamlit (`:8501`).
  5. Validate full fallback lifecycle in `scratch/test_phase06_9_controlled_fallback.py` proving immediate failover under simulated downtime and seamless recovery when MySQL connectivity is restored.
- **Reason**: Successfully activates MySQL as the primary operational store with 100% data consistency, zero partial reads, certified KPI parity, and zero downtime fallback. Verified across 11 Phase 06.9 live validation tests, 9 live network socket probes, and 15 Phase 06.8 integration tests.


## ADR-026 — Phase 06.10 Comprehensive Acceptance Verification, Single-Use Session-Bound Tickets & Power BI Assessment
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`tests/test_phase06_10_acceptance_and_readiness.py` + `scratch/inspect_pbix.py` + `scratch/parse_pbix_visuals.py` + `NEWCHAGES/PHASE_06_10/`)
- **Context**: In Phase 06.10, NovaNest required an exhaustive, multi-dimensional end-to-end acceptance audit and production readiness evaluation covering all software layers under live MySQL 8.0.46 data (`novanest_db`, 304,405 records), including Power BI Desktop `.pbix` compatibility, cross-layer mathematical reconciliation, security defense mechanisms, latency/concurrency benchmarking, and failure recovery.
- **Decision**:
  1. Author and execute `tests/test_phase06_10_acceptance_and_readiness.py` covering 14 discrete integration, security, performance, and failure recovery scenarios.
  2. Validate session-bound single-use SSE streaming tickets: ensure `GET /api/ai/ask/stream?ticket=...` requires matching `session_id`, rejects static tokens in query strings with 401, and rejects ticket reuse with 401.
  3. Validate recursive SQL AST injection defense across 19 distinct attack vectors, confirming that DDL, DML writes, system table access (`sqlite_master`, `information_schema`), pragmas, attach commands, and multi-statements are strictly rejected while safe read-only queries are preserved.
  4. Perform non-destructive read-only static analysis on `powerbi/NovaNest.pbix` (5.64 MB), confirming 5 report pages (66 visuals, 27 DAX measures) are fully compatible with `novanest_db` schemas and feasible for live MySQL refresh.
  5. Establish baseline latency distributions for analytical aggregations over 49,971 records: mean = 509.55ms (p95 = 541.78ms), with 100% success rate under concurrent multi-worker loads.
- **Reason**: Formally certifies the complete NovaNest application software stack as accepted, mathematically grounded, secure, and production-ready for deployment.


## ADR-027 — Phase 06.11 Multi-Stage Containerization, Unbuffered SSE Nginx Edge Proxy & CI/CD Security
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`docker/Dockerfile.*` + `docker-compose.yml` + `docker-compose.prod.yml` + `docker/nginx.conf` + `.dockerignore` + `.github/workflows/ci.yml` + `tests/test_phase06_11_containerization.py` + `NEWCHAGES/PHASE_06_11/`)
- **Context**: In Phase 06.11, NovaNest required reproducible, secure, and production-ready containerization across all platform tiers (FastAPI backend, Streamlit dashboard, React SPA, and MySQL 8.0). Requirements included non-root user execution, dependency isolation, internal network protection (disallowing public MySQL exposure), dedicated unbuffered reverse proxying for real-time Server-Sent Events (SSE), persistent volumes, resource limits, CI/CD with vulnerability scanning, and disaster recovery validation without altering business logic or risking live database records.
- **Decision**:
  1. Implement multi-stage Docker builds across all three application tiers (`docker/Dockerfile.api`, `docker/Dockerfile.streamlit`, `docker/Dockerfile.frontend`), creating non-root system user `novanest` (UID 10001) for Python runtimes, pinning isolated dependencies (`docker/requirements-api.txt`, `docker/requirements-streamlit.txt`), and using Node 20 / Nginx 1.27 Alpine for the React SPA.
  2. Implement an enterprise Nginx configuration (`docker/nginx.conf`) providing standard REST proxying with 120s timeouts and a dedicated regex proxy block (`/api/ai/(ask/stream|stream)`) disabling buffering (`proxy_buffering off`, `proxy_cache off`, `chunked_transfer_encoding on`, `proxy_read_timeout 86400s`) to guarantee low-latency SSE telemetry delivery.
  3. Author multi-service development Compose specification (`docker-compose.yml`) orchestrating `db`, `api`, `frontend`, and `streamlit` with healthcheck dependencies (`service_healthy`), persistent storage (`novanest_mysql_data`), CPU and memory bounds, and internal network isolation (`novanest_net`), explicitly omitting public host port exposure for MySQL port 3306.
  4. Author production Compose specification (`docker-compose.prod.yml`) utilizing Docker Secrets for database passwords and API tokens, enforcing `restart: always` and `json-file` log rotation (20MB, 5 files).
  5. Establish GitHub Actions CI/CD workflow (`.github/workflows/ci.yml`) automating backend testing with MySQL service container, AST security linter, React production build, Docker Buildx image creation, and Trivy container vulnerability scanning.
  6. Execute live non-destructive disaster recovery backup via `mysqldump`, creating a 15.10 MB SQL archive (`scratch/novanest_backup_live.sql`) and programmatically verifying that all 10 tables and exactly 304,405 records are preserved with zero modifications to `novanest_db`.
  7. Formally document that Docker CLI / daemon is absent on the current local Windows development host; container specifications are certified 100% syntactically and structurally via automated unit tests (`tests/test_phase06_11_containerization.py`), while active local servers remain undisturbed.
- **Reason**: Guarantees zero risk to live databases, establishes hardened container definitions, prevents secret exposure, and delivers an enterprise deployment foundation ready for container staging.


## ADR-028 — Phase 06.11.1 Docker Runtime Enablement Audit, Service Non-Interference & Approval Gate
- **Date**: 2026-11-14
- **Status**: `AUDIT_COMPLETE_PENDING_APPROVAL` (`tests/test_phase06_11_1_readiness_audit.py` + `docker/Dockerfile.streamlit` + `docker/mysql/init/02_init_users.sql` + `NEWCHAGES/PHASE_06_11_1/`)
- **Context**: In Phase 06.11.1, NovaNest required pre-flight runtime validation for the containerization assets created in Phase 06.11. Docker Engine was absent on the local Windows 11 host. Governance strictly mandates: (1) inspect Windows OS and WSL2 status, (2) request user approval before installing or changing system-level components, (3) do not terminate existing FastAPI, Streamlit, or MySQL processes, (4) perform deep configuration audit to identify missing paths or credential risks, and (5) verify absolute safety of the 304,405 records in `novanest_db`.
- **Decision**:
  1. Formally audit the host environment (Windows 11 Home 64-bit Build 26200, WSL2 absent, Docker Desktop absent) and assert this absence transparently in automated tests (`tests/test_phase06_11_1_readiness_audit.py`).
  2. Protect running services: probe ports 8000 (FastAPI PID 26652), 8501 (Streamlit PID 11388), and 3306 (MySQL PID 7664) and ensure zero disruption to developer processes.
  3. Correct audit finding in `docker/Dockerfile.streamlit`: add `COPY datasets/engineered/` to support Phase 3/4 metrics loaded by `streamlit_app/utils/data_loader.py`.
  4. Correct audit finding in `docker/mysql/init/02_init_users.sql`: replace hardcoded development passwords with placeholders, relying on runtime container environment injection.
  5. Safeguard `novanest_db`: enforce named Docker volume `novanest_mysql_data` (never mounting the host MySQL directory) and certify the 15.10 MB SQL dump file (`scratch/novanest_backup_live.sql`).
  6. Provide concrete, non-destructive step-by-step installation instructions for WSL2 (`wsl --install --no-distribution`) and Docker Desktop (`winget install -e --id Docker.DockerDesktop`), and formally request explicit user approval before proceeding with system installations.
- **Reason**: Preserves 100% of existing application state, eliminates container configuration defects prior to build, guarantees database safety, and upholds strict user consent governance.


## ADR-029 — Phase 06.11.2 Docker Runtime Containerization, Isolated Database Restore & Port Conflict Mitigation
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`docker/Dockerfile.*` + `docker-compose.yml` + `tests/test_phase06_11_2_docker_runtime.py` + `NEWCHAGES/PHASE_06_11_2/`)
- **Context**: In Phase 06.11.2, Docker Desktop 4.99.0 and WSL2 Linux runtime became operational on the Windows host. NovaNest required building all container images (FastAPI backend, Streamlit dashboard, React SPA with Nginx), running containers under Docker Compose, restoring and validating the isolated container database without touching host `novanest_db`, and preventing host port collisions with running developer services (:8000, :8501, :3306).
- **Decision**:
  1. Build multi-stage hardened images for `novanest-api:test`, `novanest-streamlit:test`, and `novanest-frontend:test`.
  2. Protect host processes by binding Streamlit container to `${STREAMLIT_HOST_PORT:-8502}:8501`, API container to `${API_HOST_PORT:-8001}:8000` (and `:80:80` via Nginx edge reverse proxy), and keeping MySQL port 3306 unexposed on the host network.
  3. Start container database on named volume `novanest_mysql_data`, restore `scratch/novanest_backup_live.sql`, and verify 10 tables with all 304,405 records.
  4. Execute automated runtime verification suite `tests/test_phase06_11_2_docker_runtime.py`.
- **Reason**: Guarantees zero host service disruption, zero host data risk, clean container isolation, and reproducible production deployment readiness.


## ADR-030 — Phase 06.12 Automated CI/CD Pipeline & Multi-Tier Verification Strategy
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`.github/workflows/ci.yml` + `docker/requirements-api.txt` + `docker/Dockerfile.api` + `docker/nginx.conf` + `tests/run_ci_pipeline.py` + `test-results/` + `NEWCHAGES/PHASE_06_12/`)
- **Context**: In Phase 06.12, NovaNest required an automated, reproducible, and verifiable Continuous Integration (CI) pipeline covering all platform tiers. Governance mandates that: (1) creating YAML files alone does not constitute CI delivery—actual execution must be demonstrated, (2) no GitHub pushes or remote executions are permitted without explicit human approval, (3) no development credentials may be exposed in CI definitions, (4) container vulnerabilities identified during Phase 06.11.2 must be investigated and remediated where safe, and (5) machine-readable test reports (JUnit XML, JSON summaries) must be generated and preserved.
- **Decision**:
  1. Hardened `.github/workflows/ci.yml`: sanitized all hardcoded passwords using GitHub secret interpolations (`${{ secrets.DB_APP_PASSWORD || '...' }}`), enforced top-level least-privilege permissions (`contents: read, security-events: write`), partitioned testing into 5 discrete parallel jobs (`backend-ci`, `ai-platform-ci`, `frontend-ci`, `security-audit`, `docker-build-and-scan`), and configured test artifact preservation via `actions/upload-artifact@v4`.
  2. Remediated fixable High vulnerabilities: pinned `starlette>=0.49.1`, `setuptools>=78.1.1`, and `wheel>=0.46.1` in `docker/requirements-api.txt`, added `apt-get upgrade -y` in `docker/Dockerfile.api` to patch Debian OS libraries, and added `server_tokens off;` in `docker/nginx.conf`.
  3. Built local execution harness `tests/run_ci_pipeline.py` executing all 5 CI stages locally:
     - Stage 1 (Backend CI): 42 tests passed in 54.97s (`run_all_tests.py`, `test_phase05_3_security_and_contracts.py`, `test_phase06_7_mysql_integration.py`, `test_phase06_10_acceptance_and_readiness.py`).
     - Stage 2 (AI Platform CI): 52 tests passed in 34.86s (5 domain agents in `test_phase06_2_domain_agents.py`, Master Orchestrator & SSE in `test_phase06_3_orchestrator.py`, Universal AI in `test_ask_novanest_ai_suite.py`).
     - Stage 3 (Frontend CI): 4 checks passed in 8.50s (Oxlint 0 errors, TypeScript `tsc -b` 0 errors, Vite production build, Nginx `nginx -t` OK).
     - Stage 4 (Docker CI): 19 tests passed in 2.30s (Compose dev & prod config validation, 4/4 live container health probes).
     - Stage 5 (Security CI): 3 checks passed in 0.003s (SQL AST injection defense, secret scanning with 0 leaks, SQL keyword validator).
  4. Standardized test reporting: generated 5 JUnit XML reports and a consolidated `ci-summary.json` in `test-results/`.
- **Reason**: Delivers empirical, reproducible proof of platform quality with 100% pass rate (120/120 tests), zero credential exposure, robust vulnerability defense, and zero disruption to live developer services.


## ADR-031 — Phase 06.13 Production Security Hardening, Base Image Remediation, OWASP Compliance & Encrypted Disaster Recovery
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`docker/Dockerfile.frontend` + `docker/Dockerfile.api` + `docker/requirements-streamlit.txt` + `docker/nginx.conf` + `api/auth.py` + `api/main.py` + `python/ai/agents/contracts.py` + `python/backup_recovery.py` + `tests/test_phase06_13_security_hardening.py` + `NEWCHAGES/PHASE_06_13/`)
- **Context**: In Phase 06.13, NovaNest required end-to-end security hardening prior to production deployment. Vulnerability scanning had revealed high risk in legacy container images (18 Critical / 68 High CVEs in `novanest-platform-frontend`), outdated dependencies (Pillow 10.4.0 with 4 Critical CVEs in Streamlit), potential brute-force attack vectors on API endpoints, prompt injection and exfiltration risks in the multi-agent AI system, and the need for verified, encrypted disaster recovery with strict RTO (< 30s) and RPO (< 24h) guarantees.
- **Decision**:
  1. Base Image Remediation: Migrated `docker/Dockerfile.frontend` to `nginx:alpine-slim` with `apk upgrade --no-cache`, eliminating 100% of Critical CVEs (down from 18 to 0) and 98.5% of High CVEs (down from 68 to 1), with container size dropping to 6.8 MB. Upgraded Streamlit image dependencies to `streamlit>=1.40.0`, `pillow>=11.1.0`, and `tornado>=6.4.2`.
  2. Fail-Closed API Security & Rate Limiting: Enhanced `api/auth.py` with sliding-window `RateLimiter` (300 req/min general, 60 req/min AI) and 10-failure IP lockout (60s lockout); rejected static query parameter tokens (`?token=...`); deployed single-use `StreamTicketManager` (60s TTL).
  3. OWASP HTTP Security Headers: Added HTTP middleware in `api/main.py` injecting `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and strict `Content-Security-Policy`. Suppressed `Server` version banners in both FastAPI and Nginx.
  4. Multi-Agent AI Defense: Expanded `_INJECTION_RULES` in `python/ai/agents/contracts.py` to neutralize instruction overrides, secret exfiltration, script injection, jailbreak/DAN persona hijack, markdown image URL exfiltration, and SQL grounding bypass directives.
  5. Cryptographic Session Isolation: Maintained HMAC peppered session namespaces (`make_scoped_session_key`) guaranteeing complete cross-principal isolation, combined with automated PII redaction (email, phone, PAN).
  6. Encrypted Disaster Recovery: Built `python/backup_recovery.py` automating live transaction-safe `mysqldump`, OpenSSL AES-256-CBC PBKDF2 (100k iter) encryption with salt, decryption roundtrip with bit-for-bit SHA-256 match (`ebc0d58ac42e3cbd9f10441e92f62fa492e03827809e1d8e49d3f8249ef78aa4`), achieving an RTO of 0.178s (< 30s target) and RPO < 24h.
  7. Automated Regression Suite: Created `tests/test_phase06_13_security_hardening.py` (25/25 passed in 11.18s) and integrated it into `tests/run_ci_pipeline.py`, achieving a 100% pass rate (145/145 tests passed across all 5 stages).
- **Reason**: Delivers enterprise-grade security posture, eliminates container vulnerabilities, guarantees data privacy, protects AI agents against adversarial attacks, certifies rapid disaster recovery, and preserves all 304,405 records without service disruption.


## ADR-032 — Phase 07 Advanced Machine Learning Optimization, Native TreeSHAP Explainability, Model Registry & Honest Confidence Gating
- **Date**: 2026-11-14
- **Status**: `IMPLEMENTED_VERIFIED` (`python/ml/model_registry.py` + `python/ml/explainability.py` + `python/ml/phase07_churn_optimization.py` + `python/ml/phase07_eta_optimization.py` + `python/ml/phase07_demand_optimization.py` + `python/ml/phase07_restaurant_optimization.py` + `python/ml/phase07_anomaly_optimization.py` + `tests/test_phase07_ml_optimization.py` + `NEWCHAGES/PHASE_07/`)
- **Context**: In Phase 07, NovaNest required upgrading machine learning intelligence from initial baselines to production-grade, highly optimized, explainable ML models. Models needed rigorous benchmarking across modern gradient boosting architectures (XGBoost, LightGBM, HistGradientBoosting, Random Forest, Ridge), leakage-free feature boundaries, native TreeSHAP and permutation explainability, versioned model governance via a unified Model Registry with cryptographic SHA-256 lineage and rollback, and honest confidence gating across all five domain agents and the Master Orchestrator.
- **Decision**:
  1. Production Model Registry: Built `python/ml/model_registry.py` managing versions (`v1`, `v2`, `v3`), dataset SHA-256 hashes, automated rollback (`rollback_model`), and confidence tiers (`HIGH`, `MODERATE`, `LOW_EMPIRICAL`, `OPERATIONAL_GATED`). Initialized `models/registry_index.json` tracking all models.
  2. Native TreeSHAP Explainability: Developed `python/ml/explainability.py` leveraging native C++ TreeSHAP engines built directly into XGBoost and LightGBM boosters, eliminating fragile external C-extension dependencies under Windows AppLocker. Provided exact local feature attributions, base expectation, directional drivers/dampeners, and empirical prediction intervals (90% and 95% confidence bounds).
  3. Model 1 (Customer Churn): Benchmarked 6 algorithms with 3-fold probability calibration (Brier score 0.0781); evaluated Calibrated Random Forest (ROC-AUC 0.5062, PR-AUC 0.0950, 91.46% accuracy). Assigned `LOW_EMPIRICAL` confidence tier due to synthetic data ceiling; generated actionable retention segments (High-Value At-Risk, Discount-Sensitive, Loyal Advocates).
  4. Model 2 (Delivery ETA): Enforced strict dispatch-time feature boundaries; benchmarked 6 algorithms; selected HistGradientBoosting (MAE 11.5158m, RMSE 13.3159m); produced stratified breakdowns by City, Distance Tier, and Vehicle Type; established 90% prediction intervals (±21.9m).
  5. Model 3 (Demand Forecast): Created gap-free daily contiguous grid; executed 3-fold rolling-origin backtest; HistGradientBoosting achieved MAE 4.6878, WAPE 17.20%, and MASE 0.654 (a 35% error reduction over Seasonal Naive baseline MAE 7.1714); established within-city R² breakdowns.
  6. Model 4 (Restaurant Performance): Implemented multi-target modeling (Orders, Revenue, Ratings); Ridge L2 achieved MAE 1.3248 orders/month, outperforming expanding mean and prior-month baselines; established city breakdowns and order volume intervals.
  7. Model 5 (Anomaly & Fraud Detection): Audited all 49,971 platform orders (₹48,451,925.00 GMV); benchmarked Dual Z-score/IQR vs Isolation Forest vs LOF; consensus ensemble flagged 628 high-risk orders (₹519,596.00 exposure); enforced strict enterprise policy of 0 confirmed fraud labels without proof (100% compliant).
  8. Honest Confidence Gating in AI Agents: Updated `BaseDomainAgent` and domain agents (`CustomerAgent`, `OperationsAgent`, `RestaurantAgent`) to dynamically query `ModelRegistry`. Weak models automatically emit honest limitations, preventing automated hallucination of false certainty.
  9. Automated Regression Suite: Created `tests/test_phase07_ml_optimization.py` (10/10 tests passed in 11.787s) and integrated it into `tests/run_ci_pipeline.py`.
- **Reason**: Establishes scientific honesty, rigorous benchmarking, native TreeSHAP interpretability, cryptographic dataset lineage, automated rollback, and transparent confidence gating without compromising existing data or interrupting services.

## ADR-033 — Phase 08 Prescriptive Business Intelligence, Multi-Domain Optimization & Human-in-the-Loop Lifecycle Governance
- **Date**: 2026-11-15
- **Status**: `IMPLEMENTED_VERIFIED` (`python/decision/prescriptive_contracts.py` + `python/decision/customer_retention_intelligence.py` + `python/decision/revenue_optimization.py` + `python/decision/restaurant_optimization.py` + `python/decision/rider_operations_optimization.py` + `python/decision/scenario_simulation_engine.py` + `python/decision/financial_impact_engine.py` + `python/decision/recommendation_lifecycle.py` + `python/decision/prescriptive_engine.py` + `tests/test_phase08_prescriptive_intelligence.py` + `NEWCHAGES/PHASE_08/`)
- **Context**: In Phase 08, NovaNest required transforming from predictive analytics into an evidence-grounded, prescriptive business decision support platform. To operationalize decision support without risk, the platform required: multi-factor customer risk segmentation that prevents ungrounded automated action on `LOW_EMPIRICAL` churn scores; rigorous unit contribution margin breakdown across delivered orders; merchant bottleneck diagnosis and custom action plans; logistics workload analysis with explicit live telemetry caveats; controlled What-If scenario simulations with non-guaranteed projection notices; mathematical financial impact calculations (Gross Benefit, Cost, Net Impact, ROI, Payback Days); and a 6-state recommendation lifecycle enforcing mandatory human approval before operational or financial execution.
- **Decision**:
  1. Prescriptive Data Contracts: Created `python/decision/prescriptive_contracts.py` defining standardized recommendation contracts, lifecycle enums, and financial models. Enhanced `ActionRecommendation` in `python/ai/agents/contracts.py` with 14 additive fields with backward-compatible defaults.
  2. Customer Retention Intelligence: Built `python/decision/customer_retention_intelligence.py` combining RFM recency drop-offs (>45d), order frequency, and spend tiers. Churn ML predictions are gated strictly as exploratory flags with `LOW_EMPIRICAL` caveats; no commercial action is taken without verified behavioral inactivity. Enforced discount caps (15-20%) and minimum order values (MOV).
  3. Revenue Optimization: Built `python/decision/revenue_optimization.py` computing unit contribution margin across 47,994 delivered orders (Gross GMV ₹46,590,125.00, Net Revenue ₹46,425,992.00, Contribution Margin ₹7,826,320.00). Plugged promotional subsidy leakage by capping discounts at 20% and simulated fee restructuring (+₹10 on >5km, ₹15 small-basket handling fee). Strictly separated Realized Revenue from Projected Revenue.
  4. Restaurant Optimization: Built `python/decision/restaurant_optimization.py` diagnosing all 1,500 partner restaurants; generated customized partner action plans (+5 min prep buffers, tamper-evident thermal packaging).
  5. Rider Logistics Optimization: Built `python/decision/rider_operations_optimization.py` analyzing fleet workload across 4,000 riders, mitigating 16,119 SLA breaches (>45 mins), integrating Phase 07 90% ETA prediction intervals, and enforcing explicit live GPS telematics caveats.
  6. What-If Scenario Simulations: Built `python/decision/scenario_simulation_engine.py` supporting 5 controlled business simulations with Baseline vs. Assumptions vs. Projected Outcomes and explicit non-guaranteed projection disclaimers.
  7. Financial Impact Engine: Built `python/decision/financial_impact_engine.py` calculating net financial impact, ROI, payback days, and audited post-realization benefit variance against initial projections.
  8. Recommendation Lifecycle Manager: Built `python/decision/recommendation_lifecycle.py` enforcing the 6-state lifecycle (`Proposed` -> `Approved` / `Rejected` -> `In progress` -> `Implemented` -> `Outcome measured`). Attempting execution without human approval raises `HumanApprovalRequiredError`.
  9. Domain AI Agent Integration: Integrated prescriptive fields across `DecisionAgent`, `CustomerAgent`, `FinancialAgent`, `OperationsAgent`, and `RestaurantAgent`, while updating `next_best_action.py` with 100% backward compatibility for API and Streamlit.
  10. Dedicated Verification Suite: Created `tests/test_phase08_prescriptive_intelligence.py` (10/10 passed in 13.33s), verified regression suite (35/35 passed in 15.78s), and preserved all 304,405 records in `novanest_db`.
- **Reason**: Elevates NovaNest into an evidence-grounded, financially quantified prescriptive decision intelligence platform with rigorous human-in-the-loop safety, mathematical transparency, and complete platform stability.

## ADR-034 — Phase 09 Executive UI, Recommendation Action Center & Multi-Platform Experience
- **Date**: 2026-11-15
- **Status**: `IMPLEMENTED_VERIFIED` (`api/main.py` + `frontend/src/views/DecisionIntelligenceView.tsx` + `frontend/src/views/DecisionSimulatorView.tsx` + `frontend/src/views/CustomerIntelligenceView.tsx` + `frontend/src/views/RestaurantIntelligenceView.tsx` + `frontend/src/views/OperationsIntelligenceView.tsx` + `frontend/src/services/api.ts` + `streamlit_app/pages/06_Decision_Intelligence.py` + `streamlit_app/pages/08_Decision_Simulator.py` + `streamlit_app/pages/02_Customer_Intelligence.py` + `streamlit_app/pages/03_Restaurant_Intelligence.py` + `streamlit_app/pages/04_Operations_Intelligence.py` + `tests/test_phase09_executive_ui_and_parity.py` + `NEWCHAGES/PHASE_09/`)
- **Context**: Phase 08 produced high-fidelity prescriptive intelligence, multi-factor risk segmentations, financial unit contribution margin models, and a 6-state recommendation lifecycle manager. In Phase 09, NovaNest required transforming this backend capability into an interactive, multi-platform executive decision-support experience across both React and Streamlit. The implementation required: strict single-source-of-truth parity (zero duplication of financial formulas or recommendation logic in frontend code); full human-in-the-loop approval workflows with actor audit logging; interactive what-if simulation controls with non-guaranteed projection disclaimers; contextual action cards in Customer, Restaurant, and Operations views; and rigorous RBAC enforcement.
- **Decision**:
  1. Prescriptive REST Gateway (`api/main.py`): Exposed 13 dedicated prescriptive endpoints under `/api/prescriptive/*`. Enforced token-based RBAC (`operator` scope for mutating actions like Approve, Reject, In-Progress, Implement, Record Outcome, and Simulate; `read` scope for data views).
  2. Single Source of Truth & Zero Duplication: React consumes typed REST endpoints via `frontend/src/services/api.ts`; Streamlit directly imports shared Python modules (`python.decision.*`). Both platforms utilize identical underlying engines, guaranteeing 100% mathematical, ID, and lifecycle state parity.
  3. Executive Recommendation Center (`frontend/src/views/DecisionIntelligenceView.tsx` & `streamlit_app/pages/06_Decision_Intelligence.py`): Built unified command centers featuring portfolio summary strips (8 interventions, ₹6,12,801.80 gross benefit, ₹2,36,590.00 cost, ₹3,76,211.80 net impact, 1.72x ROI), multi-criteria filters (domain, priority, tier, status), action cards, and contribution margin waterfall views.
  4. Human-in-the-Loop Lifecycle UI: Implemented modal dialogs and form controls for Approve (requires actor + notes), Reject (requires mandatory rationale), Mark in Progress, Mark Implemented, and Record Realized Outcome (audits actual benefits/costs and computes variance % against initial projections). Unapproved executions raise `HumanApprovalRequiredError` (HTTP 400).
  5. What-If Scenario Decision Lab (`frontend/src/views/DecisionSimulatorView.tsx` & `streamlit_app/pages/08_Decision_Simulator.py`): Built interactive controls across 5 canonical scenarios (Discount Capping, Delivery Fee Surcharging, Rider Fleet Expansion, Kitchen Prep Acceleration, VIP Retention Defense) with parameter sliders, comparison tables, charts, and amber projection disclaimer callouts (`is_simulation_projection=True`).
  6. Contextual Action Cards:
     - Customer 360: Embedded prescriptive action cards with RFM recency grounded in `order_datetime`, discount caps (15-20%), MOV rules, and prominent `LOW_EMPIRICAL` churn model warning banners.
     - Restaurant 360: Embedded partner diagnosis and tailored action plans (+5m prep buffer, packaging audit) targeting 511 high-cancellation partners.
     - Rider Operations: Embedded fleet workload cards and tail risk analysis (>45m: 16,119 orders, 32.26%) with mandatory live GPS telematics caveats.
  7. Financial Reconciliations: Reconciled VIP retention economics (+₹14,628.16 net impact on 344 At-Risk VIPs across 4 repeat orders over 60 days), promotional subsidies (2,449 orders with >25% discounts totaling ₹166,477.00 leakage vs ₹2,082,585.00 total delivered discounts), restaurant recovered orders (669 partner-remediation orders vs 720 surge-dispatch orders), and canonical deterministic IDs (`REC-RET-VIP-001` through `REC-OPS-FLT-001`).
  8. Automated Testing & Safety: Built `tests/test_phase09_executive_ui_and_parity.py` (15/15 passed in 14.03s), verified full regressions (45/45 passed), confirmed production React build (`tsc -b && vite build` in 1.91s, 0 errors), confirmed Streamlit compilation (9/9 pages, 0 errors), and preserved all 304,405 records in `novanest_db`.
- **Reason**: Provides operational leaders with an intuitive, mathematically grounded, and strictly governed decision cockpit across platforms, transforming AI predictions into safe, audited business interventions while preserving platform integrity and data safety.

## ADR-035 — Phase 10 Production Operations, Autonomic Monitoring & Incident Resilience
- **Date**: 2026-11-15
- **Status**: `IMPLEMENTED_VERIFIED` (`python/operations/metrics.py` + `python/operations/tracing.py` + `python/operations/health_circuit_breaker.py` + `python/operations/alert_webhook.py` + `python/operations/backup_automation.py` + `python/operations/disaster_recovery_simulation.py` + `python/operations/performance_benchmarks.py` + `docker/prometheus/` + `docker/grafana/` + `docker-compose.monitoring.yml` + `api/main.py` + `api/loader.py` + `frontend/src/services/api.ts` + `tests/test_phase10_production_operations.py` + `NEWCHAGES/PHASE_10/`)
- **Context**: In Phase 10, NovaNest required transforming the containerized, multi-platform platform into an observable, resilient, maintainable, and self-healing operations infrastructure. The system required: comprehensive Prometheus metrics without exposing sensitive endpoints publicly; provisioned Grafana dashboards separating live operational metrics from historical analytics; W3C distributed tracing with automated secret/PII redaction; tiered health checks and self-healing circuit breakers to prevent cascade failures; HMAC-signed webhook alert dispatching; transaction-safe encrypted database backups with retention pruning; and empirical disaster recovery simulation measuring actual RTO/RPO without ungrounded claims.
- **Decision**:
  1. Prometheus Metrics Engine: Created isolated `NOVANEST_REGISTRY` tracking API requests, latency percentiles, error rates, active connections, pool utilization, container health, CPU, memory, and prescriptive business telemetry. Implemented dynamic endpoint normalizer preventing label explosion and protected `/api/metrics` with Bearer auth and network origin filtering.
  2. Grafana Dashboards & Provisioning: Created 4 modular dashboards in `docker/grafana/dashboards/` (`application_health.json`, `database_health.json`, `infrastructure_health.json`, `business_operations.json`) with automated datasource provisioning and `docker-compose.monitoring.yml`.
  3. OpenTelemetry Distributed Tracing: Implemented W3C `traceparent` propagation (`00-{trace_id}-{span_id}-{flags}`) across React -> Nginx -> FastAPI -> Master Orchestrator -> Domain Agents -> MySQL. Deployed in-memory ring buffer (1,000 spans) and automated attribute sanitizer redacting secrets (`[REDACTED_SECRET]`), emails (`[REDACTED_EMAIL]`), and phone numbers (`[REDACTED_PHONE]`).
  4. Autonomic Health Checks & Circuit Breaker: Implemented tiered health probes (`/api/health/live`, `/api/health/ready`, `/api/health/db`, `/api/health/containers`) and thread-safe `CircuitBreaker` guarding MySQL operations. Automatically trips to `OPEN` on failure, routing to local CSV cache in sub-millisecond time (0.0003s) with zero dropped requests.
  5. Operational Alerting & Webhook Dispatcher: Configured all 8 critical alert rules in `docker/prometheus/alert_rules.yml`. Implemented webhook dispatcher with HMAC-SHA256 signature verification and automated URL secret masking (`hooks.slack.com/.../********`).
  6. Database Backup Automation & Isolated Restoration: Automated encrypted database backups using mysqldump and AES-256-CBC PBKDF2 (100k iter) encryption with automated 7-day retention pruning. Engineered isolated restoration engine strictly preventing targeting production database `novanest_db` (`ValueError: CRITICAL SAFETY VIOLATION`).
  7. Disaster Recovery & Empirical RTO/RPO: Executed 6 failure simulations proving empirical RTO (0.150s < 30.0s SLA, 200x faster) and empirical RPO (0.05h < 24.0h SLA, 480x fresher) with zero data loss (304,405 records preserved intact).
  8. Performance & Monitoring Overhead: Verified sub-millisecond API response latency (p50: 0.004 ms, p95: 0.008 ms) and measured Prometheus metrics collection overhead: 0.0032 ms (3.2 microseconds) per request (< 1.0 ms SLA budget).
  9. Verification & Safety: Created dedicated test suite `tests/test_phase10_production_operations.py` (15/15 passed in 6.46s), verified 100% regression suite pass rate (75/75 tests passed), confirmed clean React build (1.48s), and preserved all 304,405 records in `novanest_db`.
- **Reason**: Delivers enterprise-grade observability, autonomic resilience, and deterministic disaster recovery for NovaNest without premature Kubernetes complexity, protecting platform uptime and business continuity while maintaining complete data safety.

---

### ADR-036: SRE Evidence Validation, Defect Rectification & Operational Realism
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: Phase 10 established an operations, monitoring, and resilience foundation. However, independent SRE audit during Phase 10.1 identified operational drifts and theoretical assumptions: stale container images, uninstantiated Prometheus/Grafana Compose services, RTO metrics conflating ciphertext decryption with real DB import, ungrounded 3-minute RPO claims in the absence of continuous binlog shipping, latency microbenchmarks masking live TCP network times, and plaintext encrypted backup sidecars lacking cryptographic authenticity.
- **Decision**:
  1. *Container Fleet Rectification*: Corrected Starlette dependency conflicts, fixed non-root filesystem permissions, aligned Grafana dashboard volume mappings, and rebuilt Docker images. Attached Prometheus (:9090) and Grafana (:3001) to Docker Compose, bringing all 6 containers to `Up (healthy)`.
  2. *Empirical RTO Measurement*: Conducted full database restoration into isolated test database `novanest_restore_isolated`. Separately measured and disclosed: Decryption (0.26s) + SQL import and schema/data insertion (7.51s) + Foreign key validation (0.17s) + Row count audit (0.18s) = **7.95s End-to-End Database RTO** (< 30.0s SLA).
  3. *Empirical RPO Grounding*: Replaced ungrounded 3-minute claims with the empirical **24.0-hour bound** dictated by daily full snapshot frequency. Recommended continuous binlog archiving for Phase 11.
  4. *Live HTTP Benchmarking*: Differentiated in-process telemetry overhead (0.012 ms / 12 μs) from real TCP round-trip HTTP times: direct FastAPI (p50 = 20.09 ms) vs Nginx edge reverse proxy (p50 = 25.85 ms, +5.77 ms proxy overhead).
  5. *Authenticated Backup Encryption*: Upgraded encrypted backups from unauthenticated AES-256-CBC to Encrypt-then-MAC by generating HMAC-SHA256 signature sidecars (`.sql.enc.sig`). Tampered ciphertexts are detected and aborted prior to AES decryption, defeating padding oracle attacks.
  6. *Availability vs Durability Transparency*: Formally documented that during database outages, circuit breakers maintain 100% read availability via cached snapshots, but write operations are suspended to protect data durability and prevent split-brain state.
  7. *Database Safety*: Zero modification to production data: all 10 canonical tables, 304,405 records, and 11 foreign keys verified intact in `novanest_db`.
- **Reason**: Guarantees complete scientific honesty, audit transparency, and cryptographic robustness for NovaNest production go-live commissioning.

---

### ADR-037: Production Go-Live Commissioning & Sub-15-Minute RPO Binary Log Archiving
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: In Phase 10.1, the SRE evidence audit rectified the RPO claim to 24.0 hours, demonstrating that daily snapshots alone cannot protect against intraday data loss without automated incremental binary log archiving. Additionally, production go-live commissioning required hardened multi-environment configurations, TLSv1.2/1.3 reverse proxying with HSTS, non-wildcard CORS allowlists, automated high-entropy secret generation and rotation runbooks, zero plaintext secret leakage in logs, external HMAC-signed alert webhook dispatching across all 8 failure modes, regression resolution, and full end-to-end User Acceptance Testing (UAT).
- **Decision**:
  1. *Sub-15-Minute Empirical RPO via MySQL Binary Log Archiving*: Implemented `python/operations/binlog_archiver.py` provisioned with dedicated least-privilege user `novanest_backup` (`RELOAD`, `REPLICATION CLIENT`, `LOCK TABLES`). The archiver rotates active binary logs (`FLUSH BINARY LOGS;`), encrypts closed logs with AES-256-CBC PBKDF2, signs each archive with an HMAC-SHA256 sidecar (`.enc.sig`, Encrypt-then-MAC), updates `backup/binlogs/manifest.json`, and deletes raw unencrypted binlogs. Empirically certified that archiving on a 15-minute (900-second) cycle slashes potential data loss from **24.0 hours down to $\le$ 15.0 minutes** (a 96x improvement).
  2. *Isolated Restoration Guardrails*: Enforced strict programmatic aborts (`ValueError: CRITICAL SAFETY VIOLATION`) if any restoration or binlog replay attempt targets production `novanest_db`. All recovery drills must target isolated schemas (`novanest_restore_isolated`).
  3. *Production Environment & TLS Hardening*: Defined environment profiles in `config/environments/` (`.env.development`, `.env.staging`, `.env.production`). Deployed `docker/nginx.prod.conf` enforcing TLSv1.2/1.3 on port 443 with Mozilla modern ciphers, HSTS (`max-age=31536000`), port 80 HTTP-to-HTTPS 301 redirect, non-wildcard CORS allowlists (`https://novanest.app`, `https://app.novanest.app`), secure session cookies, and Nginx rate limiting (`50r/s burst=30` API, `10r/s burst=5` AI).
  4. *Cryptographic Secrets Management*: Authored `python/operations/secret_rotation.py` generating 64-byte urlsafe cryptographic secrets with entropy > 4.5 bits/char. Enforced complete `.gitignore` exclusion of all `.env*` files and strict masking (`[REDACTED_SECRET]`) in all logs and transcripts.
  5. *External Alert Webhook Verification*: Validated HMAC-SHA256 signature generation and target URL token masking across all 8 operational alert conditions (`ApiUnavailable`, `DatabaseUnavailable`, `HighLatencyExceeded`, `DiskSpaceExhaustion`, `HighMemoryUtilization`, `BackupAgeExceeded`, `ContainerCrashDetected`, `CircuitBreakerTripped`).
  6. *End-to-End User Acceptance Testing (UAT)*: Validated 8 comprehensive executive and operational journeys in `tests/test_phase11_uat_suite.py` (Executive Overview KPIs, Recommendation Portfolio ROI, Multi-Criteria Filtering, Lifecycle Governance, Customer 360 with `LOW_EMPIRICAL` Churn Caveat, Restaurant 360 Partner Diagnosis, Rider Operations Fleet Workload & Live GPS Telematics Disclaimer, Ask NovaNest Conversational AI Memory & AST Routing).
  7. *Full Platform Regression & Zero Mutation*: Rectified legacy test assumptions (container ports vs host ports, agent confidence status assertion). Verified 100% pass across complete platform test suites (**113 / 113 automated tests passed**). Preserved all 304,405 records in MySQL `novanest_db`.
- **Reason**: Formally certifies NovaNest as fully commissioned, hardened, and ready for controlled production deployment with proven data protection, high availability, and operational integrity.

---

### ADR-038: Phase 12 Final Documentation, Demonstration Preparation & Project Readiness
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: With Phase 11 production go-live commissioning certified, NovaNest required comprehensive academic and technical documentation, a rehearsed live demonstration script, a university evaluation slide deck, and a formal handover inventory. All materials needed to adhere to absolute scientific honesty, distinguish historical facts from predictions and simulations, and provide full operational transparency without claiming unauthorized public deployment.
- **Decision**:
  1. *Comprehensive Deliverables Catalog*: Authored 11 technical documents at the project root: `README.md` (executive platform guide), `PROJECT_REPORT.md` (12-page academic thesis), `SYSTEM_ARCHITECTURE.md` (multi-tier blueprint and Mermaid diagrams), `DATABASE_DOCUMENTATION.md` (canonical schema, ER diagram, 11 foreign keys, SQL KPI formulas), `AI_ML_DOCUMENTATION.md` (5 domain agents, Master Orchestrator, 5 ML models, TreeSHAP, confidence tiers), `API_DOCUMENTATION.md` (OpenAPI REST specification across all 35+ endpoints), `DEPLOYMENT_GUIDE.md` (multi-environment configs, Docker Compose, SRE runbooks), `SECURITY_DOCUMENTATION.md` (threat model, OWASP defense, SQL AST sandbox, Encrypt-then-MAC), `DEMO_SCRIPT.md` (18-minute rehearsed live demo across 10 chapters), `KNOWN_LIMITATIONS.md` (transparent disclosure of synthetic data constraints and sensor absences), and `PRESENTATION.md` (20-slide university evaluation presentation deck).
  2. *Scientific Honesty and Epistemic Distinctions*: Enforced clear separation across historical accounting ground truths (MySQL), probabilistic model predictions (with confidence tiers `LOW_EMPIRICAL` and `BASELINE_ONLY`), and counterfactual simulations (`is_simulation_projection: True`).
  3. *Zero Source Code & Data Mutation*: Preserved all application source code, configuration files, and all 304,405 records in MySQL `novanest_db` with zero modifications.
  4. *Controlled Handover Declaration*: Formally declared NovaNest fully verified and ready for academic examination and controlled production deployment, without claiming unauthorized public deployment.
- **Reason**: Delivers an audit-grade academic and technical handover package ensuring full transparency, reproducibility, and evaluative excellence for capstone and enterprise review committees.

---

### ADR-039: Phase 13 Ultimate Executive Dashboard Architecture & Synchronization Design
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: In Phase 13, NovaNest required transforming the existing multi-tier platform into a cohesive, enterprise-grade Executive Business Intelligence Dashboard. Key requirements included: single-pane executive visibility with 10 canonical KPI cards comparing current performance against prior period baselines; multi-granularity financial intelligence (daily, weekly, monthly toggle) and payment method distributions; customer retention intelligence with acquisition trajectories, new vs repeat order dynamics, and high-value VIP customer identification; restaurant performance rankings (top 20) with prep duration SLAs and underperforming merchant remediation; operations intelligence with delivery vitals and rider fleet rankings; dedicated multi-agent AI Decision Center on the Executive Overview integrating all 5 domain agents via the Master Orchestrator with human approval action gates; synchronized multi-criteria global filtering; and absolute data preservation (304,405 records preserved intact in MySQL `novanest_db`).
- **Decision**:
  1. *Backend Data Layer & Canonical KPI Engine*: Extended `api/main.py` with `_apply_global_filters`, `_calc_delta_metrics`, and `_compute_previous_period_financials`. Upgraded `/api/overview` to emit backwards-compatible `kpis` alongside 10 canonical `kpi_cards` (`total_gmv`, `net_platform_revenue`, `total_orders`, `delivered_orders`, `avg_order_value`, `contribution_margin`, `active_customers`, `active_restaurants`, `active_riders`, `delivery_success_rate`) with values, previous period comparisons, percentage changes, trend directions (`up`, `down`, `neutral`), calculation tooltips, and real-time MySQL synchronization metadata.
  2. *Domain Intelligence API Enhancements*:
     - `/api/financial/overview`: Added `revenue_trends` across daily (30 days), weekly (20 weeks), and monthly (full year) granularities, payment method percentage distribution (UPI 54.9%, Cards 25.0%, Cash/Wallet 20.2%), and monthly AOV trend lines.
     - `/api/customer/overview`: Added monthly customer acquisition trajectory, new vs. repeat customer ratio (89.99% repeat), top 10 high-value VIP customers by CLV, and explicit `LOW_EMPIRICAL` churn tier badge.
     - `/api/restaurant/overview`: Added Top 20 restaurant ranking table with prep duration SLAs, revenue share %, cancellation rates, and underperforming partners remediation candidates.
     - `/api/operations/overview`: Added delivery vitals (49,971 total deliveries, 47,994 completed, 30.1m avg duration, 4.0% late rate, 83.3% fleet utilization), Top 15 rider performance rankings, city operations breakdown, and explicit `BASELINE_ONLY` telematics notice.
  3. *Synchronized Multi-Criteria Global Filter Bar*: Engineered `GlobalFilterBar.tsx` supporting Quick Date Presets (All Time, Last 30 Days, Last 90 Days, Year-to-Date, Custom Range), City dropdown (`All`, `Bangalore`, `Chennai`, `Hyderabad`, `Coimbatore`, `Vijayawada`), Restaurant ID, Customer Segment, Order Status, and Payment Method. Centralized filter state in `App.tsx` and synchronized parameters across all endpoints via `GlobalFilterParams`. Added URL search parameters and hash deep-linking (`?tab=...&city=...`).
  4. *Prescriptive AI Business Intelligence Center*: Integrated dedicated AI intelligence hub on the Executive Overview featuring indicators for all 5 domain agents (Financial, Customer, Operations, Restaurant, Decision) unified by the Master Orchestrator. Surfaced prescriptive recommendations with supporting evidence, relevant KPIs, data source attribution, confidence levels, expected impact, simulation estimates (`is_simulation_projection: True`), and human approval workflow buttons (`Approve` / `Reject`).
  5. *Enterprise UI/UX Design System*: Designed modern glassmorphic dashboard interface with high-contrast typography, responsive 2x5 KPI grid, interactive formula popups (`HelpCircle`), trend badges, and loading skeletons.
  6. *Dedicated Verification Suite & Zero Mutation*: Authored `tests/test_phase13_ultimate_dashboard.py` (10/10 passed in 45.28s) and executed regression suite `tests/test_phase11_uat_suite.py` (8/8 passed in 9.93s). Preserved all 304,405 records across all 10 canonical MySQL tables in `novanest_db` with zero modifications.
  7. *Visual Evidence Archive*: Captured 6 full-viewport screenshots using headless Chrome CLI directly from live Docker containers on port 80 and archived them in `NEWCHAGES/PHASE13/screenshots/`.
- **Reason**: Successfully transforms NovaNest into an enterprise-ready, AI-augmented Food Delivery Business Intelligence Platform that empowers executive decision-makers with real-time audited ground truths, multi-dimensional filtering, transparent formulas, and governed prescriptive interventions.














---

## ADR-040: Phase 14 Advanced AI Business Copilot & Decision Intelligence Architecture
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: In Phase 14, NovaNest required transforming the platform into an advanced conversational AI-powered Food Delivery Business Intelligence and Decision Support Platform. Executives need to query business metrics in natural language, investigate operational anomalies, drill into causal root causes, simulate strategic decisions via counterfactual scenarios, and receive evidence-backed prescriptive recommendations with human approval workflows. The solution must extend the existing multi-tier architecture (React SPA, FastAPI, MySQL 8.0.46, Master Orchestrator, 5 Domain Agents, Prescriptive Engine, and Digital Twin) without building a duplicate prototype, mutating canonical database records (304,405 records), or bypassing security and statistical truth boundaries.
- **Decision**:
  1. *Scenario Simulation Engine Expansion*: Added a 6th strategic business lever (`order_demand_fluctuation` / `order_demand_change`) to `python/decision/scenario_simulation_engine.py` modeling fleet capacity strain, delivery SLA degradation, and driver capacity constraints without any database mutation (`is_simulation_projection: True`).
  2. *Modular AI Copilot Backend Subsystem (`python/ai/copilot/`)*:
     - `copilot_engine.py`: Central `ExecutiveAiCopilot` orchestrator class coordinating Master Orchestrator, multi-agent dispatch (Financial, Customer, Operations, Restaurant, Decision), intent routing, territory scoping, execution tracing, and rich executive markdown response formatting.
     - `executive_summaries.py`: Multi-timeframe (Daily, Weekly, Monthly) and multi-domain (Financial, Customer, Restaurant, Operations, Strategy) grounded executive summaries with strict epistemic classifications (`verified_facts`, `model_predictions`, `strategic_interpretations`, `simulated_projections`).
     - `root_cause_engine.py`: Empirical causal diagnostics for Delivery Delays, Order Cancellations, Customer Churn, and Margin Compression with factor weights, correlation vs causation caveats, and uncertainty disclosures.
     - `business_alerts.py`: Proactive alert scanner with severity ratings (`CRITICAL`, `WARNING`, `INFO`) and mandatory statistical screening flags (`is_confirmed_loss: False`, `is_statistical_screening: True`).
  3. *FastAPI Copilot Gateway*: Added 6 dedicated REST endpoints in `api/main.py` under `/api/copilot/*` (`/query`, `/summaries`, `/root-cause`, `/alerts`, `/simulate`, `/recommendations`) with scope-based security (`read`/`operator`) and input normalization.
  4. *Prescriptive Contract Alignment*: Updated `to_action_recommendation_dict()` in `python/decision/prescriptive_contracts.py` to include `domain` and structured `financial_impact` dict for unified Copilot and frontend recommendation consumption.
  5. *Enterprise React Copilot Interface (`ExecutiveAiCopilot.tsx`)*: Built a dedicated 5-subtab interactive Copilot panel inside the React SPA supporting deep linking (`?tab=copilot&subtab=...`), suggested executive prompts, streaming/history, evidence cards, execution traces, and human-in-the-loop approval workflows (`Approve` / `Reject`). Added top-level navigation item in `Sidebar.tsx` and launcher button in `ExecutiveOverviewView.tsx`.
  6. *Rigorous Automated Verification*: Created `tests/test_phase14_ai_copilot.py` (11/11 tests passing in 47.90s, 100% OK), ran regression on Phase 13 (10/10 passing in 72.43s) and Phase 11 UAT (8/8 passing in 11.03s), compiled production build with zero TypeScript errors, verified live Docker containers, and archived 6 high-resolution 1920x1200 screenshots.
- **Reason**: Successfully transforms NovaNest into an enterprise conversational AI copilot and decision intelligence suite that gives executive leadership unprecedented natural-language visibility, diagnostic causal reasoning, counterfactual simulation power, and governed prescriptive decision workflows while strictly preserving canonical data integrity (304,405 records) and scientific truth boundaries.

---

## ADR-041: Phase 15 Advanced Power BI & Executive Intelligence Architecture
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: In Phase 15, NovaNest required transforming the existing Power BI report (`powerbi/NovaNest.pbix`) into a unified, enterprise-grade analytical platform that integrates financial, customer, restaurant, rider, operational, predictive, and AI-generated insights without unnecessarily rebuilding the existing data model. Key constraints included: preserving the existing PBIX as an immutable backup; validating and expanding DAX measures to align with canonical backend calculations; resolving the historical `orders` vs `orders_table` naming difference through explicit source mapping; enabling transaction and partner drill-throughs; integrating Phase 14 AI Copilot outputs; configuring enterprise MySQL refresh runbooks; reconciling at least 20 canonical KPIs across all 5 platform tiers; and preserving all 304,405 records in MySQL `novanest_db`.
- **Decision**:
  1. *Asset Protection Protocol*: Backed up original `NovaNest.pbix` (5.64 MB) to `powerbi/NovaNest_backup_phase15.pbix` and `powerbi/NovaNest_original.pbix` prior to modification.
  2. *Canonical Data Model & Source Mapping*: Formalized star schema in `powerbi/model_schema.json` mapping `orders` to the canonical MySQL `orders` view (which selects all columns from `orders_table`), permanently resolving naming discrepancies across platforms.
  3. *Canonical DAX Governance Catalog*: Authored `powerbi/dax_measures_catalog.dax` structuring 55+ production DAX measures across 7 domains including 10 certified executive KPI cards with MoM variance, growth %, and trend indicators. Reconciled Contribution Margin to match canonical unit economics (23.59% - 24.54%).
  4. *10-Page Enterprise Report Expansion*: Expanded `Report/Layout` in `powerbi/NovaNest.pbix` from 5 to 10 distinct sections with 101 visual elements: Executive Command Dashboard, Financial Intelligence, Customer 360, Restaurant Intelligence, Operations Intelligence, City-Wise Business Intelligence, Predictive Analytics & ML Quality, AI Copilot Insights & Decision Support, Financial Transaction Drill-Through, and Restaurant Partner Drill-Through.
  5. *Advanced Features*: Added 5 interactive Bookmarks, report-page tooltips, synchronized slicers, and mobile layout configurations.
  6. *Data Source & Refresh Runbook*: Authored `powerbi/mysql_connection_guide.md` with parameterized Power Query M scripts, On-Premises Data Gateway setup, and scheduled refresh protocols.
  7. *25-Point Cross-Platform Reconciliation*: Reconciled 25 canonical KPIs across MySQL, FastAPI, Power BI, and React with 24/25 exact match and 1/1 explained variance.
  8. *Automated Verification*: Authored `tests/test_phase15_powerbi_intelligence.py` (12/12 passed), executed Phase 14 (11/11 passed), Phase 13 (10/10 passed), and Phase 11 UAT (8/8 passed) regressions for 41/41 total tests passed. Captured 10 high-resolution screenshots.
- **Reason**: Successfully transforms NovaNest Power BI into a premier enterprise analytics platform that delivers complete cross-tier harmony, verified mathematical truth, and deep decision support while strictly adhering to data preservation and governance protocols.

---

## ADR-042: Phase 16 Ultimate UI/UX & Experience Engineering Architecture
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: In Phase 16, NovaNest required transforming the user experience into a visually polished, consistent, responsive, enterprise-grade AI-powered Business Intelligence platform. Requirements spanned: unified design tokens across React and Streamlit; accessible UI components avoiding color-only indicators; advanced analytical data tables with server/client pagination without loading 50,000 orders into DOM; shimmering skeleton loaders with zero fabricated fallback metrics; responsive multi-viewport adaptability across desktop, laptop, tablet, and mobile viewports; and AI Copilot conversational ergonomics (Markdown and JSON export, 1-click response copying, and conversation reset). All existing FastAPI endpoints, MySQL database records (304,405 rows), calculations, and epistemic markers (`LOW_EMPIRICAL`, `BASELINE_ONLY`, `is_simulation_projection: True`) had to remain 100% intact.
- **Decision**:
  1. *Reusable Accessible Component Architecture (`frontend/src/components/ui/`)*:
     - `DataTable.tsx`: Generic typed data table with real-time search filtering, multi-column sorting (ascending/descending with keyboard Enter/Space support), client-side pagination (5, 10, 25, 50 rows per page), column visibility dropdown, CSV data export, and expandable row details drawer.
     - `SkeletonLoader.tsx`: Accessible shimmer loading component supporting `kpi`, `chart`, `table`, `card` variants with `aria-busy="true"` and `aria-live="polite"`.
     - `StatusBadge.tsx`: WCAG AA compliant badge component pairing icons (`CheckCircle2`, `AlertTriangle`, `XCircle`, `Info`, `Clock`) with text to ensure color-blind accessibility.
  2. *Domain Views Upgrade*:
     - Upgraded `ExecutiveOverviewView`, `CustomerIntelligenceView`, `RestaurantIntelligenceView`, `OperationsIntelligenceView`, and `FinancialIntelligenceView` to use `SkeletonLoader` instead of generic spinners and interactive `DataTable` components for merchant rankings, VIP cohorts, operational anomalies, and revenue leakage screening.
  3. *AI Business Copilot Ergonomics*:
     - Integrated `handleExportMarkdown` and `handleExportJSON` to allow executives to export complete conversation transcripts, verified facts, and prescriptive recommendations.
     - Added 1-click "Copy Answer" with visual toast checkmark feedback and instant conversation history clear.
  4. *Responsive Navigation Architecture*:
     - Updated `Sidebar.tsx` to support both persistent desktop navigation (`hidden md:flex`) and a slide-over mobile drawer (`md:hidden`) with touch dismiss, backdrop blur, and keyboard `Escape` listener.
     - Updated `HeaderNav.tsx` with mobile hamburger toggle button visible on `< md` viewports and explicit ARIA labels.
     - Orchestrated `mobileSidebarOpen` state in `App.tsx`.
  5. *Design Tokens & Accessibility*:
     - Enhanced `frontend/src/index.css` with global high-contrast `:focus-visible` outline rings for keyboard navigation and comprehensive `@media (prefers-reduced-motion: reduce)` animation resets.
     - Harmonized Streamlit tokens in `streamlit_app/styles/theme.css` with matching Obsidian & Sapphire palette tokens and typography.
  6. *Automated Verification & Evidence*:
     - Authored `tests/test_phase16_ui_ux_experience.py` (11/11 tests passed in 48.78s, 100% OK).
     - Executed regression suites: Phase 15 (12/12 passed), database zero-mutation audit (exactly 304,405 records preserved).
     - Captured 9 multi-viewport headless Chrome screenshots across Desktop (1920x1200), Tablet (1024x768), and Mobile (375x812).
- **Reason**: Successfully elevates NovaNest into an enterprise-class, accessible, and responsive AI business intelligence platform while strictly upholding non-destructive data integrity and scientific honesty.

---

## ADR-043: Phase 17 Performance & Scalability Architecture
- **Date**: 2026-11-15
- **Status**: ACCEPTED & IMPLEMENTED
- **Context**: In Phase 17, NovaNest required end-to-end performance and scalability engineering across the React frontend, FastAPI backend, MySQL queries, AI Copilot response times, server-side pagination, Docker resource utilization, and concurrent user scalability (10, 25, 50 users). All 304,405 records across all 10 canonical tables and existing security, RBAC, and calculation logic had to be preserved without exception.
- **Decision**:
  1. *Frontend Dynamic Code-Splitting*:
     - Refactored `frontend/src/App.tsx` with `React.lazy` and `Suspense` for all 10 domain views and Copilot, backed by `SkeletonLoader` shimmer states.
     - Configured manual vendor chunking in `frontend/vite.config.ts` (`vendor-react`, `vendor-charts`, `vendor-icons`, `vendor-three`).
     - Result: Main application bundle dropped by 92.6% (995.65 kB to 73.54 kB), eliminating large chunk warnings and accelerating initial load times.
  2. *Database Composite Indexing*:
     - Created covering composite indexes on `orders_table` (`idx_orders_status_dt`, `idx_orders_cust_status`) and `deliveries` (`idx_deliveries_rider_dur`).
     - Multi-table join aggregation dropped from 865.0ms to 160.0ms (5.4x speedup, 81.5% reduction), eliminating disk filesorts.
  3. *Multi-Tiered Caching Engine (`api/cache.py`)*:
     - Built thread-safe L1 memory LRU cache with configurable TTL (default 60s) and optional Redis L2 peering.
     - Integrated cache checks into `/api/overview`, `/api/customer/overview`, `/api/restaurant/overview`, `/api/operations/overview`, and `/api/financial/overview`.
     - Result: Executive Overview hit latency dropped from 1,045.5ms to 13.1ms (79.7x speedup).
  4. *Server-Side Dataset Pagination Engine (`api/pagination.py`)*:
     - Implemented `/api/records/{entity}` supporting orders, customers, restaurants, riders, deliveries, and transactions.
     - Strictly enforced immutable sorting whitelists, bounded limits (default 25, max 100), and total counts to prevent unbounded memory queries.
  5. *AI Copilot Inquiry Acceleration*:
     - Added secure deterministic query hashing for read-only analytical Copilot questions in `ExecutiveAiCopilot`.
     - Repeat decision inquiries dropped from 1,508.3ms to 13.6ms (110.8x speedup).
  6. *Concurrency & Load Resilience*:
     - Executed load test suite `scripts/load_test_phase17.py` simulating 10, 25, and 50 concurrent users (600 requests) with 0.0% error rate and ~78 RPS.
  7. *Observability & Verification*:
     - Provisioned dedicated Grafana dashboard `performance_scalability.json` visualizing cache hit ratios, throughput, and latency percentiles.
     - Authored `tests/test_phase17_performance_scalability.py` (10/10 PASS in 1.256s); Phase 16 regression passed in 17.40s (down from 76.93s).
- **Reason**: Provides enterprise-grade responsiveness, sub-second latency, and horizontal scalability while guaranteeing 100% database integrity and security preservation.

---

### ADR-044: Independent Security Hardening and UI Contract Resilience

- **Status**: Accepted & Implemented (Phase 18)
- **Context**:
  An independent defensive security audit of the NovaNest platform and penetration tests uncovered 5 security posture gaps (PII exposure via pagination IDOR, fail-open sort column fallback, excessive MySQL DDL privileges, dropped Nginx security headers on static assets). Simultaneously, live dashboard users experienced unhandled React exceptions (`Cannot read properties of undefined (reading 'slice')` and `.map()`) caused by data contract discrepancies between backend analytical models and frontend TypeScript assumptions.
- **Decision**:
  1. *Role-Based Access Control on Customer PII*: Gated `/api/records/customers` strictly behind the `operator` role scope, preventing `viewer` principals from accessing sensitive customer names, addresses, and subscription details.
  2. *Fail-Closed Input Validation*: Replaced permissive sort column fallback in `api/pagination.py` with strict whitelist enforcement, rejecting SQL injection probes and unrecognized columns with HTTP 400 Bad Request.
  3. *Database Least Privilege*: Revoked `ALL PRIVILEGES` from application user `novanest_app`, granting read-only access to master data and write access restricted strictly to transaction/log tables. DDL is strictly denied.
  4. *Contract Alignment & Client-Side Normalization*: Synchronized backend serialization to return `supporting_evidence` as an array alongside financial chart details, and added boundary normalizers in `frontend/src/services/api.ts` with local `ErrorBoundary` fallback wrappers in React views.
  5. *Nginx Header Preservation*: Added security headers explicitly inside child static asset location blocks in `docker/nginx.conf` to counteract Nginx header inheritance cancellation.
  6. *Automated Security Regression Suite*: Authored `tests/test_phase18_security_audit.py` with 15 automated test cases validating fail-closed auth, RBAC boundaries, SQLi rejection, security headers, MySQL privileges, and data integrity.
- **Reason**: Guarantees defense-in-depth, protects confidential customer PII, eliminates runtime UI crash vectors, and ensures resilient enterprise security posture without altering any canonical database records.

---

### ADR-045: Enterprise Design System & Complete Theme Transformation

- **Status**: Accepted & Implemented (Phase 18 Theme)
- **Context**:
  NovaNest's legacy dashboard UI utilized a dark emerald green cockpit aesthetic that did not align with executive business intelligence standards and lacked cross-platform brand harmony across React, Streamlit, and Power BI. The user requested an immediate, comprehensive transformation of the entire application into a modern, clean enterprise dashboard adhering strictly to the official NovaNest colour palette (Background `#F8FAFC`, Primary `#2563EB`, Accent `#F97316`, Main Text `#1E293B`) with supporting white surfaces (`#FFFFFF`), borders (`#E2E8F0`), and semantic indicators.
- **Decision**:
  1. *Centralized Token System & Backward-Compatible Aliases*: Configured brand tokens in `frontend/tailwind.config.js` and defined CSS variables under `:root` and `[data-theme="novanest"]` in `frontend/src/index.css`. Mapped legacy dark `obsidian` tokens to enterprise light equivalents and added global CSS normalization rules to prevent dark container remnants.
  2. *Complete Purge of Legacy Emerald Theme*: Replaced the default theme in `ThemeContext.tsx` with `'novanest'`, completely removing the legacy dark `'emerald'` theme option.
  3. *Full-Stack Aesthetic Transformation*:
     - Transformed HeaderNav, Sidebar, KpiCards, DataTables, FilterBars, and Hero banners to clean white surfaces with slate-200 borders, deep slate text, and royal blue accents.
     - Restyled all 9 analytical views, conversational Copilot, and floating chatbot with royal blue message bubbles, white response cards, and vibrant orange action buttons.
  4. *Cross-Platform Streamlit Synchronization*: Configured `.streamlit/config.toml` with `primaryColor="#2563EB"` and `backgroundColor="#F8FAFC"`, and updated `streamlit_app/styles/theme.css`.
  5. *Power BI Enterprise Theming*: Formulated `powerbi/novanest_theme.json` with official data colors and injected the theme into `powerbi/NovaNest_themed.pbix` while backing up the original report to `powerbi/NovaNest_backup_phase18_theme.pbix`.
  6. *Zero Backend / Database Mutation*: Strict non-functional requirement enforced: all 304,405 canonical records in MySQL `novanest_db` remain 100% unaltered.
  7. *Automated & Visual Verification*: Authored `tests/test_phase18_theme_transformation.py` (9/9 PASS) and captured 10 full 1920x1080 viewport screenshots validating every transformed screen.
- **Reason**: Delivers a cohesive, accessible, executive-ready presentation tier across all user touchpoints while preserving existing backend analytical pipelines and transactional data models.



