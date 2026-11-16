"""
Page 9: NovaNest Command Center & Digital Twin
----------------------------------------------
Unified analytical Digital Twin orchestrating cross-system state representations,
downstream dependency impact chains, and systemic anomaly alerts.
"""

from pathlib import Path
import datetime
import pandas as pd
import streamlit as st

import bootstrap
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from utils.data_loader import load_all_datasets
from utils.formatting import format_currency, format_number, format_percent
from components.navigation import render_sidebar
from components.page_header import render_page_header
from components.kpi_components import render_kpi_row
from components.status_components import render_section_header, render_callout, render_data_table
from components.insight_components import render_insight_summary

from digital_twin.twin_engine import build_digital_twin_state
from digital_twin.twin_dependencies import get_impact_chain
from ai.insights.business_insights import generate_business_insights
from decision.next_best_action import generate_next_best_actions

st.set_page_config(page_title=f"Command Center — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data & Build Twin State
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

twin_state = build_digital_twin_state(data)

fin = twin_state.financial_state
cust = twin_state.customer_state
rest = twin_state.restaurant_state
ops = twin_state.operations_state
alerts = twin_state.alerts

health_score = fin.get("Business_Health_Score")
late_deliv = ops.get("Late_Deliveries")
ops_fulfillment = ops.get("Fulfillment_Rate")
at_risk_cust = cust.get("High_Churn_Risk_Customers")

# Header
render_page_header(
    title="NovaNest Command Center & Digital Twin",
    subtitle="Unified Autonomous Orchestration, Systemic Telemetry & Cross-Domain Impact Chains",
    category="DIGITAL TWIN ORCHESTRATION",
    data_source=data_source
)

# Top Telemetry KPIs
render_kpi_row([
    {
        "label": "Platform Twin Health Index",
        "value": f"{health_score}/100" if health_score is not None else "Unavailable",
        "subtext": "Composite systemic vitality",
        "delta": ("Nominal operations" if health_score >= 80 else "Caution threshold") if health_score is not None else "Data unavailable",
        "delta_positive": bool(health_score is not None and health_score >= 80),
        "accent": "emerald" if (health_score is not None and health_score >= 80) else "amber"
    },
    {
        "label": "Financial Margin Health",
        "value": format_percent((fin.get("Profit_Margin") or 0) * 100),
        "subtext": f"{format_currency(fin.get('Gross_Revenue') or 0)} GMV",
        "delta": "Target: > 10%",
        "delta_positive": (fin.get("Profit_Margin") or 0) >= 0.10,
        "accent": "blue"
    },
    {
        "label": "Customer Base Stability",
        "value": format_number(cust.get("Total_Customers") or 0),
        "subtext": f"{at_risk_cust:,} churn risk" if at_risk_cust is not None else "Churn score unavailable",
        "delta": "Retention monitored" if at_risk_cust is not None else "Model pending",
        "delta_positive": at_risk_cust is None or at_risk_cust < 500,
        "accent": "violet"
    },
    {
        "label": "Logistics Dispatch Health",
        "value": format_percent(ops_fulfillment) if ops_fulfillment is not None else "Unavailable",
        "subtext": f"{late_deliv:,} delayed (>45m)" if late_deliv is not None else "Delivery telemetry unavailable",
        "delta": "90% SLA standard",
        "delta_positive": bool(ops_fulfillment is not None and ops_fulfillment >= 90.0),
        "accent": "cyan"
    },
    {
        "label": "Active Systemic Alerts",
        "value": str(len(alerts)),
        "subtext": "Cross-domain trigger warnings",
        "delta": "Real-time monitor",
        "delta_positive": len(alerts) == 0,
        "accent": "crimson" if len(alerts) > 0 else "emerald"
    }
])

# 4-Pillar Digital Twin Matrix
render_section_header("Four-Pillar Digital Twin Telemetry Matrix", tag="SYSTEMIC STATE")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="nn-kpi-card accent-blue" style="min-height: 220px;">
        <div class="nn-kpi-label">Pillar 1: Financial Twin</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.35rem 0;">Gross Revenue & Margin</div>
        <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.6;">
            • <strong>Gross GMV:</strong> {format_currency(fin.get('Gross_Revenue') or 0)}<br>
            • <strong>Net Platform Inflow:</strong> {format_currency(fin.get('Net_Platform_Revenue') or 0)}<br>
            • <strong>Profit Margin:</strong> {format_percent((fin.get('Profit_Margin') or 0) * 100)}<br>
            • <strong>Exposure Candidates:</strong> {format_currency(fin.get('Revenue_Leakage_Est') or 0)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    ret_rate_val = cust.get("Retention_Rate")
    ret_str = format_percent(ret_rate_val * 100) if ret_rate_val is not None else "Unavailable"
    hr_str = f"{at_risk_cust:,}" if at_risk_cust is not None else "Unavailable"
    st.markdown(f"""
    <div class="nn-kpi-card accent-violet" style="min-height: 220px;">
        <div class="nn-kpi-label">Pillar 2: Customer Twin</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.35rem 0;">Audience & Retention</div>
        <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.6;">
            • <strong>Registered Users:</strong> {format_number(cust.get('Total_Customers') or 0)}<br>
            • <strong>Active Orderers:</strong> {format_number(cust.get('Active_Customers') or 0)}<br>
            • <strong>High Churn Risk:</strong> {hr_str}<br>
            • <strong>Retention Index:</strong> {ret_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    avg_r_val = rest.get("Avg_Rating")
    avg_r_str = f"{avg_r_val:.2f} ★" if avg_r_val is not None else "Unavailable"
    healthy_r = rest.get("Healthy_Restaurants")
    cancel_r = rest.get("High_Cancellation_Partners")
    st.markdown(f"""
    <div class="nn-kpi-card accent-amber" style="min-height: 220px;">
        <div class="nn-kpi-label">Pillar 3: Restaurant Twin</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.35rem 0;">Merchant Operations</div>
        <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.6;">
            • <strong>Partner Count:</strong> {format_number(rest.get('Total_Restaurants') or 0)}<br>
            • <strong>Healthy Partners:</strong> {format_number(healthy_r) if healthy_r is not None else 'Unavailable'}<br>
            • <strong>High Cancel Partners:</strong> {f'{cancel_r:,}' if cancel_r is not None else 'Unavailable'}<br>
            • <strong>Avg Network Rating:</strong> {avg_r_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    avg_eta_val = ops.get("Avg_Delivery_Time")
    eta_str = f"{avg_eta_val:.1f} mins" if avg_eta_val is not None else "Unavailable"
    late_str = f"{late_deliv:,}" if late_deliv is not None else "Unavailable"
    st.markdown(f"""
    <div class="nn-kpi-card accent-cyan" style="min-height: 220px;">
        <div class="nn-kpi-label">Pillar 4: Operations Twin</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.35rem 0;">Dispatch & Logistics</div>
        <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.6;">
            • <strong>Total Orders:</strong> {format_number(ops.get('Total_Orders') or 0)}<br>
            • <strong>Late Deliveries (>45m):</strong> {late_str}<br>
            • <strong>Avg Delivery Time:</strong> {eta_str}<br>
            • <strong>Logistics Risk Level:</strong> {ops.get('Logistics_Risk', 'Unavailable')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Systemic Dependency Ripple Simulator
render_section_header("Systemic Dependency Ripple Graph", tag="IMPACT CHAIN ENGINE")

d_col1, d_col2 = st.columns([1, 2])

with d_col1:
    event_choice = st.selectbox(
        "Select Trigger Event to Trace Ripple Impacts:",
        [
            ("demand_spike", "Surge Demand Spike (+30% Orders)"),
            ("high_discount", "Unrestrained Discount Subsidy Stacking"),
            ("restaurant_churn", "Critical Restaurant Partner Churn")
        ],
        format_func=lambda x: x[1],
        key="dep_event_select"
    )
    chain = get_impact_chain(event_choice[0])

with d_col2:
    chain_html = ""
    for idx, step in enumerate(chain):
        is_last = idx == len(chain) - 1
        arrow = "→" if not is_last else "⚡"
        color = "#EF4444" if is_last else "#60A5FA"
        chain_html += f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.45rem;">
            <div style="width: 22px; height: 22px; border-radius: 50%; background: rgba(59,130,246,0.2); border: 1px solid rgba(59,130,246,0.4); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; color: #93C5FD;">{idx+1}</div>
            <div style="font-size: 0.88rem; font-weight: 600; color: {color};">{step}</div>
        </div>
        """
    st.markdown(f"""
    <div style="background: var(--nn-bg-card); border: 1px solid var(--nn-border); border-radius: 8px; padding: 1.25rem;">
        <div style="font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 0.65rem;">Causal Downstream Propagation Chain</div>
        {chain_html}
    </div>
    """, unsafe_allow_html=True)

# Active Systemic Alerts Queue
render_section_header("Active Systemic Anomaly Signals", tag="TELEMETRY ALERTS")

if alerts:
    for idx, a in enumerate(alerts):
        sev = str(a.get("Severity", "Warning")).upper()
        lvl = "danger" if sev == "CRITICAL" else ("warning" if sev in ("HIGH", "MEDIUM", "WARNING") else "info")
        render_callout(
            title=f"[{sev}] {a.get('Category', 'System')} — {a.get('Signal', 'Telemetry Signal')}",
            message=f"{a.get('Business_Impact', '')}<br><strong>Recommended Action:</strong> {a.get('Recommended_Action', '')}",
            level=lvl
        )
else:
    render_callout(
        title="Zero Active Systemic Anomalies",
        message="All cross-domain digital twin telemetry channels are performing within established operational tolerances.",
        level="success"
    )

# Automated Action Dispatcher
render_section_header("Autonomous Action Dispatcher", tag="DISPATCH ENGINE")
actions = generate_next_best_actions(data.get("orders", pd.DataFrame()))
for idx, act in enumerate(actions):
    st.markdown(f"""
    <div style="background: var(--nn-bg-card); border: 1px solid var(--nn-border); border-left: 3px solid #3B82F6; border-radius: 6px; padding: 0.85rem 1.15rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.85rem; font-weight: 600; color: #F8FAFC;">{act}</div>
        <span style="font-size: 0.7rem; font-weight: 700; color: #34D399; background: rgba(16,185,129,0.15); padding: 0.2rem 0.5rem; border-radius: 4px;">ACTIVE DISPATCH</span>
    </div>
    """, unsafe_allow_html=True)
