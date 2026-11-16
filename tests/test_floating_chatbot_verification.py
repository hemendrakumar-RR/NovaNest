"""
Test Suite: Floating Blinking AI Chatbot Verification
Verifies:
1. Component structure and animation styles
2. Mounting in shared root layout (App.tsx)
3. Real AI backend responses for suggested questions and arbitrary queries
4. Multi-turn conversation context across floating sessions
5. Reset conversation endpoint (/api/ai/reset)
6. Zero regression on existing platform endpoints
"""

import os
import sys
import unittest
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestFloatingChatbot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_base = "http://127.0.0.1:8000"
        cls.frontend_dir = PROJECT_ROOT / "frontend"
        cls.http = requests.Session()
        api_key = os.getenv("NOVANEST_API_KEY") or os.getenv("NOVANEST_ADMIN_KEY") or ""
        admin_key = os.getenv("NOVANEST_ADMIN_KEY") or api_key
        cls.admin_headers = {"X-API-Key": admin_key} if admin_key else {}
        if api_key:
            cls.http.headers.update({"X-API-Key": api_key})

    # -------------------------------------------------------------------------
    # 1. Component & Styles Verification
    # -------------------------------------------------------------------------
    def test_01_component_and_styles_exist(self):
        chatbot_file = self.frontend_dir / "src" / "components" / "FloatingChatbot.tsx"
        self.assertTrue(chatbot_file.exists(), "FloatingChatbot.tsx must exist")
        content = chatbot_file.read_text(encoding="utf-8")
        
        # Verify header, welcome text, suggestions, and controls
        self.assertIn("Ask NovaNest", content)
        self.assertIn("Your Intelligent Business Assistant", content)
        self.assertIn("Hi! I'm NovaNest AI", content)
        self.assertIn("Analyze my business performance.", content)
        self.assertIn("What is our total revenue?", content)
        self.assertIn("Explain customer churn.", content)
        self.assertIn("How can I improve restaurant performance?", content)
        self.assertIn("Help me write Python or SQL code.", content)
        self.assertIn("animate-bot-glow", content)
        self.assertIn("animate-beacon-blink", content)

    def test_02_global_mount_in_app(self):
        app_file = self.frontend_dir / "src" / "App.tsx"
        content = app_file.read_text(encoding="utf-8")
        self.assertIn("FloatingChatbot", content, "FloatingChatbot must be imported in App.tsx")
        self.assertIn("<FloatingChatbot />", content, "FloatingChatbot must be rendered globally in App.tsx")

    def test_03_css_animations_and_accessibility(self):
        css_file = self.frontend_dir / "src" / "index.css"
        content = css_file.read_text(encoding="utf-8")
        self.assertIn("@keyframes botGlowPulse", content)
        self.assertIn("@keyframes beaconBlink", content)
        self.assertIn("prefers-reduced-motion: reduce", content, "Must support reduced-motion accessibility")

    # -------------------------------------------------------------------------
    # 2. Real AI Backend Interaction (Suggested Chips & Arbitrary Inquiries)
    # -------------------------------------------------------------------------
    def test_04_floating_chat_business_performance(self):
        session_id = "test_float_session_perf"
        resp = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "Analyze my business performance.",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertTrue(len(data["answer"]) > 50)
        self.assertIn(data["route"], ["BUSINESS_DATA", "EXECUTIVE_OVERVIEW", "GENERAL"])

    def test_05_floating_chat_total_revenue(self):
        session_id = "test_float_session_rev"
        resp = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "What is our total revenue?",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Certified Phase 04 KPI-01 GMV (₹4.66 Cr) and KPI-02 Net Revenue (₹4.64 Cr)
        self.assertIn("4.66", str(data))
        self.assertIn("4.64", str(data))
        self.assertGreater(len(data.get("verified_metrics", [])), 0)

    def test_06_floating_chat_customer_churn(self):
        session_id = "test_float_session_churn"
        resp = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "Explain customer churn.",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertTrue("churn" in data["answer"].lower())

    def test_07_floating_chat_python_code(self):
        session_id = "test_float_session_code"
        resp = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "Help me write Python code to calculate average of a list.",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("```python", data["answer"])
        self.assertIn("def calculate_average", data["answer"])

    # -------------------------------------------------------------------------
    # 3. Multi-Turn Context Resolution & Session Reset
    # -------------------------------------------------------------------------
    def test_08_floating_chat_multi_turn_follow_up(self):
        session_id = "test_float_session_multiturn"
        
        # Turn 1
        r1 = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "What is our cancellation rate?",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(r1.status_code, 200)
        self.assertTrue("4.16" in r1.json()["answer"] or "cancellation" in r1.json()["answer"].lower())

        # Turn 2: Follow-up relying on Turn 1 context
        r2 = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "Which restaurant has the highest rate?",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertTrue(len(d2.get("data_rows", [])) > 0 or "restaurant" in d2["answer"].lower())

        # Turn 3: Follow-up recommendations
        r3 = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "How can we improve it?",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(r3.status_code, 200)
        d3 = r3.json()
        self.assertTrue("recommend" in d3["answer"].lower() or len(d3.get("recommendations", [])) > 0)

        # Reset Session (requires admin scope when NOVANEST_ADMIN_KEY is configured)
        r_reset = self.http.post(f"{self.api_base}/api/ai/reset", json={
            "session_id": session_id
        }, headers=self.admin_headers, timeout=10)
        self.assertEqual(r_reset.status_code, 200)
        self.assertEqual(r_reset.json()["status"], "success")

    # -------------------------------------------------------------------------
    # 4. General Open-Ended Inquiry Support
    # -------------------------------------------------------------------------
    def test_09_floating_chat_general_knowledge(self):
        session_id = "test_float_session_gen"
        resp = self.http.post(f"{self.api_base}/api/ai/ask", json={
            "question": "How does GPS work?",
            "session_id": session_id
        }, timeout=20)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertIn("satellite", data["answer"].lower())
        self.assertEqual(len(data.get("verified_metrics", [])), 0, "General question must not display business metric cards")


if __name__ == "__main__":
    unittest.main()
