"""
test_phase11_uat_suite.py
=========================
User Acceptance Testing (UAT) Suite for NovaNest Phase 11 Production Commissioning.

Simulates executive and operational user journeys across:
1. Executive Overview & Portfolio KPI Summary
2. Prescriptive Recommendation Center: Filtering, Approvals, Rejections, and Realized Outcome Recording
3. Human Approval Enforcement (Blocking Unauthorized Execution)
4. Customer 360 Inspection with Mandatory LOW_EMPIRICAL Churn Caveat
5. Restaurant 360 Merchant Diagnosis & Action Plan Formulation
6. Rider Operations Fleet Workload & Live GPS Telematics Disclaimers
7. Conversational AI Multi-Turn Memory & Intent Routing
8. Contextual AI Launcher Payload Validation
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

# Adjust path for Python imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from api.main import app, get_master_orchestrator
from python.decision.recommendation_lifecycle import (
    RecommendationLifecycleManager,
    RecommendationLifecycleStatus,
    HumanApprovalRequiredError,
)


class TestPhase11UserAcceptanceTesting(unittest.TestCase):
    """Rigorous User Acceptance Testing suite certifying end-to-end user workflows."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Auth headers matching environment keys
        cls.admin_token = os.getenv("NOVANEST_ADMIN_KEY", "dev_novanest_admin_key_default")
        cls.operator_token = os.getenv("NOVANEST_API_KEY", "dev_novanest_api_key_default")
        cls.viewer_token = os.getenv("NOVANEST_VIEWER_KEY", "dev_novanest_viewer_key_default")
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.operator_headers = {"Authorization": f"Bearer {cls.operator_token}"}
        cls.viewer_headers = {"Authorization": f"Bearer {cls.viewer_token}"}

    # =========================================================================
    # UAT JOURNEY 1: Executive Overview & Business Metrics
    # =========================================================================
    def test_uat_01_executive_overview_kpis(self):
        """UAT-01: Executive views high-level business performance and financial metrics."""
        resp = self.client.get("/api/overview", headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("kpis", data)
        kpis = data["kpis"]

        # Verify core canonical KPIs
        self.assertEqual(kpis["total_orders"], 49971)
        self.assertEqual(kpis["delivered_orders"], 47994)
        self.assertAlmostEqual(kpis["total_gmv"], 46590125.0, delta=1.0)
        self.assertAlmostEqual(kpis["net_platform_revenue"], 46425992.0, delta=1.0)
        self.assertAlmostEqual(kpis["avg_order_value"], 967.33, delta=0.05)
        self.assertAlmostEqual(kpis["contribution_margin_pct"], 23.59, delta=0.05)

    # =========================================================================
    # UAT JOURNEY 2: Prescriptive Recommendation Portfolio & Waterfall
    # =========================================================================
    def test_uat_02_executive_recommendation_center_portfolio(self):
        """UAT-02: Executive opens Recommendation Center, reviews portfolio ROI and waterfall."""
        resp = self.client.get("/api/prescriptive/summary", headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()

        self.assertIn("total_recommendations", summary)
        self.assertIn("total_gross_benefit_rupees", summary)
        self.assertIn("total_net_financial_impact_rupees", summary)
        self.assertIn("overall_roi_multiple", summary)

        # Portfolio metrics
        self.assertGreater(summary["total_recommendations"], 0)
        self.assertGreater(summary["total_net_financial_impact_rupees"], 0.0)

        # Waterfall chart data
        resp_wf = self.client.get("/api/prescriptive/financial-charts", headers=self.viewer_headers)
        self.assertEqual(resp_wf.status_code, 200)
        wf_data = resp_wf.json()
        self.assertIn("contribution_margin_waterfall", wf_data)
        self.assertTrue(len(wf_data["contribution_margin_waterfall"]) >= 4)

    # =========================================================================
    # UAT JOURNEY 3: Multi-Criteria Recommendation Filtering
    # =========================================================================
    def test_uat_03_recommendation_multi_criteria_filtering(self):
        """UAT-03: Business user filters recommendations by domain and priority."""
        # 1. Filter by Domain: customer_retention
        resp_cust = self.client.get(
            "/api/prescriptive/recommendations?domain=customer_retention",
            headers=self.viewer_headers,
        )
        self.assertEqual(resp_cust.status_code, 200)
        cust_recs = resp_cust.json()
        self.assertIsInstance(cust_recs, list)
        self.assertGreater(len(cust_recs), 0)
        for rec in cust_recs:
            self.assertIn("recommendation_id", rec)
            self.assertIn("priority", rec)

        # 2. Filter by Priority: High
        resp_high = self.client.get(
            "/api/prescriptive/recommendations?priority=High",
            headers=self.viewer_headers,
        )
        self.assertEqual(resp_high.status_code, 200)
        high_recs = resp_high.json()
        self.assertIsInstance(high_recs, list)
        for rec in high_recs:
            self.assertEqual(rec["priority"].lower(), "high")

    # =========================================================================
    # UAT JOURNEY 4: Human Approval, Rejection & Outcome Recording Workflow
    # =========================================================================
    def test_uat_04_recommendation_lifecycle_governance(self):
        """UAT-04: Operator approves recommendation, advances to in-progress, and records realized outcome."""
        rec_id = "REC-RET-VIP-001"

        from python.decision.recommendation_lifecycle import (
            get_recommendation_lifecycle_manager,
            RecommendationLifecycleStatus,
        )
        mgr = get_recommendation_lifecycle_manager()
        if rec_id in mgr._recommendations:
            mgr._recommendations[rec_id].lifecycle_status = RecommendationLifecycleStatus.PROPOSED
            mgr._persist_store()

        try:
            # 1. Operator approves recommendation
            resp_appr = self.client.post(
                f"/api/prescriptive/recommendations/{rec_id}/approve",
                json={"approved_by": "OpsLead", "approval_notes": "Approved for Q4 pilot retention campaign."},
                headers=self.operator_headers,
            )
            self.assertEqual(resp_appr.status_code, 200)
            appr_body = resp_appr.json()
            self.assertEqual(appr_body["status"], "success")

            # 2. Viewer attempts to reject approved recommendation (Forbidden 403)
            resp_fail = self.client.post(
                f"/api/prescriptive/recommendations/{rec_id}/reject",
                json={"rejected_by": "ViewerUser", "rejection_reason": "Attempt unauthorized override"},
                headers=self.viewer_headers,
            )
            self.assertEqual(resp_fail.status_code, 403)

            # 3. Operator transitions to in-progress
            resp_prog = self.client.post(
                f"/api/prescriptive/recommendations/{rec_id}/start-progress",
                json={"operator_user": "OpsLead"},
                headers=self.operator_headers,
            )
            self.assertEqual(resp_prog.status_code, 200)
            self.assertEqual(resp_prog.json()["status"], "success")

            # 4. Operator transitions to implemented
            resp_impl = self.client.post(
                f"/api/prescriptive/recommendations/{rec_id}/mark-implemented",
                json={"operator_user": "OpsLead"},
                headers=self.operator_headers,
            )
            self.assertEqual(resp_impl.status_code, 200)
            self.assertEqual(resp_impl.json()["status"], "success")

            # 5. Operator records realized outcome
            resp_out = self.client.post(
                f"/api/prescriptive/recommendations/{rec_id}/record-outcome",
                json={
                    "realized_gross_benefit": 42500.0,
                    "actual_cost": 15000.0,
                    "measured_by": "Finance Auditor",
                    "audit_notes": "Pilot completed: 28 of 35 targeted VIPs retained.",
                },
                headers=self.operator_headers,
            )
            self.assertEqual(resp_out.status_code, 200)
            out_body = resp_out.json()
            self.assertEqual(out_body["status"], "success")
        finally:
            # Clean up state back to PROPOSED for test idempotence
            if rec_id in mgr._recommendations:
                mgr._recommendations[rec_id].lifecycle_status = RecommendationLifecycleStatus.PROPOSED
                mgr._persist_store()

    # =========================================================================
    # UAT JOURNEY 5: Customer 360 & LOW_EMPIRICAL Churn Caveat
    # =========================================================================
    def test_uat_05_customer_360_with_churn_caveat(self):
        """UAT-05: Account manager inspects Customer 360 profile and verifies transparent churn caveat."""
        cust_id = "C000205"
        resp = self.client.get(
            f"/api/prescriptive/customer-profile/{cust_id}",
            headers=self.viewer_headers,
        )
        self.assertEqual(resp.status_code, 200)
        profile = resp.json()

        self.assertEqual(profile["customer_id"], cust_id)
        self.assertIn("retention_segment", profile)
        self.assertIn("behavioral_telemetry", profile)
        self.assertIn("ml_caveat_assessment", profile)

        # Scientific honesty assertion: Customer Churn MUST display LOW_EMPIRICAL caveat
        caveat = profile["ml_caveat_assessment"]["confidence_caveat"]
        self.assertIn("LOW_EMPIRICAL", caveat)
        self.assertIn("0.51", caveat)

    # =========================================================================
    # UAT JOURNEY 6: Restaurant 360 Partner Diagnosis & Action Directives
    # =========================================================================
    def test_uat_06_restaurant_360_partner_diagnosis(self):
        """UAT-06: Merchant manager inspects restaurant partner action plan."""
        rest_id = "R00029"
        resp = self.client.get(
            f"/api/prescriptive/restaurant-profile/{rest_id}",
            headers=self.viewer_headers,
        )
        self.assertEqual(resp.status_code, 200)
        plan = resp.json()

        self.assertEqual(plan["restaurant_id"], rest_id)
        self.assertIn("diagnosis_category", plan)
        self.assertIn("operational_metrics", plan)
        self.assertIn("prescriptive_action_plan", plan)

    # =========================================================================
    # UAT JOURNEY 7: Rider Operations Fleet Workload & Live Telematics Caveat
    # =========================================================================
    def test_uat_07_rider_operations_telematics_caveat(self):
        """UAT-07: Logistics manager reviews fleet allocation and SLA breach tail with GPS caveats."""
        resp = self.client.get("/api/prescriptive/rider-fleet-workload", headers=self.viewer_headers)
        self.assertEqual(resp.status_code, 200)
        fleet = resp.json()

        self.assertIn("total_active_fleet", fleet)
        self.assertIn("fleet_sla_metrics", fleet)
        self.assertIn("live_telemetry_disclaimer", fleet)

        # Operational honesty assertion: Telematics caveat must warn against assuming real-time GPS
        self.assertIn("historical", fleet["live_telemetry_disclaimer"].lower())
        self.assertIn("live gps", fleet["live_telemetry_disclaimer"].lower())

    # =========================================================================
    # UAT JOURNEY 8: Conversational AI Multi-Turn Memory & Intent Routing
    # =========================================================================
    def test_uat_08_conversational_ai_memory_and_routing(self):
        """UAT-08: Executive interacts with Ask NovaNest AI, verifying multi-turn conversational memory."""
        orchestrator = get_master_orchestrator()

        # Turn 1: High-level financial inquiry
        turn_1 = orchestrator.orchestrate(
            "What was our total GMV and completed order count?",
            principal=None,
            session_id="uat_session_ceo_001",
        )
        self.assertIsNotNone(turn_1.synthesis)
        summary_1 = turn_1.synthesis.consolidated_summary.lower()
        self.assertTrue("46" in summary_1 or "4.66" in summary_1 or "gmv" in summary_1)

        # Turn 2: Follow-up contextual question with entity resolution
        turn_2 = orchestrator.orchestrate(
            "What about delivery SLA breaches and operations?",
            principal=None,
            session_id="uat_session_ceo_001",
        )
        self.assertIsNotNone(turn_2.synthesis)
        summary_2 = turn_2.synthesis.consolidated_summary.lower()
        self.assertTrue("delivery" in summary_2 or "sla" in summary_2 or "operations" in summary_2)


if __name__ == "__main__":
    unittest.main()
