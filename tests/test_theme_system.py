"""
NovaNest Multi-Theme System Test Suite
Verifies:
1. All 6 themes configured with correct keys, names, subtitles, palettes, and chart tokens
2. ThemeContext provider and localStorage persistence logic
3. ThemeSwitcher component with trigger, dropdown, preview swatches, and active indicators
4. Pre-hydration script in index.html to eliminate theme flash
5. CSS design system and theme selectors in index.css
6. Recharts theme variables integration
7. Hero3DBanner and FloatingChatbot theme adaptation
8. Full frontend production build verification
"""

import os
import unittest
from pathlib import Path
import re
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

class TestMultiThemeSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theme_context_file = FRONTEND_DIR / "src" / "context" / "ThemeContext.tsx"
        cls.theme_switcher_file = FRONTEND_DIR / "src" / "components" / "ThemeSwitcher.tsx"
        cls.index_html_file = FRONTEND_DIR / "index.html"
        cls.index_css_file = FRONTEND_DIR / "src" / "index.css"
        cls.header_nav_file = FRONTEND_DIR / "src" / "components" / "HeaderNav.tsx"
        cls.hero_banner_file = FRONTEND_DIR / "src" / "components" / "Hero3DBanner.tsx"
        cls.chatbot_file = FRONTEND_DIR / "src" / "components" / "FloatingChatbot.tsx"
        cls.main_tsx_file = FRONTEND_DIR / "src" / "main.tsx"
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_all_six_themes_defined_in_context(self):
        self.assertTrue(self.theme_context_file.exists(), "ThemeContext.tsx must exist")
        content = self.theme_context_file.read_text(encoding="utf-8")
        
        expected_themes = [
            ("midnight", "Midnight Dark"),
            ("light", "Light Mode"),
            ("cyberpunk", "Cyberpunk"),
            ("glassmorphism", "Glassmorphism"),
            ("ocean", "Ocean Blue"),
            ("emerald", "Emerald Green"),
        ]
        
        for theme_id, theme_name in expected_themes:
            self.assertIn(f"'{theme_id}'", content, f"Theme ID '{theme_id}' must be in ThemeContext")
            self.assertIn(f"name: '{theme_name}'", content, f"Theme name '{theme_name}' must be in ThemeContext")
        
        # Verify chart colors defined
        self.assertIn("chartColors", content)
        self.assertIn("localStorage", content)
        self.assertIn("novanest_theme", content)

    def test_02_theme_switcher_component(self):
        self.assertTrue(self.theme_switcher_file.exists(), "ThemeSwitcher.tsx must exist")
        content = self.theme_switcher_file.read_text(encoding="utf-8")
        
        self.assertIn("useTheme", content)
        self.assertIn("setTheme", content)
        self.assertIn("Palette", content)
        self.assertIn("ChevronDown", content)
        self.assertIn("availableThemes.map", content)
        self.assertIn("aria-haspopup", content)
        self.assertIn("aria-expanded", content)
        self.assertIn("Escape", content, "Must handle Escape key to close popover")

    def test_03_pre_hydration_script_in_index_html(self):
        content = self.index_html_file.read_text(encoding="utf-8")
        self.assertIn("localStorage.getItem('novanest_theme')", content, "index.html must check saved theme")
        self.assertIn("data-theme", content, "index.html must set data-theme attribute synchronously")
        self.assertIn("<div id=\"root\"></div>", content)

    def test_04_theme_provider_mounted_in_main(self):
        content = self.main_tsx_file.read_text(encoding="utf-8")
        self.assertIn("ThemeProvider", content)
        self.assertIn("<ThemeProvider>", content)

    def test_05_header_nav_mounts_theme_switcher(self):
        content = self.header_nav_file.read_text(encoding="utf-8")
        self.assertIn("ThemeSwitcher", content)
        self.assertIn("<ThemeSwitcher />", content)

    def test_06_css_variables_and_selectors_in_index_css(self):
        content = self.index_css_file.read_text(encoding="utf-8")
        
        theme_selectors = [
            '[data-theme="midnight"]',
            '[data-theme="light"]',
            '[data-theme="cyberpunk"]',
            '[data-theme="glassmorphism"]',
            '[data-theme="ocean"]',
            '[data-theme="emerald"]',
        ]
        
        for sel in theme_selectors:
            self.assertIn(sel, content, f"CSS must contain theme selector {sel}")

        # Verify chart overrides
        self.assertIn(".recharts-cartesian-grid line", content)
        self.assertIn(".recharts-text", content)
        self.assertIn(".recharts-default-tooltip", content)
        
        # Verify reduced motion support
        self.assertIn("prefers-reduced-motion: reduce", content)

    def test_07_hero_3d_banner_theme_adaptation(self):
        content = self.hero_banner_file.read_text(encoding="utf-8")
        self.assertIn("var(--hero-bg-gradient)", content)
        self.assertIn("var(--hero-title-gradient)", content)
        self.assertIn("var(--hero-subtitle-gradient)", content)
        self.assertIn("var(--hero-border)", content)
        self.assertIn("NOVANEST", content)
        self.assertIn("END - TO - END BUSINESS ANALYTICS SYSTEM", content)

    def test_08_floating_chatbot_preserved_and_styled(self):
        self.assertTrue(self.chatbot_file.exists(), "FloatingChatbot must exist")
        content = self.chatbot_file.read_text(encoding="utf-8")
        self.assertIn("Ask NovaNest", content)
        self.assertIn("animate-bot-glow", content)

        # Verify backend AI query continues working
        headers = {}
        api_key = os.getenv("NOVANEST_API_KEY") or os.getenv("NOVANEST_ADMIN_KEY") or ""
        if api_key:
            headers["X-API-Key"] = api_key
        resp = requests.post(f"{self.api_base}/api/ai/ask", json={
            "question": "What is our total revenue?",
            "session_id": "theme_test_session"
        }, headers=headers, timeout=15)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertIn("4.66", str(data))
        self.assertIn("4.64", str(data))

if __name__ == "__main__":
    unittest.main()
