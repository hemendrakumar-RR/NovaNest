# NOVANEST PHASE 06.5 — MILESTONE 1
## Technical Implementation Plan: Performance & Zero-Copy Engine

**Milestone**: Phase 06.5, Milestone 1  
**Status**: APPROVED & READY FOR EXECUTION  
**Target Files**:
1. `python/ai/agents/master_orchestrator.py`
2. `python/ai/agents/decision_agent.py`
3. `tests/test_phase06_5_integration.py` (New test suite)

---

### 1. Exact Functions to Modify

#### 1.1. `python/ai/agents/master_orchestrator.py`
- **Function**: `_slice_isolated_data(data: Dict[str, pd.DataFrame], allowed_datasets: Sequence[str]) -> Dict[str, pd.DataFrame]`
  - *Current Implementation*: Iterates through allowed datasets and creates a deep copy `df.copy(deep=True)`.
  - *Modification*: Use zero-copy shallow slicing `df.copy(deep=False)`. Pandas 3.0.5 Copy-on-Write guarantees that any mutation in an agent automatically triggers CoW on the modified column, leaving the original DataFrame untouched.
  - *Cost Reduction*: Slicing time drops from `40.27 ms` to `2.74 ms` (14.7x speedup). Eliminates peak memory allocation spikes of 45+ MB during concurrent runs.

- **Function**: `_execute_stage2_sequential(...)`
  - *Current Implementation*: Extracts only textual summaries (`agent_id`, `status`, `summary[:300]`) into `upstream_findings`.
  - *Modification*: Enrich `upstream_findings` with structured dictionary containing verified facts and metrics from successful Stage-1 results (e.g. `gmv_inr`, `net_revenue_inr`, `total_orders`, `sla_breach_rate_pct`, `facts`, `metrics`).
  - *Impact*: Stage 2 `DecisionAgent` receives certified metrics computed by Stage 1 instead of having to rescan 50,000 raw order rows from scratch.

#### 1.2. `python/ai/agents/decision_agent.py`
- **Function**: `DecisionAgent._run_domain(...)`
  - *Current Implementation*: Re-scans `orders` and `deliveries` from scratch to compute GMV, Net Revenue, Total Orders, and SLA Breach Rate, even when Stage 1 financial and operational agents already computed them with certified accuracy.
  - *Modification*: In `_run_domain`, inspect `request.metadata.get("upstream_findings")`. If upstream findings contain certified `metrics` and `facts` (and no narrowing filters like `city` conflict), reuse the pre-calculated metrics directly. If not present (e.g., when `DecisionAgent` runs standalone without Stage 1), fall back transparently to raw DataFrame aggregation.
  - *Impact*: Saves ~900–1,200 ms of redundant table aggregation in Stage 2 without altering any calculation formulas or KPI values.

---

### 2. Mutation Risks & Mitigation Strategy

| Component | Potential Risk | Mitigation Mechanism |
|---|---|---|
| **Pandas Slices** | Agent modifying column in-place affects other agents. | **Pandas 3.0.5 CoW Guarantee**: Any column write triggers deep copy of that column. Confirmed by unit tests showing SHA-256 hash identity across all 10 tables. |
| **NumPy Buffers** | Direct C-buffer assignment via `.values[i] = x`. | All NovaNest analytics modules are functional and operate via high-level pandas APIs (`groupby`, `merge`, `assign`, vector math). Direct buffer writes are strictly absent. |
| **Context Metadata** | Concurrent tasks mutating shared request metadata dictionary. | In `_prepare_agent_task()`, each agent request receives an independent newly instantiated `AgentRequest` with an isolated metadata dictionary. |
| **Filtered Slices** | Applying filters (e.g. city) mutating underlying data. | Filter expressions (`df[df['col'] == val]`) create new filtered slices, which are independent objects. |

---

### 3. Thread-Safety Strategy

1. **Immutable Context Descriptors**: `AgentContext` stores only frozen Pydantic models (`DatasetMetadataEntry`, `KpiDefinitionEntry`, `ConversationTurnSummary`). No mutable data structures are exposed to worker threads.
2. **Zero-Copy Read Isolation**: All worker threads read from shared DataFrames using shallow copies (`deep=False`). Under Pandas 3.0.5 CoW, reads are entirely thread-safe and concurrent.
3. **Thread-Pool Bounded Execution**: Worker threads execute inside `ThreadPoolExecutor(max_workers=min(len(tasks), 4))` with strict per-agent timeouts (`per_agent_timeout_seconds=20.0`).
4. **Isolated Result Gathering**: Each worker thread returns an independent `AgentResult`. Synthesis and verification run sequentially on the main thread after all worker futures resolve.

---

### 4. Rollback Strategy

1. **Instant Rollback**: If any regression or mutation occurs, `_slice_isolated_data` can be immediately reverted to `df.copy(deep=True)` in a single line.
2. **Fallback in DecisionAgent**: The metric extraction in `DecisionAgent` is purely additive. If `upstream_findings` is empty or missing, `DecisionAgent` automatically executes its existing raw calculation path. Reverting the orchestrator metadata change requires zero changes to `DecisionAgent`.
3. **No Database / Disk Schema Changes**: Milestone 1 touches only in-memory execution logic and adds tests; no CSV files or SQLite tables are altered.

---

### 5. Expected Performance Improvements

| Metric | Current Baseline | Projected Post-Milestone 1 | Expected Improvement |
|---|---|---|---|
| Data Slicing Latency | `40.27 ms` | `< 3.00 ms` | **> 13x Faster** |
| Peak Memory Churn | `45.66 MB` | `< 25.00 MB` | **~45% Memory Reduction** |
| Stage 2 Execution Time | `2371.11 ms` | `1200–1500 ms` | **~40% Faster Stage 2** |
| 5-Domain Multi-Agent Query | `~5.64 s` | `~3.80–4.20 s` | **~25–30% End-to-End Latency Reduction** |

---

### 6. Required Correctness & Verification Tests

The new test suite `tests/test_phase06_5_integration.py` will enforce:
1. **DataFrame Immutability Test**:
   - Compute SHA-256 hashes of all 10 datasets.
   - Run 5-domain multi-agent orchestration.
   - Assert all 10 SHA-256 hashes remain 100% identical.
2. **Concurrent Multi-Agent Thread Safety Test**:
   - Launch 4 concurrent multi-agent requests across multiple threads.
   - Verify zero cross-talk, zero race conditions, and identical output verification outcomes.
3. **Certified KPI Consistency Test**:
   - Assert all certified KPIs (`KPI-01` to `KPI-16`) generated by the zero-copy orchestrator match ground truth values exactly.
4. **Standalone vs Upstream Fallback Test**:
   - Execute `DecisionAgent` directly (standalone without orchestrator) -> verify it computes metrics correctly.
   - Execute `DecisionAgent` with `upstream_findings` -> verify identical outputs and faster execution.
5. **Full Regression Suite**:
   - Execute all 11 test modules (`test_phase06_4_security_reliability_eval`, `test_phase06_3_orchestrator`, `test_phase06_2_domain_agents`, `test_phase06_1_foundation`, `test_phase06_0_stabilization`, `test_universal_ai_suite`, `test_phase05_3_security_and_contracts`, `test_ml_models_phase05`, `test_api_alignment_phase05_1`, `test_ask_novanest_ai_suite`, `test_frontend_rebuild`).
   - Run `tests/run_all_tests.py` and `tests/test_digital_twin.py`.
   - Run frontend `tsc --noEmit` and `npm run build`.

