"""
Page 5: Financial Intelligence & Unit Economics
-----------------------------------------------
Gross Merchandise Value (GMV), Platform Commission Take Rates, Delivery Fee Revenues,
Subsidy Audits, Net Unit Economics, and Critical Revenue Leakage Intelligence.
"""

from pathlib import Path
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
from components.status_components import render_section_header, render_data_table, render_callout
from components.contextual_ai import build_contextual_payload, render_contextual_ai_inline

st.set_page_config(page_title=f"Financial Intelligence — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

orders_df = data.get("orders", pd.DataFrame())
orders_eng = data.get("orders_engineered", pd.DataFrame())
promotions_df = data.get("promotions", pd.DataFrame())
leakage_df = data.get("revenue_leakage", pd.DataFrame())
restaurants_df = data.get("restaurants", pd.DataFrame())

# Apply city filter if chosen
if filters["city"] != "All" and not orders_df.empty and "city" in restaurants_df.columns:
    city_rest_ids = set(restaurants_df[restaurants_df["city"] == filters["city"]]["restaurant_id"])
    orders_df = orders_df[orders_df["restaurant_id"].isin(city_rest_ids)]
    if not orders_eng.empty:
        orders_eng = orders_eng[orders_eng["restaurant_id"].isin(city_rest_ids)]

# Header
render_page_header(
    title="Financial Intelligence & Unit Economics",
    subtitle="Platform P&L Breakdown, Take Rate Velocity, Subsidy Audits & Revenue Leakage Detection",
    category="UNIT ECONOMICS & P&L",
    data_source=data_source,
    record_count=len(orders_df)
)

# Calculate Financial P&L Metrics aligned with Certified Phase 04 KPIs
non_cancelled = orders_df[orders_df["order_status"] != "Cancelled"] if not orders_df.empty and "order_status" in orders_df.columns else orders_df
delivered_df = orders_df[orders_df["order_status"] == "Delivered"] if not orders_df.empty and "order_status" in orders_df.columns else orders_df
deliv_count = len(delivered_df)

total_gmv = float(non_cancelled["order_amount"].sum()) if not non_cancelled.empty and "order_amount" in non_cancelled.columns else 0.0
net_revenue = float(delivered_df["final_amount"].sum()) if not delivered_df.empty and "final_amount" in delivered_df.columns else (
    float(delivered_df["order_amount"].sum()) if not delivered_df.empty and "order_amount" in delivered_df.columns else 0.0
)

eng_deliv = orders_eng[orders_eng["order_status"] == "Delivered"] if not orders_eng.empty and "order_status" in orders_eng.columns else orders_eng
comm_col = "commission_revenue" if not eng_deliv.empty and "commission_revenue" in eng_deliv.columns else (
    "commission_amount" if not eng_deliv.empty and "commission_amount" in eng_deliv.columns else None
)
if not eng_deliv.empty and comm_col:
    commission_rev = float(eng_deliv[comm_col].sum())
    delivery_fee_rev = float(eng_deliv["delivery_fee"].sum()) if "delivery_fee" in eng_deliv.columns else 0.0
    discount_spent = float(eng_deliv["discount_amount"].sum()) if "discount_amount" in eng_deliv.columns else 0.0
    realized_profit = float(eng_deliv["estimated_profit"].sum()) if "estimated_profit" in eng_deliv.columns else (commission_rev + delivery_fee_rev - discount_spent)
else:
    commission_rev = 0.0
    delivery_fee_rev = float(delivered_df["delivery_fee"].sum()) if not delivered_df.empty and "delivery_fee" in delivered_df.columns else 0.0
    discount_spent = float(delivered_df["discount_amount"].sum()) if not delivered_df.empty and "discount_amount" in delivered_df.columns else 0.0
    realized_profit = 0.0

take_rate = (commission_rev / total_gmv * 100.0) if total_gmv > 0 else 0.0
contrib_margin = (realized_profit / net_revenue * 100.0) if net_revenue > 0 else 0.0
leakage_amount = float(leakage_df["potential_leakage_amount"].sum()) if not leakage_df.empty and "potential_leakage_amount" in leakage_df.columns else 0.0

city_scope = f" in {filters['city']}" if filters["city"] != "All" else ""

render_kpi_row([
    {
        "label": "Gross Merchandise Value (GMV)",
        "value": format_currency(total_gmv),
        "subtext": "Non-cancelled gross food value (KPI-01)",
        "delta": f"{len(non_cancelled):,} active orders",
        "delta_positive": True,
        "accent": "blue",
        "ai_payload": build_contextual_payload(
            dashboard_name="Financial Intelligence",
            kpi_or_chart_id="kpi_fin_gmv",
            selected_metric="Gross Merchandise Value (GMV)",
            metric_value=total_gmv,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze platform GMV, realized volume, and order throughput{city_scope}.",
        ),
    },
    {
        "label": "Net Revenue (Platform Inflow)",
        "value": format_currency(net_revenue),
        "subtext": f"Delivered final inflow ({deliv_count:,} orders)",
        "delta": f"{take_rate:.2f}% commission take rate",
        "delta_positive": True,
        "accent": "emerald",
        "ai_payload": build_contextual_payload(
            dashboard_name="Financial Intelligence",
            kpi_or_chart_id="kpi_fin_net_revenue",
            selected_metric="Net Revenue (Platform Inflow)",
            metric_value=net_revenue,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze platform net revenue inflows, commission velocity, and take rates{city_scope}.",
        ),
    },
    {
        "label": "Realized Operating Profit",
        "value": format_currency(realized_profit),
        "subtext": f"{contrib_margin:.2f}% realized margin (KPI-12)",
        "delta": f"{format_currency(commission_rev)} commission",
        "delta_positive": contrib_margin >= 12.0,
        "accent": "cyan",
        "ai_payload": build_contextual_payload(
            dashboard_name="Financial Intelligence",
            kpi_or_chart_id="kpi_fin_realized_profit",
            selected_metric="Realized Operating Profit",
            metric_value=realized_profit,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze realized operating profit and contribution margin breakdown{city_scope}.",
        ),
    },
    {
        "label": "Promotional Subsidies",
        "value": format_currency(discount_spent),
        "subtext": "Delivered order discounts",
        "delta": f"{(discount_spent / total_gmv * 100.0 if total_gmv > 0 else 0.0):.2f}% of GMV",
        "delta_positive": discount_spent <= (total_gmv * 0.08),
        "accent": "amber",
        "ai_payload": build_contextual_payload(
            dashboard_name="Financial Intelligence",
            kpi_or_chart_id="kpi_fin_subsidies",
            selected_metric="Promotional Subsidies",
            metric_value=discount_spent,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Audit promotional subsidies and customer discount burn rate{city_scope}.",
        ),
    },
    {
        "label": "Potential Risk Exposure",
        "value": format_currency(leakage_amount),
        "subtext": "Unverified screening candidates",
        "delta": f"{len(leakage_df):,} audit flags (unconfirmed)",
        "delta_positive": leakage_amount == 0,
        "accent": "crimson",
        "ai_payload": build_contextual_payload(
            dashboard_name="Financial Intelligence",
            kpi_or_chart_id="kpi_fin_leakage",
            selected_metric="Potential Risk Exposure",
            metric_value=leakage_amount,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Investigate potential revenue leakage and uncollected platform commissions{city_scope}.",
        ),
    }
])

# Discovery Tabs
tab1, tab2, tab3 = st.tabs([
    "💵 P&L Waterfall & Unit Economics",
    "🛡️ Risk Exposure Audit Candidates",
    "🎟️ Promotion Catalog Metadata"
])

with tab1:
    render_section_header("Unit Economics Breakdown (Per Completed Order)", tag="UNIT MARGINS")
    avg_order = (net_revenue / deliv_count) if deliv_count > 0 else 0.0
    avg_comm = (commission_rev / deliv_count) if deliv_count > 0 else 0.0
    avg_deliv = (delivery_fee_rev / deliv_count) if deliv_count > 0 else 0.0
    avg_disc = (discount_spent / deliv_count) if deliv_count > 0 else 0.0
    avg_net = (realized_profit / deliv_count) if deliv_count > 0 else 0.0

    u1, u2, u3, u4, u5 = st.columns(5)
    with u1:
        st.metric("Net AOV (KPI-03)", format_currency(avg_order))
    with u2:
        st.metric("Avg Commission (+)", format_currency(avg_comm))
    with u3:
        st.metric("Avg Delivery Fee (+)", format_currency(avg_deliv))
    with u4:
        st.metric("Avg Discount Subsidy (-)", format_currency(avg_disc))
    with u5:
        st.metric("Realized Profit / Order", format_currency(avg_net), delta=f"{contrib_margin:.2f}%")

    if not orders_df.empty and not restaurants_df.empty and "city" in restaurants_df.columns:
        merged_fin = non_cancelled.merge(restaurants_df[["restaurant_id", "city"]], on="restaurant_id", how="left")
        city_fin = merged_fin.groupby("city").agg(
            GMV=("order_amount", "sum"),
            Non_Cancelled_Orders=("order_id", "count")
        ).reset_index()
        if not eng_deliv.empty and "city" not in eng_deliv.columns and "restaurant_id" in eng_deliv.columns:
            eng_city = eng_deliv.merge(restaurants_df[["restaurant_id", "city"]], on="restaurant_id", how="left")
            city_comm = eng_city.groupby("city").agg(
                Realized_Commission=(comm_col, "sum") if comm_col else ("order_amount", "count"),
                Delivered_Orders=("order_id", "count"),
                Net_Revenue=("final_amount", "sum")
            ).reset_index()
            city_fin = city_fin.merge(city_comm, on="city", how="left")
            city_fin["Net_AOV"] = (city_fin["Net_Revenue"] / city_fin["Delivered_Orders"]).apply(format_currency)
            city_fin["Realized_Commission"] = city_fin["Realized_Commission"].apply(format_currency)
            city_fin["Net_Revenue"] = city_fin["Net_Revenue"].apply(format_currency)
        else:
            city_fin["Net_AOV"] = (city_fin["GMV"] / city_fin["Non_Cancelled_Orders"]).apply(format_currency)
        city_fin["GMV"] = city_fin["GMV"].apply(format_currency)
        render_section_header("Metro Financial Contribution", tag="CITY REVENUE")
        render_data_table(city_fin)
        render_contextual_ai_inline(
            build_contextual_payload(
                dashboard_name="Financial Intelligence",
                kpi_or_chart_id="table_city_financial_contribution",
                selected_metric="Metro Financial Contribution",
                active_filters=filters,
                city=filters.get("city"),
                suggested_prompt=f"Analyze financial contribution, GMV yield, and realized commission take rate across metro cities{city_scope}.",
            ),
            key="fin_city_contrib_inline",
        )

with tab2:
    render_section_header("Potential Risk Exposure Audit (Investigation Candidates)", tag="RISK RADAR")
    if not leakage_df.empty:
        critical_leaks = leakage_df[leakage_df.get("risk_level", "") == "Critical Leakage"]
        render_callout(
            title="Potential Financial Risk Screening Candidates (Unverified)",
            message=(
                f"Screened {len(leakage_df):,} investigation candidates ({len(critical_leaks):,} critical flags; "
                f"total potential exposure: {format_currency(leakage_amount)}), spanning Cancelled Commission Loss "
                "and Post-Discount Margin Deficit flags. Flags reflect potential risk pending promo funding split "
                "and ledger reconciliation — not confirmed financial losses or fraud."
            ),
            level="warning"
        )
        render_data_table(leakage_df.head(60))
    else:
        render_callout(
            title="No Screening Flags Detected",
            message="Promotion rules and fee schedules have zero flagged investigation candidates.",
            level="success"
        )

with tab3:
    render_section_header("Promotional Campaign Catalog Metadata", tag="CAMPAIGN CATALOG")
    st.caption("Note: Order-level promo_id attribution is absent in orders.csv; campaign ROI and redemptions are unavailable.")
    if not promotions_df.empty:
        render_data_table(promotions_df)
    else:
        st.info("Promotions dataset unavailable.")
