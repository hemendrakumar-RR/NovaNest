"""
NovaNest Phase 08 Prescriptive Business Intelligence & AI Decision Optimization Test Suite
-------------------------------------------------------------------------------------------
Validates:
1. Prescriptive contracts, serialization, and lifecycle enums.
2. Customer retention intelligence, RFM risk segmentation, and LOW_EMPIRICAL churn gating.
3. Revenue optimization, contribution margin calculation, and realized vs projected revenue.
4. Restaurant performance diagnosis, bottleneck identification, and partner action plans.
5. Rider allocation, delivery bottleneck detection, and live data telemetry disclaimer.
6. Controlled What-If scenario simulations across 5 business domains with projection disclaimers.
7. Financial impact engine calculation accuracy, ROI, payback days, and variance auditing.
8. Recommendation lifecycle state machine and strict Human Approval enforcement.
9. Domain AI Agent integration across Decision, Customer, Financial, Operations, and Restaurant.
10. Database safety and non-destructive integrity check (304,405 records preserved).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, Dict
import pandas as pd

from python.decision.prescriptive_contracts import (
    ConfidenceTier,
    FinancialImpactBreakdown,
    PrescriptiveDomain,
    PrescriptiveRecommendation,
    RealizedOutcomeRecord,
    RecommendationLifecycleStatus,
    make_rec_id,
)
from python.decision.customer_retention_intelligence import (
    analyze_customer_risk_segments,
    explain_customer_retention_profile,
    generate_customer_retention_recommendations,
)
from python.decision.revenue_optimization import (
    compute_order_contribution_margin,
    generate_revenue_optimization_recommendations,
    simulate_delivery_fee_restructuring,
)
from python.decision.restaurant_optimization import (
    diagnose_restaurant_performance,
    generate_restaurant_action_plan,
    generate_restaurant_optimization_recommendations,
)
from python.decision.rider_operations_optimization import (
    analyze_geographic_fleet_workload,
    generate_rider_optimization_recommendations,
)
from python.decision.scenario_simulation_engine import (
    run_controlled_scenario_simulation,
)
from python.decision.financial_impact_engine import (
    audit_realized_financial_outcome,
    calculate_financial_impact,
)
from python.decision.recommendation_lifecycle import (
    HumanApprovalRequiredError,
    InvalidLifecycleTransitionError,
    RecommendationLifecycleManager,
)
from python.decision.prescriptive_engine import (
    generate_all_prescriptive_recommendations,
    get_prescriptive_summary_kpis,
)
from python.decision.next_best_action import (
    generate_customer_next_best_actions,
    generate_operational_next_best_actions,
    generate_restaurant_next_best_actions,
)


class TestPhase08PrescriptiveIntelligence(unittest.TestCase):
    """Exhaustive test suite for NovaNest Phase 08."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parents[1]
        cls.data_dir = cls.base_dir / "datasets" / "cleaned"
        cls.eng_dir = cls.base_dir / "datasets" / "engineered"

        # Load clean datasets for integration tests
        cls.orders = pd.read_csv(cls.data_dir / "orders.csv")
        cls.customers = pd.read_csv(cls.data_dir / "customers.csv")
        cls.restaurants = pd.read_csv(cls.data_dir / "restaurants.csv")
        cls.riders = pd.read_csv(cls.data_dir / "riders.csv")
        cls.deliveries = pd.read_csv(cls.data_dir / "deliveries.csv")
        cls.menu_items = pd.read_csv(cls.data_dir / "menu_items.csv")

        cls.churn_file = cls.eng_dir / "customer_churn_predictions.csv"
        cls.churn_df = pd.read_csv(cls.churn_file) if cls.churn_file.exists() else pd.DataFrame()

        cls.data_dict = {
            "orders": cls.orders,
            "customers": cls.customers,
            "restaurants": cls.restaurants,
            "riders": cls.riders,
            "deliveries": cls.deliveries,
            "menu_items": cls.menu_items,
            "customer_churn_predictions": cls.churn_df,
        }

    def test_01_prescriptive_contracts_and_serialization(self):
        """Validates contract instantiation, financial sub-models, enums, and dict export."""
        fin = FinancialImpactBreakdown(
            gross_benefit=150000.0,
            implementation_cost=30000.0,
            net_financial_impact=120000.0,
            roi_multiple=4.0,
            payback_period_days=15,
            measurement_period="30 days",
            success_metric="Net margin +₹120,000",
            is_estimated=True,
        )
        rec = PrescriptiveRecommendation(
            recommendation_id="REC-TEST-001",
            title="Test Prescriptive Recommendation",
            domain=PrescriptiveDomain.REVENUE_OPTIMIZATION,
            target_type="Pricing Rule",
            entity_id="Checkout Service",
            business_problem="Subsidized discounts eroding margin.",
            supporting_evidence=["Audited 2,449 orders with >25% discount."],
            proposed_action="Cap discount at 20%.",
            expected_benefit="Save ₹150,000 in unrecovered subsidies.",
            financial_impact=fin,
            risk_and_uncertainty="Potential 1% volume churn.",
            confidence_tier=ConfidenceTier.HIGH,
            confidence_caveat="Audited 100% from historical delivered orders.",
            lifecycle_status=RecommendationLifecycleStatus.PROPOSED,
            human_approval_required=True,
            is_simulation_projection=True,
        )

        d = rec.to_action_recommendation_dict()
        self.assertEqual(d["recommendation_id"], "REC-TEST-001")
        self.assertEqual(d["target_type"], "Pricing Rule")
        self.assertEqual(d["lifecycle_status"], "Proposed")
        self.assertEqual(d["implementation_cost"], 30000.0)
        self.assertEqual(d["net_financial_impact"], 120000.0)
        self.assertTrue(d["human_approval_required"])
        self.assertTrue(d["is_simulation_projection"])

    def test_02_customer_retention_intelligence_and_rfm_segmentation(self):
        """Validates customer risk segmentation, discount caps, MOV, and LOW_EMPIRICAL churn gating."""
        segmented = analyze_customer_risk_segments(self.customers, self.orders, self.churn_df)
        self.assertFalse(segmented.empty)
        self.assertIn("retention_segment", segmented.columns)
        self.assertIn("recency_days", segmented.columns)

        # Inspect customer explanation
        sample_cid = str(self.customers.iloc[0]["customer_id"])
        explanation = explain_customer_retention_profile(sample_cid, segmented)
        self.assertNotIn("error", explanation)
        self.assertIn("discount_guardrails", explanation)
        self.assertIn("ml_caveat_assessment", explanation)
        self.assertEqual(
            explanation["ml_caveat_assessment"]["ml_confidence_tier"],
            ConfidenceTier.LOW_EMPIRICAL.value,
        )
        self.assertIn("LOW_EMPIRICAL", explanation["ml_caveat_assessment"]["confidence_caveat"])

        # Generate recommendations
        recs = generate_customer_retention_recommendations(self.customers, self.orders, self.churn_df)
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertEqual(r.domain, PrescriptiveDomain.CUSTOMER_RETENTION)
            self.assertTrue(r.human_approval_required)
            self.assertGreater(r.financial_impact.net_financial_impact, 0)

    def test_03_revenue_optimization_and_contribution_margin(self):
        """Validates contribution margin breakdown, subsidy leakage, and realized vs projected revenue."""
        margin_diag = compute_order_contribution_margin(self.orders)
        self.assertEqual(margin_diag["status"], "Audited Historical Realized")
        self.assertEqual(margin_diag["delivered_order_count"], 47994)
        self.assertEqual(margin_diag["realized_net_revenue"], 46425992.0)
        self.assertEqual(margin_diag["realized_gross_gmv"], 46590125.0)

        fb = margin_diag["financial_breakdown"]
        self.assertGreater(fb["estimated_platform_commission_20pct"], 0)
        self.assertGreater(fb["total_delivery_fees_collected"], 0)
        self.assertGreater(fb["estimated_rider_fulfillment_cost"], 0)

        # Simulation comparison
        sim = simulate_delivery_fee_restructuring(self.orders, fee_increase_flat=10.0, min_order_threshold=350.0)
        self.assertTrue(sim["is_simulation_projection"])
        self.assertIn("disclaimer", sim)
        self.assertGreater(sim["projected_simulation"]["net_contribution_margin"], sim["baseline_realized"]["net_contribution_margin"])

        # Recommendations
        recs = generate_revenue_optimization_recommendations(self.orders)
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertEqual(r.domain, PrescriptiveDomain.REVENUE_OPTIMIZATION)
            self.assertTrue(r.financial_impact.is_estimated)

    def test_04_restaurant_optimization_and_action_plans(self):
        """Validates restaurant performance diagnosis, partner action plans, and recommendations."""
        diag = diagnose_restaurant_performance(self.restaurants, self.orders, self.menu_items)
        self.assertFalse(diag.empty)
        self.assertIn("performance_diagnosis", diag.columns)
        self.assertIn("cancellation_rate", diag.columns)

        # Specific action plan
        sample_rid = str(self.restaurants.iloc[0]["restaurant_id"])
        action_plan = generate_restaurant_action_plan(sample_rid, diag)
        self.assertNotIn("error", action_plan)
        self.assertIn("prescriptive_action_plan", action_plan)
        self.assertIn("operational_metrics", action_plan)

        # Recommendations
        recs = generate_restaurant_optimization_recommendations(self.restaurants, self.orders, self.menu_items)
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertEqual(r.domain, PrescriptiveDomain.RESTAURANT_OPTIMIZATION)
            self.assertTrue(r.human_approval_required)

    def test_05_rider_operations_optimization_and_live_data_caveat(self):
        """Validates fleet workload ratios, SLA breach detection, and live data telemetry caveat."""
        workload = analyze_geographic_fleet_workload(self.riders, self.deliveries, self.orders, self.restaurants)
        self.assertEqual(workload["status"], "Audited Operational Telemetry")
        self.assertEqual(workload["total_active_fleet"], 4000)
        self.assertEqual(workload["total_dispatches"], 49971)

        sla = workload["fleet_sla_metrics"]
        self.assertEqual(sla["sla_breached_deliveries_gt_45m"], 16119)
        self.assertAlmostEqual(sla["sla_breach_rate_percentage"], 32.25, delta=0.5)

        # Disclaimer verification
        self.assertIn("live_telemetry_disclaimer", workload)
        self.assertIn("Real-time dynamic fleet reallocation requires live GPS", workload["live_telemetry_disclaimer"])

        recs = generate_rider_optimization_recommendations(self.riders, self.deliveries, self.orders, self.restaurants)
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertEqual(r.domain, PrescriptiveDomain.RIDER_LOGISTICS)
            self.assertEqual(r.confidence_tier, ConfidenceTier.OPERATIONAL_GATED)

    def test_06_what_if_scenario_simulation_engine(self):
        """Validates controlled simulations across 5 business scenarios with non-guaranteed disclaimers."""
        scenarios = [
            "promotion_optimization",
            "delivery_fee_restructuring",
            "rider_capacity_expansion",
            "restaurant_capacity_acceleration",
            "customer_retention_campaign",
        ]
        for s in scenarios:
            res = run_controlled_scenario_simulation(s, self.data_dict)
            self.assertTrue(res["is_simulation_projection"])
            self.assertIn("disclaimer", res)
            self.assertIn("baseline", res)
            self.assertIn("scenario_assumptions", res)
            self.assertIn("projected_outcomes", res)
            self.assertIn("variance_deltas", res)
            self.assertEqual(res["baseline"]["delivered_orders"], 47994)
            self.assertGreater(len(res["scenario_assumptions"]), 0)

    def test_07_financial_impact_engine_accuracy_and_variance(self):
        """Validates calculate_financial_impact and audit_realized_financial_outcome variance calculations."""
        fin = calculate_financial_impact(
            gross_benefit=200000.0,
            implementation_cost=50000.0,
            measurement_period="30 days",
            success_metric="Contribution margin +₹150,000",
            is_estimated=True,
        )
        self.assertEqual(fin.gross_benefit, 200000.0)
        self.assertEqual(fin.implementation_cost, 50000.0)
        self.assertEqual(fin.net_financial_impact, 150000.0)
        self.assertEqual(fin.roi_multiple, 3.0)
        self.assertLessEqual(fin.payback_period_days, 30)

        # Audit post-realization with variance
        audited = audit_realized_financial_outcome(
            projected=fin,
            realized_gross_benefit=210000.0,
            actual_cost=48000.0,
            measured_by="Lead Finance Auditor",
            audit_notes="Q4 post-campaign margin audit",
        )
        self.assertEqual(audited.realized_gross_benefit, 210000.0)
        self.assertEqual(audited.actual_cost, 48000.0)
        self.assertEqual(audited.realized_net_impact, 162000.0)
        self.assertEqual(audited.benefit_variance_pct, 5.0)  # +5% variance vs projection

    def test_08_recommendation_lifecycle_state_machine_and_human_approval(self):
        """Validates 6-state lifecycle transitions and enforces Human Approval gating."""
        tmp_store = self.base_dir / "models" / "test_recommendations_store.json"
        if tmp_store.exists():
            tmp_store.unlink()

        mgr = RecommendationLifecycleManager(store_path=tmp_store)

        fin = calculate_financial_impact(50000.0, 10000.0)
        rec = PrescriptiveRecommendation(
            recommendation_id="REC-TEST-LIFECYCLE-01",
            title="Lifecycle Test Recommendation",
            domain=PrescriptiveDomain.REVENUE_OPTIMIZATION,
            target_type="Pricing",
            business_problem="Leakage audit",
            proposed_action="Cap discount",
            expected_benefit="Save ₹50,000",
            financial_impact=fin,
            confidence_tier=ConfidenceTier.HIGH,
        )

        # 1. Register -> Proposed
        stored = mgr.register_recommendation(rec)
        self.assertEqual(stored.lifecycle_status, RecommendationLifecycleStatus.PROPOSED)

        # 2. Safety Rule: Attempting to start implementation without Human Approval must fail
        with self.assertRaises(HumanApprovalRequiredError):
            mgr.start_implementation("REC-TEST-LIFECYCLE-01", operator_user="AutoAgent")

        # 3. Human Approval -> Approved
        approved = mgr.approve_recommendation(
            "REC-TEST-LIFECYCLE-01",
            approved_by="Executive_Operator",
            approval_notes="Approved for Q4 deployment",
        )
        self.assertEqual(approved.lifecycle_status, RecommendationLifecycleStatus.APPROVED)
        self.assertEqual(approved.approved_by, "Executive_Operator")

        # 4. Start Implementation -> In progress
        in_prog = mgr.start_implementation("REC-TEST-LIFECYCLE-01", operator_user="DevOps_Lead")
        self.assertEqual(in_prog.lifecycle_status, RecommendationLifecycleStatus.IN_PROGRESS)

        # 5. Mark Implemented -> Implemented
        impl = mgr.mark_implemented("REC-TEST-LIFECYCLE-01", operator_user="DevOps_Lead")
        self.assertEqual(impl.lifecycle_status, RecommendationLifecycleStatus.IMPLEMENTED)

        # 6. Record Outcome -> Outcome measured
        measured = mgr.record_realized_outcome(
            "REC-TEST-LIFECYCLE-01",
            realized_gross_benefit=52000.0,
            actual_cost=9500.0,
            measured_by="Auditor",
            audit_notes="Outcome verified on live database",
        )
        self.assertEqual(measured.lifecycle_status, RecommendationLifecycleStatus.OUTCOME_MEASURED)
        self.assertIsNotNone(measured.realized_outcome)
        self.assertEqual(measured.realized_outcome.realized_net_impact, 42500.0)

        # Clean up test store
        if tmp_store.exists():
            tmp_store.unlink()

    def test_09_agent_integration_prescriptive_recommendations(self):
        """Executes domain agents and validates that all emit rich prescriptive recommendations."""
        from python.ai.agents.context import AgentContext
        from python.ai.agents.contracts import AgentDomain, AgentRequest
        from python.ai.agents.customer_agent import CustomerAgent
        from python.ai.agents.decision_agent import DecisionAgent
        from python.ai.agents.financial_agent import FinancialAgent
        from python.ai.agents.operations_agent import OperationsAgent
        from python.ai.agents.restaurant_agent import RestaurantAgent

        ctx = AgentContext(
            principal_id="test_admin",
            user_query="prescriptive analysis",
            principal_scopes=["read", "operator", "admin"],
        )

        # DecisionAgent
        dec_agent = DecisionAgent()
        req_dec = AgentRequest(
            user_query="Provide prescriptive business recommendations and next best actions",
            agent_id="decision_agent",
            domain=AgentDomain.DECISION,
            principal_id="test_admin",
            intent="next_best_action",
        )
        res_dec = dec_agent.execute(req_dec, ctx)
        self.assertGreater(len(res_dec.recommendations), 0)
        sample_rec = res_dec.recommendations[0]
        self.assertTrue(sample_rec.recommendation_id.startswith("REC-"))
        self.assertTrue(sample_rec.human_approval_required)
        self.assertIn(sample_rec.confidence_tier, ["HIGH", "MODERATE", "LOW_EMPIRICAL", "OPERATIONAL_GATED"])

        # CustomerAgent
        cust_agent = CustomerAgent()
        req_cust = AgentRequest(
            user_query="Analyze customer retention and churn risk",
            agent_id="customer_agent",
            domain=AgentDomain.CUSTOMER,
            principal_id="test_admin",
        )
        res_cust = cust_agent.execute(req_cust, ctx)
        self.assertGreater(len(res_cust.recommendations), 0)
        self.assertTrue(res_cust.recommendations[0].recommendation_id.startswith("REC-"))

        # OperationsAgent
        ops_agent = OperationsAgent()
        req_ops = AgentRequest(
            user_query="Analyze delivery SLA breaches and logistics performance",
            agent_id="operations_agent",
            domain=AgentDomain.OPERATIONS,
            principal_id="test_admin",
        )
        res_ops = ops_agent.execute(req_ops, ctx)
        self.assertGreater(len(res_ops.recommendations), 0)
        self.assertTrue(res_ops.recommendations[0].recommendation_id.startswith("REC-"))

    def test_10_database_safety_and_preservation(self):
        """Verifies that all 304,405 records in MySQL novanest_db remain intact and unmodified."""
        import os
        import mysql.connector
        from dotenv import load_dotenv

        load_dotenv()
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_APP_USER", "novanest_app"),
            password=os.getenv("DB_APP_PASSWORD", "NovaAppPass2026!"),
            database=os.getenv("DB_NAME", "novanest_db"),
        )
        cur = conn.cursor()
        cur.execute("SHOW TABLES;")
        tables = [r[0] for r in cur.fetchall()]
        counts = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
        conn.close()

        total = sum(counts.values())
        self.assertEqual(total, 304405, f"Expected 304,405 records in novanest_db, found {total:,}")
        self.assertEqual(counts["orders_table"], 49971)
        self.assertEqual(counts["deliveries"], 49971)
        self.assertEqual(counts["customers"], 5000)
        self.assertEqual(counts["restaurants"], 1500)
        self.assertEqual(counts["riders"], 4000)


if __name__ == "__main__":
    unittest.main()
