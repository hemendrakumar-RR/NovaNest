"""
Test Suite: Universal Intelligent AI Assistant (Ask NovaNest AI)
Tests the 15 specific scenarios required by Phase 10 of the universal assistant specification:
1. Greetings & casual conversation
2. Conceptual explanation (Machine Learning in simple words)
3. Technical comparison (SQL vs NoSQL)
4. Code generation (Python program to calculate average of a list)
5. Mathematical / algorithm explanation (Cosine similarity)
6. Programmatic calculation (Compound interest on 2000 at 20% for 2 years)
7. Grounded business data (Total revenue with verified metrics)
8. Root cause analysis (Why are cancellations increasing?)
9. Entity-level business analytics (Which restaurants have highest cancellation rates?)
10. Data-backed business recommendations (Ways to improve customer retention)
11. Decision Simulator integration (What happens if delivery time decreases by 10%?)
12. Multi-turn conversation memory with follow-up resolution
13. Arbitrary unseen question outside business domain (How does GPS work?)
14. Transparent behavior when API key is unconfigured
15. Resilient error handling when provider encounters failure
"""

import sys
import unittest
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from python.ai.analyst.orchestrator import AskNovaNestOrchestrator, analyze_business_inquiry
from python.ai.analyst.universal_router import classify_query
from python.ai.analyst.universal_engine import compute_calculation, get_offline_knowledge_response
from python.ai.analyst.conversation_manager import reset_session, get_session_history
from python.ai.provider.mock_provider import MockAIProvider


class UniversalAITestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orchestrator = AskNovaNestOrchestrator()
        # Ensure we test with local offline provider for deterministic test suite
        # (per prompt: "Do not make paid API calls during automated tests unless explicitly configured")
        cls.mock_provider = MockAIProvider()

    def setUp(self):
        # Reset conversation manager state for clean isolated testing
        from python.ai.analyst.conversation_manager import _SESSIONS
        _SESSIONS.clear()

    # -------------------------------------------------------------
    # 1. Greetings and casual conversation
    # -------------------------------------------------------------
    def test_01_greeting_and_casual_conversation(self):
        query = "Hi, how are you?"
        resp = self.orchestrator.process_query(query, session_id="test-greeting", ai_provider=self.mock_provider)
        
        self.assertEqual(resp["route"], "GREETING")
        self.assertIn("NovaNest", resp["answer"])
        self.assertEqual(len(resp["verified_metrics"]), 0, "Greetings must not inject business KPI cards")
        self.assertFalse(resp["requires_business_data"])
        self.assertIn(resp["provider_status"], ["ready", "mock"])

    # -------------------------------------------------------------
    # 2. Conceptual explanation (ML in simple words)
    # -------------------------------------------------------------
    def test_02_explain_machine_learning_simple_words(self):
        query = "Explain machine learning in simple words."
        resp = self.orchestrator.process_query(query, session_id="test-ml", ai_provider=self.mock_provider)
        
        self.assertIn(resp["route"], ["GENERAL", "CONCEPTUAL"])
        self.assertIn("Machine Learning", resp["answer"])
        self.assertIn("pattern", resp["answer"].lower())
        self.assertEqual(len(resp["verified_metrics"]), 0, "General knowledge must not query or display business metrics")
        self.assertFalse(resp["requires_business_data"])

    # -------------------------------------------------------------
    # 3. Technical comparison (SQL vs NoSQL)
    # -------------------------------------------------------------
    def test_03_sql_vs_nosql_comparison(self):
        query = "What is the difference between SQL and NoSQL?"
        resp = self.orchestrator.process_query(query, session_id="test-sql-nosql", ai_provider=self.mock_provider)
        
        self.assertIn(resp["route"], ["PROGRAMMING", "TECHNICAL_COMPARISON", "GENERAL"])
        self.assertIn("SQL", resp["answer"])
        self.assertIn("NoSQL", resp["answer"])
        self.assertIn("|", resp["answer"], "Should provide a markdown table comparison")
        self.assertEqual(len(resp["verified_metrics"]), 0, "Technical concept question must not query business database")

    # -------------------------------------------------------------
    # 4. Code generation (Python average of a list)
    # -------------------------------------------------------------
    def test_04_python_program_average_of_list(self):
        query = "Write a Python program to calculate the average of a list."
        resp = self.orchestrator.process_query(query, session_id="test-code", ai_provider=self.mock_provider)
        
        # Must NOT be intercepted by NL2SQL just because it contains the word "average" or "list"
        self.assertEqual(resp["route"], "PROGRAMMING")
        self.assertIn("```python", resp["answer"])
        self.assertIn("def calculate_average", resp["answer"])
        self.assertIn("sum(", resp["answer"])
        self.assertFalse(resp["requires_business_data"], "Programming questions must not query MySQL")
        self.assertEqual(len(resp["verified_metrics"]), 0)

    # -------------------------------------------------------------
    # 5. Math / Algorithmic explanation (Cosine similarity)
    # -------------------------------------------------------------
    def test_05_explain_cosine_similarity(self):
        query = "Explain cosine similarity with an example."
        resp = self.orchestrator.process_query(query, session_id="test-cosine", ai_provider=self.mock_provider)
        
        self.assertIn(resp["route"], ["MATHEMATICS", "PROGRAMMING", "GENERAL"])
        self.assertIn("Cosine Similarity", resp["answer"])
        self.assertTrue("dot product" in resp["answer"].lower() or "formula" in resp["answer"].lower())
        self.assertEqual(len(resp["verified_metrics"]), 0)

    # -------------------------------------------------------------
    # 6. Exact Programmatic Calculation (Compound interest)
    # -------------------------------------------------------------
    def test_06_calculate_compound_interest(self):
        query = "Calculate compound interest on 2000 at 20% for 2 years."
        resp = self.orchestrator.process_query(query, session_id="test-calc", ai_provider=self.mock_provider)
        
        self.assertEqual(resp["route"], "CALCULATION")
        # Formula: A = 2000 * (1 + 0.20)^2 = 2000 * 1.44 = 2880
        # CI = 2880 - 2000 = 880
        self.assertIn("880", resp["answer"])
        self.assertIn("2,880", resp["answer"])
        self.assertIn("A = P", resp["answer"])
        self.assertEqual(len(resp["verified_metrics"]), 0, "Math calculation must not query restaurant database")

    # -------------------------------------------------------------
    # 7. Grounded Business Data (Total revenue)
    # -------------------------------------------------------------
    def test_07_grounded_total_revenue(self):
        query = "What is our total revenue?"
        resp = self.orchestrator.process_query(query, session_id="test-rev", ai_provider=self.mock_provider)
        
        self.assertIn(resp["route"], ["BUSINESS_DATA", "EXECUTIVE_OVERVIEW"])
        self.assertTrue(resp["requires_business_data"])
        self.assertGreater(len(resp["verified_metrics"]), 0, "Must contain verified business metrics")
        
        # Compute authoritative certified GMV (KPI-01) and Net Revenue (KPI-02) from source data
        import json
        import pandas as pd

        orders_df = pd.read_csv(PROJECT_ROOT / "datasets" / "cleaned" / "orders.csv")
        expected_gmv = float(orders_df[orders_df["order_status"] != "Cancelled"]["order_amount"].sum())
        expected_net_rev = float(orders_df[orders_df["order_status"] == "Delivered"]["final_amount"].sum())
        expected_gmv_cr = f"₹{expected_gmv / 10_000_000:.2f} Cr"
        expected_net_rev_cr = f"₹{expected_net_rev / 10_000_000:.2f} Cr"

        kpi_defs_path = PROJECT_ROOT / "datasets" / "analytics" / "kpi_definitions.json"
        if kpi_defs_path.exists():
            kpi_defs = json.loads(kpi_defs_path.read_text(encoding="utf-8"))
            self.assertAlmostEqual(expected_gmv, float(kpi_defs["KPI-01"]["value"]), places=2)
            self.assertAlmostEqual(expected_net_rev, float(kpi_defs["KPI-02"]["value"]), places=2)

        metric_map = {m.get("label", m.get("metric", "")): str(m["value"]) for m in resp["verified_metrics"]}
        self.assertTrue(any("Revenue" in name or "GMV" in name for name in metric_map))
        self.assertIn(expected_gmv_cr, metric_map.values(), f"Grounded GMV must equal certified {expected_gmv_cr}")
        self.assertIn(expected_net_rev_cr, metric_map.values(), f"Grounded Net Revenue must equal certified {expected_net_rev_cr}")
        self.assertIsNotNone(resp["provenance"])

    # -------------------------------------------------------------
    # 8. Root Cause Analysis (Why are cancellations increasing?)
    # -------------------------------------------------------------
    def test_08_root_cause_cancellations(self):
        query = "Why are cancellations increasing?"
        resp = self.orchestrator.process_query(query, session_id="test-rca", ai_provider=self.mock_provider)
        
        self.assertEqual(resp["route"], "ROOT_CAUSE")
        self.assertTrue(resp["requires_business_data"])
        self.assertIsNotNone(resp["root_cause_analysis"])
        self.assertGreater(len(resp["root_cause_analysis"]["contributing_factors"]), 0)
        self.assertIn("cancellation", resp["answer"].lower())

    # -------------------------------------------------------------
    # 9. Entity-level business analytics (Highest cancellation rates)
    # -------------------------------------------------------------
    def test_09_restaurants_highest_cancellation_rates(self):
        query = "Which restaurants have the highest cancellation rates?"
        resp = self.orchestrator.process_query(query, session_id="test-rest-canc", ai_provider=self.mock_provider)
        
        self.assertIn(resp["route"], ["BUSINESS_DATA", "NL2SQL"])
        self.assertTrue(resp["requires_business_data"])
        self.assertGreater(len(resp["verified_metrics"]), 0)
        self.assertGreater(len(resp["data_rows"]), 0, "Must return data rows with actual restaurant records")

    # -------------------------------------------------------------
    # 10. Data-backed business recommendations (Improve customer retention)
    # -------------------------------------------------------------
    def test_10_suggest_ways_to_improve_retention(self):
        query = "Suggest ways to improve customer retention."
        resp = self.orchestrator.process_query(query, session_id="test-rec", ai_provider=self.mock_provider)
        
        self.assertEqual(resp["route"], "RECOMMENDATIONS")
        self.assertGreater(len(resp["recommendations"]), 0, "Must provide structured recommendations")
        self.assertTrue(any("churn" in r["title"].lower() or "retention" in r["title"].lower() or "loyalty" in r["title"].lower() for r in resp["recommendations"]))

    # -------------------------------------------------------------
    # 11. Decision Simulator integration (Delivery time decrease 10%)
    # -------------------------------------------------------------
    def test_11_decision_simulator_delivery_time(self):
        query = "What happens if delivery time decreases by 10%?"
        resp = self.orchestrator.process_query(query, session_id="test-sim", ai_provider=self.mock_provider)
        
        self.assertEqual(resp["route"], "SIMULATION")
        self.assertIsNotNone(resp["simulation_results"])
        self.assertTrue("Decision Simulation" in resp["answer"] or "Revenue Impact" in resp["answer"])
        self.assertGreater(len(resp["simulation_results"]["comparison_data"]), 0)

    # -------------------------------------------------------------
    # 12. Multi-turn conversation memory with follow-up resolution
    # -------------------------------------------------------------
    def test_12_multi_turn_conversation_memory(self):
        session_id = "test-session-multiturn-12"
        
        # Turn 1: "What is our cancellation rate?"
        resp1 = self.orchestrator.process_query("What is our cancellation rate?", session_id=session_id, ai_provider=self.mock_provider)
        self.assertTrue(resp1["requires_business_data"])
        self.assertTrue("4.16" in resp1["answer"] or "cancellation" in resp1["answer"].lower())
        
        # Turn 2: "Which restaurant has the highest rate?"
        # Assistant must understand "rate" means cancellation rate from turn 1
        resp2 = self.orchestrator.process_query("Which restaurant has the highest rate?", session_id=session_id, ai_provider=self.mock_provider)
        self.assertTrue(resp2["requires_business_data"])
        self.assertIn("restaurant", resp2["answer"].lower())
        self.assertTrue("cancellation" in resp2.get("resolved_query", "").lower() or len(resp2["data_rows"]) > 0)
        
        # Turn 3: "How can we improve it?"
        resp3 = self.orchestrator.process_query("How can we improve it?", session_id=session_id, ai_provider=self.mock_provider)
        self.assertIn("recommend", resp3["answer"].lower())
        
        # Turn 4: Clear topic change - "What is Python?"
        # Must NOT retain cancellation intent or query business database!
        resp4 = self.orchestrator.process_query("What is Python?", session_id=session_id, ai_provider=self.mock_provider)
        self.assertFalse(resp4["requires_business_data"], "Topic shift to Python must not query business data")
        self.assertEqual(len(resp4["verified_metrics"]), 0)
        self.assertIn("Python", resp4["answer"])

    # -------------------------------------------------------------
    # 13. Arbitrary unseen question outside business domain
    # -------------------------------------------------------------
    def test_13_arbitrary_unseen_question_gps(self):
        query = "How does GPS work?"
        resp = self.orchestrator.process_query(query, session_id="test-gps", ai_provider=self.mock_provider)
        
        self.assertEqual(resp["route"], "GENERAL")
        self.assertFalse(resp["requires_business_data"])
        self.assertEqual(len(resp["verified_metrics"]), 0)
        self.assertIn("satellite", resp["answer"].lower())
        self.assertNotIn("Please choose from predefined questions", resp["answer"])

    # -------------------------------------------------------------
    # 14. Transparent behavior when API key is missing / unconfigured
    # -------------------------------------------------------------
    def test_14_unconfigured_ai_provider_transparency(self):
        from python.ai.provider.gemini_provider import GeminiAIProvider
        
        # Instantiate with no key
        unconfigured_provider = GeminiAIProvider(api_key="")
        status = unconfigured_provider.get_status()
        self.assertEqual(status["status"], "unconfigured")
        self.assertIn("Missing GEMINI_API_KEY", status["message"])
        
        # Process a general query with unconfigured provider
        resp = self.orchestrator.process_query("Explain quantum computing", session_id="test-unconf", ai_provider=unconfigured_provider)
        self.assertEqual(resp["provider_status"], "unconfigured")
        # Universal engine provides high quality fallback synthesis while clearly reporting status
        self.assertTrue(len(resp["answer"]) > 50)
        self.assertIn("quantum", resp["answer"].lower())

    # -------------------------------------------------------------
    # 15. Resilient error handling when provider encounters failure
    # -------------------------------------------------------------
    def test_15_provider_error_handling(self):
        class BrokenProvider:
            provider_name = "failing-provider"
            model_name = "failing-model"
            
            def get_status(self):
                return {"status": "error", "message": "Simulated upstream provider outage"}
                
            def generate_response(self, prompt, **kwargs):
                raise RuntimeError("503 Upstream Service Unavailable")
                
            def chat(self, messages, **kwargs):
                raise RuntimeError("503 Upstream Service Unavailable")

        broken = BrokenProvider()
        resp = self.orchestrator.process_query("What is the difference between SQL and NoSQL?", session_id="test-broken", ai_provider=broken)
        
        # Must not crash, must return clean response with error status indicated
        self.assertEqual(resp["provider_status"], "error")
        self.assertIn("SQL", resp["answer"])
        self.assertIn("NoSQL", resp["answer"])
        self.assertIn("|", resp["answer"])


if __name__ == "__main__":
    unittest.main()
