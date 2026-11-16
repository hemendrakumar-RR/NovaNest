"""
Page 2: Customer Intelligence & Segmentation
---------------------------------------------
RFM segmentation, Customer Lifetime Value (CLV), Cohort Retention Analysis,
Customer 360 profiling, Digital Twin representation, and Hybrid AI Recommendations.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

import bootstrap
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from utils.data_loader import load_all_datasets
from utils.formatting import format_currency, format_number, format_percent
from components.navigation import render_sidebar
from components.page_header import render_page_header
from components.kpi_components import render_kpi_row
from components.chart_components import render_bar_chart, render_donut_chart, style_figure
from components.status_components import render_section_header, render_data_table, render_callout
from components.contextual_ai import build_contextual_payload, render_contextual_ai_inline

from intelligence.customer.clv import calculate_customer_clv
from intelligence.customer.rfm import calculate_advanced_rfm
from intelligence.customer.cohort import calculate_cohort_matrix
from intelligence.customer.customer_360 import build_customer_360_profile
from intelligence.customer.cust_twin import create_customer_digital_twin
from ai.recommendations.hybrid_recommender import get_hybrid_recommendations

st.set_page_config(page_title=f"Customer Intelligence — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

orders_df = data.get("orders", pd.DataFrame())
customers_df = data.get("customers", pd.DataFrame())
menu_df = data.get("menu_items", pd.DataFrame())
churn_df = data.get("customer_churn_predictions", pd.DataFrame())

# Harmonize order columns for intelligence modules
orders_prep = orders_df.copy()
if "order_datetime" not in orders_prep.columns and "order_time" in orders_prep.columns:
    orders_prep["order_datetime"] = orders_prep["order_time"]
if "final_amount" not in orders_prep.columns and "order_amount" in orders_prep.columns:
    orders_prep["final_amount"] = orders_prep["order_amount"]

# Header
render_page_header(
    title="Customer Intelligence & Behavioral Analytics",
    subtitle="RFM Segmentation, Cohort Retention Curves, Lifetime Value & AI Customer Digital Twins",
    category="CUSTOMER ANALYTICS",
    data_source=data_source,
    record_count=len(customers_df)
)

# Run Analytical Engines
clv_df = calculate_customer_clv(orders_prep, customers_df) if not orders_prep.empty and not customers_df.empty else pd.DataFrame()
rfm_df = calculate_advanced_rfm(orders_prep, customers_df) if not orders_prep.empty and not customers_df.empty else pd.DataFrame()

# Top KPIs
total_customers = len(customers_df)
clv_col = "CLV_Segment" if (not clv_df.empty and "CLV_Segment" in clv_df.columns) else ("CLV_Tier" if not clv_df.empty and "CLV_Tier" in clv_df.columns else None)
high_clv_count = len(clv_df[clv_df[clv_col].isin(["Very High Value", "High Value"])]) if clv_col else 0
avg_clv = clv_df["Estimated_CLV"].mean() if not clv_df.empty and "Estimated_CLV" in clv_df.columns else 0
at_risk_count = len(churn_df[churn_df.get("Churn_Risk", "") == "High Risk"]) if not churn_df.empty and "Churn_Risk" in churn_df.columns else 0

city_scope = f" in {filters['city']}" if filters["city"] != "All" else ""

render_kpi_row([
    {
        "label": "Total Active Customers",
        "value": format_number(total_customers),
        "subtext": "Registered user base",
        "delta": f"{customers_df['city'].nunique()} metros" if not customers_df.empty and 'city' in customers_df.columns else "Active",
        "delta_positive": True,
        "accent": "blue",
        "ai_payload": build_contextual_payload(
            dashboard_name="Customer Intelligence",
            kpi_or_chart_id="kpi_active_customers",
            selected_metric="Total Active Customers",
            metric_value=total_customers,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze active customer growth, registration trends, and retention health{city_scope}.",
        ),
    },
    {
        "label": "Average Projected CLV",
        "value": format_currency(avg_clv),
        "subtext": "12-month expected spend",
        "delta": "High value potential",
        "delta_positive": True,
        "accent": "emerald",
        "ai_payload": build_contextual_payload(
            dashboard_name="Customer Intelligence",
            kpi_or_chart_id="kpi_avg_clv",
            selected_metric="Average Projected CLV",
            metric_value=avg_clv,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze customer lifetime value distribution and high-value customer drivers{city_scope}.",
        ),
    },
    {
        "label": "High-Value Segment",
        "value": format_number(high_clv_count),
        "subtext": "Top 50% spend quartile",
        "delta": f"{(high_clv_count/total_customers*100):.1f}% of users" if total_customers > 0 else "0%",
        "delta_positive": True,
        "accent": "violet",
        "ai_payload": build_contextual_payload(
            dashboard_name="Customer Intelligence",
            kpi_or_chart_id="kpi_high_value_segment",
            selected_metric="High-Value Customer Segment",
            metric_value=high_clv_count,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze high-value customer segments and revenue concentration{city_scope}.",
        ),
    },
    {
        "label": "Imminent Churn Risk",
        "value": format_number(at_risk_count),
        "subtext": "High churn probability",
        "delta": "Intervention required",
        "delta_positive": False,
        "accent": "crimson",
        "ai_payload": build_contextual_payload(
            dashboard_name="Customer Intelligence",
            kpi_or_chart_id="kpi_churn_risk",
            selected_metric="Imminent Churn Risk",
            metric_value=at_risk_count,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Why are customers churning and what retention actions should be prioritized{city_scope}?",
        ),
    }
])

# Tabs for Customer Discovery
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 RFM Segmentation",
    "💎 Lifetime Value (CLV)",
    "📈 Cohort Retention",
    "👤 Customer 360 & Digital Twin",
    "⚠️ Churn Risk Radar"
])

with tab1:
    render_section_header("9-Segment RFM Behavioral Matrix", tag="SEGMENTATION ENGINE")
    if not rfm_df.empty and "RFM_Segment" in rfm_df.columns:
        seg_counts = rfm_df["RFM_Segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Customer Count"]
        
        c1, c2 = st.columns([1, 1])
        with c1:
            render_donut_chart(seg_counts, names="Segment", values="Customer Count", title="Customer Distribution across RFM Segments")
        with c2:
            seg_metrics = rfm_df.groupby("RFM_Segment").agg(
                Customers=("customer_id", "count"),
                Avg_Recency_Days=("Recency", "mean"),
                Avg_Orders=("Frequency", "mean"),
                Total_Spend=("Monetary", "sum")
            ).reset_index()
            seg_metrics["Avg_Recency_Days"] = seg_metrics["Avg_Recency_Days"].round(1)
            seg_metrics["Avg_Orders"] = seg_metrics["Avg_Orders"].round(1)
            seg_metrics["Total_Spend"] = seg_metrics["Total_Spend"].apply(format_currency)
            render_data_table(seg_metrics)
            render_contextual_ai_inline(
                build_contextual_payload(
                    dashboard_name="Customer Intelligence",
                    kpi_or_chart_id="chart_rfm_segments",
                    selected_metric="RFM Behavioral Segments",
                    active_filters=filters,
                    city=filters.get("city"),
                    suggested_prompt=f"Analyze RFM customer segment distribution, churn vulnerability, and growth opportunities{city_scope}.",
                ),
                key="cust_rfm_inline",
            )
    else:
        st.info("RFM segmentation calculating or datasets unavailable.")

with tab2:
    render_section_header("Customer Lifetime Value (CLV) Tiers", tag="PREDICTIVE VALUE ENGINE")
    if not clv_df.empty and clv_col:
        c1, c2 = st.columns([1, 1])
        with c1:
            tier_dist = clv_df[clv_col].value_counts().reset_index()
            tier_dist.columns = ["Tier", "Count"]
            render_bar_chart(tier_dist, x="Tier", y="Count", title="Distribution of Customers by CLV Tier")
        with c2:
            render_callout(
                title="CLV Calculation Architecture",
                message="CLV calculates historical customer spend + 12-month projected forward velocity weighted by order frequency and tenure dynamics. Customers in Very High Value represent the priority target for loyalty rewards and VIP retention.",
                level="info"
            )
            display_cols = [c for c in ["customer_id", "Total_Orders", "Total_Spent", "Total_Revenue", "AOV", "Estimated_CLV", clv_col] if c in clv_df.columns]
            render_data_table(clv_df[display_cols].head(50))
    else:
        st.info("CLV data unavailable.")

with tab3:
    render_section_header("Cohort Monthly Retention Matrix", tag="RETENTION CURVES")
    if not orders_prep.empty:
        try:
            retention_matrix, cohort_summary = calculate_cohort_matrix(orders_prep)
            if not retention_matrix.empty:
                # Plotly Heatmap for Cohort Retention
                matrix_display = retention_matrix.copy()
                fig = px.imshow(
                    matrix_display,
                    labels=dict(x="Months Since First Order", y="Acquisition Cohort", color="Retention %"),
                    x=[f"Month {col}" for col in matrix_display.columns],
                    y=[str(idx) for idx in matrix_display.index],
                    color_continuous_scale="Blues",
                    aspect="auto"
                )
                fig = style_figure(fig, height=400)
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Cohort matrix produced empty results.")
        except Exception as e:
            st.warning(f"Could not compute cohort matrix: {e}")
    else:
        st.info("Order history unavailable for cohort analysis.")

with tab4:
    render_section_header("Customer 360 Profile & Digital Twin Inspector", tag="TWIN STATE")
    if not customers_df.empty:
        customer_options = customers_df["customer_id"].head(200).tolist()
        selected_cid = st.selectbox("Select Customer to Inspect:", customer_options, key="cust_360_select")

        # Build 360 profile
        c_churn_df = churn_df if not churn_df.empty else pd.DataFrame()
        profile_360 = build_customer_360_profile(
            customer_id=selected_cid,
            customers_df=customers_df,
            orders_df=orders_prep,
            rfm_df=rfm_df,
            clv_df=clv_df,
            churn_df=c_churn_df
        )

        if profile_360:
            twin_obj = create_customer_digital_twin(profile_360)
            twin_dict = twin_obj.to_dict()
            id_block = profile_360.get("identity", {})
            met_block = profile_360.get("metrics", {})
            intel_block = profile_360.get("intelligence", {})
            cust_name = id_block.get("customer_name") or id_block.get("name") or selected_cid
            cust_persona = id_block.get("customer_persona") or id_block.get("persona") or "N/A"
            recency_val = met_block.get("Recency_Days")
            recency_str = f"{recency_val} days ago" if recency_val is not None else "Unavailable"

            p1, p2, p3 = st.columns([1, 1, 1])
            with p1:
                st.markdown(f"""
                <div class="nn-kpi-card accent-blue">
                    <div class="nn-kpi-label">Customer Profile</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #fff;">{cust_name}</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.35rem;">
                        <strong>City:</strong> {id_block.get('city', 'N/A')}<br>
                        <strong>Persona:</strong> {cust_persona}<br>
                        <strong>Registered:</strong> {id_block.get('signup_date', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with p2:
                st.markdown(f"""
                <div class="nn-kpi-card accent-violet">
                    <div class="nn-kpi-label">Behavior & Intelligence</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #fff;">{intel_block.get('RFM_Segment', 'Unavailable')}</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.35rem;">
                        <strong>Recency:</strong> {recency_str}<br>
                        <strong>Total Orders:</strong> {met_block.get('Total_Orders', 0)}<br>
                        <strong>Total Spend:</strong> ₹{met_block.get('Total_Spent', 0):,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with p3:
                risk_lvl = intel_block.get('Churn_Risk', 'Unavailable')
                risk_accent = "crimson" if risk_lvl == "High Risk" else "emerald"
                st.markdown(f"""
                <div class="nn-kpi-card accent-{risk_accent}">
                    <div class="nn-kpi-label">Retention & Action</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #fff;">{risk_lvl}</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.35rem;">
                        <strong>CLV:</strong> ₹{(intel_block.get('Estimated_CLV') or 0):,.2f}<br>
                        <strong>Action:</strong> {twin_dict.get('recommended_action', 'Standard nurture flow')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # PHASE 09 PRESCRIPTIVE RETENTION & GUARDRAILS
            try:
                from python.decision.customer_retention_intelligence import explain_customer_retention_profile
                prescriptive_cust = explain_customer_retention_profile(selected_cid, data)
                if prescriptive_cust:
                    st.markdown("##### 🎯 Prescriptive Retention Action & Guardrails (Phase 09)")
                    caveat_info = prescriptive_cust.get("ml_caveat_assessment", {})
                    st.warning(f"⚠️ **{caveat_info.get('ml_confidence_tier')}:** {caveat_info.get('confidence_caveat')}")

                    g = prescriptive_cust.get("discount_guardrails", {})
                    g_c1, g_c2, g_c3, g_c4 = st.columns(4)
                    with g_c1:
                        st.metric("Discount Ceiling", f"{g.get('max_discount_percentage', 0.0)}%")
                    with g_c2:
                        st.metric("Min Basket (MOV)", f"₹{g.get('minimum_order_value_required', 0.0):.0f}")
                    with g_c3:
                        st.metric("Subsidy Voucher Budget", f"₹{g.get('capped_subsidy_budget', 0.0):.0f}")
                    with g_c4:
                        st.metric("Projected Margin", f"₹{g.get('projected_contribution_margin', 0.0):.0f}")

                    st.info(f"📋 **Prescriptive Operational Directive:** {prescriptive_cust.get('prescriptive_action')}")
            except Exception as e:
                pass

            render_contextual_ai_inline(
                build_contextual_payload(
                    dashboard_name="Customer Intelligence",
                    kpi_or_chart_id="customer_360_profile",
                    selected_metric=f"Customer 360: {cust_name}",
                    entity_type="customer",
                    entity_id=selected_cid,
                    entity_name=cust_name,
                    active_filters=filters,
                    city=id_block.get('city'),
                    suggested_prompt=f"Analyze order behavior, CLV tier, churn probability, and personalized next actions for customer {selected_cid} ({cust_name}).",
                ),
                key=f"cust_360_ai_{selected_cid}",
            )

            # Recommendations for this customer
            render_section_header("Personalized Hybrid AI Recommendations", tag="RECOMMENDER ENGINE")
            try:
                recs_df = get_hybrid_recommendations(selected_cid, orders_prep, menu_df, top_k=4)
                if isinstance(recs_df, pd.DataFrame) and not recs_df.empty:
                    recs = recs_df.to_dict(orient="records")
                elif isinstance(recs_df, list) and len(recs_df) > 0:
                    recs = recs_df
                else:
                    recs = []

                if recs:
                    r_cols = st.columns(len(recs))
                    for col, r in zip(r_cols, recs):
                        with col:
                            st.markdown(f"""
                            <div class="nn-kpi-card accent-cyan" style="min-height: 140px;">
                                <div style="font-size: 0.95rem; font-weight: 700; color: #fff;">{r.get('item_name', r.get('item_id', 'Menu Item'))}</div>
                                <div style="font-size: 0.75rem; color: #60A5FA; font-weight: 600;">{r.get('category', r.get('cuisine_type', 'Popular'))} • ₹{r.get('price', 199):.0f}</div>
                                <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 0.4rem;">{r.get('ai_explanation', r.get('explanation', 'Recommended based on your preferences.'))}</div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("No personalized recommendations generated for this customer.")
            except Exception as e:
                st.caption(f"Recommender engine note: {e}")

with tab5:
    render_section_header("Predictive Churn Risk Radar", tag="RETENTION RADAR")
    if not churn_df.empty:
        high_risk_df = churn_df[churn_df.get("Churn_Risk", "") == "High Risk"] if "Churn_Risk" in churn_df.columns else churn_df
        render_callout(
            title="Active Churn Risk Alerts",
            message=f"Machine learning model flagged {len(high_risk_df):,} customers exceeding the 65% churn probability threshold. Proactive automated coupon dispatch is recommended.",
            level="warning"
        )
        render_data_table(high_risk_df)
    else:
        st.info("Churn predictions table currently empty or generating.")
