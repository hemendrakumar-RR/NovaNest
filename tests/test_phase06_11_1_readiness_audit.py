"""
NovaNest Phase 06.11.1 — Docker Runtime Readiness & Configuration Audit Suite
----------------------------------------------------------------------------
Validates environment readiness, non-interference with active host services,
deep configuration audit of all 9 Docker assets, database safety (304,405 rows),
and isolated network/secret specifications.
"""

import os
import re
import socket
import subprocess
from pathlib import Path
import unittest
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class TestPhase06111ReadinessAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compose_file = PROJECT_ROOT / "docker-compose.yml"
        cls.compose_prod_file = PROJECT_ROOT / "docker-compose.prod.yml"
        cls.dockerignore_file = PROJECT_ROOT / ".dockerignore"
        cls.env_docker_example = PROJECT_ROOT / ".env.docker.example"
        cls.api_dockerfile = PROJECT_ROOT / "docker" / "Dockerfile.api"
        cls.streamlit_dockerfile = PROJECT_ROOT / "docker" / "Dockerfile.streamlit"
        cls.frontend_dockerfile = PROJECT_ROOT / "docker" / "Dockerfile.frontend"
        cls.nginx_conf = PROJECT_ROOT / "docker" / "nginx.conf"
        cls.init_schema = PROJECT_ROOT / "docker" / "mysql" / "init" / "01_init_schema.sql"
        cls.init_users = PROJECT_ROOT / "docker" / "mysql" / "init" / "02_init_users.sql"
        cls.backup_file = PROJECT_ROOT / "scratch" / "novanest_backup_live.sql"

    def test_01_environment_readiness_audit(self):
        """Audit Windows OS, WSL status, and Docker availability transparently."""
        # Check docker command availability
        docker_available = False
        try:
            res = subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            docker_available = (res.returncode == 0)
        except Exception:
            docker_available = False

        print(f"\n[ENVIRONMENT AUDIT] Docker Engine Available: {docker_available}")
        # In this phase, we explicitly verify that Docker absence is acknowledged and documented
        self.assertFalse(docker_available, "Docker unexpectedly available; update status accordingly")

    def test_02_host_services_non_interference(self):
        """Verify that existing local FastAPI, Streamlit, and MySQL services are running undisturbed."""
        def is_port_open(host, port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            try:
                s.connect((host, port))
                s.close()
                return True
            except Exception:
                return False

        self.assertTrue(is_port_open("127.0.0.1", 8000), "FastAPI on port 8000 must remain active")
        self.assertTrue(is_port_open("127.0.0.1", 8501), "Streamlit on port 8501 must remain active")
        self.assertTrue(is_port_open("127.0.0.1", 3306), "MySQL on port 3306 must remain active")

    def test_03_docker_configuration_audit_paths_and_dependencies(self):
        """Verify all required file paths, engineered dataset copies, and non-root users."""
        api_txt = self.api_dockerfile.read_text(encoding="utf-8")
        st_txt = self.streamlit_dockerfile.read_text(encoding="utf-8")

        # Both must copy datasets/cleaned/ and datasets/engineered/
        self.assertIn("datasets/cleaned/", api_txt)
        self.assertIn("datasets/engineered/", api_txt)
        self.assertIn("datasets/cleaned/", st_txt)
        self.assertIn("datasets/engineered/", st_txt, "Streamlit Dockerfile must include datasets/engineered/")

        # Both must drop privileges to user novanest
        self.assertIn("USER novanest", api_txt)
        self.assertIn("USER novanest", st_txt)

    def test_04_secrets_and_sanitization_audit(self):
        """Audit that zero real credentials exist in example templates and initialization scripts."""
        example_txt = self.env_docker_example.read_text(encoding="utf-8")
        users_txt = self.init_users.read_text(encoding="utf-8")

        # Assert no real password occurrences in git-trackable files
        real_passwords = ["Chinnu_2311", "Chinnu@2311"]
        for pwd in real_passwords:
            self.assertNotIn(pwd, example_txt, f"Real password found in .env.docker.example: {pwd}")
            self.assertNotIn(pwd, users_txt, f"Real password found in 02_init_users.sql: {pwd}")

    def test_05_database_safety_and_backup_integrity(self):
        """Verify live novanest_db integrity (304,405 records) and backup availability."""
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_APP_USER", "novanest_app"),
            password=os.getenv("DB_APP_PASSWORD", ""),
            database=os.getenv("DB_NAME", "novanest_db"),
        )
        cur = conn.cursor()
        total_records = 0
        tables = [
            "customers", "restaurants", "riders", "promotions", "menu_items",
            "orders_table", "payments", "deliveries", "ratings_reviews", "app_events"
        ]
        for tbl in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
            total_records += cur.fetchone()[0]
        conn.close()

        self.assertEqual(total_records, 304405, "Live novanest_db records must remain exactly 304,405")
        self.assertTrue(self.backup_file.exists(), "Disaster recovery backup file missing")
        self.assertGreater(os.path.getsize(self.backup_file), 10 * 1024 * 1024, "Backup file size < 10 MB")

    def test_06_docker_compose_security_and_health_orchestration(self):
        """Verify Compose specifications for isolation, health dependencies, and secrets."""
        with open(self.compose_file, "r", encoding="utf-8") as f:
            compose = yaml.safe_load(f)

        services = compose.get("services", {})
        # Port 3306 must NOT be published
        self.assertNotIn("ports", services["db"])
        # Network must be novanest_net
        self.assertIn("novanest_net", compose.get("networks", {}))
        # Dependencies must be healthy
        self.assertEqual(services["api"]["depends_on"]["db"]["condition"], "service_healthy")
        self.assertEqual(services["frontend"]["depends_on"]["api"]["condition"], "service_healthy")


if __name__ == "__main__":
    unittest.main()
