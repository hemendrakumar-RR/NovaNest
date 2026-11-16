"""
NovaNest Platform Test Suite - Phase 18 Theme Transformation
Tests the official NovaNest Enterprise Theme across React, Streamlit, Power BI, and MySQL integrity.

Official Palette:
- Background: #F8FAFC (slate-50)
- Primary: #2563EB (blue-600)
- Accent: #F97316 (orange-500)
- Main Text: #1E293B (slate-800)
Supporting:
- White surface: #FFFFFF
- Secondary background: #F1F5F9
- Border: #E2E8F0
- Muted text: #64748B
- Success: #16A34A
- Warning: #F59E0B
- Error: #DC2626
"""

import os
import json
import zipfile
import unittest

class TestPhase18ThemeTransformation(unittest.TestCase):

    def test_01_tailwind_config_tokens(self):
        """Verify official brand tokens are configured in Tailwind."""
        path = "frontend/tailwind.config.js"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("#F8FAFC", content, "Background color #F8FAFC missing in Tailwind config")
        self.assertIn("#2563EB", content, "Primary color #2563EB missing in Tailwind config")
        self.assertIn("#F97316", content, "Accent color #F97316 missing in Tailwind config")
        self.assertIn("#1E293B", content, "Text color #1E293B missing in Tailwind config")

    def test_02_theme_context_default_novanest(self):
        """Verify default theme is 'novanest' and 'emerald' is purged."""
        path = "frontend/src/context/ThemeContext.tsx"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("'novanest'", content, "Official 'novanest' theme missing in ThemeContext")
        self.assertNotIn("id: 'emerald'", content, "Legacy 'emerald' dark theme still present in ThemeContext")

    def test_03_index_css_theme_variables(self):
        """Verify CSS custom properties in index.css adhere to official palette."""
        path = "frontend/src/index.css"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("--bg-app: #F8FAFC;", content, "--bg-app not set to #F8FAFC")
        self.assertIn("--primary: #2563EB;", content, "--primary not set to #2563EB")
        self.assertIn("--accent: #F97316;", content, "--accent not set to #F97316")
        self.assertIn("--text-primary: #1E293B;", content, "--text-primary not set to #1E293B")
        self.assertNotIn("[data-theme=\"emerald\"]", content, "[data-theme=\"emerald\"] still exists in index.css")

    def test_04_streamlit_config_toml(self):
        """Verify .streamlit/config.toml defines official theme."""
        path = ".streamlit/config.toml"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('primaryColor="#2563EB"', content)
        self.assertIn('backgroundColor="#F8FAFC"', content)
        self.assertIn('secondaryBackgroundColor="#F1F5F9"', content)
        self.assertIn('textColor="#1E293B"', content)

    def test_05_streamlit_theme_css(self):
        """Verify streamlit_app/styles/theme.css defines official palette variables."""
        path = "streamlit_app/styles/theme.css"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("--nn-bg-app: #F8FAFC;", content)
        self.assertIn("--nn-bg-card: #FFFFFF;", content)
        self.assertIn("--nn-accent-blue: #2563EB;", content)
        self.assertIn("--nn-accent-orange: #F97316;", content)
        self.assertIn("--nn-text-primary: #1E293B;", content)

    def test_06_powerbi_theme_json(self):
        """Verify powerbi/novanest_theme.json conforms to schema."""
        path = "powerbi/novanest_theme.json"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with open(path, "r", encoding="utf-8") as f:
            theme = json.load(f)
        self.assertEqual(theme["background"], "#F8FAFC")
        self.assertEqual(theme["foreground"], "#1E293B")
        self.assertEqual(theme["tableAccent"], "#2563EB")
        self.assertIn("#2563EB", theme["dataColors"])
        self.assertIn("#F97316", theme["dataColors"])

    def test_07_powerbi_themed_pbix_integrity(self):
        """Verify powerbi/NovaNest_themed.pbix exists and contains valid layout."""
        path = "powerbi/NovaNest_themed.pbix"
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        with zipfile.ZipFile(path, "r") as z:
            names = z.namelist()
            self.assertIn("Report/Layout", names)
            self.assertIn("DataModel", names)
            self.assertIn("Report/StaticResources/SharedResources/BaseThemes/CY24SU10.json", names)

    def test_08_screenshots_captured(self):
        """Verify all 10 visual screenshots exist and are populated."""
        expected_shots = [
            "01_theme_executive_overview.png",
            "02_theme_customer_360.png",
            "03_theme_restaurant_intelligence.png",
            "04_theme_operations_intelligence.png",
            "05_theme_financial_intelligence.png",
            "06_theme_executive_ai_copilot.png",
            "07_theme_decision_center.png",
            "08_theme_decision_simulator.png",
            "09_theme_digital_twin_command_center.png",
            "10_theme_streamlit_dashboard.png",
        ]
        shots_dir = "NEWCHAGES/PHASE18_THEME/screenshots"
        for shot in expected_shots:
            full_path = os.path.join(shots_dir, shot)
            self.assertTrue(os.path.exists(full_path), f"Missing screenshot {shot}")
            size = os.path.getsize(full_path)
            self.assertGreater(size, 5000, f"Screenshot {shot} too small ({size} bytes)")

    def test_09_production_dist_built(self):
        """Verify frontend/dist exists with built html and assets."""
        self.assertTrue(os.path.exists("frontend/dist/index.html"))
        self.assertTrue(os.path.exists("frontend/dist/assets"))


if __name__ == "__main__":
    unittest.main()
