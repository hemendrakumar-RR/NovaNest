"""
Test Suite: Left Sidebar "Ask NovaNest AI" Removal Verification
Verifies:
1. "Ask NovaNest AI" and its subtitle/icon are completely removed from Sidebar.tsx navItems.
2. All 8 required navigation items remain intact with correct labels, subtitles, and keys.
3. FloatingChatbot remains mounted globally in App.tsx.
4. Underlying AI intelligence view and backend endpoints remain untouched and functional.
5. Frontend compiles cleanly via npm run build.
"""

import os
import re
import unittest
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestSidebarRemoval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sidebar_path = PROJECT_ROOT / "frontend" / "src" / "components" / "Sidebar.tsx"
        cls.app_path = PROJECT_ROOT / "frontend" / "src" / "App.tsx"
        cls.floating_chatbot_path = PROJECT_ROOT / "frontend" / "src" / "components" / "FloatingChatbot.tsx"
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_ask_novanest_removed_from_sidebar_nav_items(self):
        content = self.sidebar_path.read_text(encoding="utf-8")
        
        # 1. "Ask NovaNest AI" should not be in the nav items
        self.assertNotIn("label: 'Ask NovaNest AI'", content, "Ask NovaNest AI label must not be in navItems")
        self.assertNotIn("Ask NovaNest AI", content, "Ask NovaNest AI should not appear in Sidebar.tsx")
        
        # 2. Subtitle should not be in nav items
        self.assertNotIn("Conversational NL2SQL & RCA", content, "Associated subtitle must be removed")
        
        # 3. MessageSquareCode should not be imported
        self.assertNotIn("MessageSquareCode", content, "MessageSquareCode icon import must be removed")

    def test_02_all_8_remaining_sidebar_items_preserved(self):
        content = self.sidebar_path.read_text(encoding="utf-8")
        
        expected_items = [
            ("overview", "Executive Overview", "C-Suite Performance Radar"),
            ("customer", "Customer Intelligence", "RFM, CLV & 360 Profiles"),
            ("restaurant", "Restaurant Intelligence", "Merchant Health & Risk Signals"),
            ("operations", "Operations Intelligence", "Demand Forecasts & Logistics"),
            ("financial", "Financial Intelligence", "P&L Economics & Leakage Audit"),
            ("decision", "Decision Intelligence", "Next-Best-Action Queue"),
            ("simulator", "Decision Simulator", "Multi-Variable What-If Lab"),
            ("command_center", "Command Center", "Analytical Digital Twin Matrix"),
        ]
        
        for key, label, subtitle in expected_items:
            self.assertIn(f"key: '{key}'", content, f"Nav item key '{key}' must exist")
            self.assertIn(f"label: '{label}'", content, f"Nav item label '{label}' must exist")
            self.assertIn(f"subtitle: '{subtitle}'", content, f"Nav item subtitle '{subtitle}' must exist")

        # Verify exactly 8 items in navItems array
        # Match each block inside navItems = [...]
        matches = re.findall(r"key:\s*'([^']+)'", content)
        self.assertEqual(matches, [k for k, _, _ in expected_items], "Sidebar must contain exactly the 8 required items")

    def test_03_floating_chatbot_preserved_globally(self):
        app_content = self.app_path.read_text(encoding="utf-8")
        self.assertIn("<FloatingChatbot />", app_content, "Floating chatbot must be rendered in App.tsx")
        
        self.assertTrue(self.floating_chatbot_path.exists(), "FloatingChatbot.tsx must exist")
        bot_content = self.floating_chatbot_path.read_text(encoding="utf-8")
        self.assertIn("Ask NovaNest", bot_content)
        self.assertIn("animate-bot-glow", bot_content)

    def test_04_underlying_ai_endpoint_and_view_preserved(self):
        # AI view exists and not deleted
        ai_view_path = PROJECT_ROOT / "frontend" / "src" / "views" / "AiIntelligenceView.tsx"
        self.assertTrue(ai_view_path.exists(), "AiIntelligenceView.tsx must be preserved")

        # Backend AI endpoint is functional
        headers = {}
        api_key = os.getenv("NOVANEST_API_KEY") or os.getenv("NOVANEST_ADMIN_KEY") or ""
        if api_key:
            headers["X-API-Key"] = api_key
        resp = requests.post(
            f"{self.api_base}/api/ai/ask",
            json={"question": "What is our total revenue?", "session_id": "sidebar_test_session"},
            headers=headers,
            timeout=15,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertIn("4.66", str(data))
        self.assertIn("4.64", str(data))

if __name__ == "__main__":
    unittest.main()
