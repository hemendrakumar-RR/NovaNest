"""
NovaNest — Enterprise Business Analytics & Intelligence Hub
------------------------------------------------------------
Main application entry point orchestrating platform telemetry,
high-level executive vitals, module routing, and multi-domain intelligence.
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
from components.chart_components import render_line_chart, render_bar_chart, render_donut_chart
from components.status_components import render_section_header, render_callout
from components.insight_components import render_insight_summary

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# 1. Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

orders_df = data.get("orders", pd.DataFrame())
customers_df = data.get("customers", pd.DataFrame())
restaurants_df = data.get("restaurants", pd.DataFrame())
deliveries_df = data.get("deliveries", pd.DataFrame())
orders_eng = data.get("orders_engineered", pd.DataFrame())

# Apply Global City Filter if selected
if filters["city"] != "All" and not orders_df.empty and "city" in restaurants_df.columns:
    city_rest_ids = set(restaurants_df[restaurants_df["city"] == filters["city"]]["restaurant_id"])
    filtered_orders = orders_df[orders_df["restaurant_id"].isin(city_rest_ids)]
else:
    filtered_orders = orders_df

# 2. Page Header
render_page_header(
    title="Enterprise Mission Control",
    subtitle="Unified Business Intelligence, Multi-Agent Decision Engine & Digital Twin",
    category="NOVANEST CORE",
    data_source=data_source,
    record_count=len(filtered_orders)
)

# 3. Calculate Core Platform Vitals (aligned with Phase 04 Certified KPIs)
total_orders = len(filtered_orders)
has_status = "order_status" in filtered_orders.columns
non_cancelled = filtered_orders[filtered_orders["order_status"] != "Cancelled"] if total_orders > 0 and has_status else filtered_orders
delivered_orders = filtered_orders[filtered_orders["order_status"] == "Delivered"] if total_orders > 0 and has_status else filtered_orders
total_gmv = float(non_cancelled["order_amount"].sum()) if not non_cancelled.empty and "order_amount" in non_cancelled else 0.0
net_revenue = float(delivered_orders["final_amount"].sum()) if not delivered_orders.empty and "final_amount" in delivered_orders else total_gmv
delivered_count = len(delivered_orders)
fulfillment_rate = (delivered_count / total_orders * 100.0) if total_orders > 0 else 0.0

active_customers = len(customers_df)
active_restaurants = len(restaurants_df)
metro_count = restaurants_df["city"].nunique() if not restaurants_df.empty and "city" in restaurants_df.columns else 0
rating_col = "avg_rating" if "avg_rating" in restaurants_df.columns else ("rating" if "rating" in restaurants_df.columns else None)
avg_partner_rating = float(restaurants_df[rating_col].dropna().mean()) if (not restaurants_df.empty and rating_col and not restaurants_df[rating_col].dropna().empty) else None

# Core KPI Row
render_kpi_row([
    {
        "label": "Gross Merchandise Value",
        "value": format_currency(total_gmv),
        "subtext": "Non-cancelled order value (KPI-01)",
        "delta": f"Net Inflow: {format_currency(net_revenue)}",
        "delta_positive": total_gmv > 0,
        "accent": "blue"
    },
    {
        "label": "Total Orders Placed",
        "value": format_number(total_orders),
        "subtext": f"{delivered_count:,} successfully delivered",
        "delta": f"{len(non_cancelled):,} active orders",
        "delta_positive": delivered_count > 0,
        "accent": "emerald"
    },
    {
        "label": "Fulfillment Rate",
        "value": format_percent(fulfillment_rate),
        "subtext": "Delivered share of total orders",
        "delta": "95% SLA benchmark",
        "delta_positive": fulfillment_rate >= 95,
        "accent": "cyan"
    },
    {
        "label": "Customer Base",
        "value": format_number(active_customers),
        "subtext": "Registered user accounts",
        "delta": f"{metro_count} metros" if metro_count > 0 else "Unavailable",
        "delta_positive": active_customers > 0,
        "accent": "violet"
    },
    {
        "label": "Partner Network",
        "value": format_number(active_restaurants),
        "subtext": "Verified food merchants",
        "delta": f"{avg_partner_rating:.2f}★ avg rating" if avg_partner_rating is not None else "Rating unavailable",
        "delta_positive": avg_partner_rating is None or avg_partner_rating >= 4.0,
        "accent": "amber"
    }
])

# 4. Intelligence Module Directory (Direct Launch Grid)
render_section_header("Intelligence Modules", tag="PLATFORM NAVIGATION")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="nn-kpi-card accent-blue" style="min-height: 160px; margin-bottom: 0.5rem;">
        <div class="nn-kpi-label">Module 01</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Executive Overview</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">High-level revenue trends, volume performance, unit margins, and market-level fulfillment.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Executive Overview →", key="launch_m1", width="stretch"):
        st.switch_page("pages/01_Executive_Overview.py")

    st.markdown("""
    <div class="nn-kpi-card accent-emerald" style="min-height: 160px; margin-bottom: 0.5rem; margin-top: 1rem;">
        <div class="nn-kpi-label">Module 04</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Operations Intelligence</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Live dispatch radar, demand forecasting, heatmaps, rider allocation & bottleneck alerts.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Operations Intelligence →", key="launch_m4", width="stretch"):
        st.switch_page("pages/04_Operations_Intelligence.py")

    st.markdown("""
    <div class="nn-kpi-card accent-violet" style="min-height: 160px; margin-bottom: 0.5rem; margin-top: 1rem;">
        <div class="nn-kpi-label">Module 07</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Ask NovaNest AI</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Natural language query conversational engine with automated SQL safety barrier.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Ask NovaNest AI →", key="launch_m7", width="stretch"):
        st.switch_page("pages/07_Ask_NovaNest.py")

with col2:
    st.markdown("""
    <div class="nn-kpi-card accent-violet" style="min-height: 160px; margin-bottom: 0.5rem;">
        <div class="nn-kpi-label">Module 02</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Customer Intelligence</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">RFM segmentation, customer lifetime value (CLV), cohort retention, and churn prevention.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Customer Intelligence →", key="launch_m2", width="stretch"):
        st.switch_page("pages/02_Customer_Intelligence.py")

    st.markdown("""
    <div class="nn-kpi-card accent-amber" style="min-height: 160px; margin-bottom: 0.5rem; margin-top: 1rem;">
        <div class="nn-kpi-label">Module 05</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Financial Intelligence</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Unit economics, contribution margins, subsidy auditing, and revenue leakage detection.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Financial Intelligence →", key="launch_m5", width="stretch"):
        st.switch_page("pages/05_Financial_Intelligence.py")

    st.markdown("""
    <div class="nn-kpi-card accent-cyan" style="min-height: 160px; margin-bottom: 0.5rem; margin-top: 1rem;">
        <div class="nn-kpi-label">Module 08</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Decision Simulator</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Multi-variable what-if business simulation engine for pricing, commissions & incentives.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Decision Simulator →", key="launch_m8", width="stretch"):
        st.switch_page("pages/08_Decision_Simulator.py")

with col3:
    st.markdown("""
    <div class="nn-kpi-card accent-amber" style="min-height: 160px; margin-bottom: 0.5rem;">
        <div class="nn-kpi-label">Module 03</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Restaurant Intelligence</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Merchant health scores, early risk warning system, kitchen SLA benchmarks & cuisine mix.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Restaurant Intelligence →", key="launch_m3", width="stretch"):
        st.switch_page("pages/03_Restaurant_Intelligence.py")

    st.markdown("""
    <div class="nn-kpi-card accent-blue" style="min-height: 160px; margin-bottom: 0.5rem; margin-top: 1rem;">
        <div class="nn-kpi-label">Module 06</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">Decision Intelligence</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Next-Best-Action engine synthesizing customer retention, partner SLA & operations.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Decision Intelligence →", key="launch_m6", width="stretch"):
        st.switch_page("pages/06_Decision_Intelligence.py")

    st.markdown("""
    <div class="nn-kpi-card accent-crimson" style="min-height: 160px; margin-bottom: 0.5rem; margin-top: 1rem;">
        <div class="nn-kpi-label">Module 09</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 0.2rem 0;">NovaNest Command Center</div>
        <div style="font-size: 0.8rem; color: #94A3B8;">Unified Digital Twin orchestrator, cross-system dependency graph & automated alerts.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open NovaNest Command Center →", key="launch_m9", width="stretch"):
        st.switch_page("pages/09_NovaNest_Command_Center.py")

# 5. Executive Pulse Trends
render_section_header("Platform Real-Time Pulse", tag="TELEMETRY SNAPSHOT")

chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    if not filtered_orders.empty and "order_time" in filtered_orders.columns:
        orders_trend = filtered_orders.copy()
        orders_trend["date"] = pd.to_datetime(orders_trend["order_time"]).dt.date
        daily_metrics = orders_trend.groupby("date").agg(
            Revenue=("order_amount", "sum"),
            Orders=("order_id", "count")
        ).reset_index().tail(30)
        render_line_chart(daily_metrics, x="date", y="Revenue", title="30-Day Platform Revenue Velocity (₹)")
    else:
        st.info("Order time-series data unavailable.")

with chart_col2:
    if not filtered_orders.empty and not restaurants_df.empty:
        merged_city = filtered_orders.merge(restaurants_df[["restaurant_id", "city"]], on="restaurant_id", how="left")
        city_breakdown = merged_city.groupby("city")["order_id"].count().reset_index()
        city_breakdown.columns = ["City", "Volume"]
        render_donut_chart(city_breakdown, names="City", values="Volume", title="Order Volume by Metro")
    else:
        st.info("City distribution data unavailable.")
