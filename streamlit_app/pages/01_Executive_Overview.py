"""
Page 1: Executive Overview
--------------------------
Enterprise view of platform revenue, order volumes, market penetration,
fulfillment health, and partner network velocity.
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
from components.status_components import render_section_header, render_data_table
from components.contextual_ai import build_contextual_payload, render_contextual_ai_inline

st.set_page_config(page_title=f"Executive Overview — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

orders_df = data.get("orders", pd.DataFrame())
customers_df = data.get("customers", pd.DataFrame())
restaurants_df = data.get("restaurants", pd.DataFrame())
deliveries_df = data.get("deliveries", pd.DataFrame())

# Apply filters
if filters["city"] != "All" and not orders_df.empty and "city" in restaurants_df.columns:
    city_rest_ids = set(restaurants_df[restaurants_df["city"] == filters["city"]]["restaurant_id"])
    orders_df = orders_df[orders_df["restaurant_id"].isin(city_rest_ids)]

if filters["status"] != "All" and not orders_df.empty and "order_status" in orders_df.columns:
    orders_df = orders_df[orders_df["order_status"] == filters["status"]]

# Header
render_page_header(
    title="Executive Overview",
    subtitle="Global Platform KPIs, Financial Growth Velocity & Multi-City Market Health",
    category="EXECUTIVE INTELLIGENCE",
    data_source=data_source,
    record_count=len(orders_df)
)

# Metric Calculations aligned with Certified Phase 04 KPIs
total_orders = len(orders_df)
has_status = "order_status" in orders_df.columns
non_cancelled = orders_df[orders_df["order_status"] != "Cancelled"] if not orders_df.empty and has_status else orders_df
delivered_df = orders_df[orders_df["order_status"] == "Delivered"] if not orders_df.empty and has_status else orders_df
total_gmv = float(non_cancelled["order_amount"].sum()) if not non_cancelled.empty and "order_amount" in non_cancelled.columns else 0.0
net_revenue = float(delivered_df["final_amount"].sum()) if not delivered_df.empty and "final_amount" in delivered_df.columns else total_gmv
delivered_count = len(delivered_df)
avg_order_value = (net_revenue / delivered_count) if delivered_count > 0 else 0.0
gross_aov = (total_gmv / delivered_count) if delivered_count > 0 else 0.0
cancelled_count = int((orders_df["order_status"] == "Cancelled").sum()) if has_status else 0
cancel_rate = (cancelled_count / total_orders * 100.0) if total_orders > 0 else 0.0
fulfillment_rate = (delivered_count / total_orders * 100.0) if total_orders > 0 else 0.0
active_merchants = non_cancelled["restaurant_id"].nunique() if (not non_cancelled.empty and "restaurant_id" in non_cancelled.columns) else 0

city_scope = f" in {filters['city']}" if filters["city"] != "All" else ""

render_kpi_row([
    {
        "label": "Gross Revenue (GMV)",
        "value": format_currency(total_gmv),
        "subtext": "Non-cancelled gross transaction value",
        "delta": f"Net Inflow: {format_currency(net_revenue)}",
        "delta_positive": total_gmv > 0,
        "accent": "blue",
        "ai_payload": build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="kpi_gmv",
            selected_metric="Gross Revenue (GMV)",
            metric_value=total_gmv,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze platform GMV and revenue velocity{city_scope}.",
        ),
    },
    {
        "label": "Fulfillment Orders",
        "value": format_number(delivered_count),
        "subtext": f"{total_orders:,} total orders placed",
        "delta": f"{fulfillment_rate:.1f}% delivered",
        "delta_positive": fulfillment_rate >= 90.0,
        "accent": "emerald",
        "ai_payload": build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="kpi_fulfillment",
            selected_metric="Fulfillment Orders",
            metric_value=delivered_count,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze order fulfillment and delivery performance{city_scope}.",
        ),
    },
    {
        "label": "Net Average Order Value",
        "value": format_currency(avg_order_value),
        "subtext": "Delivered final inflow per order",
        "delta": f"Gross AOV: {format_currency(gross_aov)}",
        "delta_positive": avg_order_value >= 400,
        "accent": "cyan",
        "ai_payload": build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="kpi_aov",
            selected_metric="Net Average Order Value",
            metric_value=avg_order_value,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze average order value dynamics and basket sizes{city_scope}.",
        ),
    },
    {
        "label": "Cancellation Rate",
        "value": format_percent(cancel_rate),
        "subtext": f"{cancelled_count:,} cancelled orders",
        "delta": "< 4.0% SLA threshold",
        "delta_positive": cancel_rate < 4.0,
        "accent": "crimson" if cancel_rate >= 5.0 else "amber",
        "ai_payload": build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="kpi_cancellation",
            selected_metric="Cancellation Rate",
            metric_value=cancel_rate,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Why are orders getting cancelled and what are the root causes{city_scope}?",
        ),
    },
    {
        "label": "Transacting Merchants",
        "value": format_number(active_merchants),
        "subtext": "Active restaurant partners",
        "delta": f"{len(restaurants_df):,} onboarded" if not restaurants_df.empty else "Active",
        "delta_positive": active_merchants > 0,
        "accent": "violet",
        "ai_payload": build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="kpi_merchants",
            selected_metric="Transacting Merchants",
            metric_value=active_merchants,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze restaurant partner participation and merchant distribution{city_scope}.",
        ),
    }
])

# Charts Section 1: Revenue & Volume Over Time
render_section_header("Revenue & Volume Velocity", tag="TEMPORAL DYNAMICS")

c1, c2 = st.columns([2, 1])

time_col = "order_datetime" if "order_datetime" in non_cancelled.columns else ("order_time" if "order_time" in non_cancelled.columns else None)
with c1:
    if not non_cancelled.empty and time_col:
        trend_df = non_cancelled.copy()
        trend_df["date"] = pd.to_datetime(trend_df[time_col], errors="coerce").dt.date
        trend_df = trend_df.dropna(subset=["date"])
        daily_perf = trend_df.groupby("date").agg(
            GMV=("order_amount", "sum"),
            Orders=("order_id", "count")
        ).reset_index().sort_values("date").tail(45)
        render_line_chart(daily_perf, x="date", y="GMV", title="Daily Non-Cancelled GMV Velocity (₹)")
        render_contextual_ai_inline(
            build_contextual_payload(
                dashboard_name="Executive Overview",
                kpi_or_chart_id="chart_revenue_velocity",
                selected_metric="Revenue Velocity Trend",
                active_filters=filters,
                city=filters.get("city"),
                suggested_prompt=f"Analyze daily revenue velocity trends and detect growth anomalies{city_scope}.",
            ),
            key="exec_rev_trend_inline",
        )
    else:
        st.info("Time series order data not available.")

with c2:
    if not orders_df.empty and "order_status" in orders_df.columns:
        status_counts = orders_df["order_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        render_donut_chart(status_counts, names="Status", values="Count", title="Order Fulfillment Split")
    else:
        st.info("Status distribution data not available.")

# Charts Section 2: Market & Persona Performance
render_section_header("Market Expansion & Customer Personas", tag="SEGMENT PERFORMANCE")

c3, c4 = st.columns(2)

with c3:
    if not non_cancelled.empty and not restaurants_df.empty and "city" in restaurants_df.columns:
        merged_res = non_cancelled.merge(restaurants_df[["restaurant_id", "city"]], on="restaurant_id", how="left")
        city_stats = merged_res.groupby("city").agg(
            Revenue=("order_amount", "sum")
        ).reset_index().sort_values(by="Revenue", ascending=False)
        render_bar_chart(city_stats, x="city", y="Revenue", title="Non-Cancelled GMV Contribution by Metro (₹)")
    else:
        st.info("City performance data unavailable.")

with c4:
    if not non_cancelled.empty and not customers_df.empty and "customer_persona" in customers_df.columns:
        merged_cust = non_cancelled.merge(customers_df[["customer_id", "customer_persona"]], on="customer_id", how="left")
        persona_stats = merged_cust.groupby("customer_persona").agg(
            Orders=("order_id", "count")
        ).reset_index().sort_values(by="Orders", ascending=False)
        render_bar_chart(persona_stats, x="customer_persona", y="Orders", title="Order Volume by Customer Persona")
    else:
        st.info("Persona performance data unavailable.")

# Top Performing Partners Table
render_section_header("Top Performing Restaurant Partners", tag="MERCHANT LEADERBOARD")

if not non_cancelled.empty and not restaurants_df.empty:
    merchant_table = non_cancelled.groupby("restaurant_id").agg(
        Orders=("order_id", "count"),
        Gross_Sales=("order_amount", "sum")
    ).reset_index()
    rating_col = "avg_rating" if "avg_rating" in restaurants_df.columns else ("rating" if "rating" in restaurants_df.columns else None)
    merge_cols = ["restaurant_id", "restaurant_name", "city", "cuisine_type"] + ([rating_col] if rating_col else [])
    merchant_table = merchant_table.merge(restaurants_df[merge_cols], on="restaurant_id", how="left")
    merchant_table = merchant_table.sort_values(by="Gross_Sales", ascending=False).head(15)
    merchant_table["Gross_Sales"] = merchant_table["Gross_Sales"].apply(lambda v: format_currency(v))
    rename_map = {
        "restaurant_id": "Partner ID",
        "restaurant_name": "Restaurant Name",
        "city": "City",
        "cuisine_type": "Cuisine",
        "Orders": "Orders",
        "Gross_Sales": "Gross Sales",
    }
    if rating_col:
        rename_map[rating_col] = "Rating"
    else:
        merchant_table["Rating"] = "N/A"
    merchant_table = merchant_table.rename(columns=rename_map)
    render_data_table(merchant_table[["Partner ID", "Restaurant Name", "City", "Cuisine", "Rating", "Orders", "Gross Sales"]])
    render_contextual_ai_inline(
        build_contextual_payload(
            dashboard_name="Executive Overview",
            kpi_or_chart_id="table_top_merchants",
            selected_metric="Top Restaurant Partners",
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Which top restaurants are driving our revenue and which need SLA intervention{city_scope}?",
        ),
        key="exec_top_merchants_inline",
    )
else:
    st.info("No non-cancelled orders available for the selected filters.")
