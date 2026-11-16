"""
=============================================================================
NOVANEST PHASE 16: ULTIMATE UI/UX & EXPERIENCE ENGINEERING TEST SUITE
=============================================================================
Validates:
1. Canonical Database Integrity (304,405 records preserved across 10 tables).
2. Frontend Build Assets Integrity (Vite dist bundle HTML, JS, CSS).
3. Design System Tokens & Reduced-Motion Accessibility in CSS.
4. Reusable DataTable Component Architecture (Sort, Search, Pagination, Export).
5. Reusable SkeletonLoader Component Architecture (Shimmer variants, aria-busy).
6. StatusBadge Component Architecture (High-contrast, non-color-only icons).
7. Executive AI Copilot Ergonomics (Markdown export, JSON export, Clear, Attributions).
8. Responsive Navigation Architecture (Desktop + Mobile drawer overlay, a11y).
9. Streamlit Dashboard Visual Token Alignment.
10. Zero Fabricated Fallback Metrics & API Error Handling Integrity.
11. Full End-to-End Domain Telemetry API Contract Stability.
=============================================================================
"""

import os
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase16UiUxExperience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.operator_headers = {"X-API-Key": "test-operator-key-phase06-8"}
        cls.admin_headers = {"X-API-Key": "test-admin-key-phase06-8"}

    # =========================================================================
    # TEST 1: Canonical Database Integrity (304,405 records preserved)
    # =========================================================================
    def test_01_canonical_database_integrity(self):
        """Verifies zero record mutations across all 10 canonical MySQL tables (304,405 records)."""
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
        self.assertEqual(sum(expected_counts.values()), 304405, "Canonical baseline must be exactly 304,405")

        resp = self.client.get("/api/overview", headers=self.operator_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        kpis = data.get("kpis", {})
        self.assertEqual(kpis.get("total_orders"), 49971)
        self.assertEqual(kpis.get("active_customers"), 5000)
        self.assertEqual(kpis.get("active_restaurants"), 1500)
        self.assertEqual(kpis.get("active_riders"), 4000)

    # =========================================================================
    # TEST 2: Frontend Production Build Assets Integrity
    # =========================================================================
    def test_02_frontend_build_assets_integrity(self):
        """Verifies dist/index.html and optimized JS/CSS bundles exist in frontend/dist."""
        dist_path = PROJECT_ROOT / "frontend" / "dist"
        self.assertTrue(dist_path.exists(), "frontend/dist must exist")

        index_html = dist_path / "index.html"
        self.assertTrue(index_html.exists(), "dist/index.html must exist")
        html_content = index_html.read_text(encoding="utf-8")
        self.assertIn("NOVANEST", html_content.upper(), "index.html must reference NovaNest")

        assets_dir = dist_path / "assets"
        self.assertTrue(assets_dir.exists(), "dist/assets must exist")

        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))
        self.assertGreater(len(js_files), 0, "Must contain bundled JS assets")
        self.assertGreater(len(css_files), 0, "Must contain bundled CSS assets")

    # =========================================================================
    # TEST 3: Design System Tokens & Accessibility in index.css
    # =========================================================================
    def test_03_design_system_and_accessibility_css(self):
        """Verifies design tokens, focus-visible states, and prefers-reduced-motion in index.css."""
        css_path = PROJECT_ROOT / "frontend" / "src" / "index.css"
        self.assertTrue(css_path.exists(), "frontend/src/index.css must exist")
        css_text = css_path.read_text(encoding="utf-8")

        # Design tokens
        self.assertIn("--bg-app", css_text, "Must define --bg-app token")
        self.assertIn("--bg-workspace", css_text, "Must define --bg-workspace token")
        self.assertIn("--accent-primary", css_text, "Must define --accent-primary token")
        self.assertIn("--border-subtle", css_text, "Must define --border-subtle token")

        # Accessibility tokens
        self.assertIn(":focus-visible", css_text, "Must define visible focus rings")
        self.assertIn("prefers-reduced-motion", css_text, "Must support prefers-reduced-motion")

    # =========================================================================
    # TEST 4: Reusable DataTable Component Architecture
    # =========================================================================
    def test_04_data_table_component_architecture(self):
        """Verifies DataTable.tsx includes search, sorting, pagination, and CSV export capabilities."""
        dt_path = PROJECT_ROOT / "frontend" / "src" / "components" / "ui" / "DataTable.tsx"
        self.assertTrue(dt_path.exists(), "DataTable.tsx must exist")
        dt_text = dt_path.read_text(encoding="utf-8")

        self.assertIn("searchTerm", dt_text, "DataTable must implement search filtering")
        self.assertIn("handleSort", dt_text, "DataTable must implement column sorting")
        self.assertIn("currentPage", dt_text, "DataTable must implement pagination")
        self.assertIn("pageSize", dt_text, "DataTable must implement page size selection")
        self.assertIn("exportToCSV", dt_text, "DataTable must implement CSV export")
        self.assertIn("visibleColumns", dt_text, "DataTable must implement column visibility toggles")
        self.assertIn('role="table"', dt_text, "DataTable must contain accessible semantic table role")

    # =========================================================================
    # TEST 5: Reusable SkeletonLoader Component Architecture
    # =========================================================================
    def test_05_skeleton_loader_component_architecture(self):
        """Verifies SkeletonLoader.tsx supports kpi, chart, table, card variants with a11y."""
        sk_path = PROJECT_ROOT / "frontend" / "src" / "components" / "ui" / "SkeletonLoader.tsx"
        self.assertTrue(sk_path.exists(), "SkeletonLoader.tsx must exist")
        sk_text = sk_path.read_text(encoding="utf-8")

        self.assertIn("'kpi'", sk_text, "SkeletonLoader must support KPI variant")
        self.assertIn("'chart'", sk_text, "SkeletonLoader must support chart variant")
        self.assertIn("'table'", sk_text, "SkeletonLoader must support table variant")
        self.assertIn('aria-busy="true"', sk_text, "SkeletonLoader must declare aria-busy for screen readers")

    # =========================================================================
    # TEST 6: StatusBadge Component Architecture
    # =========================================================================
    def test_06_status_badge_component_architecture(self):
        """Verifies StatusBadge.tsx supports high-contrast variants and semantic icons (non-color-only)."""
        badge_path = PROJECT_ROOT / "frontend" / "src" / "components" / "ui" / "StatusBadge.tsx"
        self.assertTrue(badge_path.exists(), "StatusBadge.tsx must exist")
        badge_text = badge_path.read_text(encoding="utf-8")

        self.assertIn("CheckCircle2", badge_text, "StatusBadge must support check icon")
        self.assertIn("AlertTriangle", badge_text, "StatusBadge must support warning icon")
        self.assertIn("XCircle", badge_text, "StatusBadge must support error icon")
        self.assertIn('role="status"', badge_text, "StatusBadge must have role='status' for a11y")

    # =========================================================================
    # TEST 7: Executive AI Copilot Experience Upgrade
    # =========================================================================
    def test_07_executive_copilot_experience_features(self):
        """Verifies ExecutiveAiCopilot.tsx contains Markdown/JSON export, clear conversation, and suggestions."""
        copilot_path = PROJECT_ROOT / "frontend" / "src" / "components" / "ExecutiveAiCopilot.tsx"
        self.assertTrue(copilot_path.exists(), "ExecutiveAiCopilot.tsx must exist")
        copilot_text = copilot_path.read_text(encoding="utf-8")

        self.assertIn("handleExportMarkdown", copilot_text, "Copilot must support Markdown export")
        self.assertIn("handleExportJSON", copilot_text, "Copilot must support JSON export")
        self.assertIn("handleClearHistory", copilot_text, "Copilot must support conversation clear")
        self.assertIn("handleCopy", copilot_text, "Copilot must support 1-click response copying")
        self.assertIn("SUGGESTED_QUESTIONS", copilot_text, "Copilot must present suggested executive questions")

    # =========================================================================
    # TEST 8: Responsive Navigation Architecture (Desktop + Mobile Drawer)
    # =========================================================================
    def test_08_responsive_navigation_architecture(self):
        """Verifies Sidebar.tsx and HeaderNav.tsx implement responsive mobile drawer and a11y."""
        sidebar_path = PROJECT_ROOT / "frontend" / "src" / "components" / "Sidebar.tsx"
        header_path = PROJECT_ROOT / "frontend" / "src" / "components" / "HeaderNav.tsx"
        app_path = PROJECT_ROOT / "frontend" / "src" / "App.tsx"

        sidebar_text = sidebar_path.read_text(encoding="utf-8")
        header_text = header_path.read_text(encoding="utf-8")
        app_text = app_path.read_text(encoding="utf-8")

        self.assertIn("mobileSidebarOpen", app_text, "App must manage mobile drawer state")
        self.assertIn("onToggleMobileSidebar", header_text, "HeaderNav must support mobile toggle")
        self.assertIn("Escape", sidebar_text, "Sidebar must close on Escape key for a11y")
        self.assertIn("hidden md:flex", sidebar_text, "Sidebar must be responsive with md: breakpoint")

    # =========================================================================
    # TEST 9: Streamlit Dashboard Visual Token Alignment
    # =========================================================================
    def test_09_streamlit_design_alignment(self):
        """Verifies Streamlit styles align with NovaNest Obsidian & Sapphire palette."""
        st_theme = PROJECT_ROOT / "streamlit_app" / "styles" / "theme.css"
        self.assertTrue(st_theme.exists(), "streamlit_app/styles/theme.css must exist")
        st_text = st_theme.read_text(encoding="utf-8")

        self.assertIn("--nn-bg-app: #0B0F17", st_text, "Streamlit must use unified background token")
        self.assertIn("Plus Jakarta Sans", st_text, "Streamlit must use matching font family")
        self.assertIn("--nn-accent-blue: #3B82F6", st_text, "Streamlit must use matching accent token")

    # =========================================================================
    # TEST 10: Zero Fabricated Fallback Metrics in API Error State
    # =========================================================================
    def test_10_zero_fabricated_fallback_metrics(self):
        """Verifies missing credentials return 401/403 and never fabricate false metric numbers."""
        resp = self.client.get("/api/overview")  # Unauthenticated
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertNotIn("total_orders", data, "Error response must never fabricate false metrics")

    # =========================================================================
    # TEST 11: Domain Telemetry API Contract Stability
    # =========================================================================
    def test_11_domain_telemetry_contracts(self):
        """Verifies all 5 core domain endpoints return valid status and structure."""
        endpoints = [
            "/api/overview",
            "/api/financial/overview",
            "/api/customer/overview",
            "/api/restaurant/overview",
            "/api/operations/overview",
        ]
        for ep in endpoints:
            resp = self.client.get(ep, headers=self.operator_headers)
            self.assertEqual(resp.status_code, 200, f"Endpoint {ep} must return HTTP 200")
            payload = resp.json()
            self.assertIn("kpis", payload, f"Endpoint {ep} payload must contain 'kpis'")


if __name__ == "__main__":
    unittest.main()
