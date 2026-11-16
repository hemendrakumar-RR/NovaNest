# NOVANEST PHASE 06.4 — PERFORMANCE & RESOURCE BENCHMARK RESULTS

- **Phase**: `06.4`
- **Date**: `2026-11-12`
- **Benchmark Runner**: [`python/ai/agents/evaluation.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/python/ai/agents/evaluation.py) (`run_performance_benchmarks(iterations=3, concurrent_workers=4)`)
- **Active Data Store**: `CSV File Store (Cleaned & Engineered)`

---

## 1. Host Environment Profile

| Property | Observed Value |
|---|---|
| Operating System | `Windows-11-10.0.26200-SP0` |
| Python Runtime | `3.14.4` (`AMD64`) |
| Logical CPU Cores | `16` |
| System Memory | `23.64 GB` |

---

## 2. Latency, Concurrency, Memory, Timeout & Recovery Measurements

| Benchmark Suite | Metric | Observed Value |
|---|---|---|
| Single-Agent Execution (`3` iterations) | Mean | `407.559 ms` |
| Single-Agent Execution (`3` iterations) | P50 / P95 | `407.695 ms` / `421.706 ms` |
| Multi-Agent Parallel Executive Sweep (`3` iterations) | Mean | `9600.491 ms` |
| Multi-Agent Parallel Executive Sweep (`3` iterations) | P50 / P95 | `9581.175 ms` / `9694.243 ms` |
| Parallel vs Sequential Comparison (`warm analytics`) | Sequential / Parallel / Speedup | `1581.762 ms` / `1646.239 ms` / `0.961x` |
| Concurrent Execution (`4` simultaneous requests) | Total Wall Time | `1672.308 ms` |
| Concurrent Execution (`4` simultaneous requests) | Per-Request Mean / P95 | `1653.866 ms` / `1669.366 ms` |
| `tracemalloc` Memory Profiling | Before / After / Peak Traced | `0.0 MB` / `0.294 MB` / `51.408 MB` |
| Per-Agent Timeout Cutoff (`550ms` simulated delay) | Configured / Observed Cutoff / Status | `150.0 ms` / `272.039 ms` / `timeout` |
| Transient Read Failure Retry Recovery | Attempts Executed / Status / Elapsed | `2` / `success` / `440.473 ms` |

---

## 3. Observed Engineering Interpretation

- **Parallel vs Sequential (`0.961x` ratio on warm in-memory DataFrames)**: Because the domain agents execute synchronous pandas/NumPy aggregations inside Python CPython 3.14 threads, the GIL limits pure CPU-bound thread scaling compared to sequential execution; however, concurrent Stage-1 dispatch prevents an individual slow or external I/O-bound agent from delaying sibling completions beyond the configured per-agent timeout, while the `BoundedSemaphore` (`max_concurrent_requests`) caps concurrent memory spikes cleanly (`51.408 MB` traced peak).
- **Timeout Isolation**: When an agent exceeds `150.0 ms`, `AgentContext.fork_for_agent` cancels the stalled child at `272.039 ms` (returned `"timeout"` cleanly) without cancelling healthy peers or leaking orphan threads.
- **Bounded Retry Recovery**: Recoverable transient read-only errors execute at most 1 retry with exponential backoff (`2` total attempts, completing in `440.473 ms`), while security denials, validation rejections, and SQL sandbox paths never retry.

