"""
NovaNest Customer Intelligence Agent (Phase 06.2)
-------------------------------------------------
Specializes in RFM Segmentation, CLV & Cumulative ARPU, Repeat Purchase Rate (KPI-14),
Cohort Retention (KPI-15), Customer 360 lookup (operator+ RBAC gated), and
Churn Risk Indicators with explicit Phase 05 ML caveat disclosures.

Strict Security & Grounding Rules:
- Requires `operator` (or `admin`) RBAC scope before reading customer records.
- Permitted SQL tables: `customers`, `orders`, `ratings_reviews`.
- Explicitly separates validated historical behavioral KPIs from experimental
  leak-free churn predictions (`ROC-AUC = 0.5161`, `NEEDS_MORE_DATA`).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from python.ai.agents.base import (
    BaseDomainAgent,
    df_to_table_rows,
    ensure_python_path,
    filter_df_by_city,
    load_model_v2_json,
    make_provenance,
    safe_float,
    safe_round,
    sanitize_scalar,
    sanitize_table_rows,
)
from python.ai.agents.context import AgentContext
from python.ai.agents.contracts import (
    ActionRecommendation,
    AgentDomain,
    AgentError,
    AgentRequest,
    AgentResult,
    AgentStatus,
    ChartSpec,
    DataProvenance,
    GroundedFact,
    ModelCaveat,
    SeverityLevel,
    SqlAuditTrace,
    sanitize_text,
)


def _infer_customer_intent(request: AgentRequest) -> str:
    if request.intent:
        return request.intent.strip().lower()
    if request.filters.get("customer_id"):
        return "customer_360"
    q = request.user_query.lower()
    if any(k in q for k in ("cohort", "retention")):
        return "cohort_analysis"
    if any(k in q for k in ("churn", "attrition", "risk", "probability")):
        return "churn_indicators"
    if any(k in q for k in ("360", "c360", "profile", "customer_id")):
        return "customer_360"
    if any(k in q for k in ("rfm", "segment", "clv", "repeat")):
        return "segmentation_rfm"
    return "customer_overview"


def _build_churn_caveat() -> ModelCaveat:
    try:
        from python.ai.agents.base import make_model_caveat_from_registry
        return make_model_caveat_from_registry("customer_churn", "customer")
    except Exception:
        metrics_json = load_model_v2_json("customer_churn/churn_metrics_v2.json")
        selected = str(metrics_json.get("selected_model", "RandomForest_Calibrated"))
        tm = metrics_json.get("test_metrics", {}) if isinstance(metrics_json.get("test_metrics"), dict) else {}
        roc_auc = safe_round(tm.get("roc_auc", 0.5161), 4, default=0.5161)
        recall = safe_round(tm.get("recall", 0.0632), 4, default=0.0632)
        precision = safe_round(tm.get("precision", 0.1364), 4, default=0.1364)
        return ModelCaveat(
            model_name=f"customer_churn_v2 ({selected})",
            domain="customer",
            validation_status="NEEDS_MORE_DATA",
            metric_summary=f"roc_auc={roc_auc}, recall={recall}, precision={precision}",
            warning=(
                "Experimental Phase 05 churn model has near-random discrimination and low recall; "
                "do not rely solely on ML churn scores for automated spend decisions. Prefer validated RFM, cohort, and repeat metrics."
            ),
            is_production_ready=False,
        )


class CustomerAgent(BaseDomainAgent):
    """Domain intelligence agent for customer segmentation, retention, C360, and churn indicators."""

    AGENT_ID = "customer_agent"
    DOMAIN = AgentDomain.CUSTOMER
    VERSION = "1.0.0"
    DESCRIPTION = (
        "Analyzes customer RFM segments, CLV, repeat purchase rate, cohort retention, "
        "scoped C360 profiles, and experimental churn risk indicators under operator RBAC gating."
    )
    CAPABILITIES = (
        "rfm_segmentation",
        "clv_analysis",
        "repeat_purchase_tracking",
        "cohort_retention",
        "churn_risk_indicators",
        "customer_360_lookup",
    )
    SUPPORTED_INTENTS = (
        "customer_overview",
        "segmentation_rfm",
        "cohort_analysis",
        "churn_indicators",
        "customer_360",
        "sql",
    )
    ALLOWED_TABLES = ("customers", "orders", "ratings_reviews")
    ALLOWED_DATASETS = ("customers", "orders", "ratings_reviews", "customer_churn_predictions")
    REQUIRED_SCOPES = ("operator",)

    def _run_domain(
        self,
        *,
        request: AgentRequest,
        context: AgentContext,
        data: Dict[str, pd.DataFrame],
        data_source_label: str,
        sql_trace: Optional[SqlAuditTrace],
        sql_rows: List[Dict[str, Any]],
    ) -> AgentResult:
        ensure_python_path()
        intent = _infer_customer_intent(request)
        city_filter = request.filters.get("city")
        customer_id_filter = request.filters.get("customer_id")
        filters_desc = ([f"city={city_filter}"] if city_filter else []) + (
            [f"customer_id={customer_id_filter}"] if customer_id_filter else []
        )

        customers_raw = data.get("customers", pd.DataFrame())
        orders_raw = data.get("orders", pd.DataFrame())
        reviews_raw = data.get("ratings_reviews", pd.DataFrame())
        churn_raw = data.get("customer_churn_predictions", pd.DataFrame())

        if customers_raw.empty:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.BLOCKED,
                summary="Primary 'customers' dataset is missing or empty; customer intelligence blocked.",
                provenance=[make_provenance(data_source_label, "customers", customers_raw)],
                errors=[
                    AgentError(
                        code="MISSING_PRIMARY_DATASET",
                        message="Primary 'customers' dataset is required for customer analysis.",
                        agent_id=self.AGENT_ID,
                        recoverable=True,
                        severity=SeverityLevel.ERROR,
                    )
                ],
                data_gaps=["customers dataset missing or empty"],
            )

        if "customer_id" not in customers_raw.columns:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.ERROR,
                summary="Customers dataset missing required 'customer_id' identifier column.",
                provenance=[make_provenance(data_source_label, "customers", customers_raw)],
                errors=[
                    AgentError(
                        code="SCHEMA_MISMATCH",
                        message="Customers dataset lacks required 'customer_id' column.",
                        agent_id=self.AGENT_ID,
                        recoverable=False,
                        severity=SeverityLevel.ERROR,
                    )
                ],
                data_gaps=["Missing customers.customer_id column"],
            )

        customers = filter_df_by_city(customers_raw, city_filter) if city_filter else customers_raw
        if customers.empty:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.PARTIAL,
                summary=f"No customers matched city filter '{city_filter}'.",
                provenance=[make_provenance(data_source_label, "customers", customers_raw, filters_applied=filters_desc)],
                data_gaps=[f"Zero matching customers for city '{city_filter}'"],
            )

        cust_ids = set(customers["customer_id"])
        orders = (
            orders_raw[orders_raw["customer_id"].isin(cust_ids)].copy()
            if (not orders_raw.empty and "customer_id" in orders_raw.columns)
            else pd.DataFrame()
        )
        churn_df = (
            churn_raw[churn_raw["customer_id"].isin(cust_ids)].copy()
            if (not churn_raw.empty and "customer_id" in churn_raw.columns)
            else pd.DataFrame()
        )
        reviews_df = (
            reviews_raw[reviews_raw["customer_id"].isin(cust_ids)].copy()
            if (not reviews_raw.empty and "customer_id" in reviews_raw.columns)
            else pd.DataFrame()
        )

        data_gaps: List[str] = []
        total_customers = int(len(customers))
        facts: List[GroundedFact] = [
            GroundedFact(
                label="Total Customers",
                value=total_customers,
                unit="customers",
                source=f"{data_source_label}:customers",
            )
        ]
        metrics: Dict[str, Any] = {"total_customers": total_customers}

        # Validated behavioral metrics (RFM, CLV, Repeat Rate, Cohort Retention)
        rfm_df = pd.DataFrame()
        clv_df = pd.DataFrame()
        segment_rows: List[Dict[str, Any]] = []
        cohort_rows: List[Dict[str, Any]] = []

        if orders.empty:
            data_gaps.append("orders dataset empty or unjoined: RFM, CLV, repeat rate, and cohort retention omitted")
        else:
            order_counts = orders.groupby("customer_id").size()
            repeat_customers = int((order_counts > 1).sum())
            repeat_rate_pct = safe_round((repeat_customers / total_customers) * 100.0, 2) if total_customers > 0 else 0.0
            metrics["repeat_customers"] = repeat_customers
            metrics["repeat_purchase_rate_pct"] = repeat_rate_pct
            facts.append(
                GroundedFact(
                    label="Repeat Purchase Rate",
                    value=repeat_rate_pct,
                    unit="%",
                    kpi_id=None if city_filter else "KPI-14",
                    source=f"{data_source_label}:orders+customers",
                )
            )

            delivered = orders[orders["order_status"] == "Delivered"] if "order_status" in orders.columns else orders
            realized_net_rev = safe_round(
                delivered["final_amount"].sum() if "final_amount" in delivered.columns else 0.0, 2
            )
            realized_arpu = safe_round(realized_net_rev / total_customers, 2) if total_customers > 0 else 0.0
            metrics["realized_arpu_inr"] = realized_arpu
            facts.append(
                GroundedFact(
                    label="Historical Realized Spend per Customer (ARPU)",
                    value=realized_arpu,
                    unit="INR",
                    kpi_id=None if city_filter else "KPI-16",
                    source=f"{data_source_label}:orders+customers",
                )
            )

            # Cohort retention via existing analytics module
            try:
                from python.analytics.cohort_analysis import compute_cohort_retention_matrix

                if "order_datetime" in orders.columns and "order_id" in orders.columns:
                    ret_matrix, _, cohort_stats = compute_cohort_retention_matrix(orders)
                    m1_ret = safe_round(cohort_stats.get("avg_month_1_retention_pct", 0.0), 2)
                    metrics["cohort_m1_retention_pct"] = m1_ret
                    facts.append(
                        GroundedFact(
                            label="Cohort Retention Rate (Month 1 Average)",
                            value=m1_ret,
                            unit="%",
                            kpi_id=None if city_filter else "KPI-15",
                            source=f"{data_source_label}:cohort_analysis",
                        )
                    )
                    if not ret_matrix.empty:
                        ret_reset = ret_matrix.reset_index()
                        ret_reset.columns = [str(c) for c in ret_reset.columns]
                        cohort_rows = df_to_table_rows(ret_reset, max_rows=20)
            except Exception as exc:
                data_gaps.append(f"Cohort retention calculation skipped: {exc}")

            # RFM Segmentation via existing intelligence module
            try:
                from python.intelligence.customer.rfm import calculate_advanced_rfm

                rfm_df = calculate_advanced_rfm(orders, customers)
                if not rfm_df.empty and "RFM_Segment" in rfm_df.columns:
                    seg_grp = (
                        rfm_df.groupby("RFM_Segment", as_index=False)
                        .agg(
                            customers=("customer_id", "count"),
                            avg_monetary_inr=("Monetary", "mean"),
                            avg_frequency=("Frequency", "mean"),
                        )
                        .sort_values("customers", ascending=False)
                    )
                    seg_grp["avg_monetary_inr"] = seg_grp["avg_monetary_inr"].round(2)
                    seg_grp["avg_frequency"] = seg_grp["avg_frequency"].round(2)
                    segment_rows = df_to_table_rows(seg_grp, max_rows=20)
                    metrics["rfm_segments_count"] = int(len(seg_grp))
            except Exception as exc:
                data_gaps.append(f"RFM segmentation skipped: {exc}")

            # CLV via existing intelligence module
            try:
                from python.intelligence.customer.clv import calculate_customer_clv

                clv_df = calculate_customer_clv(orders, customers)
                if not clv_df.empty and "Estimated_CLV" in clv_df.columns:
                    avg_clv = safe_round(clv_df["Estimated_CLV"].mean(), 2)
                    metrics["avg_estimated_clv_inr"] = avg_clv
                    facts.append(
                        GroundedFact(
                            label="Average Estimated CLV (12M Heuristic Projection)",
                            value=avg_clv,
                            unit="INR",
                            source=f"{data_source_label}:calculate_customer_clv",
                            is_confirmed=False,
                        )
                    )
            except Exception as exc:
                data_gaps.append(f"CLV calculation skipped: {exc}")

        # Experimental Churn Risk distribution (no fabricated fallback probabilities!)
        churn_rows: List[Dict[str, Any]] = []
        high_risk_count = 0
        avg_churn_prob: Optional[float] = None
        if churn_df.empty or "Churn_Risk" not in churn_df.columns:
            data_gaps.append("customer_churn_predictions missing or empty: churn risk breakdown omitted")
        else:
            high_risk_count = int((churn_df["Churn_Risk"] == "High Risk").sum())
            high_risk_pct = safe_round((high_risk_count / len(churn_df)) * 100.0, 2)
            metrics["churn_predictions_count"] = int(len(churn_df))
            metrics["high_risk_churn_customers"] = high_risk_count
            metrics["high_risk_churn_pct"] = high_risk_pct
            facts.append(
                GroundedFact(
                    label="High Risk Churn Customers (Experimental ML Score)",
                    value=high_risk_count,
                    unit="customers",
                    source=f"{data_source_label}:customer_churn_predictions",
                    is_confirmed=False,
                )
            )
            facts.append(
                GroundedFact(
                    label="High Risk Churn Share",
                    value=high_risk_pct,
                    unit="%",
                    source=f"{data_source_label}:customer_churn_predictions",
                    is_confirmed=False,
                )
            )
            if "Churn_Probability" in churn_df.columns:
                avg_churn_prob = safe_round(
                    pd.to_numeric(churn_df["Churn_Probability"], errors="coerce").dropna().mean(), 4
                )
                metrics["avg_churn_probability"] = avg_churn_prob
                facts.append(
                    GroundedFact(
                        label="Average Churn Probability (Experimental ML)",
                        value=avg_churn_prob,
                        unit="probability",
                        source=f"{data_source_label}:customer_churn_predictions",
                        is_confirmed=False,
                    )
                )
            dist = (
                churn_df.groupby("Churn_Risk", as_index=False)
                .agg(
                    customers=("customer_id", "count"),
                    avg_probability=("Churn_Probability", "mean")
                    if "Churn_Probability" in churn_df.columns
                    else ("customer_id", "count"),
                )
                .sort_values("customers", ascending=False)
            )
            if "avg_probability" in dist.columns:
                dist["avg_probability"] = dist["avg_probability"].round(4)
            churn_rows = df_to_table_rows(dist, max_rows=10)

        # Ratings context
        if not reviews_df.empty and "restaurant_rating" in reviews_df.columns:
            metrics["customer_reviews_count"] = int(len(reviews_df))

        # Optional single-customer C360 lookup (explicitly excludes unrelated customers / raw PII dump)
        c360_rows: List[Dict[str, Any]] = []
        c360_rec_text: Optional[str] = None
        if customer_id_filter is not None:
            cid = str(customer_id_filter).strip()
            if cid not in set(customers_raw["customer_id"].astype(str)):
                data_gaps.append(f"Requested customer_id '{cid}' not found")
            else:
                try:
                    from python.intelligence.customer.customer_360 import build_customer_360_profile

                    profile = build_customer_360_profile(
                        cid,
                        orders_raw,
                        customers_raw,
                        churn_raw,
                        rfm_df if not rfm_df.empty else None,
                        clv_df if not clv_df.empty else None,
                    )
                    if profile:
                        ident = profile.get("identity", {})
                        p_met = profile.get("metrics", {})
                        p_int = profile.get("intelligence", {})
                        c360_rec_text = sanitize_text(str(profile.get("recommendation", "")))
                        c360_row = {
                            "customer_id": sanitize_scalar(ident.get("customer_id", cid)),
                            "city": sanitize_scalar(ident.get("city")),
                            "persona": sanitize_scalar(ident.get("persona")),
                            "subscription_type": sanitize_scalar(ident.get("subscription_type")),
                            "total_orders": sanitize_scalar(p_met.get("Total_Orders")),
                            "total_spent_inr": sanitize_scalar(p_met.get("Total_Spent")),
                            "aov_inr": sanitize_scalar(p_met.get("AOV")),
                            "recency_days": sanitize_scalar(p_met.get("Recency_Days")),
                            "rfm_segment": sanitize_scalar(p_int.get("RFM_Segment")),
                            "estimated_clv_inr": sanitize_scalar(p_int.get("Estimated_CLV")),
                            "churn_risk": sanitize_scalar(p_int.get("Churn_Risk")),
                            "churn_probability": sanitize_scalar(p_int.get("Churn_Probability")),
                        }
                        c360_rows = [c360_row]
                        metrics["c360_total_orders"] = int(p_met.get("Total_Orders", 0))
                        metrics["c360_total_spent_inr"] = safe_round(p_met.get("Total_Spent", 0.0), 2)
                except Exception as exc:
                    data_gaps.append(f"Customer 360 profile lookup error: {exc}")

        charts: List[ChartSpec] = []
        if segment_rows:
            charts.append(
                ChartSpec(
                    chart_type="bar",
                    title="Customers by RFM Segment",
                    x_key="RFM_Segment",
                    y_key="customers",
                    data=segment_rows,
                )
            )
        if churn_rows:
            charts.append(
                ChartSpec(
                    chart_type="bar",
                    title="Experimental Churn Risk Distribution",
                    x_key="Churn_Risk",
                    y_key="customers",
                    data=churn_rows,
                )
            )

        if sql_rows:
            table_rows = sql_rows
        elif intent == "customer_360" and c360_rows:
            table_rows = c360_rows
        elif intent == "cohort_analysis" and cohort_rows:
            table_rows = cohort_rows
        elif intent == "churn_indicators" and churn_rows:
            table_rows = churn_rows
        else:
            table_rows = segment_rows or churn_rows or cohort_rows

        caveats = [_build_churn_caveat()]
        recommendations: List[ActionRecommendation] = []
        if c360_rec_text:
            recommendations.append(
                ActionRecommendation(
                    title="Scoped Customer 360 Action",
                    target_type="Customer",
                    entity_id=str(customer_id_filter),
                    evidence=f"RFM/Churn profile retrieved for customer '{sanitize_text(str(customer_id_filter))}'.",
                    expected_impact="Targeted retention action.",
                    confidence="Validated behavioral history + experimental churn signal",
                    action=c360_rec_text,
                    priority="Medium",
                    recommendation_id=f"REC-C360-{str(customer_id_filter)[:12]}",
                    business_problem="Individual customer account behavioral inactivity or retention risk.",
                    proposed_action=c360_rec_text,
                    expected_benefit="Improve 1-on-1 customer retention and basket frequency.",
                    implementation_cost=50.0,
                    net_financial_impact=450.0,
                    risk_and_uncertainty="Subject to customer communication preferences and coupon expiry.",
                    confidence_tier="MODERATE",
                    measurement_period="30 days",
                    success_metric="Customer repeat order within 30 days.",
                    lifecycle_status="Proposed",
                    human_approval_required=True,
                    is_simulation_projection=True,
                )
            )
        elif high_risk_count > 0:
            recommendations.append(
                ActionRecommendation(
                    title="Triage Validated At-Risk RFM Cohorts Before Churn Campaigns",
                    target_type="Customer Retention",
                    entity_id="rfm_at_risk",
                    evidence=(
                        f"{high_risk_count:,} High Risk churn flags observed alongside validated "
                        f"cohort and repeat purchase telemetry; churn ML caveat: NEEDS_MORE_DATA."
                    ),
                    expected_impact="Prevents wasted incentive spend caused by low ML churn recall.",
                    confidence="Validated Behavioral Metrics High; Experimental Churn ML Low",
                    action="Prioritize RFM Recency/Frequency drop-offs before acting solely on ML churn probability.",
                    priority="Medium",
                    recommendation_id="REC-RET-COH-001",
                    business_problem=f"Overreliance on exploratory ML churn scores risks subsidizing customers who would order organically.",
                    proposed_action="Prioritize RFM Recency/Frequency drop-offs (>45 days) before allocating retention discount budgets.",
                    expected_benefit="Protects against wasted incentive spend; estimated savings ₹65,000.",
                    implementation_cost=15000.0,
                    net_financial_impact=50000.0,
                    risk_and_uncertainty="May delay outreach to borderline accounts while waiting for RFM threshold breach.",
                    confidence_tier="LOW_EMPIRICAL",
                    measurement_period="45 days",
                    success_metric="Zero retention budget allocated solely to unverified ML churn predictions.",
                    lifecycle_status="Proposed",
                    human_approval_required=True,
                    is_simulation_projection=True,
                )
            )

        provenance: List[DataProvenance] = [
            make_provenance(data_source_label, "customers", customers, filters_applied=filters_desc),
        ]
        if not orders.empty:
            provenance.append(make_provenance(data_source_label, "orders", orders, filters_applied=filters_desc))
        if not churn_df.empty:
            provenance.append(make_provenance(data_source_label, "customer_churn_predictions", churn_df, filters_applied=filters_desc))
        if not reviews_df.empty:
            provenance.append(make_provenance(data_source_label, "ratings_reviews", reviews_df))

        scope_label = f" in city '{city_filter}'" if city_filter else ""
        repeat_txt = (
            f", repeat purchase rate {metrics['repeat_purchase_rate_pct']:.2f}%"
            if "repeat_purchase_rate_pct" in metrics
            else ""
        )
        m1_txt = (
            f", Month 1 cohort retention {metrics['cohort_m1_retention_pct']:.2f}%"
            if "cohort_m1_retention_pct" in metrics
            else ""
        )
        arpu_txt = (
            f", realized ARPU ₹{metrics['realized_arpu_inr']:,.2f}"
            if "realized_arpu_inr" in metrics
            else ""
        )
        churn_txt = (
            f"; experimental churn screening flags {high_risk_count:,} High Risk accounts "
            f"({metrics.get('high_risk_churn_pct', 0.0):.2f}%)"
            if not churn_df.empty
            else ""
        )
        summary = (
            f"Customer intelligence{scope_label}: {total_customers:,} customers{repeat_txt}"
            f"{m1_txt}{arpu_txt}{churn_txt}."
        )
        narrative_parts = [
            "Validated behavioral metrics (RFM, Cohort Retention, Repeat Purchase Rate) are reported separately from experimental ML churn scores.",
        ]
        if avg_churn_prob is not None:
            narrative_parts.append(
                f"Average experimental churn probability is {avg_churn_prob:.4f}; Phase 05 v2 model validation status is NEEDS_MORE_DATA."
            )
        if data_gaps:
            narrative_parts.append(f"Data gaps: {'; '.join(data_gaps)}.")

        status = AgentStatus.PARTIAL if data_gaps else AgentStatus.SUCCESS
        return AgentResult(
            request_id=request.request_id,
            execution_id=request.execution_id,
            agent_id=self.AGENT_ID,
            domain=self.DOMAIN,
            status=status,
            summary=summary,
            narrative=" ".join(narrative_parts),
            facts=facts,
            metrics=metrics,
            table_rows=sanitize_table_rows(table_rows),
            charts=charts,
            recommendations=recommendations,
            caveats=caveats,
            provenance=provenance,
            sql_traces=[sql_trace] if sql_trace is not None else [],
            data_gaps=data_gaps,
        )


__all__ = ["CustomerAgent"]
