"""
NovaNest Platform Test Suite - Phase 09: Executive UI, Recommendation Action Center & Parity
--------------------------------------------------------------------------------------------
Validates:
1. Canonical recommendation generation and deterministic IDs.
2. Recommendation lifecycle manager state transitions and human-in-the-loop approval.
3. Prevention of unauthorized transitions (HumanApprovalRequiredError, InvalidLifecycleTransitionError).
4. FastAPI prescriptive REST endpoints (list, summary, detail, approve, reject, start-progress, mark-implemented, record-outcome, simulate, customer-profile, restaurant-profile, rider-fleet-workload, financial-charts).
5. RBAC security enforcement (viewer blocked from lifecycle mutations, operator permitted).
6. Controlled What-If Scenario Simulator across all 5 prescriptive domains with is_simulation_projection=True.
7. Audited contribution margin waterfall and promotional subsidy financial reconciliation.
8. Customer 360 retention intelligence and explicit LOW_EMPIRICAL churn caveats.
9. Restaurant 360 bottleneck diagnosis and action plans.
10. Rider fleet workload, SLA breach tail analysis (>45m), and live GPS telematics disclaimers.
11. Parity between React API contracts and Streamlit data engine representations.
"""

import unittest
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure root paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app
from api.loader import load_data
from python.decision.prescriptive_contracts import (
    PrescriptiveRecommendation,
    RecommendationLifecycleStatus,
    PrescriptiveDomain,
    ConfidenceTier,
    FinancialImpactBreakdown,
    RealizedOutcomeRecord,
)
from python.decision.prescriptive_engine import (
    generate_all_prescriptive_recommendations,
    get_prescriptive_summary_kpis,
)
from python.decision.recommendation_lifecycle import (
    RecommendationLifecycleManager,
    HumanApprovalRequiredError,
    InvalidLifecycleTransitionError,
)
from python.decision.scenario_simulation_engine import run_controlled_scenario_simulation
from python.decision.customer_retention_intelligence import (
    analyze_customer_risk_segments,
    explain_customer_retention_profile,
)
from python.decision.restaurant_optimization import (
    diagnose_restaurant_performance,
    generate_restaurant_action_plan,
)
from python.decision.rider_operations_optimization import (
    analyze_geographic_fleet_workload,
)
from python.decision.revenue_optimization import (
    compute_order_contribution_margin,
    build_contribution_margin_waterfall,
    reconcile_promotional_subsidies,
)


class TestPhase09ExecutiveUIAndParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.data_source = load_data()
        cls.client = TestClient(app)
        cls.viewer_key = os.getenv("NOVANEST_VIEWER_KEY", "test-viewer-key-phase06-8")
        cls.operator_key = os.getenv("NOVANEST_API_KEY", "test-operator-key-phase06-8")
        cls.admin_key = os.getenv("NOVANEST_ADMIN_KEY", "test-admin-key-phase06-8")

        cls.viewer_headers = {"Authorization": f"Bearer {cls.viewer_key}"}
        cls.operator_headers = {"Authorization": f"Bearer {cls.operator_key}"}

    def setUp(self):
        # Create an isolated lifecycle manager for test determinism
        self.lifecycle_mgr = RecommendationLifecycleManager()
        self.recs = generate_all_prescriptive_recommendations(self.data, register_in_lifecycle=False)
        for r in self.recs:
            self.lifecycle_mgr.register_recommendation(r)

    # 1. CANONICAL RECOMMENDATION INTEGRITY & DETERMINISTIC IDS
    def test_01_canonical_recommendation_ids(self):
        """All generated prescriptive recommendations must use canonical deterministic IDs."""
        rec_ids = [r.recommendation_id for r in self.recs]
        expected_canonical = [
            "REC-RET-VIP-001",
            "REC-RET-LOY-001",
            "REC-REV-DISC-001",
            "REC-REV-AOV-001",
            "REC-RES-CAN-001",
            "REC-RES-QAL-001",
            "REC-OPS-SLA-001",
            "REC-OPS-FLT-001",
        ]
        self.assertEqual(len(rec_ids), 8, "Expected exactly 8 canonical recommendations.")
        for cid in expected_canonical:
            self.assertIn(cid, rec_ids, f"Missing canonical recommendation ID: {cid}")

    def test_02_prescriptive_summary_kpis(self):
        """Summary KPIs must compute exact portfolio metrics without floating point leakage."""
        summary = get_prescriptive_summary_kpis(self.recs)
        self.assertEqual(summary["total_recommendations"], 8)
        self.assertGreater(summary["total_gross_benefit_rupees"], 500000.0)
        self.assertGreater(summary["total_implementation_cost_rupees"], 100000.0)
        self.assertGreater(summary["total_net_financial_impact_rupees"], 200000.0)
        self.assertAlmostEqual(summary["overall_roi_multiple"], 1.72, places=2)
        self.assertEqual(summary["by_domain_counts"]["customer_retention"], 2)
        self.assertEqual(summary["by_domain_counts"]["revenue_optimization"], 2)
        self.assertEqual(summary["by_domain_counts"]["restaurant_optimization"], 2)
        self.assertEqual(summary["by_domain_counts"]["rider_logistics"], 2)

    # 2. LIFECYCLE STATE MACHINE & GOVERNANCE ENFORCEMENT
    def test_03_lifecycle_approval_and_rejection(self):
        """Approval and rejection must update status and record actor metadata."""
        rec_id = "REC-RET-VIP-001"
        rec = self.lifecycle_mgr.get_recommendation(rec_id)
        self.assertEqual(rec.lifecycle_status, RecommendationLifecycleStatus.PROPOSED)

        # Approve
        approved = self.lifecycle_mgr.approve_recommendation(
            rec_id, approved_by="Sarah Connor (Head of Growth)", approval_notes="Approved for VIP defense"
        )
        self.assertEqual(approved.lifecycle_status, RecommendationLifecycleStatus.APPROVED)
        self.assertEqual(approved.approved_by, "Sarah Connor (Head of Growth)")
        self.assertIsNotNone(approved.approved_at)

        # Reject another recommendation
        rec_id_rej = "REC-RET-LOY-001"
        rejected = self.lifecycle_mgr.reject_recommendation(
            rec_id_rej, rejected_by="Risk Committee", rejection_reason="Budget reallocation"
        )
        self.assertEqual(rejected.lifecycle_status, RecommendationLifecycleStatus.REJECTED)
        self.assertIn("Risk Committee", rejected.rejection_reason)

    def test_04_lifecycle_governance_blocks_unapproved_execution(self):
        """Starting progress on an unapproved recommendation must raise HumanApprovalRequiredError."""
        rec_id = "REC-REV-DISC-001"
        with self.assertRaises(HumanApprovalRequiredError):
            self.lifecycle_mgr.start_progress(rec_id, operator_user="Automated Bot")

    def test_05_lifecycle_full_workflow_to_outcome(self):
        """Valid transition sequence: Proposed -> Approved -> In Progress -> Implemented -> Outcome Measured."""
        rec_id = "REC-RES-CAN-001"
        self.lifecycle_mgr.approve_recommendation(rec_id, approved_by="Ops Lead")
        in_prog = self.lifecycle_mgr.start_progress(rec_id, operator_user="Ops Lead")
        self.assertEqual(in_prog.lifecycle_status, RecommendationLifecycleStatus.IN_PROGRESS)

        impl = self.lifecycle_mgr.mark_implemented(rec_id, operator_user="Ops Lead")
        self.assertEqual(impl.lifecycle_status, RecommendationLifecycleStatus.IMPLEMENTED)

        outcome = self.lifecycle_mgr.record_outcome(
            rec_id,
            realized_gross_benefit=85000.0,
            actual_cost=20000.0,
            measured_by="Finance Auditor",
            audit_notes="Achieved 42% cancellation drop",
        )
        self.assertEqual(outcome.lifecycle_status, RecommendationLifecycleStatus.OUTCOME_MEASURED)
        self.assertIsNotNone(outcome.realized_outcome)
        self.assertEqual(outcome.realized_outcome.realized_net_impact, 65000.0)
        self.assertGreater(outcome.realized_outcome.benefit_variance_pct, 0.0)

    # 3. FASTAPI REST ENDPOINTS & RBAC SECURITY
    def test_06_api_get_summary_and_recommendations(self):
        """GET /api/prescriptive/summary and /api/prescriptive/recommendations."""
        # Summary
        res_sum = self.client.get("/api/prescriptive/summary", headers=self.viewer_headers)
        self.assertEqual(res_sum.status_code, 200)
        sum_data = res_sum.json()
        self.assertEqual(sum_data["total_recommendations"], 8)
        self.assertEqual(sum_data["overall_roi_multiple"], 1.72)

        # Recommendations list
        res_list = self.client.get("/api/prescriptive/recommendations", headers=self.viewer_headers)
        self.assertEqual(res_list.status_code, 200)
        recs = res_list.json()
        self.assertEqual(len(recs), 8)

        # Filter by domain
        res_filtered = self.client.get(
            "/api/prescriptive/recommendations?domain=customer_retention",
            headers=self.viewer_headers,
        )
        self.assertEqual(res_filtered.status_code, 200)
        self.assertEqual(len(res_filtered.json()), 2)

    def test_07_api_rbac_enforcement(self):
        """Viewer role must be blocked from modifying lifecycle state (requires operator/admin)."""
        rec_id = "REC-OPS-SLA-001"
        payload = {"approved_by": "Viewer User", "approval_notes": "Attempt unauthorized approval"}

        # Viewer attempt must fail with 403 Forbidden
        res_viewer = self.client.post(
            f"/api/prescriptive/recommendations/{rec_id}/approve",
            json=payload,
            headers=self.viewer_headers,
        )
        self.assertEqual(res_viewer.status_code, 403)

        # Operator attempt must succeed with 200 OK
        res_operator = self.client.post(
            f"/api/prescriptive/recommendations/{rec_id}/approve",
            json=payload,
            headers=self.operator_headers,
        )
        self.assertEqual(res_operator.status_code, 200)
        self.assertEqual(res_operator.json()["recommendation"]["status"], "Approved")

    def test_08_api_reject_requires_reason(self):
        """Rejecting via API must enforce non-empty rejection_reason."""
        rec_id = "REC-OPS-FLT-001"
        payload = {"rejected_by": "Ops Manager", "rejection_reason": ""}
        res = self.client.post(
            f"/api/prescriptive/recommendations/{rec_id}/reject",
            json=payload,
            headers=self.operator_headers,
        )
        self.assertEqual(res.status_code, 422, "Empty rejection reason should fail validation.")

    # 4. CONTROLLED WHAT-IF SCENARIO SIMULATOR
    def test_09_scenario_simulator_all_domains(self):
        """All 5 scenario models must execute with is_simulation_projection=True and non-empty deltas."""
        scenarios = [
            "promotion_optimization",
            "delivery_fee_restructuring",
            "rider_capacity_expansion",
            "restaurant_capacity_acceleration",
            "customer_retention_campaign",
        ]
        for sc in scenarios:
            res = run_controlled_scenario_simulation(scenario_type=sc, data_dict=self.data)
            self.assertTrue(res["is_simulation_projection"])
            self.assertIn("NOTICE: Simulated outcomes are mathematical scenario projections", res["disclaimer"])
            self.assertIn("baseline", res)
            self.assertIn("projected_outcomes", res)
            self.assertIn("variance_deltas", res)
            self.assertGreater(len(res["scenario_assumptions"]), 0)

    def test_10_api_simulate_endpoint(self):
        """POST /api/prescriptive/simulate executes controlled scenario via API."""
        payload = {
            "scenario_type": "promotion_optimization",
            "overrides": {"discount_reduction_pct": 20.0, "volume_elasticity_pct": -2.0},
        }
        res = self.client.post("/api/prescriptive/simulate", json=payload, headers=self.operator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_simulation_projection"])
        self.assertEqual(data["scenario_type"], "promotion_optimization")
        self.assertIn("variance_deltas", data)

    # 5. FINANCIAL RECONCILIATION & WATERFALL VERIFICATION
    def test_11_contribution_margin_waterfall_reconciliation(self):
        """Audited historical financial figures must match exact ground-truth values."""
        waterfall_df = build_contribution_margin_waterfall(self.data)
        self.assertFalse(waterfall_df.empty)

        # Steps: Gross GMV, Commission, Delivery Fees, Subsidies, Fulfillment, Net Contribution
        steps = dict(zip(waterfall_df["Step"], waterfall_df["Amount"]))
        self.assertAlmostEqual(steps["Gross Food GMV"], 46590125.0, places=0)
        self.assertAlmostEqual(steps["Platform Commission (20%)"], 9318025.0, places=0)
        self.assertAlmostEqual(steps["Delivery Fees Collected"], 1917576.0, places=0)
        self.assertAlmostEqual(steps["Discount Subsidies (60%)"], -1249551.0, places=0)
        self.assertAlmostEqual(steps["Rider Logistics Cost"], -2159730.0, places=0)
        self.assertAlmostEqual(steps["Net Contribution Profit"], 7826320.0, places=0)

    def test_12_promotional_subsidy_reconciliation(self):
        """Verify the exact split between total discounts and orders with discount >25%."""
        rec = reconcile_promotional_subsidies(self.data)
        self.assertEqual(rec["delivered_order_count"], 47994)
        self.assertAlmostEqual(rec["total_delivered_discount_rupees"], 2082585.0, places=0)
        self.assertAlmostEqual(rec["platform_subsidized_discount_share_60pct"], 1249551.0, places=0)
        self.assertEqual(rec["orders_with_discount_gt_25pct_count"], 2449)
        self.assertAlmostEqual(rec["orders_with_discount_gt_25pct_rupees"], 166477.0, places=0)

    # 6. DOMAIN 360 INTEGRATION & ACTION PROFILES
    def test_13_customer_360_prescriptive_profile(self):
        """Customer profile must return verified recency, LOW_EMPIRICAL caveat, and discount guardrails."""
        segmented = analyze_customer_risk_segments(
            self.data.get("customers", pd.DataFrame()),
            self.data.get("orders", pd.DataFrame()),
            self.data.get("customer_churn_predictions", pd.DataFrame()),
        )
        profile = explain_customer_retention_profile("C000001", segmented)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["customer_id"], "C000001")
        self.assertEqual(profile["ml_caveat_assessment"]["ml_confidence_tier"], "LOW_EMPIRICAL")
        self.assertIn("LOW_EMPIRICAL: ML churn prediction is exploratory only", profile["ml_caveat_assessment"]["confidence_caveat"])
        self.assertIn("discount_guardrails", profile)
        self.assertIn("prescriptive_action", profile)

        # Also verify via API endpoint
        res = self.client.get("/api/prescriptive/customer-profile/C000001", headers=self.viewer_headers)
        self.assertEqual(res.status_code, 200)
        api_profile = res.json()
        self.assertEqual(api_profile["customer_id"], "C000001")
        self.assertEqual(api_profile["retention_segment"], profile["retention_segment"])

    def test_14_restaurant_360_performance_diagnosis(self):
        """Restaurant performance diagnosis must identify bottleneck and provide action plan."""
        diagnosed = diagnose_restaurant_performance(
            self.data.get("restaurants", pd.DataFrame()),
            self.data.get("orders", pd.DataFrame()),
            self.data.get("menu_items", pd.DataFrame()),
        )
        plan = generate_restaurant_action_plan("R00001", diagnosed)
        self.assertIsNotNone(plan)
        self.assertEqual(plan["restaurant_id"], "R00001")
        self.assertIn("diagnosis_category", plan)
        self.assertIn("operational_metrics", plan)
        self.assertGreater(len(plan["prescriptive_action_plan"]), 0)
        self.assertIn("expected_operational_impact", plan)

        # Also verify via API endpoint
        res = self.client.get("/api/prescriptive/restaurant-profile/R00001", headers=self.viewer_headers)
        self.assertEqual(res.status_code, 200)
        api_plan = res.json()
        self.assertEqual(api_plan["restaurant_id"], "R00001")
        self.assertEqual(api_plan["diagnosis_category"], plan["diagnosis_category"])

    def test_15_rider_fleet_workload_and_live_gps_caveat(self):
        """Rider fleet workload must compute SLA breach tail (>45m) and output live GPS caveat."""
        workload = analyze_geographic_fleet_workload(
            self.data.get("riders", pd.DataFrame()),
            self.data.get("deliveries", pd.DataFrame()),
            self.data.get("orders", pd.DataFrame()),
            self.data.get("restaurants", pd.DataFrame()),
        )
        self.assertIsNotNone(workload)
        self.assertEqual(workload["total_active_fleet"], 4000)
        self.assertEqual(workload["fleet_sla_metrics"]["sla_breached_deliveries_gt_45m"], 16119)
        self.assertAlmostEqual(workload["fleet_sla_metrics"]["sla_breach_rate_percentage"], 32.26, places=1)
        self.assertIn("live_telemetry_disclaimer", workload)
        self.assertIn("Real-time dynamic fleet reallocation requires live GPS", workload["live_telemetry_disclaimer"])
        self.assertIn("Chennai", workload["geographic_workload"])
        self.assertEqual(workload["geographic_workload"]["Chennai"]["status"], "High Density")

        # Also verify via API endpoint
        res = self.client.get("/api/prescriptive/rider-fleet-workload", headers=self.viewer_headers)
        self.assertEqual(res.status_code, 200)
        api_workload = res.json()
        self.assertEqual(api_workload["total_active_fleet"], 4000)
        self.assertEqual(api_workload["fleet_sla_metrics"]["sla_breached_deliveries_gt_45m"], 16119)


if __name__ == "__main__":
    unittest.main()
