# PHASE_06 - PHASE PLAN

Initialized on 2026-11-07.


---

## Phase 06 Architecture & Implementation Planning Blueprint (2026-11-11)

- **Document Status**: `PROPOSED_ARCHITECTURE_BLUEPRINT` (Planning Only — **NO implementation started**)
- **Baseline Codebase & Commit**: `main` @ `21b2e2b` (post-Phase 05.3 Closure)
- **Scope Classification**: `VERIFIED` current audit findings, `PARTIALLY_VERIFIED` integration surfaces, `BLOCKED` live MySQL state, and `PROPOSED` Phase 06 target architecture.

### 1. Objective
Upgrade NovaNest's existing single-intent conversational AI (`python/ai/analyst/`) and disconnected Streamlit Page 07 legacy AI (`python/ai/conversational/`) into a deterministic, security-hardened, observable **Multi-Agent Decision Intelligence Subsystem** that:
1. Reuses NovaNest's verified Phase 01–05.3 analytics engines (`python/analytics/*`, `python/intelligence/*`, `python/digital_twin/*`, `python/decision_simulation/*`, `python/decision/*`), AST SQL sandbox (`python/ai/analyst/sql_ast.py`), and RBAC/CORS layer (`api/auth.py`).
2. Replaces brittle keyword-only routing and hardcoded RCA/recommendation templates (`root_cause.py`, `orchestrator.py`, `data_grounding.py` residual defaults) with structured **Master Orchestrator + 5 Specialized Domain Agents**.
3. Enforces strict data grounding (`kpi_definitions.json`, CSV/SQLite read-only sandbox, optional MySQL), explicit ML confidence caveats (`0/5` Phase 05 models production-ready on synthetic data), principal-scoped memory with TTL eviction, and unified React + Streamlit UX.

### 2. Core Design Principles (Non-Negotiable)
1. **Deterministic Computation First, LLM Synthesis Second**: Agents compute numbers ONLY via certified Python analytics engines or validated read-only SQL queries. LLMs (Gemini `gemini-2.5-flash` / `MockAIProvider`) narrate pre-computed, schema-validated tool outputs—never raw arithmetic.
2. **Modular Over-Engineering Avoidance**: Implement in-process async/thread-pool multi-agent orchestration inside Python/FastAPI (`concurrent.futures` / `asyncio.gather`) using typed Python Pydantic contracts (`AgentTask`, `AgentResult`, `AgentContext`) rather than heavyweight external distributed frameworks (no Kafka, Celery, Neo4j, or standalone vector DB clusters unless future scale requires them).
3. **Fail-Closed Grounding & Honest Confidence**: Never substitute general knowledge for missing business telemetry (e.g., promo attribution, traffic/GPS, confirmed fraud labels), and propagate Phase 05 validation statuses (`NEEDS_MORE_DATA`, `BASELINE_ONLY`, `EXPERIMENTAL`) directly to every UI badge.
4. **Unified Contract Across FastAPI, React, and Streamlit**: Eliminate Page 07 legacy fork (`python/ai/conversational/*` deprecation/adapter) so React `AiIntelligenceView.tsx`, `FloatingChatbot.tsx`, and Streamlit `07_Ask_NovaNest.py` execute the identical backend/orchestrator pipeline.

### 3. Blueprint Document Index (`NEWCHAGES/PHASE_06/`)
| Document | Coverage |
|---|---|
| [`ARCHITECTURE_DESIGN.md`](./ARCHITECTURE_DESIGN.md) | Audited baseline vs proposed Multi-Agent topology, Mermaid architecture diagram, reuse vs new module matrix |
| [`AGENT_SPECIFICATIONS.md`](./AGENT_SPECIFICATIONS.md) | Detailed input/output schemas, reused engines, failure fallbacks, and guardrails for Master + 5 Domain Agents |
| [`DATA_FLOW_DESIGN.md`](./DATA_FLOW_DESIGN.md) | `AgentContext`, scoped session memory, TTL/eviction, `DatasetMetadataRegistry`, `kpi_definitions.json` grounding, SQL/CSV/MySQL flow |
| [`API_CONTRACTS.md`](./API_CONTRACTS.md) | Additive backward-compatible `/api/ai/ask` schema, proposed `/api/ai/v2/*`, RBAC fix on `/api/ai/reset`, React & Streamlit UX specs |
| [`SECURITY_DESIGN.md`](./SECURITY_DESIGN.md) | Principal-scoped session isolation, per-agent RBAC & table ACLs, prompt-injection defense, numeric reconciliation guardrails, audit logging |
| [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md) | Measurable routing, financial reconciliation (`0.05`), grounding, hallucination, security, latency, and React/Streamlit UI verification gates |
| [`IMPLEMENTATION_ROADMAP.md`](./IMPLEMENTATION_ROADMAP.md) | Sequential sub-phases `Phase 06.0` through `Phase 06.8` with entry/exit gates and critical Phase 06.0 stabilization prerequisites |
| [`RISK_REGISTER.md`](./RISK_REGISTER.md) | Operational, security, ML-overconfidence, MySQL blockage, schema drift, and latency risks with concrete mitigations |

### 4. Non-Goals (Phase 06 Scope Boundaries)
- Retraining Phase 05 ML models without new real-world behavioral/GPS/fraud telemetry (`0/5` production-ready constraint remains).
- Deploying distributed microservice queues or external vector infrastructure.
- Altering certified Phase 04 KPI definitions (`KPI-01`..`KPI-16`) or Power BI `.pbix` artifacts.
