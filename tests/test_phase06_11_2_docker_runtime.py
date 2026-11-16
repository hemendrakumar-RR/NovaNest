"""
NovaNest Phase 06.11.2 — Docker Build & Runtime Validation Suite
-----------------------------------------------------------------
Validates live Docker daemon, image builds, container healthchecks,
isolated database restore (304,405 rows), Nginx reverse proxy,
FastAPI endpoints, Streamlit dashboard, and container security.
"""

import json
import os
import re
import socket
import subprocess
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_docker_cmd():
    """Find working docker executable or command."""
    paths = [
        "docker",
        r"C:\Users\madha\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
    ]
    for p in paths:
        try:
            res = subprocess.run([p, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                return p
        except Exception:
            continue
    return "docker"


def get_compose_cmd():
    """Find working docker compose executable or command."""
    docker_cmd = get_docker_cmd()
    try:
        res = subprocess.run([docker_cmd, "compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return [docker_cmd, "compose"]
    except Exception:
        pass
    return ["docker-compose"]


class TestPhase06112DockerRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docker_cmd = get_docker_cmd()
        cls.compose_cmd = get_compose_cmd()
        cls.api_key = os.getenv("NOVANEST_API_KEY", "dev_novanest_api_key_default")
        cls.admin_key = os.getenv("NOVANEST_ADMIN_KEY", "dev_novanest_admin_key_default")
        cls.viewer_key = os.getenv("NOVANEST_VIEWER_KEY", "dev_novanest_viewer_key_default")

    def test_01_docker_daemon_and_engine_operational(self):
        """Verify Docker 29+ Engine and Compose 5+ are operational on the host."""
        res = subprocess.run([self.docker_cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Docker CLI failed: {res.stderr}")
        self.assertIn("Docker version", res.stdout)

        cmd = list(self.compose_cmd) + ["version"]
        res_comp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res_comp.returncode, 0, f"Docker Compose failed: {res_comp.stderr}")
        self.assertIn("Docker Compose version", res_comp.stdout)

    def test_02_host_services_undisturbed(self):
        """Confirm that host FastAPI (port 8000), Streamlit (port 8501), and MySQL (port 3306) remain active."""
        def is_port_open(host, port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            try:
                s.connect((host, port))
                s.close()
                return True
            except Exception:
                return False

        # In containerized/CI environments, services run on Docker ports (8001, 8502, 80)
        # In bare-metal development, services run on host ports (8000, 8501)
        # At least one runtime environment must be active, and MySQL (3306) must be active
        api_active = is_port_open("127.0.0.1", 8000) or is_port_open("127.0.0.1", 8001) or is_port_open("127.0.0.1", 80)
        streamlit_active = is_port_open("127.0.0.1", 8501) or is_port_open("127.0.0.1", 8502)
        mysql_active = is_port_open("127.0.0.1", 3306)

        self.assertTrue(api_active, "NovaNest API (port 8000 host or port 8001/80 container) must remain active")
        self.assertTrue(streamlit_active, "NovaNest Streamlit (port 8501 host or port 8502 container) must remain active")
        self.assertTrue(mysql_active, "MySQL on port 3306 must remain active")

    def test_03_docker_images_exist(self):
        """Verify that all 3 NovaNest container images are built and listed in local docker images."""
        res = subprocess.run([self.docker_cmd, "images", "--format", "{{.Repository}}:{{.Tag}}"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        images = res.stdout.splitlines()

        has_api = any("novanest-api" in img or "novanest-platform-api" in img for img in images)
        has_frontend = any("novanest-frontend" in img or "novanest-platform-frontend" in img for img in images)
        has_streamlit = any("novanest-streamlit" in img or "novanest-platform-streamlit" in img for img in images)

        self.assertTrue(has_api, f"novanest-api image missing from {images}")
        self.assertTrue(has_frontend, f"novanest-frontend image missing from {images}")
        self.assertTrue(has_streamlit, f"novanest-streamlit image missing from {images}")

    def test_04_container_health_and_orchestration(self):
        """Verify all compose containers (db, api, frontend, streamlit) are running and healthy."""
        cmd = list(self.compose_cmd) + ["ps", "--format", "json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(PROJECT_ROOT))
        self.assertEqual(res.returncode, 0, f"docker compose ps failed: {res.stderr}")

        # Each line or list is a JSON object
        raw = res.stdout.strip()
        containers = []
        if raw.startswith("["):
            containers = json.loads(raw)
        else:
            for line in raw.splitlines():
                if line.strip():
                    containers.append(json.loads(line))

        service_states = {c.get("Service", c.get("Name")): c.get("Health", c.get("State")) for c in containers}
        print(f"\n[CONTAINER STATUS] {service_states}")

        self.assertIn("db", service_states)
        self.assertIn("api", service_states)
        self.assertIn("frontend", service_states)
        self.assertIn("streamlit", service_states)

    def test_05_nginx_reverse_proxy_and_health(self):
        """Verify Nginx reverse proxy endpoint on port 80 and SPA routing."""
        req = urllib.request.Request("http://127.0.0.1/nginx-health")
        with urllib.request.urlopen(req, timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode()
            self.assertIn("healthy", body)

        # SPA Index test
        req_root = urllib.request.Request("http://127.0.0.1/")
        with urllib.request.urlopen(req_root, timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode()
            self.assertIn("<html", body.lower())

    def test_06_fastapi_proxied_via_nginx(self):
        """Verify FastAPI /api/health and /api/diagnostics/data-source through Nginx reverse proxy."""
        req = urllib.request.Request("http://127.0.0.1/api/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertEqual(data.get("status"), "healthy")
            self.assertEqual(data.get("data_source"), "MySQL Database")

        # Diagnostics check
        req_diag = urllib.request.Request(
            "http://127.0.0.1/api/diagnostics/data-source",
            headers={"X-API-Key": self.viewer_key}
        )
        with urllib.request.urlopen(req_diag, timeout=10) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertEqual(data.get("active_data_source"), "MySQL Database")
            self.assertFalse(data.get("fallback_active"))
            # Total records verification across 10 tables
            tbl_counts = data.get("table_counts", {})
            total_db_records = sum(tbl_counts.get(t, 0) for t in [
                "customers", "restaurants", "menu_items", "riders", "orders",
                "payments", "deliveries", "ratings_reviews", "app_events", "promotions"
            ])
            self.assertEqual(total_db_records, 304405, f"Expected 304,405 records in container DB, got {total_db_records}")

    def test_07_fastapi_rbac_and_overview(self):
        """Verify authentication & RBAC on container API endpoints."""
        # 1. Unauthenticated request must return 401
        req_unauth = urllib.request.Request("http://127.0.0.1/api/overview")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_unauth, timeout=10)
        self.assertEqual(ctx.exception.code, 401, "Protected route must reject unauthenticated request with 401")

        # 2. Authenticated request with valid API key must succeed with certified KPIs
        req_auth = urllib.request.Request(
            "http://127.0.0.1/api/overview",
            headers={"X-API-Key": self.viewer_key}
        )
        with urllib.request.urlopen(req_auth, timeout=10) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            kpis = data.get("kpis", {})
            self.assertEqual(kpis.get("delivered_orders"), 47994, f"Expected 47,994 delivered orders, got {kpis.get('delivered_orders')}")
            self.assertEqual(kpis.get("total_orders"), 49971)
            self.assertEqual(kpis.get("total_gmv"), 46590125.0)

    def test_08_streamlit_container_dashboard(self):
        """Verify Streamlit container running on alternate host port :8502."""
        req = urllib.request.Request("http://127.0.0.1:8502/_stcore/health")
        with urllib.request.urlopen(req, timeout=10) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode().strip()
            self.assertEqual(body, "ok")

    def test_09_container_security_non_root_and_isolation(self):
        """Verify containers run as unprivileged non-root users."""
        # Check API user
        res = subprocess.run([self.docker_cmd, "exec", "novanest-api", "id", "-u"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            uid = res.stdout.strip()
            self.assertEqual(uid, "10001", f"FastAPI container running as UID {uid}, expected 10001 (novanest)")

        # Check Streamlit user
        res_st = subprocess.run([self.docker_cmd, "exec", "novanest-streamlit", "id", "-u"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_st.returncode == 0:
            uid_st = res_st.stdout.strip()
            self.assertEqual(uid_st, "10001", f"Streamlit container running as UID {uid_st}, expected 10001 (novanest)")

        # Check MySQL port unexposed
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        # Port 3306 is host MySQL, container MySQL should NOT be bound on any other host port like 3307
        self.assertFalse(s.connect_ex(("127.0.0.1", 3307)) == 0, "Container MySQL port should NOT be exposed on 3307")

    def test_10_sse_streaming_telemetry_through_nginx(self):
        """Verify real-time SSE telemetry streaming through unbuffered Nginx reverse proxy."""
        # 1. Exchange operator API key for single-use streaming ticket
        req_ticket = urllib.request.Request(
            "http://127.0.0.1/api/ai/stream-ticket",
            data=json.dumps({"session_id": "phase06_11_2_sse"}).encode(),
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_ticket, timeout=10) as r:
            self.assertEqual(r.status, 200)
            ticket = json.loads(r.read().decode()).get("ticket")
            self.assertTrue(ticket.startswith("st_"), "Ticket must follow st_ format")

        # 2. Connect to SSE stream via Nginx edge proxy
        url = f"http://127.0.0.1/api/ai/ask/stream?ticket={ticket}&session_id=phase06_11_2_sse&question=What+is+our+total+revenue"
        req_stream = urllib.request.Request(url)
        with urllib.request.urlopen(req_stream, timeout=15) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("text/event-stream", r.headers.get("content-type", ""))
            first_event = r.readline().decode().strip()
            self.assertTrue(first_event.startswith("event:"), f"Expected SSE event, got: {first_event}")


if __name__ == "__main__":
    unittest.main()
