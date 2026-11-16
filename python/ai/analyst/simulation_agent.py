"""
NovaNest Decision Simulator Agent
Connects conversational inquiries to the existing multi-variable Monte Carlo simulation engine.
Executes scenario runs with parameter validation and deterministic impact calculations.
"""

import re
import pandas as pd
from typing import Dict, Any, Tuple
try:
    from decision_simulation.scenario_engine import run_scenario
except ImportError:
    from python.decision_simulation.scenario_engine import run_scenario


def parse_simulation_parameters(query: str) -> Tuple[str, Dict[str, float]]:
    """
    Parses user query into validated simulation parameters.
    """
    q = query.lower()

    params = {
        "commission_change_pct": 0.0,
        "delivery_fee_change_pct": 0.0,
        "discount_change_pct": 0.0,
        "demand_change_pct": 0.0,
        "churn_reduction_pct": 0.0,
        "aov_change_pct": 0.0
    }

    scenario_name = "Custom What-If Scenario"

    # Presets
    if "aggressive" in q or "expansion" in q:
        scenario_name = "Aggressive Market Expansion"
        params["demand_change_pct"] = 15.0
        params["discount_change_pct"] = 5.0
        params["commission_change_pct"] = -1.0
        return scenario_name, params

    if "profit" in q or "margin optimization" in q:
        scenario_name = "Profit Margin Optimization"
        params["commission_change_pct"] = 2.0
        params["discount_change_pct"] = -5.0
        params["delivery_fee_change_pct"] = 5.0
        return scenario_name, params

    if "retention" in q or "churn reduction" in q:
        scenario_name = "VIP Customer Retention Focus"
        params["churn_reduction_pct"] = 6.0
        params["discount_change_pct"] = 3.0
        return scenario_name, params

    # Extract percentage changes using regex
    comm_match = re.search(r"commission.*?(?:by|to)?\s*([+-]?\d+(?:\.\d+)?)\s*%", q)
    if comm_match:
        params["commission_change_pct"] = float(comm_match.group(1))

    fee_match = re.search(r"(?:delivery\s*fee|fees?).*?(?:by|to)?\s*([+-]?\d+(?:\.\d+)?)", q)
    if fee_match:
        params["delivery_fee_change_pct"] = float(fee_match.group(1))

    disc_match = re.search(r"discount.*?(?:by|to)?\s*([+-]?\d+(?:\.\d+)?)\s*%", q)
    if disc_match:
        params["discount_change_pct"] = float(disc_match.group(1))

    demand_match = re.search(r"(?:demand|volume|orders).*?(?:by|to)?\s*([+-]?\d+(?:\.\d+)?)\s*%", q)
    if demand_match:
        params["demand_change_pct"] = float(demand_match.group(1))

    churn_match = re.search(r"churn.*?(?:by|to)?\s*([+-]?\d+(?:\.\d+)?)\s*%", q)
    if churn_match:
        params["churn_reduction_pct"] = float(churn_match.group(1))

    # If no numbers were matched, provide a modest default scenario
    if all(v == 0.0 for v in params.values()):
        scenario_name = "Balanced Strategy (+5% Demand, -3% Subsidy)"
        params["demand_change_pct"] = 5.0
        params["discount_change_pct"] = -3.0

    return scenario_name, params


def execute_conversational_simulation(query: str, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Executes a scenario simulation and generates conversational results with comparison charts.
    """
    scenario_name, params = parse_simulation_parameters(query)

    sim_data = {
        "orders": data.get("orders", pd.DataFrame()),
        "customers": data.get("customers", pd.DataFrame()),
        "restaurants": data.get("restaurants", pd.DataFrame()),
        "orders_engineered": data.get("orders_engineered", pd.DataFrame()),
        "deliveries": data.get("deliveries", pd.DataFrame()),
        "customer_churn_predictions": data.get("customer_churn_predictions", pd.DataFrame()),
    }

    raw_results = run_scenario(scenario_name, params, sim_data)

    fin = raw_results["results"]["financial"]
    cust = raw_results["results"]["customer"]
    ops = raw_results["results"]["operations"]
    rec = raw_results["recommendation"]

    base_rev = fin["baseline"]["Platform_Revenue"]
    sim_rev = fin["simulated"]["Platform_Revenue"]
    rev_diff = fin["impact"]["Platform_Revenue_Diff"]
    margin_diff = fin["impact"]["Margin_Diff"] * 100

    base_gmv = fin["baseline"].get("Gross_Revenue", 0)
    sim_gmv = fin["simulated"].get("Gross_Revenue", 0)
    base_orders = fin["baseline"].get("Orders", 0)
    sim_orders = fin["simulated"].get("Orders", 0)

    comparison_data = [
        {"metric": "Platform Revenue (₹L)", "Baseline": round(base_rev / 100000, 2), "Simulated": round(sim_rev / 100000, 2)},
        {"metric": "Gross GMV (₹Cr)", "Baseline": round(base_gmv / 10000000, 2), "Simulated": round(sim_gmv / 10000000, 2)},
        {"metric": "Total Orders (k)", "Baseline": round(base_orders / 1000, 1), "Simulated": round(sim_orders / 1000, 1)},
    ]

    summary_text = (
        f"**Decision Simulation Results: {scenario_name}**\n\n"
        f"- **Platform Revenue Impact:** {'+' if rev_diff >= 0 else ''}₹{rev_diff:,.2f} "
        f"({'+' if rev_diff >= 0 else ''}{(rev_diff / base_rev * 100 if base_rev > 0 else 0.0):.2f}% shift)\n"
        f"- **Take-Rate Margin Shift:** {'+' if margin_diff >= 0 else ''}{margin_diff:.2f}%\n"
        f"- **Customer Impact:** {cust['impact']['Churn_Reduction']:,} accounts preserved from churn\n"
        f"- **Operational ETA Shift:** {ops['impact']['ETA_Diff_Mins']:+.1f} mins\n\n"
        f"**Strategic Decision Recommendation:**\n"
        f"*{rec['Decision']}* — {rec['Expected_Benefit']} {rec['Main_Risk']}"
    )

    return {
        "scenario_name": scenario_name,
        "parameters": params,
        "financial_impact": {
            "baseline_revenue": base_rev,
            "simulated_revenue": sim_rev,
            "revenue_diff": rev_diff,
            "margin_diff_pct": margin_diff
        },
        "customer_impact": cust["impact"],
        "operations_impact": ops["impact"],
        "recommendation": rec,
        "comparison_data": comparison_data,
        "summary": summary_text,
        "suggested_chart": {
            "type": "bar",
            "title": f"Scenario Simulation Comparison: Baseline vs {scenario_name}",
            "x_key": "metric",
            "y_key": "Simulated",
            "secondary_key": "Baseline",
            "data": comparison_data
        }
    }
