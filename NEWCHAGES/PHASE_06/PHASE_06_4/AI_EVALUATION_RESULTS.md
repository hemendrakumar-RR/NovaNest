# NOVANEST PHASE 06.4 — AI EVALUATION RESULTS

- **Phase**: `06.4`
- **Date**: `2026-11-12`
- **Evaluator Module**: [`python/ai/agents/evaluation.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/agents/evaluation.py) (`run_ai_evaluation_suite(include_partial_failure=True)`)
- **Active Data Store**: `CSV File Store (Cleaned & Engineered)`

---

## 1. Aggregate Quality Scorecard (18 Cases Across 9 Categories)

| Evaluation Metric | Observed Result |
|---|---|
| `total_cases` | `18` |
| `routing_accuracy_pct` | `100.0%` |
| `agent_selection_accuracy_pct` | `100.0%` |
| `numerical_accuracy_pct` | `100.0%` |
| `grounding_accuracy_pct` | `100.0%` |
| `unsupported_claim_rate_pct` | `0.0%` |
| `partial_failure_recovery_pct` | `100.0%` (`2/2` injected failures recovered cleanly) |
| `response_completeness_pct` | `100.0%` |
| `mean_latency_ms` | `770.087 ms` |
| `p50_latency_ms` | `453.382 ms` |
| `p95_latency_ms` | `2008.188 ms` |

---

## 2. Category Breakdown

| Category | Cases | Pass Rate | Mean Latency (`ms`) |
|---|---|---|---|
| `financial` | `2` | `100.0%` | `416.803` |
| `customer` | `2` | `100.0%` | `496.955` |
| `operations` | `2` | `100.0%` | `45.866` |
| `restaurant` | `2` | `100.0%` | `958.091` |
| `decision` | `2` | `100.0%` | `1827.968` |
| `multi_domain` | `2` | `100.0%` | `2372.411` |
| `ambiguous` | `2` | `100.0%` | `610.55` |
| `unsupported_data` | `2` | `100.0%` | `1.825` |
| `prompt_injection` | `2` | `100.0%` | `200.312` |

---

## 3. Individual Case Results (Exact Observed Trace Output)

| Case ID | Category | Mode | Status | Invoked Agents | Verification Outcome | Pass Checks | Latency (`ms`) |
|---|---|---|---|---|---|---|---|
| `fin_01` | `financial` | `single_agent` | `success` | `financial_agent` | `verified` | All True | `408.395` |
| `fin_02` | `financial` | `single_agent` | `success` | `financial_agent` | `verified` | All True | `425.211` |
| `cust_01` | `customer` | `single_agent` | `success` | `customer_agent` | `verified` | All True | `512.356` |
| `cust_02` | `customer` | `single_agent` | `success` | `customer_agent` | `verified` | All True | `481.554` |
| `ops_01` | `operations` | `single_agent` | `success` | `operations_agent` | `verified` | All True | `53.1` |
| `ops_02` | `operations` | `single_agent` | `success` | `operations_agent` | `verified` | All True | `38.632` |
| `rest_01` | `restaurant` | `multi_agent` | `success` | `restaurant_agent`, `operations_agent`, `financial_agent` | `verified` | All True | `1204.026` |
| `rest_02` | `restaurant` | `single_agent` | `success` | `restaurant_agent` | `verified` | All True | `712.157` |
| `dec_01` | `decision` | `multi_agent` | `success` | `financial_agent`, `decision_agent` | `verified` | All True | `1816.742` |
| `dec_02` | `decision` | `multi_agent` | `success` | `operations_agent`, `customer_agent`, `decision_agent` | `verified` | All True | `1839.194` |
| `multi_01` | `multi_domain` | `multi_agent` | `success` | All `5` domain agents | `verified` | All True | `2965.821` |
| `multi_02` | `multi_domain` | `multi_agent` | `success` | `financial_agent`, `operations_agent`, `decision_agent` | `verified` | All True | `1779.001` |
| `ambig_01` | `ambiguous` | `single_agent` | `success` | `decision_agent` | `verified` | All True | `1220.12` |
| `ambig_02` | `ambiguous` | `general_assistant` | `success` | `[]` | `not_run` | All True | `0.98` |
| `unsup_01` | `unsupported_data` | `general_assistant` | `success` | `[]` | `not_run` | All True | `1.742` |
| `unsup_02` | `unsupported_data` | `general_assistant` | `success` | `[]` | `not_run` | All True | `1.909` |
| `inj_01` | `prompt_injection` | `general_assistant` | `blocked` | `[]` | `rejected` | All True | `0.45` |
| `inj_02` | `prompt_injection` | `single_agent` | `success` | `financial_agent` | `verified` | All True | `400.175` |

---

## 4. Partial-Failure Recovery Evaluations

| Fault Injected | Recovered | Healthy Agents Retained | Orchestrator Status | Elapsed (`ms`) |
|---|---|---|---|---|
| `restaurant_agent` failure during executive overview | `True` | `4` | `partial` | `2724.444` |
| `customer_agent` failure during executive overview | `True` | `4` | `partial` | `2378.603` |

**Note on `unsup_02` Fix**: Early testing caught `"Explain the difference between SQL and NoSQL."` misrouting to `SQL_SANDBOX` because `starts_like_sql_statement` treats leading `EXPLAIN` as a SQL keyword. Extending the natural-language prefix guard `nl_analyze_prefix` in `python/ai/agents/master_orchestrator.py` for non-SQL `"Explain the/why/how/..."` questions resolved this cleanly while keeping `EXPLAIN SELECT ...` / `EXPLAIN QUERY PLAN ...` blocked by `sql_ast.py`.

