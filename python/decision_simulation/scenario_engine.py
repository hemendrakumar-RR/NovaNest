"""
Phase 6 — Scenario Engine
-------------------------
Coordinates empirical sub-simulators to produce complete scenario analysis
with transparent model assumptions metadata.
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from decision_simulation.customer_simulator import simulate_customer_impact
    from decision_simulation.decision_recommendation import generate_recommendation
    from decision_simulation.financial_simulator import simulate_financials
    from decision_simulation.operations_simulator import simulate_operations
    from decision_simulation.restaurant_simulator import simulate_restaurant_impact
    from decision_simulation.validation import validate_scenario_parameters
except ImportError:
    from python.decision_simulation.customer_simulator import simulate_customer_impact
    from python.decision_simulation.decision_recommendation import generate_recommendation
    from python.decision_simulation.financial_simulator import simulate_financials
    from python.decision_simulation.operations_simulator import simulate_operations
    from python.decision_simulation.restaurant_simulator import simulate_restaurant_impact
    from python.decision_simulation.validation import validate_scenario_parameters


def run_scenario(scenario_name: str, params: dict, data_dict: dict) -> Dict[str, Any]:
    """Executes a full scenario simulation across financial, customer, merchant, and ops domains."""
    validated_params = validate_scenario_parameters(params)

    orders_df = data_dict.get("orders")
    customers_df = data_dict.get("customers")
    restaurants_df = data_dict.get("restaurants")
    orders_eng_df = data_dict.get("orders_engineered")
    deliveries_df = data_dict.get("deliveries")
    churn_df = data_dict.get("customer_churn_predictions")

    financial_results = simulate_financials(
        orders_df, validated_params, orders_engineered_df=orders_eng_df, restaurants_df=restaurants_df
    )
    customer_results = simulate_customer_impact(customers_df, validated_params, churn_df=churn_df)
    restaurant_results = simulate_restaurant_impact(
        restaurants_df, orders_df, validated_params, orders_engineered_df=orders_eng_df
    )
    ops_results = simulate_operations(orders_df, validated_params, deliveries_df=deliveries_df)

    recommendation = generate_recommendation(
        scenario_name,
        financial_results,
        customer_results,
        ops_results,
    )

    assumptions: List[str] = [
        "Scenario engine projects deterministic linear elasticity multipliers over observed baseline cohorts (Cancelled orders excluded)."
    ]
    for section in (financial_results, customer_results, ops_results):
        meta = section.get("metadata", {})
        if meta.get("assumption_note"):
            assumptions.append(meta["assumption_note"])
        if meta.get("churn_note"):
            assumptions.append(meta["churn_note"])
        if meta.get("acquisition_assumption_note"):
            assumptions.append(meta["acquisition_assumption_note"])

    return {
        "scenario_name": scenario_name,
        "parameters": validated_params,
        "results": {
            "financial": financial_results,
            "customer": customer_results,
            "restaurant": restaurant_results,
            "operations": ops_results,
        },
        "recommendation": recommendation,
        "scenario_assumptions": assumptions,
    }
