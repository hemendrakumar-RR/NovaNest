"""
Live HTTP Latency and Throughput Benchmark Suite for NovaNest Phase 11.
Measures latency percentiles (p50, p95, p99), RPS throughput, and error rates
over TCP connections through the Nginx reverse proxy (port 80) and direct container (port 8001).
"""

import os
import time
import statistics
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("NOVANEST_VIEWER_KEY", "dev_novanest_viewer_key_default")
BASE_URL_NGINX = "http://127.0.0.1:80"
BASE_URL_DIRECT = "http://127.0.0.1:8001"

def benchmark_endpoint(url: str, headers: dict = None, total_requests: int = 100, concurrency: int = 5):
    headers = headers or {}
    latencies = []
    status_codes = []
    
    def single_req():
        req = urllib.request.Request(url, headers=headers)
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                latency = (time.perf_counter() - t0) * 1000.0
                return latency, resp.status
        except urllib.error.HTTPError as e:
            latency = (time.perf_counter() - t0) * 1000.0
            return latency, e.code
        except Exception:
            latency = (time.perf_counter() - t0) * 1000.0
            return latency, 500

    start_wall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(lambda _: single_req(), range(total_requests)))
    total_time = time.perf_counter() - start_wall

    latencies = [r[0] for r in results]
    status_codes = [r[1] for r in results]
    latencies.sort()

    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    mean_lat = statistics.mean(latencies)
    rps = total_requests / total_time if total_time > 0 else 0
    errors = sum(1 for c in status_codes if c >= 400)

    return {
        "url": url,
        "requests": total_requests,
        "concurrency": concurrency,
        "rps": round(rps, 2),
        "mean_ms": round(mean_lat, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "error_count": errors,
        "error_rate_pct": round((errors / total_requests) * 100.0, 2),
    }

def main():
    print("=== RUNNING NOVANEST LIVE HTTP BENCHMARKS ===")
    
    # 1. Direct API Health (Port 8001)
    res_direct_health = benchmark_endpoint(f"{BASE_URL_DIRECT}/api/health", total_requests=100, concurrency=5)
    print(f"Direct API Health (:8001): p50={res_direct_health['p50_ms']}ms, p95={res_direct_health['p95_ms']}ms, p99={res_direct_health['p99_ms']}ms, RPS={res_direct_health['rps']}, Errors={res_direct_health['error_count']}")
    
    # 2. Nginx Proxied Health (Port 80)
    res_nginx_health = benchmark_endpoint(f"{BASE_URL_NGINX}/api/health", total_requests=100, concurrency=5)
    print(f"Nginx Proxied Health (:80): p50={res_nginx_health['p50_ms']}ms, p95={res_nginx_health['p95_ms']}ms, p99={res_nginx_health['p99_ms']}ms, RPS={res_nginx_health['rps']}, Errors={res_nginx_health['error_count']}")
    
    # 3. Nginx Proxied Frontend SPA (Port 80)
    res_nginx_spa = benchmark_endpoint(f"{BASE_URL_NGINX}/", total_requests=50, concurrency=5)
    print(f"Nginx Proxied Frontend SPA (:80): p50={res_nginx_spa['p50_ms']}ms, p95={res_nginx_spa['p95_ms']}ms, p99={res_nginx_spa['p99_ms']}ms, RPS={res_nginx_spa['rps']}, Errors={res_nginx_spa['error_count']}")

    # 4. Nginx Proxied Authenticated Overview (Port 80)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    res_nginx_overview = benchmark_endpoint(f"{BASE_URL_NGINX}/api/overview", headers=headers, total_requests=25, concurrency=2)
    print(f"Nginx Proxied Overview (:80): p50={res_nginx_overview['p50_ms']}ms, p95={res_nginx_overview['p95_ms']}ms, p99={res_nginx_overview['p99_ms']}ms, RPS={res_nginx_overview['rps']}, Errors={res_nginx_overview['error_count']}")

if __name__ == "__main__":
    main()
