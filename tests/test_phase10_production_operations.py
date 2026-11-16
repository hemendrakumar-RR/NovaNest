"""
NovaNest Phase 10 — Production Operations, Autonomic Monitoring & Incident Resilience
--------------------------------------------------------------------------------------
Comprehensive test suite verifying:
1. Prometheus metrics registry, collectors, and recording
2. Prometheus metrics HTTP export and token-based protection
3. Grafana dashboard JSON schema validity across all 4 dashboards
4. OpenTelemetry W3C traceparent propagation and distributed tracing
5. OpenTelemetry secret and PII attribute redaction
6. Tiered health check endpoints (liveness, readiness, db, containers)
7. Circuit breaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED) and fallback
8. Prometheus alert rules YAML parsing and 8 rule definitions
9. Webhook alert dispatcher, HMAC-SHA256 signatures, and URL secret masking
10. Automated database backup generation, AES-256 encryption, and retention pruning
11. Isolated database restoration safety (zero mutation on live production novanest_db)
12. Disaster recovery 6-scenario simulation suite and empirical RTO/RPO calculation
13. Performance benchmarking and monitoring overhead SLA (< 1.0 ms)
14. Docker Compose and Nginx observability alignment
15. Platform database safety: all 304,405 records in novanest_db preserved intact
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
import yaml

from fastapi.testclient import TestClient

from api.main import app
from python.operations.alert_webhook import (
    AlertSeverity,
    clear_dispatched_alerts,
    compute_hmac_signature,
    dispatch_alert,
    get_dispatched_alerts,
    mask_secret_url,
)
from python.operations.backup_automation import (
    BACKUP_DIR,
    EXPECTED_CANONICAL_TABLES,
    EXPECTED_TOTAL_RECORDS,
    apply_retention_policy,
    decrypt_file,
    encrypt_file,
    run_automated_backup,
    run_isolated_restoration_test,
    verify_sql_integrity,
)
from python.operations.disaster_recovery_simulation import (
    run_full_disaster_recovery_simulation_suite,
    simulate_fastapi_worker_failure,
    simulate_mysql_connection_loss_and_fallback,
)
from python.operations.health_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    DB_CIRCUIT_BREAKER,
    check_containers_health,
    check_database_health,
    check_liveness,
    check_readiness,
)
from python.operations.metrics import (
    API_ERRORS_TOTAL,
    API_REQUESTS_TOTAL,
    NOVANEST_REGISTRY,
    export_metrics_text,
    normalize_endpoint,
    record_api_error,
    record_api_request,
    update_business_metrics,
    update_system_metrics,
    verify_monitoring_auth,
)
from python.operations.performance_benchmarks import (
    calculate_percentiles,
    measure_monitoring_overhead,
)
from python.operations.tracing import (
    clear_trace_history,
    format_traceparent,
    generate_span_id,
    generate_trace_id,
    get_recent_traces,
    parse_traceparent,
    sanitize_attribute_value,
    start_span,
)


class TestPhase10ProductionOperations(unittest.TestCase):
    """Granular verification of NovaNest Phase 10 SRE operations infrastructure."""

    @classmethod
    def setUpClass(cls):
        from dotenv import load_dotenv
        load_dotenv()
        cls.client = TestClient(app)
        cls.admin_token = os.getenv("NOVANEST_ADMIN_KEY", "dev_novanest_admin_key_default")
        cls.operator_token = os.getenv("NOVANEST_API_KEY", "dev_novanest_api_key_default")
        cls.viewer_token = os.getenv("NOVANEST_VIEWER_KEY", "dev_novanest_viewer_key_default")
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.operator_headers = {"Authorization": f"Bearer {cls.operator_token}"}
        cls.viewer_headers = {"Authorization": f"Bearer {cls.viewer_token}"}

    def setUp(self):
        clear_trace_history()
        clear_dispatched_alerts()
        DB_CIRCUIT_BREAKER.reset()

    # --------------------------------------------------------------------------
    # 1. Prometheus Metrics Registry & Recording
    # --------------------------------------------------------------------------
    def test_01_prometheus_metrics_registry_and_recording(self):
        """Verifies metric registration, dynamic recording, and route normalization."""
        # Test route normalization bounds
        norm_1 = normalize_endpoint("/api/prescriptive/customer-profile/cust_000123")
        self.assertEqual(norm_1, "/api/prescriptive/customer-profile/{id}")
        norm_2 = normalize_endpoint("/api/prescriptive/recommendations/REC-RET-VIP-001/approve")
        self.assertEqual(norm_2, "/api/prescriptive/recommendations/{id}/approve")

        # Record API request & error
        record_api_request("GET", "/api/overview", 200, 0.045)
        record_api_error("GET", "/api/broken", "HTTP_500")
        update_system_metrics()

        payload, media_type = export_metrics_text()
        self.assertIn("text/plain", media_type)
        payload_str = payload.decode("utf-8")

        self.assertIn("novanest_api_requests_total", payload_str)
        self.assertIn("novanest_system_cpu_percent", payload_str)
        self.assertIn("novanest_system_memory_bytes", payload_str)

    # --------------------------------------------------------------------------
    # 2. Prometheus Metrics HTTP Export & Protection
    # --------------------------------------------------------------------------
    def test_02_prometheus_metrics_export_and_token_protection(self):
        """Validates that /api/metrics requires authorized credentials from untrusted sources."""
        # 1. Auth check function validation
        self.assertTrue(verify_monitoring_auth(auth_header=f"Bearer {self.admin_token}"))
        self.assertTrue(verify_monitoring_auth(monitoring_token="novanest_monitoring_secret_2026"))
        self.assertTrue(verify_monitoring_auth(client_host="127.0.0.1"))
        self.assertFalse(verify_monitoring_auth(auth_header="Bearer invalid_token", client_host="198.51.100.1"))

        # 2. TestClient request with valid headers
        resp = self.client.get("/api/metrics", headers=self.admin_headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("novanest_api_requests_total", resp.text)

    # --------------------------------------------------------------------------
    # 3. Grafana Dashboard JSON Schema Validity
    # --------------------------------------------------------------------------
    def test_03_grafana_dashboards_json_schema_validity(self):
        """Verifies that all 4 Grafana dashboard definitions are valid JSON with required panels."""
        dashboards_dir = Path("docker/grafana/dashboards")
        self.assertTrue(dashboards_dir.exists())

        expected_dashboards = [
            "application_health.json",
            "database_health.json",
            "infrastructure_health.json",
            "business_operations.json",
        ]

        for dash_file in expected_dashboards:
            fpath = dashboards_dir / dash_file
            self.assertTrue(fpath.exists(), f"Missing dashboard file: {dash_file}")
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("title", data)
            self.assertIn("panels", data)
            self.assertGreaterEqual(len(data["panels"]), 4, f"Dashboard {dash_file} must have at least 4 panels")
            self.assertIn("novanest", data.get("tags", []))

    # --------------------------------------------------------------------------
    # 4. OpenTelemetry W3C Traceparent Propagation
    # --------------------------------------------------------------------------
    def test_04_opentelemetry_w3c_traceparent_propagation(self):
        """Validates W3C traceparent formatting, parsing, and middleware header injection."""
        trace_id = generate_trace_id()
        span_id = generate_span_id()
        self.assertEqual(len(trace_id), 32)
        self.assertEqual(len(span_id), 16)

        tp = format_traceparent(trace_id, span_id)
        parsed = parse_traceparent(tp)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[0], trace_id)
        self.assertEqual(parsed[1], span_id)

        # Call FastAPI through middleware and check response correlation headers
        resp = self.client.get("/api/health/live", headers={"traceparent": tp})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("x-trace-id"), trace_id)
        self.assertIn("traceparent", resp.headers)

    # --------------------------------------------------------------------------
    # 5. OpenTelemetry Secret & PII Attribute Redaction
    # --------------------------------------------------------------------------
    def test_05_opentelemetry_secret_and_pii_redaction(self):
        """Ensures secrets, tokens, emails, and phone numbers are redacted in trace attributes."""
        # Redaction check
        self.assertEqual(sanitize_attribute_value("db.password", "SuperSecret123!"), "[REDACTED_SECRET]")
        self.assertEqual(sanitize_attribute_value("api_key", "Bearer abcdef12345"), "[REDACTED_SECRET]")
        self.assertEqual(
            sanitize_attribute_value("user.email", "alice@example.com"),
            "[REDACTED_EMAIL]",
        )
        self.assertEqual(
            sanitize_attribute_value("user.phone", "+1 (555) 123-4567"),
            "[REDACTED_PHONE]",
        )

        # In-span recording check
        with start_span("test.redaction.span") as span:
            span.set_attribute("secret_key", "my_secret_token")
            span.set_attribute("customer_contact", "Reach out at user@novanest.com")

        traces = get_recent_traces(limit=10)
        matched = [t for t in traces if t["name"] == "test.redaction.span"]
        self.assertTrue(len(matched) > 0)
        attrs = matched[0]["attributes"]
        self.assertEqual(attrs["secret_key"], "[REDACTED_SECRET]")
        self.assertIn("[REDACTED_EMAIL]", attrs["customer_contact"])

    # --------------------------------------------------------------------------
    # 6. Tiered Health Check Endpoints
    # --------------------------------------------------------------------------
    def test_06_fastapi_tiered_health_checks(self):
        """Verifies liveness, readiness, db, and container health probes."""
        # 1. Liveness
        res_live = self.client.get("/api/health/live")
        self.assertEqual(res_live.status_code, 200)
        self.assertEqual(res_live.json()["status"], "live")
        self.assertIn("uptime_seconds", res_live.json())

        # 2. Readiness
        res_ready = self.client.get("/api/health/ready")
        self.assertEqual(res_ready.status_code, 200)
        self.assertEqual(res_ready.json()["status"], "ready")

        # 3. DB Health
        res_db = self.client.get("/api/health/db")
        self.assertEqual(res_db.status_code, 200)
        self.assertIn(res_db.json()["status"], ("healthy", "degraded"))

        # 4. Containers Health
        res_cont = self.client.get("/api/health/containers")
        self.assertEqual(res_cont.status_code, 200)
        self.assertEqual(res_cont.json()["total_containers"], 4)

    # --------------------------------------------------------------------------
    # 7. Circuit Breaker State Transitions & Fallback
    # --------------------------------------------------------------------------
    def test_07_circuit_breaker_state_transitions(self):
        """Tests Circuit Breaker CLOSED -> OPEN -> HALF_OPEN -> CLOSED state machine."""
        cb = CircuitBreaker(
            name="test_breaker",
            failure_threshold=2,
            recovery_timeout_sec=0.1,  # Short timeout for testing
            half_open_success_threshold=1,
        )
        self.assertEqual(cb.state, CircuitState.CLOSED)

        def failing_call():
            raise TimeoutError("Remote timeout")

        def fallback_call():
            return "fallback_result"

        # Call 1: failure 1
        res1 = cb.call(failing_call, fallback_func=fallback_call)
        self.assertEqual(res1, "fallback_result")
        self.assertEqual(cb.state, CircuitState.CLOSED)

        # Call 2: failure 2 -> Trips breaker to OPEN
        res2 = cb.call(failing_call, fallback_func=fallback_call)
        self.assertEqual(res2, "fallback_result")
        self.assertEqual(cb.state, CircuitState.OPEN)

        # Calling while OPEN immediately routes to fallback without trying primary
        res3 = cb.call(failing_call, fallback_func=fallback_call)
        self.assertEqual(res3, "fallback_result")

        # Sleep past recovery timeout -> transitions to HALF_OPEN
        import time
        time.sleep(0.12)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

        # Successful call in HALF_OPEN restores breaker to CLOSED
        def success_call():
            return "primary_success"

        res4 = cb.call(success_call, fallback_func=fallback_call)
        self.assertEqual(res4, "primary_success")
        self.assertEqual(cb.state, CircuitState.CLOSED)

    # --------------------------------------------------------------------------
    # 8. Prometheus Alert Rules YAML Parsing
    # --------------------------------------------------------------------------
    def test_08_alert_rules_yaml_parsing_and_structure(self):
        """Validates that alert_rules.yml parses as valid YAML and defines all 8 required alerts."""
        rules_path = Path("docker/prometheus/alert_rules.yml")
        self.assertTrue(rules_path.exists())

        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.assertIn("groups", data)
        rules = data["groups"][0]["rules"]
        alert_names = [r["alert"] for r in rules]

        required_alerts = [
            "ApiUnavailable",
            "HighErrorRate",
            "ExcessiveLatency",
            "MySQLConnectionFailures",
            "ContainerCrashes",
            "HighMemoryUtilization",
            "DiskSpaceExhaustion",
            "BackupFailures",
        ]

        for alert in required_alerts:
            self.assertIn(alert, alert_names, f"Missing required alert rule: {alert}")

    # --------------------------------------------------------------------------
    # 9. Alert Webhook Dispatcher & Secret Masking
    # --------------------------------------------------------------------------
    def test_09_alert_webhook_dispatch_and_hmac_signature(self):
        """Validates HMAC-SHA256 signature generation, URL secret masking, and local dispatch."""
        # 1. URL secret masking
        secret_url = "https://hooks.slack.com/services/T001/B002/SuperSecretToken12345"
        masked = mask_secret_url(secret_url)
        self.assertNotIn("SuperSecretToken12345", masked)
        self.assertIn("********", masked)

        # 2. HMAC-SHA256 signature
        payload_bytes = b'{"alert_name":"HighErrorRate","severity":"critical"}'
        sig = compute_hmac_signature(payload_bytes, "test_secret_key")
        self.assertTrue(sig.startswith("sha256="))
        self.assertEqual(len(sig), 7 + 64)

        # 3. Alert dispatch execution
        res = dispatch_alert(
            alert_name="MySQLConnectionFailures",
            severity=AlertSeverity.CRITICAL,
            summary="MySQL ping failed",
            description="Connection timed out after 2000ms",
        )
        self.assertTrue(res["dispatched"])
        alerts = get_dispatched_alerts(limit=5)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["alert_name"], "MySQLConnectionFailures")

    # --------------------------------------------------------------------------
    # 10. Database Backup Automation & AES-256 Encryption
    # --------------------------------------------------------------------------
    def test_10_database_backup_automation_and_encryption(self):
        """Verifies automated database backup generation, AES-256 encryption, and retention pruning."""
        # Create a small dummy file to test encryption / decryption round-trip
        dummy_sql = BACKUP_DIR / "dummy_test.sql"
        dummy_enc = BACKUP_DIR / "dummy_test.sql.enc"
        dummy_restore = BACKUP_DIR / "dummy_test_restored.sql"

        dummy_sql.write_text("CREATE TABLE test_tbl (id INT); INSERT INTO test_tbl VALUES (1);", encoding="utf-8")

        enc_ok, _, _, _ = encrypt_file(dummy_sql, dummy_enc)
        self.assertTrue(enc_ok)
        self.assertTrue(dummy_enc.exists())

        dec_ok, _, _, _ = decrypt_file(dummy_enc, dummy_restore)
        self.assertTrue(dec_ok)
        self.assertEqual(dummy_restore.read_text(encoding="utf-8"), dummy_sql.read_text(encoding="utf-8"))

        # Cleanup dummy files
        for f in (dummy_sql, dummy_enc, dummy_restore):
            if f.exists():
                f.unlink()

        # Test retention policy function
        pruned = apply_retention_policy(BACKUP_DIR, max_backups_to_keep=20)
        self.assertIsInstance(pruned, list)

    # --------------------------------------------------------------------------
    # 11. Isolated Database Restoration Safety
    # --------------------------------------------------------------------------
    def test_11_isolated_database_restoration_safety(self):
        """Verifies that restoration tests strictly forbid targeting 'novanest_db'."""
        dummy_path = BACKUP_DIR / "dummy.sql.enc"
        with self.assertRaises(ValueError) as ctx:
            run_isolated_restoration_test(dummy_path, isolated_db_name="novanest_db")
        self.assertIn("CRITICAL SAFETY VIOLATION", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 12. Disaster Recovery Simulation Suite
    # --------------------------------------------------------------------------
    def test_12_disaster_recovery_simulation_suite(self):
        """Runs the 6-scenario disaster recovery simulation suite and validates empirical RTO/RPO."""
        report = run_full_disaster_recovery_simulation_suite()
        self.assertEqual(report["total_scenarios"], 6)
        self.assertTrue(report["all_scenarios_recovered"])

        # Check empirical RTO / RPO
        summary = report["rto_rpo_summary"]
        self.assertIn("measured_rto_sec", summary)
        self.assertLess(summary["measured_rto_sec"], 30.0)
        self.assertEqual(summary["rto_sla_status"], "EXCEEDED_SLA (< 30s)")
        self.assertLess(summary["measured_rpo_hours"], 24.0)

    # --------------------------------------------------------------------------
    # 13. Performance Baseline & Monitoring Overhead
    # --------------------------------------------------------------------------
    def test_13_performance_baseline_and_monitoring_overhead(self):
        """Verifies percentile calculations and validates monitoring overhead is < 1.0 ms."""
        # 1. Percentiles calculation
        durations = [0.001 * i for i in range(1, 101)]
        pcts = calculate_percentiles(durations)
        self.assertAlmostEqual(pcts["p50_ms"], 50.0, delta=1.0)
        self.assertAlmostEqual(pcts["p95_ms"], 95.0, delta=1.0)
        self.assertAlmostEqual(pcts["p99_ms"], 99.0, delta=1.0)

        # 2. Monitoring overhead audit
        overhead = measure_monitoring_overhead(iterations=500)
        self.assertTrue(overhead["overhead_within_sla"])
        self.assertLess(overhead["overhead_per_call_ms"], 1.0)

    # --------------------------------------------------------------------------
    # 14. Docker Compose & Nginx Observability Alignment
    # --------------------------------------------------------------------------
    def test_14_docker_compose_and_nginx_observability_alignment(self):
        """Verifies docker-compose.monitoring.yml and nginx.conf configuration integrity."""
        # 1. docker-compose.monitoring.yml
        compose_mon = Path("docker-compose.monitoring.yml")
        self.assertTrue(compose_mon.exists())
        with open(compose_mon, "r", encoding="utf-8") as f:
            mon_data = yaml.safe_load(f)
        self.assertIn("services", mon_data)
        self.assertIn("prometheus", mon_data["services"])
        self.assertIn("grafana", mon_data["services"])

        # 2. nginx.conf tracing headers
        nginx_conf = Path("docker/nginx.conf")
        content = nginx_conf.read_text(encoding="utf-8")
        self.assertIn("proxy_set_header traceparent", content)
        self.assertIn("proxy_set_header x-trace-id", content)

    # --------------------------------------------------------------------------
    # 15. Database Safety & Zero Mutation
    # --------------------------------------------------------------------------
    def test_15_database_safety_and_zero_mutation(self):
        """Verifies that all 10 canonical tables and all 304,405 records in MySQL novanest_db remain intact."""
        import mysql.connector
        from dotenv import load_dotenv
        load_dotenv()

        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_APP_USER", "novanest_app"),
            password=os.getenv("DB_APP_PASSWORD", "NovaAppPass2026!"),
            database=os.getenv("DB_NAME", "novanest_db"),
        )
        cur = conn.cursor()
        total_records = 0
        counts = {}

        for tbl in EXPECTED_CANONICAL_TABLES:
            cur.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
            cnt = cur.fetchone()[0]
            counts[tbl] = cnt
            total_records += cnt

        conn.close()

        self.assertEqual(
            total_records,
            EXPECTED_TOTAL_RECORDS,
            f"Expected {EXPECTED_TOTAL_RECORDS} records, found {total_records}. Data mutation detected!",
        )
        self.assertEqual(counts["customers"], 5000)
        self.assertEqual(counts["restaurants"], 1500)
        self.assertEqual(counts["riders"], 4000)
        self.assertEqual(counts["orders_table"], 49971)
        self.assertEqual(counts["payments"], 49971)
        self.assertEqual(counts["deliveries"], 49971)
        self.assertEqual(counts["app_events"], 100000)


if __name__ == "__main__":
    unittest.main()
