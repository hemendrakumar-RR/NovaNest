"""
NovaNest Prescriptive Decision Optimization Engine (Phase 08 Master Orchestration)
-----------------------------------------------------------------------------------
Integrates Customer Retention Intelligence, Revenue Optimization, Restaurant Network
Action Plans, Rider Logistics Dispatch Balancing, What-If Scenario Simulations,
and Human-in-the-Loop Recommendation Lifecycle Management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

from python.decision.prescriptive_contracts import (
    ConfidenceTier,
    FinancialImpactBreakdown,
    PrescriptiveDomain,
    PrescriptiveRecommendation,
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
    calculate_financial_impact,
    audit_realized_financial_outcome,
)
from python.decision.recommendation_lifecycle import (
    HumanApprovalRequiredError,
    InvalidLifecycleTransitionError,
    RecommendationLifecycleManager,
    get_recommendation_lifecycle_manager,
)


def generate_all_prescriptive_recommendations(
    data_dict: Dict[str, pd.DataFrame],
    register_in_lifecycle: bool = True,
) -> List[PrescriptiveRecommendation]:
    """
    Generates the complete enterprise portfolio of prescriptive recommendations
    across Customer, Revenue, Restaurant, and Logistics operational domains.
    Optionally registers all generated recommendations into the persistent lifecycle store.
    """
    orders_df = data_dict.get("orders")
    customers_df = data_dict.get("customers")
    restaurants_df = data_dict.get("restaurants")
    riders_df = data_dict.get("riders")
    deliveries_df = data_dict.get("deliveries")
    menu_items_df = data_dict.get("menu_items")
    churn_df = data_dict.get("customer_churn_predictions")

    all_recs: List[PrescriptiveRecommendation] = []

    # 1. Customer Retention Recommendations
    if customers_df is not None and not customers_df.empty:
        cust_recs = generate_customer_retention_recommendations(customers_df, orders_df, churn_df)
        all_recs.extend(cust_recs)

    # 2. Revenue Optimization Recommendations
    if orders_df is not None and not orders_df.empty:
        rev_recs = generate_revenue_optimization_recommendations(orders_df)
        all_recs.extend(rev_recs)

    # 3. Restaurant Optimization Recommendations
    if restaurants_df is not None and not restaurants_df.empty:
        rest_recs = generate_restaurant_optimization_recommendations(restaurants_df, orders_df, menu_items_df)
        all_recs.extend(rest_recs)

    # 4. Logistics & Rider Allocation Recommendations
    if riders_df is not None and not riders_df.empty and deliveries_df is not None and not deliveries_df.empty:
        ops_recs = generate_rider_optimization_recommendations(riders_df, deliveries_df, orders_df, restaurants_df)
        all_recs.extend(ops_recs)

    if register_in_lifecycle and all_recs:
        manager = get_recommendation_lifecycle_manager()
        manager.register_all(all_recs)

    return all_recs


def get_prescriptive_summary_kpis(recommendations: List[PrescriptiveRecommendation]) -> Dict[str, Any]:
    """Computes aggregate financial and operational summary across recommendations."""
    if not recommendations:
        return {
            "total_recommendations": 0,
            "total_gross_benefit_rupees": 0.0,
            "total_implementation_cost_rupees": 0.0,
            "total_net_financial_impact_rupees": 0.0,
            "by_domain_counts": {},
            "by_confidence_tier_counts": {},
        }

    total_gross = sum(r.financial_impact.gross_benefit for r in recommendations)
    total_cost = sum(r.financial_impact.implementation_cost for r in recommendations)
    total_net = sum(r.financial_impact.net_financial_impact for r in recommendations)

    domain_counts: Dict[str, int] = {}
    for r in recommendations:
        d = r.domain.value
        domain_counts[d] = domain_counts.get(d, 0) + 1

    tier_counts: Dict[str, int] = {}
    for r in recommendations:
        t = r.confidence_tier.value
        tier_counts[t] = tier_counts.get(t, 0) + 1

    return {
        "total_recommendations": len(recommendations),
        "total_gross_benefit_rupees": round(total_gross, 2),
        "total_implementation_cost_rupees": round(total_cost, 2),
        "total_net_financial_impact_rupees": round(total_net, 2),
        "overall_roi_multiple": round(total_net / total_cost, 2) if total_cost > 0 else 0.0,
        "by_domain_counts": domain_counts,
        "by_confidence_tier_counts": tier_counts,
    }
