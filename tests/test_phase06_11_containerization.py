"""
NovaNest Phase 06.11 — Containerization, Compose & CI/CD Verification Suite
-------------------------------------------------------------------------
Automated validation of Dockerfiles, Compose specs, Nginx reverse proxy,
SSE configurations, .dockerignore security, CI/CD pipeline, and backup integrity.
"""

import os
import re
from pathlib import Path
import unittest
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class TestPhase0611Containerization(unittest.TestCase):
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
        cls.ci_workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
        cls.req_api = PROJECT_ROOT / "docker" / "requirements-api.txt"
        cls.req_streamlit = PROJECT_ROOT / "docker" / "requirements-streamlit.txt"

    def test_01_docker_compose_development_spec(self):
        """Verify development docker-compose.yml syntax, services, and healthchecks."""
        self.assertTrue(self.compose_file.exists(), "docker-compose.yml missing")
        with open(self.compose_file, "r", encoding="utf-8") as f:
            compose = yaml.safe_load(f)

        services = compose.get("services", {})
        self.assertIn("db", services, "Service 'db' missing from compose")
        self.assertIn("api", services, "Service 'api' missing from compose")
        self.assertIn("frontend", services, "Service 'frontend' missing from compose")
        self.assertIn("streamlit", services, "Service 'streamlit' missing from compose")

        # Database checks: Persistent volume, healthcheck, no public exposure by default
        db_cfg = services["db"]
        self.assertIn("novanest_mysql_data:/var/lib/mysql", db_cfg.get("volumes", []))
        self.assertIn("healthcheck", db_cfg, "db healthcheck missing")
        self.assertNotIn("ports", db_cfg, "db should NOT expose ports publicly by default")
        self.assertEqual(db_cfg.get("restart"), "unless-stopped")

        # Dependency orchestration
        self.assertEqual(
            services["api"]["depends_on"]["db"]["condition"],
            "service_healthy",
            "api must wait for healthy db"
        )
        self.assertEqual(
            services["frontend"]["depends_on"]["api"]["condition"],
            "service_healthy",
            "frontend must wait for healthy api"
        )
        self.assertEqual(
            services["streamlit"]["depends_on"]["db"]["condition"],
            "service_healthy",
            "streamlit must wait for healthy db"
        )
        self.assertEqual(
            services["streamlit"]["depends_on"]["api"]["condition"],
            "service_healthy",
            "streamlit must wait for healthy api"
        )

        # Resource limits defined
        for sname in ["db", "api", "frontend", "streamlit"]:
            limits = services[sname].get("deploy", {}).get("resources", {}).get("limits", {})
            self.assertIn("cpus", limits, f"cpus limit missing for {sname}")
            self.assertIn("memory", limits, f"memory limit missing for {sname}")

        # Network isolation
        self.assertIn("novanest_net", compose.get("networks", {}))
        self.assertIn("novanest_mysql_data", compose.get("volumes", {}))

    def test_02_docker_compose_production_spec(self):
        """Verify docker-compose.prod.yml security overrides and secrets."""
        self.assertTrue(self.compose_prod_file.exists(), "docker-compose.prod.yml missing")
        with open(self.compose_prod_file, "r", encoding="utf-8") as f:
            prod_compose = yaml.safe_load(f)

        secrets = prod_compose.get("secrets", {})
        self.assertIn("db_app_password", secrets)
        self.assertIn("novanest_api_key", secrets)

        services = prod_compose.get("services", {})
        for sname in ["api", "frontend", "streamlit"]:
            cfg = services[sname]
            self.assertEqual(cfg.get("restart"), "always")
            self.assertIn("logging", cfg, f"Logging options missing for {sname}")
            self.assertEqual(cfg["logging"].get("driver"), "json-file")

    def test_03_fastapi_dockerfile_hardening(self):
        """Verify FastAPI Dockerfile multi-stage build, non-root user, and healthcheck."""
        self.assertTrue(self.api_dockerfile.exists())
        content = self.api_dockerfile.read_text(encoding="utf-8")

        self.assertIn("AS builder", content)
        self.assertIn("AS runtime", content)
        self.assertIn("useradd", content)
        self.assertIn("USER novanest", content)
        self.assertIn("EXPOSE 8000", content)
        self.assertIn("HEALTHCHECK", content)
        self.assertIn("http://localhost:8000/api/health", content)
        self.assertIn("uvicorn", content)

    def test_04_streamlit_dockerfile_hardening(self):
        """Verify Streamlit Dockerfile multi-stage build, non-root user, and healthcheck."""
        self.assertTrue(self.streamlit_dockerfile.exists())
        content = self.streamlit_dockerfile.read_text(encoding="utf-8")

        self.assertIn("AS builder", content)
        self.assertIn("AS runtime", content)
        self.assertIn("useradd", content)
        self.assertIn("USER novanest", content)
        self.assertIn("EXPOSE 8501", content)
        self.assertIn("HEALTHCHECK", content)
        self.assertIn("http://localhost:8501/_stcore/health", content)
        self.assertIn("streamlit", content)

    def test_05_react_nginx_dockerfile_hardening(self):
        """Verify React Dockerfile multi-stage build with Node 20 and Nginx Alpine."""
        self.assertTrue(self.frontend_dockerfile.exists())
        content = self.frontend_dockerfile.read_text(encoding="utf-8")

        self.assertIn("node:20-alpine AS builder", content)
        self.assertTrue("nginx:alpine-slim AS runtime" in content or "nginx:1.27-alpine AS runtime" in content)
        self.assertIn("npm run build", content)
        self.assertIn("COPY --from=builder /app/dist /usr/share/nginx/html", content)
        self.assertIn("EXPOSE 80", content)
        self.assertIn("HEALTHCHECK", content)

    def test_06_nginx_reverse_proxy_and_sse_configuration(self):
        """Verify Nginx reverse proxy routes, security headers, and SSE streaming config."""
        self.assertTrue(self.nginx_conf.exists())
        content = self.nginx_conf.read_text(encoding="utf-8")

        self.assertIn("upstream api_backend", content)
        self.assertIn("server api:8000", content)
        self.assertIn("location /api/", content)
        self.assertIn("proxy_pass http://api_backend;", content)

        # SSE streaming directives
        self.assertIn("location ~* ^/api/ai/(ask/stream|stream)", content)
        self.assertIn("proxy_buffering off;", content)
        self.assertIn("chunked_transfer_encoding on;", content)
        self.assertIn("proxy_read_timeout 86400s;", content)

        # Security headers & SPA routing
        self.assertIn("add_header X-Frame-Options", content)
        self.assertIn("add_header X-Content-Type-Options", content)
        self.assertIn("try_files $uri $uri/ /index.html;", content)

    def test_07_dockerignore_and_secret_isolation(self):
        """Verify .dockerignore excludes secrets and non-runtime files."""
        self.assertTrue(self.dockerignore_file.exists())
        content = self.dockerignore_file.read_text(encoding="utf-8")

        self.assertIn(".env", content)
        self.assertIn(".git/", content)
        self.assertIn("**/node_modules/", content)
        self.assertIn("**/__pycache__/", content)
        self.assertIn("datasets/raw/", content)
        self.assertIn("powerbi/", content)

        # Template sanitization check
        self.assertTrue(self.env_docker_example.exists())
        example_content = self.env_docker_example.read_text(encoding="utf-8")
        self.assertIn("DB_HOST=db", example_content)
        self.assertNotIn("Chinnu_2311", example_content, "Real password in example")

    def test_08_ci_cd_github_actions_workflow(self):
        """Verify GitHub Actions CI/CD workflow structure and jobs."""
        self.assertTrue(self.ci_workflow.exists())
        with open(self.ci_workflow, "r", encoding="utf-8") as f:
            ci = yaml.safe_load(f)

        jobs = ci.get("jobs", {})
        self.assertIn("backend-ci", jobs)
        self.assertIn("security-audit", jobs)
        self.assertIn("frontend-ci", jobs)
        self.assertIn("docker-build-and-scan", jobs)

        # Scan step check
        scan_job = jobs["docker-build-and-scan"]
        steps = scan_job.get("steps", [])
        has_trivy = any("trivy-action" in str(s.get("uses", "")) for s in steps)
        self.assertTrue(has_trivy, "Trivy vulnerability scan missing from CI")

    def test_09_database_and_application_non_regression(self):
        """Verify that live MySQL novanest_db remains 100% intact with 304,405 records."""
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_APP_USER", "novanest_app"),
            password=os.getenv("DB_APP_PASSWORD", ""),
            database=os.getenv("DB_NAME", "novanest_db"),
        )
        cur = conn.cursor()
        total_rows = 0
        tables = [
            "customers", "restaurants", "riders", "promotions", "menu_items",
            "orders_table", "payments", "deliveries", "ratings_reviews", "app_events"
        ]
        for tbl in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
            cnt = cur.fetchone()[0]
            total_rows += cnt
        conn.close()

        self.assertEqual(total_rows, 304405, f"Expected 304,405 records, found {total_rows}")


if __name__ == "__main__":
    unittest.main()
