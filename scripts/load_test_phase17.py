"""
NovaNest Platform — Phase 17 Concurrency, Load & Stress Testing Harness
========================================================================
Simulates concurrent multi-user traffic against core NovaNest endpoints:
- Executive Overview KPI API
- Customer Intelligence API
- Financial Intelligence API
- Server-Side Orders Pagination (/api/records/orders)
- Server-Side Filtered Customers Pagination (/api/records/customers)
- AI Copilot Decision Queries (/api/copilot/query)

Measures:
- RPS (Requests per second)
- Latency percentiles: p50, p90, p95, p99, min, max, mean
- Error rates and HTTP status distributions
- Stability under 10, 25, and 50 concurrent workers
"""

import concurrent.futures
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import requests

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8001")
AUTH_HEADER = {"Authorization": "Bearer test-operator-key-phase06-8"}

ENDPOINTS = [
    ("GET", "/api/overview", None),
    ("GET", "/api/customer/overview", None),
    ("GET", "/api/financial/overview", None),
    ("GET", "/api/records/orders?page=1&page_size=25", None),
    ("GET", "/api/records/customers?page=1&page_size=20&city=Bangalore", None),
    ("GET", "/api/performance/cache/stats", None),
    ("POST", "/api/copilot/query", {"query": "What is the current GMV and revenue?"}),
]


def send_single_request(item: Tuple[str, str, Any]) -> Tuple[bool, int, float, str]:
    method, path, payload = item
    url = f"{API_BASE}{path}"
    t0 = time.perf_counter()
    try:
        if method == "GET":
            resp = requests.get(url, headers=AUTH_HEADER, timeout=15.0)
        else:
            resp = requests.post(url, json=payload, headers=AUTH_HEADER, timeout=15.0)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        success = (resp.status_code == 200)
        return success, resp.status_code, elapsed_ms, path
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return False, 599, elapsed_ms, path


def run_concurrency_tier(concurrency: int, total_requests: int) -> Dict[str, Any]:
    print(f"\n---> Running Tier: {concurrency} Concurrent Users | {total_requests} Requests")
    request_queue = [ENDPOINTS[i % len(ENDPOINTS)] for i in range(total_requests)]
    
    start_time = time.perf_counter()
    latencies: List[float] = []
    status_codes: Dict[int, int] = {}
    success_count = 0
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_single_request, item) for item in request_queue]
        for fut in concurrent.futures.as_completed(futures):
            success, code, elapsed, path = fut.result()
            latencies.append(elapsed)
            status_codes[code] = status_codes.get(code, 0) + 1
            if success:
                success_count += 1
            else:
                error_count += 1

    total_wall_time = time.perf_counter() - start_time
    rps = round(total_requests / total_wall_time, 2) if total_wall_time > 0 else 0.0

    latencies.sort()
    p50 = round(float(np.percentile(latencies, 50)), 2)
    p90 = round(float(np.percentile(latencies, 90)), 2)
    p95 = round(float(np.percentile(latencies, 95)), 2)
    p99 = round(float(np.percentile(latencies, 99)), 2)
    min_lat = round(min(latencies), 2)
    max_lat = round(max(latencies), 2)
    mean_lat = round(float(np.mean(latencies)), 2)
    error_rate = round((error_count / total_requests) * 100, 2)

    result = {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "wall_time_sec": round(total_wall_time, 2),
        "rps": rps,
        "success_count": success_count,
        "error_count": error_count,
        "error_rate_pct": error_rate,
        "status_distribution": status_codes,
        "latencies_ms": {
            "min": min_lat,
            "mean": mean_lat,
            "p50": p50,
            "p90": p90,
            "p95": p95,
            "p99": p99,
            "max": max_lat,
        },
    }

    print(f"Results: {rps} RPS | p50: {p50}ms | p95: {p95}ms | p99: {p99}ms | Errors: {error_rate}% ({error_count}/{total_requests})")
    return result


def main():
    print("=" * 70)
    print("NOVANEST PHASE 17 — LOAD & CONCURRENCY BENCHMARK")
    print("=" * 70)

    # Warmup
    print("Warming up cache and connections...")
    for item in ENDPOINTS:
        send_single_request(item)
    time.sleep(1.0)

    tiers = [
        (10, 100),   # 10 users, 100 requests
        (25, 200),   # 25 users, 200 requests
        (50, 300),   # 50 users, 300 requests
    ]

    all_results = {}
    for conc, reqs in tiers:
        res = run_concurrency_tier(conc, reqs)
        all_results[f"tier_{conc}_users"] = res
        time.sleep(1.0)

    # Save benchmark results
    out_path = os.path.join("NEWCHAGES", "PHASE17", "load_test_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Load testing complete. Results persisted to {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
