"""
Phase 7 — Twin Alert Engine
---------------------------
Aggregates and prioritizes empirical cross-domain business alerts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def generate_twin_alerts(
    fin_metrics: Dict[str, Any],
    ops_metrics: Dict[str, Any],
    cust_metrics: Dict[str, Any],
    rest_metrics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generates unified business health alerts based on real metric thresholds."""
    alerts: List[Dict[str, Any]] = []

    profit_margin = fin_metrics.get("Profit_Margin")
    if profit_margin is not None and profit_margin < 0.05:
        alerts.append({
            "Severity": "Critical",
            "Category": "Financial",
            "Entity": "Platform",
            "Signal": "Margin Compression",
            "Metric": "Profit Margin",
            "Current_Value": f"{profit_margin * 100:.2f}%",
            "Business_Impact": "Severe risk of operating at compressed contribution margin.",
            "Recommended_Action": "Review discount funding split and minimum order thresholds.",
        })

    gross_rev = fin_metrics.get("Gross_Revenue", 0) or 0
    leakage_est = fin_metrics.get("Revenue_Leakage_Est", 0) or 0
    if gross_rev > 0 and leakage_est > (gross_rev * 0.10):
        alerts.append({
            "Severity": "High",
            "Category": "Financial",
            "Entity": "Discounts & Leakage Candidates",
            "Signal": "High Potential Revenue Leakage Exposure",
            "Metric": "Potential Leakage vs GMV",
            "Current_Value": f"{(leakage_est / gross_rev) * 100:.2f}%",
            "Business_Impact": "Potential unverified risk exposure exceeds 10% of gross revenue.",
            "Recommended_Action": "Audit promotion funding attribution and cancellation fee recovery.",
        })

    late_deliv = ops_metrics.get("Late_Deliveries")
    denom_orders = ops_metrics.get("Deliveries_Recorded") or ops_metrics.get("Total_Orders") or 0
    if late_deliv is not None and denom_orders > 0 and late_deliv > (denom_orders * 0.10):
        alerts.append({
            "Severity": "High",
            "Category": "Operations",
            "Entity": "Fleet",
            "Signal": "High Late Delivery Ratio",
            "Metric": "Delayed Deliveries (>45m)",
            "Current_Value": f"{(late_deliv / denom_orders) * 100:.1f}% ({late_deliv:,} runs)",
            "Business_Impact": "Customer satisfaction degradation and elevated cancellation risk.",
            "Recommended_Action": "Rebalance peak-hour rider supply across delayed zones.",
        })

    if rest_metrics:
        crit_partners = rest_metrics.get("Critical_Risk_Partners")
        if crit_partners is not None and crit_partners > 0:
            alerts.append({
                "Severity": "Medium",
                "Category": "Merchant Network",
                "Entity": "Partner Kitchens",
                "Signal": "Critical Partner Quality/Cancel Alerts",
                "Metric": "Critical Risk Partners",
                "Current_Value": f"{crit_partners} partners",
                "Business_Impact": "Order fulfillment risk concentrated at underperforming kitchens.",
                "Recommended_Action": "Conduct kitchen prep SLA and menu quality audit.",
            })

    if not alerts:
        alerts.append({
            "Severity": "Informational",
            "Category": "System",
            "Entity": "Platform",
            "Signal": "Healthy Operations",
            "Metric": "Systemic Threshold Check",
            "Current_Value": "Nominal",
            "Business_Impact": "No critical threshold violations detected across available telemetry.",
            "Recommended_Action": "Maintain current operational monitoring cadence.",
        })

    return alerts
