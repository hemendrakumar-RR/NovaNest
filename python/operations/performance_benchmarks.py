"""
NovaNest Platform — Performance & Reliability Benchmarking Engine
-----------------------------------------------------------------
Establishes empirical baseline measurements for API latency percentiles (p50, p90, p95, p99),
concurrent load throughput, AI domain agent execution times, database query durations,
and Prometheus metrics collection overhead (< 1.0 ms).
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import math
import os
import statistics
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

import psutil

from python.operations.metrics import record_api_request, record_db_query


def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
    """Calculates p50, p90, p95, and p99 percentiles from a list of durations."""
    if not latencies:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}

    s = sorted(latencies)
    n = len(s)

    def pct(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return s[int(k)]
        d0 = s[int(f)] * (c - k)
        d1 = s[int(c)] * (k - f)
        return d0 + d1

    return {
        "p50_ms": round(pct(50) * 1000.0, 3),
        "p90_ms": round(pct(90) * 1000.0, 3),
        "p95_ms": round(pct(95) * 1000.0, 3),
        "p99_ms": round(pct(99) * 1000.0, 3),
        "mean_ms": round(statistics.mean(latencies) * 1000.0, 3),
        "min_ms": round(min(latencies) * 1000.0, 3),
        "max_ms": round(max(latencies) * 1000.0, 3),
    }


def measure_endpoint_latency(
    url: str = "http://127.0.0.1:8000/api/health",
    iterations: int = 50,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Measures sequential request latency percentiles for a given endpoint.
    """
    latencies: List[float] = []
    success_count = 0
    req_headers = headers or {"User-Agent": "NovaNest-Benchmark/1.0"}

    for _ in range(iterations):
        req = urllib.request.Request(url, headers=req_headers)
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                dur = time.perf_counter() - t0
                if resp.status == 200:
                    latencies.append(dur)
                    success_count += 1
        except Exception:
            dur = time.perf_counter() - t0
            latencies.append(dur)

    stats = calculate_percentiles(latencies)
    stats["total_samples"] = iterations
    stats["success_rate_pct"] = round((success_count / iterations) * 100.0, 1)
    return stats


def measure_concurrent_load(
    url: str = "http://127.0.0.1:8000/api/health",
    concurrencies: Optional[List[int]] = None,
    requests_per_concurrency: int = 50,
) -> Dict[int, Dict[str, Any]]:
    """
    Executes controlled concurrent load tests at varying concurrency tiers (e.g. 10, 25, 50).
    """
    concurrencies = concurrencies or [10, 25, 50]
    results: Dict[int, Dict[str, Any]] = {}

    for c in concurrencies:
        latencies: List[float] = []
        successes = 0

        def worker() -> float:
            nonlocal successes
            req = urllib.request.Request(url, headers={"User-Agent": "NovaNest-LoadTest/1.0"})
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    dur = time.perf_counter() - t0
                    if resp.status == 200:
                        successes += 1
                    return dur
            except Exception:
                return time.perf_counter() - t0

        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=c) as executor:
            futures = [executor.submit(worker) for _ in range(requests_per_concurrency)]
            for f in concurrent.futures.as_completed(futures):
                latencies.append(f.result())

        total_wall_sec = time.perf_counter() - t_start
        throughput_rps = requests_per_concurrency / max(0.001, total_wall_sec)

        pcts = calculate_percentiles(latencies)
        results[c] = {
            "concurrency_level": c,
            "total_requests": requests_per_concurrency,
            "wall_duration_sec": round(total_wall_sec, 3),
            "throughput_rps": round(throughput_rps, 1),
            "success_rate_pct": round((successes / requests_per_concurrency) * 100.0, 1),
            "mean_ms": pcts["mean_ms"],
            "p95_ms": pcts["p95_ms"],
            "p99_ms": pcts["p99_ms"],
        }

    return results


def measure_database_query_performance() -> Dict[str, Any]:
    """
    Measures execution latencies for core analytical queries against MySQL novanest_db.
    """
    import mysql.connector
    from dotenv import load_dotenv
    load_dotenv()

    queries = {
        "simple_ping": "SELECT 1;",
        "order_count": "SELECT COUNT(*) FROM orders_table;",
        "revenue_sum": "SELECT SUM(total_amount), AVG(total_amount) FROM orders_table;",
        "customer_segmentation": "SELECT customer_id, COUNT(*) FROM orders_table GROUP BY customer_id LIMIT 100;",
        "active_riders": "SELECT COUNT(*) FROM riders WHERE is_active = 1;",
    }

    results = {}
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_APP_USER", "novanest_app"),
            password=os.getenv("DB_APP_PASSWORD", "NovaAppPass2026!"),
            database=os.getenv("DB_NAME", "novanest_db"),
        )
        cur = conn.cursor()

        for q_name, sql in queries.items():
            t0 = time.perf_counter()
            cur.execute(sql)
            cur.fetchall()
            dur_ms = (time.perf_counter() - t0) * 1000.0
            results[q_name] = round(dur_ms, 3)
            record_db_query(query_type=q_name, duration_sec=dur_ms / 1000.0)

        conn.close()
    except Exception as exc:
        results["error"] = str(exc)

    return results


def measure_monitoring_overhead(iterations: int = 1000) -> Dict[str, Any]:
    """
    Measures the exact CPU/latency overhead introduced by Prometheus metrics instrumentation.
    Validates that recording overhead is < 1.0 ms (target: < 0.05 ms per invocation).
    """
    # 1. Baseline without metrics recording
    t0 = time.perf_counter()
    for i in range(iterations):
        _ = i * 2 + 1
    baseline_sec = time.perf_counter() - t0

    # 2. Loop with metrics recording
    t1 = time.perf_counter()
    for i in range(iterations):
        _ = i * 2 + 1
        record_api_request("GET", "/api/health", 200, 0.005)
    metrics_sec = time.perf_counter() - t1

    delta_sec = max(0.0, metrics_sec - baseline_sec)
    overhead_per_call_us = (delta_sec / iterations) * 1_000_000.0
    overhead_per_call_ms = overhead_per_call_us / 1000.0

    return {
        "iterations": iterations,
        "baseline_total_sec": round(baseline_sec, 5),
        "instrumented_total_sec": round(metrics_sec, 5),
        "overhead_per_call_us": round(overhead_per_call_us, 2),
        "overhead_per_call_ms": round(overhead_per_call_ms, 4),
        "target_max_overhead_ms": 1.0,
        "overhead_within_sla": overhead_per_call_ms < 1.0,
    }


def run_full_performance_baseline_suite() -> Dict[str, Any]:
    """
    Runs the complete operational performance baseline and reliability sweep.
    """
    start_ts = time.perf_counter()
    proc = psutil.Process()
    mem_info = proc.memory_info()

    api_latency = measure_endpoint_latency(url="http://127.0.0.1:8000/api/health", iterations=30)
    concurrent_load = measure_concurrent_load(url="http://127.0.0.1:8000/api/health", concurrencies=[10, 25, 50])
    db_queries = measure_database_query_performance()
    monitoring_overhead = measure_monitoring_overhead(iterations=1000)

    total_duration = time.perf_counter() - start_ts

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_benchmark_duration_sec": round(total_duration, 3),
        "system_resources": {
            "process_memory_rss_mb": round(mem_info.rss / (1024 * 1024), 2),
            "cpu_percent": psutil.cpu_percent(interval=None),
        },
        "api_latency_baselines": api_latency,
        "concurrency_throughput": concurrent_load,
        "database_query_latencies": db_queries,
        "monitoring_overhead_audit": monitoring_overhead,
    }
