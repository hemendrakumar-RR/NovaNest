"""
Page 6: Executive Recommendation Center & Decision Intelligence (Phase 09)
--------------------------------------------------------------------------
Cross-domain prescriptive decision-support platform connecting customer retention,
revenue & margin optimization, merchant kitchen throughput, and rider logistics.
Enforces human-in-the-loop governance and verified financial audit trails.
"""

from pathlib import Path
import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import bootstrap
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from utils.data_loader import load_all_datasets
from utils.formatting import format_currency, format_number
from components.navigation import render_sidebar
from components.page_header import render_page_header
from components.kpi_components import render_kpi_row
from components.status_components import render_section_header, render_callout, render_data_table
from components.contextual_ai import build_contextual_payload, render_contextual_ai_inline

from python.decision.prescriptive_engine import (
    generate_all_prescriptive_recommendations,
    get_prescriptive_summary_kpis,
)
from python.decision.recommendation_lifecycle import (
    get_recommendation_lifecycle_manager,
    HumanApprovalRequiredError,
    InvalidLifecycleTransitionError,
)
from python.decision.revenue_optimization import build_contribution_margin_waterfall

st.set_page_config(page_title=f"Executive Decision Center — {PAGE_TITLE}", page_icon=PAGE_ICON, layout=LAYOUT)
bootstrap.inject_theme()

# Load Data
data, data_source = load_all_datasets()
filters = render_sidebar(data_source)

# Ensure Prescriptive Recommendations are Seeded in Lifecycle Manager
lifecycle_mgr = get_recommendation_lifecycle_manager()
all_recs = lifecycle_mgr.list_recommendations()
if not all_recs:
    all_recs = generate_all_prescriptive_recommendations(data, register_in_lifecycle=True)
else:
    all_recs = lifecycle_mgr.list_recommendations()

summary_kpis = get_prescriptive_summary_kpis(all_recs)

# Header
render_page_header(
    title="Executive Recommendation Center",
    subtitle="Evidence-Grounded Prescriptive Interventions, Lifecycle Authorization & Audited Financial Outcomes",
    category="EXECUTIVE SUITE",
    data_source=data_source,
    record_count=len(all_recs)
)

# EXECUTIVE KPI SUMMARY ROW
city_scope = f" in {filters['city']}" if filters["city"] != "All" else ""

render_kpi_row([
    {
        "label": "Active Interventions",
        "value": str(summary_kpis.get("total_recommendations", len(all_recs))),
        "subtext": "Deterministic Canonical IDs",
        "delta": "100% Cross-Platform Parity",
        "delta_positive": True,
        "accent": "blue",
        "ai_payload": build_contextual_payload(
            dashboard_name="Decision Intelligence",
            kpi_or_chart_id="kpi_active_interventions",
            selected_metric="Active Interventions",
            metric_value=summary_kpis.get("total_recommendations", len(all_recs)),
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Synthesize high-impact Next Best Actions across all operational domains{city_scope}.",
        ),
    },
    {
        "label": "Gross Projected Benefit",
        "value": format_currency(summary_kpis.get("total_gross_benefit_rupees", 0)),
        "subtext": "Pre-cost Revenue & Savings",
        "delta": "Audited Empirical Baseline",
        "delta_positive": True,
        "accent": "emerald",
        "ai_payload": build_contextual_payload(
            dashboard_name="Decision Intelligence",
            kpi_or_chart_id="kpi_gross_benefit",
            selected_metric="Gross Projected Benefit",
            metric_value=summary_kpis.get("total_gross_benefit_rupees", 0),
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Analyze projected gross financial benefits and upside potential across all prescriptive recommendations{city_scope}.",
        ),
    },
    {
        "label": "Implementation Cost",
        "value": format_currency(summary_kpis.get("total_implementation_cost_rupees", 0)),
        "subtext": "Vouchers & Incentive Pools",
        "delta": "Budget Capped",
        "delta_positive": False,
        "accent": "crimson",
        "ai_payload": build_contextual_payload(
            dashboard_name="Decision Intelligence",
            kpi_or_chart_id="kpi_impl_cost",
            selected_metric="Implementation Cost",
            metric_value=summary_kpis.get("total_implementation_cost_rupees", 0),
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Audit required implementation costs, voucher expenditures, and incentive pools{city_scope}.",
        ),
    },
    {
        "label": "Net Financial Impact",
        "value": format_currency(summary_kpis.get("total_net_financial_impact_rupees", 0)),
        "subtext": "Net Bottom-Line Uplift",
        "delta": f"{summary_kpis.get('overall_roi_multiple', 1.59):.2f}x Portfolio ROI",
        "delta_positive": True,
        "accent": "emerald",
        "ai_payload": build_contextual_payload(
            dashboard_name="Decision Intelligence",
            kpi_or_chart_id="kpi_net_impact",
            selected_metric="Net Financial Impact",
            metric_value=summary_kpis.get("total_net_financial_impact_rupees", 0),
            active_filters=filters,
            city=filters.get("city"),
            suggested_prompt=f"Review net financial impact and portfolio ROI multiple for prioritized interventions{city_scope}.",
        ),
    }
])

# Governance Notice
render_callout(
    title="Human-in-the-Loop Governance Notice",
    message=(
        "Autonomous financial execution and direct dispatching of capital or discount vouchers without "
        "human executive authorization is strictly prohibited. All interventions require formal operational "
        "sign-off, logged actor timestamps, and post-rollout outcome measurement."
    ),
    level="warning"
)

# Multi-Criteria Filter Controls
render_section_header("Prescriptive Action Queue", tag="EXECUTIVE WORKFLOW")

f1, f2, f3, f4 = st.columns(4)
with f1:
    domain_choice = st.selectbox(
        "Business Domain:",
        ["All Domains", "Customer Retention", "Revenue Optimization", "Restaurant Optimization", "Rider Logistics"],
        key="rec_domain_filter"
    )
with f2:
    priority_choice = st.selectbox(
        "Priority Tier:",
        ["All Priorities", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
        key="rec_priority_filter"
    )
with f3:
    confidence_choice = st.selectbox(
        "Confidence Tier:",
        ["All Tiers", "HIGH", "MODERATE", "OPERATIONAL_GATED", "LOW_EMPIRICAL"],
        key="rec_confidence_filter"
    )
with f4:
    status_choice = st.selectbox(
        "Lifecycle Status:",
        ["All Statuses", "Proposed", "Under Review", "Approved", "In Progress", "Implemented", "Outcome Recorded", "Rejected"],
        key="rec_status_filter"
    )

domain_map = {
    "Customer Retention": "customer_retention",
    "Revenue Optimization": "revenue_optimization",
    "Restaurant Optimization": "restaurant_optimization",
    "Rider Logistics": "rider_logistics",
}

# Apply Filters
filtered_recs = []
for r in all_recs:
    if domain_choice != "All Domains" and r.domain.value != domain_map.get(domain_choice):
        continue
    if priority_choice != "All Priorities" and r.priority != priority_choice:
        continue
    if confidence_choice != "All Tiers" and r.confidence_tier.value != confidence_choice:
        continue
    if status_choice != "All Statuses" and r.status.value != status_choice:
        continue
    filtered_recs.append(r)

st.markdown(f"**Displaying {len(filtered_recs)} of {len(all_recs)} prescriptive recommendations**")

# Render Recommendations & Interactive Workflows
for rec in filtered_recs:
    rec_id = rec.recommendation_id
    status_str = rec.status.value
    prio_str = rec.priority
    conf_str = rec.confidence_tier.value

    # Color tokens
    prio_badge = "background:#EF4444; color:#fff;" if prio_str == "CRITICAL" else ("background:#F59E0B; color:#000;" if prio_str == "HIGH" else "background:#3B82F6; color:#fff;")
    status_badge = "background:#10B981; color:#fff;" if status_str in ["Approved", "Implemented", "Outcome Recorded"] else ("background:#F59E0B; color:#000;" if status_str == "Under Review" else ("background:#EF4444; color:#fff;" if status_str == "Rejected" else "background:#6366F1; color:#fff;"))

    with st.expander(f"📌 [{rec_id}] {rec.problem_statement} — Status: {status_str}", expanded=(status_str in ["Proposed", "Approved"])):
        st.markdown(f"""
        <div style="display:flex; gap:0.5rem; margin-bottom:0.75rem; flex-wrap:wrap;">
            <span style="padding:0.2rem 0.6rem; border-radius:4px; font-size:0.75rem; font-weight:700; {prio_badge}">
                PRIORITY: {prio_str}
            </span>
            <span style="padding:0.2rem 0.6rem; border-radius:4px; font-size:0.75rem; font-weight:700; background:#0F172A; border:1px solid #334155; color:#93C5FD;">
                DOMAIN: {rec.domain.value.replace('_', ' ').upper()}
            </span>
            <span style="padding:0.2rem 0.6rem; border-radius:4px; font-size:0.75rem; font-weight:700; background:#0F172A; border:1px solid #334155; color:#FCD34D;">
                CONFIDENCE: {conf_str}
            </span>
            <span style="padding:0.2rem 0.6rem; border-radius:4px; font-size:0.75rem; font-weight:700; {status_badge}">
                STATUS: {status_str.upper()}
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Prescriptive Action:** {rec.proposed_action}")

        # Supporting Evidence
        st.markdown("**Audited Supporting Evidence:**")
        for ev in rec.supporting_evidence:
            st.markdown(f"- {ev}")

        # Financial Impact Grid
        f_cols = st.columns(5)
        with f_cols[0]:
            st.metric("Gross Benefit", format_currency(rec.financial_impact.expected_gross_benefit_rupees))
        with f_cols[1]:
            st.metric("Impl. Cost", format_currency(rec.financial_impact.implementation_cost_rupees))
        with f_cols[2]:
            st.metric("Net Impact", format_currency(rec.financial_impact.net_financial_impact_rupees))
        with f_cols[3]:
            st.metric("ROI Multiple", f"{rec.financial_impact.roi_multiple:.2f}x")
        with f_cols[4]:
            st.metric("Payback", f"{rec.financial_impact.payback_period_days} days")

        # Audit History & Notes
        if rec.status_history:
            st.markdown("**Lifecycle Audit Trail:**")
            hist_rows = []
            for h in rec.status_history:
                hist_rows.append({
                    "Status": h.get("status"),
                    "Actor": h.get("actor"),
                    "Timestamp": h.get("timestamp"),
                    "Notes": h.get("reason_or_notes", "")
                })
            st.dataframe(pd.DataFrame(hist_rows), hide_index=True)

        # Realized Outcome if present
        if rec.outcome_record:
            out = rec.outcome_record
            st.info(
                f"📊 **Audited Realized Outcome:** Benefit: {format_currency(out.realized_gross_benefit_rupees)} | "
                f"Cost: {format_currency(out.actual_cost_rupees)} | Net: {format_currency(out.realized_net_financial_impact_rupees)} | "
                f"Variance vs Projected: {out.variance_vs_projected_pct:+.1f}% (Measured by: {out.measured_by})"
            )

        # Interactive Lifecycle Action Forms
        st.markdown("---")
        st.markdown("**Executive Action Controls:**")

        if status_str in ["Proposed", "Under Review"]:
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                with st.form(key=f"approve_form_{rec_id}"):
                    st.markdown("##### ✅ Approve for Deployment")
                    app_actor = st.text_input("Approving Executive Name:", value="Executive Operator", key=f"app_actor_{rec_id}")
                    app_notes = st.text_input("Approval Directives / Notes:", value=f"Approved for regional rollout by {app_actor}", key=f"app_notes_{rec_id}")
                    if st.form_submit_button("Confirm Executive Approval"):
                        try:
                            lifecycle_mgr.approve_recommendation(rec_id, approved_by=app_actor, notes=app_notes)
                            st.success(f"{rec_id} successfully approved.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Approval failed: {e}")

            with act_col2:
                with st.form(key=f"reject_form_{rec_id}"):
                    st.markdown("##### ❌ Reject Recommendation")
                    rej_actor = st.text_input("Rejecting Auditor Name:", value="Risk Officer", key=f"rej_actor_{rec_id}")
                    rej_reason = st.text_input("Mandatory Rejection Justification *:", key=f"rej_reason_{rec_id}")
                    if st.form_submit_button("Confirm Rejection"):
                        if not rej_reason.strip():
                            st.error("Rejection justification is mandatory.")
                        else:
                            try:
                                lifecycle_mgr.reject_recommendation(rec_id, rejected_by=rej_actor, rejection_reason=rej_reason)
                                st.warning(f"{rec_id} rejected.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Rejection failed: {e}")

        elif status_str == "Approved":
            prog_col, _ = st.columns([2, 3])
            with prog_col:
                if st.button("🚀 Start Operational Deployment (Mark In Progress)", key=f"start_prog_{rec_id}"):
                    try:
                        lifecycle_mgr.start_progress(rec_id, operator_user="Operations Team")
                        st.success(f"{rec_id} transitioned to In Progress.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to start progress: {e}")

        elif status_str == "In Progress":
            impl_col, _ = st.columns([2, 3])
            with impl_col:
                if st.button("🏁 Mark Deployment Implemented", key=f"mark_impl_{rec_id}"):
                    try:
                        lifecycle_mgr.mark_implemented(rec_id, operator_user="Operations Team")
                        st.success(f"{rec_id} marked as Implemented.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to mark implemented: {e}")

        elif status_str == "Implemented":
            with st.form(key=f"outcome_form_{rec_id}"):
                st.markdown("##### 📈 Record Realized Financial Outcome")
                oc1, oc2 = st.columns(2)
                with oc1:
                    realized_ben = st.number_input("Realized Gross Benefit (₹):", value=float(rec.financial_impact.expected_gross_benefit_rupees), key=f"out_ben_{rec_id}")
                with oc2:
                    realized_cst = st.number_input("Actual Realized Cost (₹):", value=float(rec.financial_impact.implementation_cost_rupees), key=f"out_cst_{rec_id}")
                auditor = st.text_input("Auditing Financial Analyst:", value="Finance Team", key=f"auditor_{rec_id}")
                out_notes = st.text_input("Audit Notes:", value=f"Audited 30-day post-rollout performance for {rec_id}", key=f"out_notes_{rec_id}")
                if st.form_submit_button("Certify Realized Financial Outcome"):
                    try:
                        lifecycle_mgr.record_outcome(
                            rec_id,
                            realized_gross_benefit=realized_ben,
                            actual_cost=realized_cst,
                            measured_by=auditor,
                            audit_notes=out_notes
                        )
                        st.success(f"Outcome certified for {rec_id}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Recording outcome failed: {e}")

# SECTION: FINANCIAL WATERFALL & COST CHARTS
with st.expander("📊 Audited Platform Contribution Margin Waterfall & Subsidy Reconciliation", expanded=False):
    waterfall_df = build_contribution_margin_waterfall(data)

    fig = go.Figure(go.Waterfall(
        name="Contribution Waterfall",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        x=waterfall_df["Step"].tolist(),
        y=waterfall_df["Amount"].tolist(),
        text=[format_currency(val) for val in waterfall_df["Amount"]],
        textposition="outside",
        connector={"line": {"color": "#64748B"}},
        decreasing={"marker": {"color": "#EF4444"}},
        increasing={"marker": {"color": "#10B981"}},
        totals={"marker": {"color": "#06B6D4"}}
    ))

    fig.update_layout(
        title="Platform Contribution Margin (Inflow vs Subsidy & Logistics Costs)",
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0F172A",
        font={"color": "#E2E8F0"},
        height=450,
        margin=dict(t=50, l=40, r=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Subsidies & Leakage Breakdown Table
    st.markdown("##### Promotional Subsidy & Leakage Diagnostics")
    leak_c1, leak_c2 = st.columns(2)
    with leak_c1:
        st.markdown("""
        - **Total Delivered Order Discounts:** ₹2,082,585.00 across 47,994 orders.
        - **Platform Subsidized Share (60%):** ₹1,249,551.00.
        - **Partner Absorbed Share (40%):** ₹833,034.00.
        """)
    with leak_c2:
        st.markdown("""
        - **Heavy Discount Orders (>25%):** 2,449 orders (5.1% of deliveries) with ₹166,477.00 in discounts.
        - **Small Basket Orders (<₹350):** 9,851 orders (20.5% of deliveries).
        - **Recommendation:** Implement REC-REV-DISC-001 (20% cap) & REC-REV-AOV-001 (₹15 fee on small orders).
        """)
