"""
Page 3: Restaurant Intelligence & Risk Engine
---------------------------------------------
Comprehensive merchant analytics featuring composite Health Scores (0-100),
Automated Partner Risk Detection, Peer Group Benchmarking, and Early Warning Signals.
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
from components.chart_components import render_bar_chart, render_donut_chart, render_scatter_chart
from components.status_components import render_section_header, render_data_table, render_callout
from components.contextual_ai import build_contextual_payload, render_contextual_ai_inline

from intelligence.restaurant.health_score import calculate_restaurant_health_score
from intelligence.restaurant.risk_detection import detect_restaurant_risks
from intelligence.restaurant.benchmarking import calculate_restaurant_benchmarks
from intelligence.restaurant.early_warning import generate_restaurant_early_warnings

st.set_page_config(page_title=f"Restaurant Intelligence — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

orders_df = data.get("orders", pd.DataFrame())
restaurants_df = data.get("restaurants", pd.DataFrame())
ratings_df = data.get("ratings_reviews", pd.DataFrame())

# Harmonize orders
orders_prep = orders_df.copy()
if "order_datetime" not in orders_prep.columns and "order_time" in orders_prep.columns:
    orders_prep["order_datetime"] = orders_prep["order_time"]
if "final_amount" not in orders_prep.columns and "order_amount" in orders_prep.columns:
    orders_prep["final_amount"] = orders_prep["order_amount"]

# Filter by city if selected
if filters["city"] != "All" and not restaurants_df.empty and "city" in restaurants_df.columns:
    restaurants_df = restaurants_df[restaurants_df["city"] == filters["city"]]
    if not orders_prep.empty:
        rest_ids = set(restaurants_df["restaurant_id"])
        orders_prep = orders_prep[orders_prep["restaurant_id"].isin(rest_ids)]

# Header
render_page_header(
    title="Restaurant Intelligence & Risk Engine",
    subtitle="Composite Health Scores, Peer Group Benchmarking & Early Warning Risk Signals",
    category="MERCHANT NETWORK",
    data_source=data_source,
    record_count=len(restaurants_df)
)

# Run Analytical Pipeline
health_df = calculate_restaurant_health_score(restaurants_df, orders_prep, ratings_df) if not restaurants_df.empty and not orders_prep.empty else pd.DataFrame()
risk_df = detect_restaurant_risks(health_df) if not health_df.empty else pd.DataFrame()
benchmarked_df = calculate_restaurant_benchmarks(risk_df) if not risk_df.empty else pd.DataFrame()
alerts = generate_restaurant_early_warnings(benchmarked_df) if not benchmarked_df.empty else []

# Top KPIs
total_partners = len(restaurants_df)
avg_health = benchmarked_df["Health_Score"].mean() if not benchmarked_df.empty and "Health_Score" in benchmarked_df.columns else 0
at_risk_count = len(benchmarked_df[benchmarked_df.get("Risk_Category", "") == "Critical"]) if not benchmarked_df.empty else 0
warning_signals = len(alerts)

city_scope = f" in {filters['city']}" if filters["city"] != "All" else ""

render_kpi_row([
    {
        "label": "Partner Network",
        "value": format_number(total_partners),
        "subtext": "Active food merchants",
        "delta": "5 metro regions",
        "delta_positive": True,
        "accent": "blue",
        "ai_payload": build_contextual_payload(
            dashboard_name="Restaurant Intelligence",
            kpi_or_chart_id="kpi_partner_network",
            selected_metric="Partner Network Size",
            metric_value=total_partners,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze restaurant partner onboarding, distribution, and active supply coverage{city_scope}.",
        ),
    },
    {
        "label": "Average Health Score",
        "value": f"{avg_health:.1f}/100",
        "subtext": "Composite operational index",
        "delta": "70 threshold",
        "delta_positive": avg_health >= 70,
        "accent": "emerald" if avg_health >= 70 else "amber",
        "ai_payload": build_contextual_payload(
            dashboard_name="Restaurant Intelligence",
            kpi_or_chart_id="kpi_health_score",
            selected_metric="Average Health Score",
            metric_value=avg_health,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze composite restaurant health scores and operational bottlenecks{city_scope}.",
        ),
    },
    {
        "label": "Critical Risk Partners",
        "value": format_number(at_risk_count),
        "subtext": "Requiring immediate intervention",
        "delta": "Urgent audit",
        "delta_positive": False if at_risk_count > 0 else True,
        "accent": "crimson",
        "ai_payload": build_contextual_payload(
            dashboard_name="Restaurant Intelligence",
            kpi_or_chart_id="kpi_critical_risk",
            selected_metric="Critical Risk Partners",
            metric_value=at_risk_count,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Which restaurants are in the critical risk tier and what operational interventions are needed{city_scope}?",
        ),
    },
    {
        "label": "Active Warning Signals",
        "value": format_number(warning_signals),
        "subtext": "Operational anomaly triggers",
        "delta": "Early warning active",
        "delta_positive": warning_signals == 0,
        "accent": "amber",
        "ai_payload": build_contextual_payload(
            dashboard_name="Restaurant Intelligence",
            kpi_or_chart_id="kpi_warning_signals",
            selected_metric="Active Warning Signals",
            metric_value=warning_signals,
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Investigate active restaurant early warning signals and cancellation anomalies{city_scope}.",
        ),
    }
])

# Discovery Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Health Score Radar",
    "🛡️ Risk Engine & Tiers",
    "📈 Peer Benchmarks",
    "🔍 Partner Deep-Dive Inspector",
    "🚨 Early Warning Signals"
])

with tab1:
    render_section_header("Composite Merchant Health Scores", tag="HEALTH ENGINE")
    if not benchmarked_df.empty and "Health_Category" in benchmarked_df.columns:
        c1, c2 = st.columns([1, 1])
        with c1:
            tier_dist = benchmarked_df["Health_Category"].value_counts().reset_index()
            tier_dist.columns = ["Health Tier", "Partners"]
            render_donut_chart(tier_dist, names="Health Tier", values="Partners", title="Distribution of Health Tiers")
        with c2:
            render_scatter_chart(
                benchmarked_df,
                x="Total_Revenue",
                y="Health_Score",
                color="Health_Category",
                title="Revenue vs. Overall Health Score (₹)",
                size="Total_Orders"
            )
    else:
        st.info("Health score metrics unavailable.")

with tab2:
    render_section_header("Partner Risk Classification", tag="RISK DETECTION")
    if not benchmarked_df.empty and "Risk_Category" in benchmarked_df.columns:
        c1, c2 = st.columns([1, 2])
        with c1:
            risk_dist = benchmarked_df["Risk_Category"].value_counts().reset_index()
            risk_dist.columns = ["Risk Level", "Count"]
            render_bar_chart(risk_dist, x="Risk Level", y="Count", title="Partners by Risk Category")
        with c2:
            critical_partners = benchmarked_df[benchmarked_df["Risk_Category"] == "Critical"]
            if not critical_partners.empty:
                render_callout(
                    title="Critical Partner Alert",
                    message=f"{len(critical_partners)} merchants show severe operational degradation (rating < 3.5 or cancellation rate > 5%). Immediate kitchen quality reviews recommended.",
                    level="danger"
                )
            render_data_table(benchmarked_df[["restaurant_id", "restaurant_name", "city", "cuisine_type", "avg_rating", "Cancellation_Rate", "Risk_Category", "Risk_Reasons"]].head(50))
    else:
        st.info("Risk detection data unavailable.")

with tab3:
    render_section_header("Cuisine & City Peer Group Benchmarks", tag="PERCENTILE COHORTS")
    if not benchmarked_df.empty:
        cuisine_summary = benchmarked_df.groupby("cuisine_type").agg(
            Partners=("restaurant_id", "count"),
            Avg_Rating=("avg_rating", "mean"),
            Avg_Health=("Health_Score", "mean"),
            Total_Sales=("Total_Revenue", "sum")
        ).reset_index().sort_values(by="Total_Sales", ascending=False)
        cuisine_summary["Avg_Rating"] = cuisine_summary["Avg_Rating"].round(2)
        cuisine_summary["Avg_Health"] = cuisine_summary["Avg_Health"].round(1)
        cuisine_summary["Total_Sales"] = cuisine_summary["Total_Sales"].apply(format_currency)

        render_data_table(cuisine_summary)
    else:
        st.info("Benchmarking cohorts unavailable.")

with tab4:
    render_section_header("Partner Deep-Dive Profile", tag="INSPECTOR")
    if not benchmarked_df.empty:
        partner_list = benchmarked_df["restaurant_name"].tolist()
        selected_partner_name = st.selectbox("Select Restaurant Partner to Inspect:", partner_list, key="partner_select")
        p_row = benchmarked_df[benchmarked_df["restaurant_name"] == selected_partner_name].iloc[0]

        i1, i2, i3, i4 = st.columns(4)
        with i1:
            st.markdown(f"""
            <div class="nn-kpi-card accent-blue">
                <div class="nn-kpi-label">Health Score</div>
                <div class="nn-kpi-value">{p_row.get('Health_Score', 0):.0f}/100</div>
                <div class="nn-kpi-sub">{p_row.get('Health_Category', 'Good')}</div>
            </div>
            """, unsafe_allow_html=True)
        with i2:
            st.markdown(f"""
            <div class="nn-kpi-card accent-emerald">
                <div class="nn-kpi-label">Total Revenue</div>
                <div class="nn-kpi-value">{format_currency(p_row.get('Total_Revenue', 0))}</div>
                <div class="nn-kpi-sub">{p_row.get('Total_Orders', 0):,} Orders</div>
            </div>
            """, unsafe_allow_html=True)
        with i3:
            st.markdown(f"""
            <div class="nn-kpi-card accent-amber">
                <div class="nn-kpi-label">Customer Rating</div>
                <div class="nn-kpi-value">{p_row.get('avg_rating', 0):.2f} ★</div>
                <div class="nn-kpi-sub">{p_row.get('Review_Count', 0):,} Reviews</div>
            </div>
            """, unsafe_allow_html=True)
        with i4:
            r_cat = p_row.get('Risk_Category', 'Healthy')
            r_accent = "crimson" if r_cat == "Critical" else ("amber" if r_cat == "At Risk" else "emerald")
            st.markdown(f"""
            <div class="nn-kpi-card accent-{r_accent}">
                <div class="nn-kpi-label">Risk Category</div>
                <div class="nn-kpi-value">{r_cat}</div>
                <div class="nn-kpi-sub">{p_row.get('Cancellation_Rate', 0):.1f}% Cancel Rate</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: var(--nn-bg-card); border: 1px solid var(--nn-border); border-radius: 8px; padding: 1.25rem; margin-top: 1rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #60A5FA; text-transform: uppercase;">Peer Group Benchmarking Status</div>
            <div style="font-size: 0.85rem; color: #CBD5E1; margin-top: 0.4rem;">
                <strong>City Percentile:</strong> Top {(100 - p_row.get('City_Revenue_Percentile', 50)):.1f}% in {p_row.get('city', 'City')}<br>
                <strong>Cuisine Percentile:</strong> Top {(100 - p_row.get('Cuisine_Revenue_Percentile', 50)):.1f}% in {p_row.get('cuisine_type', 'Cuisine')}<br>
                <strong>Risk Rationale:</strong> {p_row.get('Risk_Reasons', 'Operating within safe parameters.')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # PHASE 09 RESTAURANT 360 DIAGNOSIS & ACTION PLAN
        try:
            from python.decision.restaurant_optimization import diagnose_restaurant_performance, generate_restaurant_action_plan
            rest_id = str(p_row.get("restaurant_id"))
            rest_diag = diagnose_restaurant_performance(rest_id, data)
            if rest_diag:
                st.markdown("##### 🏪 Restaurant 360 Operational Diagnosis & Action Plan (Phase 09)")
                diag_c1, diag_c2 = st.columns([1, 2])
                with diag_c1:
                    st.metric("Primary Operational Diagnosis", rest_diag.get("diagnosis_category", "Nominal"))
                    st.metric("Avg Prep Time", f"{rest_diag.get('operational_metrics', {}).get('average_prep_time_minutes', 0.0)} mins")
                with diag_c2:
                    st.markdown("**Prescriptive Intervention Directives:**")
                    for act_item in rest_diag.get("prescriptive_action_plan", []):
                        st.markdown(f"- {act_item}")
                    st.success(f"📈 **Expected Impact:** {rest_diag.get('expected_operational_impact', 'Operational recovery')}")
        except Exception as e:
            pass

        render_contextual_ai_inline(
            build_contextual_payload(
                dashboard_name="Restaurant Intelligence",
                kpi_or_chart_id="partner_deep_dive",
                selected_metric=f"Restaurant Health: {selected_partner_name}",
                entity_type="restaurant",
                entity_id=str(p_row.get('restaurant_id')),
                entity_name=selected_partner_name,
                active_filters=filters,
                city=filters.get("city"),
                suggested_prompt=f"Analyze operational health, cancellation drivers, and SLA compliance for {selected_partner_name}.",
            ),
            key=f"rest_inspect_{p_row.get('restaurant_id', 'id')}",
        )

with tab5:
    render_section_header("Operational Early Warning Signals", tag="ACTIVE ALERT QUEUE")
    if alerts:
        for idx, a in enumerate(alerts[:20]):
            severity = a.get("severity", "Warning")
            level = "danger" if severity == "Critical" else "warning"
            render_callout(
                title=f"[{severity.upper()}] {a.get('entity_name', 'Merchant')} ({a.get('entity_id')})",
                message=f"<strong>Alert Condition:</strong> {a.get('message', '')}<br><strong>Action:</strong> {a.get('action', '')}",
                level=level
            )
    else:
        render_callout(
            title="All Merchant Signals Nominal",
            message="No active critical threshold breaches detected across restaurant partners.",
            level="success"
        )
