"""
Page 8: Executive What-If Scenario Simulator (Phase 09)
-------------------------------------------------------
Controlled mathematical what-if scenario simulator across promotional caps,
delivery fee surcharges, rider surge capacity, merchant throughput, and VIP retention.
Explicitly enforces projection disclaimers and grounds all models in audited historical elasticities.
"""

from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import bootstrap
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from utils.data_loader import load_all_datasets
from utils.formatting import format_currency, format_number, format_percent
from components.navigation import render_sidebar
from components.page_header import render_page_header
from components.kpi_components import render_kpi_row
from components.status_components import render_section_header, render_callout, render_data_table
from components.contextual_ai import build_contextual_payload, render_contextual_ai_inline

from python.decision.scenario_simulation_engine import run_controlled_scenario_simulation

st.set_page_config(page_title=f"Decision Simulator — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

# Header
render_page_header(
    title="Executive What-If Scenario Simulator",
    subtitle="Simulate Pricing Elasticity, Fee Restructuring, Rider Surge Capacity & Merchant Acceleration",
    category="SCENARIO SIMULATION",
    data_source=data_source
)

# Scenario Definition Matrix
SCENARIOS = {
    "promotion_optimization": {
        "title": "Promotional Discount Capping (20% Hard Cap)",
        "domain": "Revenue Optimization",
        "description": "Enforces a strict 20% cap on promotions, reducing overall coupon expenditure by curbing excessive subsidies.",
        "defaults": {"discount_reduction_pct": 15.0, "volume_elasticity_pct": -1.5}
    },
    "delivery_fee_restructuring": {
        "title": "Delivery Fee Restructuring & Basket MOV Surcharge",
        "domain": "Revenue Optimization",
        "description": "Applies a delivery fee surcharge on orders >5km and incentivizes minimum order values above ₹350.",
        "defaults": {"fee_delta_rupees": 10.0, "aov_uplift_pct": 3.5, "volume_elasticity_pct": -2.5}
    },
    "rider_capacity_expansion": {
        "title": "Peak Hour Rider Capacity Expansion (+15% Fleet)",
        "domain": "Rider Logistics",
        "description": "Deploys a dedicated incentive pool to surge active rider rosters during dinner peak hours (19:00-22:00).",
        "defaults": {"fleet_expansion_pct": 15.0, "sla_reduction_pct": 25.0, "cost_incentive_pool": 45000.0}
    },
    "restaurant_capacity_acceleration": {
        "title": "Merchant Kitchen Prep Acceleration (-5 Mins)",
        "domain": "Restaurant Optimization",
        "description": "Optimizes kitchen dispatch buffering and prep queues to recover lost cancellation volume.",
        "defaults": {"cancellation_drop_pct": 40.0}
    },
    "customer_retention_campaign": {
        "title": "VIP Customer Retention Defense",
        "domain": "Customer Retention",
        "description": "Deploys a targeted voucher pool for verified VIP Champions inactive >60 days.",
        "defaults": {"retention_budget": 45000.0, "retention_rate_pct": 35.0}
    }
}

# Scenario Selector
render_section_header("Prescriptive Simulation Models", tag="SCENARIO SELECTION")

selected_scenario_key = st.selectbox(
    "Select What-If Scenario Archetype to Model:",
    list(SCENARIOS.keys()),
    format_func=lambda k: f"{SCENARIOS[k]['title']} [{SCENARIOS[k]['domain']}]",
    key="prescriptive_scenario_choice"
)

active_sc = SCENARIOS[selected_scenario_key]
st.info(f"📋 **Scenario Description:** {active_sc['description']}")

# Simulation Parameter Controls
render_section_header("Scenario Policy Controls & Sensitivity Sliders", tag="PARAMETERS")

param_overrides = {}

if selected_scenario_key == "promotion_optimization":
    c1, c2 = st.columns(2)
    with c1:
        param_overrides["discount_reduction_pct"] = st.slider(
            "Target Discount Reduction (%):",
            min_value=5.0, max_value=30.0,
            value=active_sc["defaults"]["discount_reduction_pct"], step=1.0,
            help="Percentage reduction in total platform-subsidized discount spend."
        )
    with c2:
        param_overrides["volume_elasticity_pct"] = st.slider(
            "Volume Elasticity Sensitivity (%):",
            min_value=-5.0, max_value=0.0,
            value=active_sc["defaults"]["volume_elasticity_pct"], step=0.5,
            help="Projected demand contraction from price-sensitive promo users."
        )

elif selected_scenario_key == "delivery_fee_restructuring":
    c1, c2, c3 = st.columns(3)
    with c1:
        param_overrides["fee_delta_rupees"] = st.slider(
            "Long-Distance Surcharge (₹ on >5km):",
            min_value=5.0, max_value=30.0,
            value=active_sc["defaults"]["fee_delta_rupees"], step=5.0
        )
    with c2:
        param_overrides["aov_uplift_pct"] = st.slider(
            "Basket AOV Uplift (% from Combo MOV):",
            min_value=1.0, max_value=10.0,
            value=active_sc["defaults"]["aov_uplift_pct"], step=0.5
        )
    with c3:
        param_overrides["volume_elasticity_pct"] = st.slider(
            "Volume Contraction (% from Surcharge):",
            min_value=-6.0, max_value=-0.5,
            value=active_sc["defaults"]["volume_elasticity_pct"], step=0.5
        )

elif selected_scenario_key == "rider_capacity_expansion":
    c1, c2, c3 = st.columns(3)
    with c1:
        param_overrides["fleet_expansion_pct"] = st.slider(
            "Peak Hour Fleet Expansion (%):",
            min_value=5.0, max_value=35.0,
            value=active_sc["defaults"]["fleet_expansion_pct"], step=5.0
        )
    with c2:
        param_overrides["sla_reduction_pct"] = st.slider(
            "SLA Breach (>45m) Reduction (%):",
            min_value=10.0, max_value=50.0,
            value=active_sc["defaults"]["sla_reduction_pct"], step=5.0
        )
    with c3:
        param_overrides["cost_incentive_pool"] = st.slider(
            "Rider Completion Bonus Pool (₹):",
            min_value=20000.0, max_value=100000.0,
            value=active_sc["defaults"]["cost_incentive_pool"], step=5000.0
        )

elif selected_scenario_key == "restaurant_capacity_acceleration":
    param_overrides["cancellation_drop_pct"] = st.slider(
        "Merchant Cancellation Reduction (%):",
        min_value=15.0, max_value=60.0,
        value=active_sc["defaults"]["cancellation_drop_pct"], step=5.0
    )

elif selected_scenario_key == "customer_retention_campaign":
    c1, c2 = st.columns(2)
    with c1:
        param_overrides["retention_budget"] = st.slider(
            "Targeted VIP Retention Voucher Pool (₹):",
            min_value=20000.0, max_value=100000.0,
            value=active_sc["defaults"]["retention_budget"], step=5000.0
        )
    with c2:
        param_overrides["retention_rate_pct"] = st.slider(
            "Target VIP Re-engagement Conversion (%):",
            min_value=15.0, max_value=60.0,
            value=active_sc["defaults"]["retention_rate_pct"], step=5.0
        )

# Execute Controlled Scenario Simulation
sim_results = run_controlled_scenario_simulation(
    scenario_type=selected_scenario_key,
    data_dict=data,
    param_overrides=param_overrides
)

# Mandatory Projection Disclaimer
render_callout(
    title="PROJECTION DISCLAIMER — HYPOTHETICAL WHAT-IF MODEL",
    message=sim_results.get("disclaimer", "Simulated outcomes are mathematical projections based on historical cohort elasticities."),
    level="warning"
)

# Projected Variance Deltas KPI Strip
render_section_header("Projected Strategic Impact & Metric Deltas", tag="VARIANCE DELTAS")

deltas = sim_results.get("variance_deltas", {})
base = sim_results.get("baseline", {})
proj = sim_results.get("projected_outcomes", {})

kpi_cols = st.columns(4)
with kpi_cols[0]:
    margin_delta = deltas.get("margin_delta_rupees", 0.0)
    st.metric(
        "Net Margin Delta",
        f"{'+' if margin_delta >= 0 else ''}{format_currency(margin_delta)}",
        delta=f"{deltas.get('margin_delta_percentage', 0.0):+.2f}% margin shift",
        delta_color="normal" if margin_delta >= 0 else "inverse"
    )
with kpi_cols[1]:
    orders_delta = deltas.get("orders_delta", 0)
    st.metric(
        "Projected Orders",
        format_number(proj.get("projected_delivered_orders", 0)),
        delta=f"{'+' if orders_delta >= 0 else ''}{format_number(orders_delta)} vs baseline",
        delta_color="normal" if orders_delta >= 0 else "inverse"
    )
with kpi_cols[2]:
    gmv_delta = deltas.get("gmv_delta", 0.0)
    st.metric(
        "Projected Gross GMV",
        format_currency(proj.get("projected_gross_gmv", 0.0)),
        delta=f"{'+' if gmv_delta >= 0 else ''}{format_currency(gmv_delta)}",
        delta_color="normal" if gmv_delta >= 0 else "inverse"
    )
with kpi_cols[3]:
    sla_prev = deltas.get("sla_breaches_prevented", 0)
    st.metric(
        "SLA Breaches Prevented",
        format_number(sla_prev),
        delta=f"New Rate: {proj.get('projected_sla_breach_rate_pct', 0.0):.1f}%",
        delta_color="normal" if sla_prev > 0 else "off"
    )

# Side-by-Side Comparison Table
render_section_header("Audited Baseline vs. Simulated Projection Comparison", tag="SIDE-BY-SIDE")

comp_df = pd.DataFrame([
    {
        "Metric": "Delivered Orders",
        "Audited Baseline": f"{format_number(base.get('delivered_orders', 0))}",
        "Simulated Projection": f"{format_number(proj.get('projected_delivered_orders', 0))}",
        "Variance Delta": f"{'+' if deltas.get('orders_delta', 0) >= 0 else ''}{format_number(deltas.get('orders_delta', 0))}"
    },
    {
        "Metric": "Gross Food GMV",
        "Audited Baseline": format_currency(base.get("realized_gross_gmv", 0.0)),
        "Simulated Projection": format_currency(proj.get("projected_gross_gmv", 0.0)),
        "Variance Delta": f"{'+' if deltas.get('gmv_delta', 0.0) >= 0 else ''}{format_currency(deltas.get('gmv_delta', 0.0))}"
    },
    {
        "Metric": "Net Platform Revenue",
        "Audited Baseline": format_currency(base.get("realized_net_revenue", 0.0)),
        "Simulated Projection": format_currency(proj.get("projected_net_revenue", 0.0)),
        "Variance Delta": f"{'+' if deltas.get('net_revenue_delta', 0.0) >= 0 else ''}{format_currency(deltas.get('net_revenue_delta', 0.0))}"
    },
    {
        "Metric": "Net Contribution Margin",
        "Audited Baseline": f"{format_currency(base.get('net_contribution_margin', 0.0))} ({base.get('margin_percentage', 0.0):.1f}%)",
        "Simulated Projection": f"{format_currency(proj.get('projected_contribution_margin', 0.0))} ({proj.get('projected_margin_percentage', 0.0):.1f}%)",
        "Variance Delta": f"{'+' if deltas.get('margin_delta_rupees', 0.0) >= 0 else ''}{format_currency(deltas.get('margin_delta_rupees', 0.0))}"
    },
    {
        "Metric": "SLA Breaches (>45m)",
        "Audited Baseline": f"{format_number(base.get('sla_breach_count', 0))} ({base.get('sla_breach_rate_pct', 0.0):.1f}%)",
        "Simulated Projection": f"{format_number(proj.get('projected_sla_breaches', 0))} ({proj.get('projected_sla_breach_rate_pct', 0.0):.1f}%)",
        "Variance Delta": f"-{format_number(deltas.get('sla_breaches_prevented', 0))} breaches"
    }
])

render_data_table(comp_df)

# Visual Comparison Chart
render_section_header("Financial Metrics Comparison (Lakhs INR)", tag="VISUAL COMPARISON")

metrics_labels = ["Gross Food GMV", "Net Revenue", "Contribution Profit"]
base_vals = [
    round(base.get("realized_gross_gmv", 0.0) / 100000, 2),
    round(base.get("realized_net_revenue", 0.0) / 100000, 2),
    round(base.get("net_contribution_margin", 0.0) / 100000, 2),
]
proj_vals = [
    round(proj.get("projected_gross_gmv", 0.0) / 100000, 2),
    round(proj.get("projected_net_revenue", 0.0) / 100000, 2),
    round(proj.get("projected_contribution_margin", 0.0) / 100000, 2),
]

fig = go.Figure(data=[
    go.Bar(name="Audited Baseline", x=metrics_labels, y=base_vals, marker_color="#475569"),
    go.Bar(name="Simulated Projection", x=metrics_labels, y=proj_vals, marker_color="#06B6D4")
])

fig.update_layout(
    barmode="group",
    paper_bgcolor="#0F172A",
    plot_bgcolor="#0F172A",
    font={"color": "#E2E8F0"},
    yaxis_title="Amount (₹ Lakhs)",
    height=400,
    margin=dict(t=30, l=40, r=40, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# Audited Assumptions
with st.expander("🔍 Grounded Scenario Assumptions & Elasticity Derivations", expanded=True):
    assumptions = sim_results.get("scenario_assumptions", [])
    for ass in assumptions:
        st.markdown(f"- {ass}")
