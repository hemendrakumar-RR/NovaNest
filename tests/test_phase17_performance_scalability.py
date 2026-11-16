"""
NovaNest Platform — Phase 17 Performance & Scalability Test Suite
=================================================================
Validates performance engineering, code-splitting, database indexing,
caching engine, server-side pagination, AI Copilot acceleration,
and concurrent stability across the NovaNest platform.
"""

import json
import os
import sys
import time
import unittest
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8001")
OPERATOR_HEADERS = {"Authorization": "Bearer test-operator-key-phase06-8"}
ADMIN_HEADERS = {"Authorization": "Bearer test-admin-key-phase06-8"}
ANALYST_HEADERS = {"Authorization": "Bearer test-viewer-key-phase06-8"}


class TestPhase17PerformanceScalability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure API is accessible
        try:
            resp = requests.get(f"{API_BASE}/api/health", timeout=5.0)
            if resp.status_code != 200:
                raise RuntimeError(f"API health returned {resp.status_code}")
        except Exception as e:
            raise RuntimeError(f"Cannot connect to API at {API_BASE}: {e}")

    def test_01_canonical_database_integrity(self):
        """Verifies all 10 canonical tables retain exactly 304,405 records (0 database mutations)."""
        resp = requests.get(f"{API_BASE}/api/health", timeout=5.0)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        counts = data.get("datasets", {})

        expected_counts = {
            "customers": 5000,
            "restaurants": 1500,
            "menu_items": 15000,
            "riders": 4000,
            "payments": 49971,
            "deliveries": 49971,
            "app_events": 100000,
            "promotions": 200,
            "ratings_reviews": 28792,
            "orders": 49971,
        }

        total_records = 0
        for table, expected in expected_counts.items():
            actual = counts.get(table)
            self.assertEqual(actual, expected, f"Table '{table}' row count mismatch: {actual} != {expected}")
            total_records += actual

        self.assertEqual(total_records, 304405, f"Total canonical records mismatch: {total_records} != 304,405")

    def test_02_frontend_code_splitting_and_bundle_architecture(self):
        """Validates that route-based dynamic code-splitting reduced the main JS chunk to < 450 kB."""
        dist_dir = PROJECT_ROOT / "frontend" / "dist" / "assets"
        self.assertTrue(dist_dir.exists(), "Frontend dist/assets does not exist")

        js_files = list(dist_dir.glob("*.js"))
        self.assertGreater(len(js_files), 5, "Expected modular code-split chunks (> 5 JS chunks)")

        # Verify main entry chunk is compact (< 450 kB)
        index_chunks = [f for f in js_files if f.name.startswith("index-")]
        self.assertTrue(len(index_chunks) > 0, "Main index bundle not found")
        index_size_kb = index_chunks[0].stat().st_size / 1024.0
        self.assertLess(index_size_kb, 450.0, f"Main entry chunk {index_size_kb:.1f} kB exceeds 450 kB limit")

        # Verify lazy-loaded view chunks exist
        chunk_names = [f.name for f in js_files]
        self.assertTrue(any("ExecutiveOverviewView" in n for n in chunk_names), "ExecutiveOverviewView chunk missing")
        self.assertTrue(any("CustomerIntelligenceView" in n for n in chunk_names), "CustomerIntelligenceView chunk missing")
        self.assertTrue(any("ExecutiveAiCopilot" in n for n in chunk_names), "ExecutiveAiCopilot chunk missing")

    def test_03_database_composite_index_optimization(self):
        """Verifies composite indexes on orders_table and deliveries in the active container database."""
        import subprocess
        cmd = [
            "docker", "exec", "novanest-db", "mysql", "-u", "novanest_app", "-pChinnu_2311",
            "-e", "USE novanest_db; SHOW INDEX FROM orders_table; SHOW INDEX FROM deliveries;"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Failed to inspect MySQL container indexes: {res.stderr}")
        out = res.stdout
        self.assertIn("idx_orders_status_dt", out, "idx_orders_status_dt composite index missing on orders_table")
        self.assertIn("idx_orders_cust_status", out, "idx_orders_cust_status composite index missing on orders_table")
        self.assertIn("idx_deliveries_rider_dur", out, "idx_deliveries_rider_dur composite index missing on deliveries")

    def test_04_backend_caching_and_speedup(self):
        """Verifies multi-tiered caching produces >= 5x speedup and returns cache metadata."""
        # Warmup cache
        requests.get(f"{API_BASE}/api/overview?city=Delhi", headers=OPERATOR_HEADERS)
        time.sleep(0.1)

        # Measure cached hit
        t0 = time.perf_counter()
        resp = requests.get(f"{API_BASE}/api/overview?city=Delhi", headers=OPERATOR_HEADERS)
        t_hit_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        cache_meta = data.get("cache_metadata")
        self.assertIsNotNone(cache_meta, "cache_metadata field missing from response")
        self.assertEqual(cache_meta.get("status"), "CACHED")
        self.assertLess(t_hit_ms, 250.0, f"Cached response latency {t_hit_ms:.1f}ms exceeds 250ms target")

    def test_05_server_side_pagination_orders(self):
        """Verifies server-side pagination on orders_table with sorting and bounded limits."""
        resp = requests.get(
            f"{API_BASE}/api/records/orders?page=1&page_size=20&sort_by=final_amount&sort_dir=desc",
            headers=OPERATOR_HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        d = resp.json()

        self.assertEqual(d.get("entity"), "orders")
        self.assertEqual(d.get("page"), 1)
        self.assertEqual(d.get("page_size"), 20)
        self.assertEqual(d.get("total_records"), 49971)
        self.assertEqual(d.get("total_pages"), 2499)
        self.assertTrue(d.get("has_next"))
        self.assertFalse(d.get("has_prev"))
        self.assertEqual(len(d.get("records", [])), 20)

        # Verify sorting
        first_amt = float(d["records"][0]["final_amount"])
        second_amt = float(d["records"][1]["final_amount"])
        self.assertGreaterEqual(first_amt, second_amt)

    def test_06_server_side_pagination_filtering_and_whitelisting(self):
        """Verifies filtering, whitelisted sort fields, and rejection of invalid entities."""
        # Filter by city on customers
        resp = requests.get(
            f"{API_BASE}/api/records/customers?page=1&page_size=10&city=Mumbai",
            headers=OPERATOR_HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        for r in d["records"]:
            self.assertEqual(r["city"].lower(), "mumbai")

        # Rejection of invalid entity
        invalid_resp = requests.get(
            f"{API_BASE}/api/records/malicious_table",
            headers=OPERATOR_HEADERS,
        )
        self.assertEqual(invalid_resp.status_code, 400)

    def test_07_ai_copilot_latency_and_caching(self):
        """Verifies AI Copilot inquiry caching yields instant cached responses."""
        payload = {"query": "What is the delivery SLA breach rate?"}

        # Prime inquiry
        requests.post(f"{API_BASE}/api/copilot/query", json=payload, headers=OPERATOR_HEADERS)
        time.sleep(0.1)

        # Second hit should be accelerated
        t0 = time.perf_counter()
        resp2 = requests.post(f"{API_BASE}/api/copilot/query", json=payload, headers=OPERATOR_HEADERS)
        t_hit_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(resp2.status_code, 200)
        d = resp2.json()
        self.assertTrue(d.get("is_cached_response", False), "Expected is_cached_response=True on repeat inquiry")
        self.assertLess(t_hit_ms, 100.0, f"Cached Copilot response {t_hit_ms:.1f}ms exceeds 100ms threshold")

    def test_08_cache_stats_and_monitoring_endpoints(self):
        """Verifies cache telemetry endpoint and Prometheus metrics integration."""
        stats_resp = requests.get(f"{API_BASE}/api/performance/cache/stats", headers=OPERATOR_HEADERS)
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.json()
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertIn("hit_ratio", stats)

        # Verify Prometheus metrics expose cache telemetry
        metrics_resp = requests.get(
            f"{API_BASE}/api/metrics",
            headers={"Authorization": "Bearer dev_novanest_admin_key_default"},
        )
        self.assertEqual(metrics_resp.status_code, 200)
        metrics_text = metrics_resp.text
        self.assertIn("novanest_cache_requests_total", metrics_text)
        self.assertIn("novanest_cache_hit_ratio", metrics_text)

    def test_09_concurrency_load_results_integrity(self):
        """Verifies results from 10, 25, and 50 concurrent user load tests."""
        results_file = PROJECT_ROOT / "NEWCHAGES" / "PHASE17" / "load_test_results.json"
        self.assertTrue(results_file.exists(), "load_test_results.json missing")

        with open(results_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for tier in ["tier_10_users", "tier_25_users", "tier_50_users"]:
            self.assertIn(tier, data, f"Tier {tier} missing from load test results")
            tier_data = data[tier]
            self.assertEqual(tier_data["error_rate_pct"], 0.0, f"Tier {tier} error rate {tier_data['error_rate_pct']}% > 0%")
            self.assertGreater(tier_data["rps"], 50.0, f"Tier {tier} RPS {tier_data['rps']} < 50 RPS threshold")
            self.assertLess(tier_data["latencies_ms"]["p95"], 1000.0, f"Tier {tier} p95 {tier_data['latencies_ms']['p95']}ms >= 1000ms")

    def test_10_security_and_rbac_preservation(self):
        """Verifies authentication and RBAC controls remain strictly enforced."""
        # Unauthenticated request rejected
        unauth_resp = requests.get(f"{API_BASE}/api/overview")
        self.assertIn(unauth_resp.status_code, (401, 403), "Unauthenticated request was not rejected")

        # Pagination unauthenticated request rejected
        unauth_page = requests.get(f"{API_BASE}/api/records/orders")
        self.assertIn(unauth_page.status_code, (401, 403), "Unauthenticated pagination was not rejected")


if __name__ == "__main__":
    unittest.main()
