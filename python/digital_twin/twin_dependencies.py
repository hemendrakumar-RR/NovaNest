"""
Phase 7 — Twin Dependency Graph
-------------------------------
Represents downstream cross-domain business impact chains programmatically
in both sequence list and structured graph formats.
"""

from __future__ import annotations

from typing import Any, Dict, List

_CHAIN_DEFS: Dict[str, Dict[str, Any]] = {
    "demand_spike": {
        "trigger": "Surge Demand Spike",
        "ripple_steps": [
            "Demand Increase",
            "Rider Capacity Pressure",
            "Higher Delivery Time",
            "Late Deliveries",
            "Customer Satisfaction Risk",
            "Potential Retention Impact",
        ],
        "impact": "ETA Slump & Cancellation Uplift",
    },
    "high_discount": {
        "trigger": "Promo Subsidy Expansion",
        "ripple_steps": [
            "High Discount Usage",
            "Lower Net Revenue",
            "Margin Compression",
            "Potential Revenue Leakage",
        ],
        "impact": "Contribution Margin Erosion",
    },
    "restaurant_churn": {
        "trigger": "Critical Merchant Attrition",
        "ripple_steps": [
            "Restaurant Churn",
            "Lower Local Variety",
            "Customer Order Frequency Drop",
            "Revenue Decline",
        ],
        "impact": "Local GMV Concentration Risk",
    },
    "operations_delay": {
        "trigger": "Transit & Kitchen Delay Shock",
        "ripple_steps": [
            "Delayed Dispatches (>45m)",
            "Elevated Order Cancellation Rate",
            "Customer Retention & Rating Decay",
        ],
        "impact": "SLA Penalty & Repeat Order Loss",
    },
    "merchant_churn": {
        "trigger": "High-Risk Partner Degradation",
        "ripple_steps": [
            "Merchant Prep SLA Breaches",
            "Order Drops & Rating Decline",
            "Local Supply Gap Across Metro",
        ],
        "impact": "Partner GMV At-Risk Exposure",
    },
    "discount_subsidy_surge": {
        "trigger": "Uncapped Coupon Subsidy Utilization",
        "ripple_steps": [
            "Post-Discount Margin Deficit",
            "Take-Rate Yield Dilution",
            "Working Capital & Subsidy Overrun",
        ],
        "impact": "Unverified Margin Deficit Candidates",
    },
}


def get_impact_chain(event_type: str) -> List[str]:
    """Returns the sequence of downstream impacts for a given event."""
    item = _CHAIN_DEFS.get(event_type)
    if item:
        return list(item["ripple_steps"])
    return ["Event", "Direct Business Impact"]


def get_structured_impact_chain(event_type: str) -> Dict[str, Any]:
    """Returns structured trigger, ripple steps, and impact summary for API/UI cards."""
    item = _CHAIN_DEFS.get(event_type)
    if item:
        return {
            "event_type": event_type,
            "trigger": item["trigger"],
            "ripple_steps": list(item["ripple_steps"]),
            "impact": item["impact"],
        }
    return {
        "event_type": event_type,
        "trigger": event_type.replace("_", " ").title(),
        "ripple_steps": ["Event", "Direct Business Impact"],
        "impact": "Downstream Variance",
    }
