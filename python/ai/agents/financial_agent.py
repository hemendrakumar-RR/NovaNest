"""
NovaNest Financial Intelligence Agent (Phase 06.2)
--------------------------------------------------
Specializes in GMV, Net Revenue, Net/Gross AOV, Take Rate, Realized Profit,
Contribution Margin, Monthly Financial Trends, City Comparisons, and
Unconfirmed Revenue Leakage / Margin Anomaly Screening.

Strict Grounding & Security Rules:
- Uses actual `orders`, `orders_engineered`, `payments`, `promotions`, `restaurants`,
  and `revenue_leakage` datasets.
- Permitted SQL tables: `orders`, `payments`, `promotions`, `restaurants`.
- Preserves `is_confirmed_loss=False` on all discount/subsidy leakage screening results
  and discloses missing promo-funding split between platform and restaurant partners.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from python.ai.agents.base import (
    BaseDomainAgent,
    df_to_table_rows,
    ensure_python_path,
    filter_df_by_city,
    make_provenance,
    safe_float,
    safe_round,
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
)


def _infer_financial_intent(request: AgentRequest) -> str:
    if request.intent:
        return request.intent.strip().lower()
    q = request.user_query.lower()
    if any(k in q for k in ("leak", "subsidy", "anomal", "discount", "negative margin", "loss")):
        return "financial_anomalies"
    if any(k in q for k in ("trend", "monthly", "month", "growth", "time series")):
        return "revenue_trends"
    if any(k in q for k in ("compare", "city", "cities", "benchmark", "payment", "promo")):
        return "financial_comparison"
    return "financial_overview"


class FinancialAgent(BaseDomainAgent):
    """Domain intelligence agent for NovaNest platform financials and leakage screening."""

    AGENT_ID = "financial_agent"
    DOMAIN = AgentDomain.FINANCIAL
    VERSION = "1.0.0"
    DESCRIPTION = (
        "Computes certified GMV, Net Revenue, Net/Gross AOV, Take Rate, Realized Profit, "
        "Contribution Margin, revenue trends, city comparisons, and unconfirmed leakage screening."
    )
    CAPABILITIES = (
        "gmv_revenue_analysis",
        "aov_unit_economics",
        "realized_profit_margin",
        "revenue_trends",
        "financial_comparisons",
        "financial_anomaly_screening",
    )
    SUPPORTED_INTENTS = (
        "financial_overview",
        "revenue_trends",
        "financial_comparison",
        "financial_anomalies",
        "sql",
    )
    ALLOWED_TABLES = ("orders", "payments", "promotions", "restaurants")
    ALLOWED_DATASETS = (
        "orders",
        "orders_engineered",
        "payments",
        "promotions",
        "revenue_leakage",
        "restaurants",
    )
    REQUIRED_SCOPES = ("read",)

    def _compute_city_financials(
        self,
        delivered: pd.DataFrame,
        non_cancelled: pd.DataFrame,
        restaurants: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        if delivered.empty:
            return []
        deliv_enriched = delivered.copy()
        nc_enriched = non_cancelled.copy()
        if "city" not in deliv_enriched.columns:
            if (
                not restaurants.empty
                and "restaurant_id" in deliv_enriched.columns
                and "restaurant_id" in restaurants.columns
                and "city" in restaurants.columns
            ):
                rest_map = restaurants[["restaurant_id", "city"]].drop_duplicates("restaurant_id")
                deliv_enriched = deliv_enriched.merge(rest_map, on="restaurant_id", how="left")
                nc_enriched = nc_enriched.merge(rest_map, on="restaurant_id", how="left")
            elif "restaurant_city" in deliv_enriched.columns:
                deliv_enriched["city"] = deliv_enriched["restaurant_city"]
                nc_enriched["city"] = nc_enriched.get("restaurant_city", "Unknown")

        if "city" not in deliv_enriched.columns:
            return []

        deliv_enriched["city"] = deliv_enriched["city"].fillna("Unknown")
        nc_enriched["city"] = nc_enriched.get("city", pd.Series("Unknown", index=nc_enriched.index)).fillna("Unknown")

        deliv_grp = (
            deliv_enriched.groupby("city", as_index=False)
            .agg(delivered_orders=("order_id", "count"), net_revenue_inr=("final_amount", "sum"))
        )
        gmv_grp = (
            nc_enriched.groupby("city", as_index=False)
            .agg(non_cancelled_orders=("order_id", "count"), gmv_inr=("order_amount", "sum"))
        )
        merged = deliv_grp.merge(gmv_grp, on="city", how="outer").fillna(0)
        merged["net_aov_inr"] = merged.apply(
            lambda r: round(r["net_revenue_inr"] / r["delivered_orders"], 2) if r["delivered_orders"] > 0 else 0.0,
            axis=1,
        )
        merged["net_revenue_inr"] = merged["net_revenue_inr"].round(2)
        merged["gmv_inr"] = merged["gmv_inr"].round(2)
        merged = merged.sort_values("net_revenue_inr", ascending=False)
        return df_to_table_rows(merged, max_rows=20)

    def _compute_monthly_trends(
        self,
        delivered: pd.DataFrame,
        non_cancelled: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        if delivered.empty or "order_datetime" not in delivered.columns:
            return []
        deliv_dt = pd.to_datetime(delivered["order_datetime"], errors="coerce")
        valid_mask = deliv_dt.notna()
        if not valid_mask.any():
            return []
        df_d = delivered.loc[valid_mask].copy()
        df_d["month"] = deliv_dt.loc[valid_mask].dt.strftime("%Y-%m")
        monthly = (
            df_d.groupby("month", as_index=False)
            .agg(delivered_orders=("order_id", "count"), net_revenue_inr=("final_amount", "sum"))
        )
        if not non_cancelled.empty and "order_datetime" in non_cancelled.columns:
            nc_dt = pd.to_datetime(non_cancelled["order_datetime"], errors="coerce")
            nc_valid = nc_dt.notna()
            if nc_valid.any():
                df_nc = non_cancelled.loc[nc_valid].copy()
                df_nc["month"] = nc_dt.loc[nc_valid].dt.strftime("%Y-%m")
                gmv_m = df_nc.groupby("month", as_index=False).agg(gmv_inr=("order_amount", "sum"))
                monthly = monthly.merge(gmv_m, on="month", how="left").fillna(0)
        monthly["net_revenue_inr"] = monthly["net_revenue_inr"].round(2)
        if "gmv_inr" in monthly.columns:
            monthly["gmv_inr"] = monthly["gmv_inr"].round(2)
        monthly = monthly.sort_values("month")
        return df_to_table_rows(monthly, max_rows=36)

    def _analyze_leakage(
        self,
        orders: pd.DataFrame,
        restaurants: pd.DataFrame,
        orders_eng: pd.DataFrame,
        leakage_df: pd.DataFrame,
        city_filter: Optional[str],
    ) -> Tuple[pd.DataFrame, str, Optional[str]]:
        """Return flagged leakage DataFrame, provenance source label, and optional data gap."""
        ensure_python_path()
        if leakage_df is not None and not leakage_df.empty:
            scoped = leakage_df.copy()
            if city_filter and "order_id" in scoped.columns and "city" not in scoped.columns:
                if "order_id" in orders.columns:
                    city_orders = filter_df_by_city(orders, city_filter)
                    if not city_orders.empty:
                        scoped = scoped[scoped["order_id"].isin(set(city_orders["order_id"]))]
            elif city_filter:
                scoped = filter_df_by_city(scoped, city_filter)
            return scoped, "revenue_leakage.csv", None

        # Dynamic engine fallback using approved intelligence engine (no fabricated values)
        if not orders.empty and not restaurants.empty and not orders_eng.empty:
            try:
                from python.intelligence.operations.revenue_leakage import detect_revenue_leakage

                computed = detect_revenue_leakage(orders, restaurants, orders_eng)
                if city_filter and "order_id" in computed.columns:
                    computed = computed[computed["order_id"].isin(set(orders["order_id"]))]
                return computed, "detect_revenue_leakage", None
            except Exception as exc:
                return pd.DataFrame(), "detect_revenue_leakage", f"Revenue leakage engine error: {exc}"

        return (
            pd.DataFrame(),
            "revenue_leakage",
            "Revenue leakage screening unavailable (missing revenue_leakage or orders_engineered/restaurants).",
        )

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
        intent = _infer_financial_intent(request)
        city_filter = request.filters.get("city")
        filters_desc = [f"city={city_filter}"] if city_filter else []

        orders_raw = data.get("orders", pd.DataFrame())
        restaurants = data.get("restaurants", pd.DataFrame())
        orders_eng_raw = data.get("orders_engineered", pd.DataFrame())
        payments_raw = data.get("payments", pd.DataFrame())
        promotions = data.get("promotions", pd.DataFrame())
        leakage_raw = data.get("revenue_leakage", pd.DataFrame())

        if orders_raw.empty:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.BLOCKED,
                summary="Primary 'orders' dataset is missing or empty; financial KPI calculation blocked.",
                provenance=[make_provenance(data_source_label, "orders", orders_raw)],
                errors=[
                    AgentError(
                        code="MISSING_PRIMARY_DATASET",
                        message="Primary 'orders' dataset is required for financial analysis.",
                        agent_id=self.AGENT_ID,
                        recoverable=True,
                        severity=SeverityLevel.ERROR,
                    )
                ],
                data_gaps=["orders dataset missing or empty"],
            )

        required_order_cols = {"order_id", "order_amount", "final_amount", "order_status"}
        missing_cols = sorted(required_order_cols - set(orders_raw.columns))
        if missing_cols:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.ERROR,
                summary=f"Orders dataset missing required financial columns: {missing_cols}.",
                provenance=[make_provenance(data_source_label, "orders", orders_raw)],
                errors=[
                    AgentError(
                        code="SCHEMA_MISMATCH",
                        message=f"Orders schema incomplete; missing columns {missing_cols}.",
                        agent_id=self.AGENT_ID,
                        recoverable=False,
                        severity=SeverityLevel.ERROR,
                    )
                ],
                data_gaps=[f"Missing orders columns: {missing_cols}"],
            )

        orders = orders_raw
        orders_eng = orders_eng_raw
        if city_filter:
            # Join restaurant city onto orders when filtering by city
            if "city" not in orders.columns and not restaurants.empty and "city" in restaurants.columns:
                city_rests = filter_df_by_city(restaurants, city_filter)
                if not city_rests.empty and "restaurant_id" in orders.columns:
                    orders = orders[orders["restaurant_id"].isin(set(city_rests["restaurant_id"]))].copy()
                else:
                    orders = orders.iloc[0:0].copy()
            else:
                orders = filter_df_by_city(orders, city_filter)
            if not orders_eng.empty and "order_id" in orders_eng.columns:
                orders_eng = orders_eng[orders_eng["order_id"].isin(set(orders["order_id"]))].copy()

        data_gaps: List[str] = []
        if orders.empty:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.PARTIAL,
                summary=f"No orders matched city filter '{city_filter}'.",
                provenance=[make_provenance(data_source_label, "orders", orders_raw, filters_applied=filters_desc)],
                data_gaps=[f"Zero matching orders for city '{city_filter}'"],
            )

        # Core certified calculations (matching kpi_engine.py & api/main.py)
        total_orders = int(len(orders))
        delivered = orders[orders["order_status"] == "Delivered"]
        non_cancelled = orders[orders["order_status"] != "Cancelled"]
        completed_orders = int(len(delivered))
        cancelled_orders = int((orders["order_status"] == "Cancelled").sum())

        gmv_inr = safe_round(non_cancelled["order_amount"].sum(), 2)
        net_revenue_inr = safe_round(delivered["final_amount"].sum(), 2)
        net_aov_inr = safe_round(net_revenue_inr / completed_orders, 2) if completed_orders > 0 else 0.0
        gross_aov_inr = safe_round(gmv_inr / completed_orders, 2) if completed_orders > 0 else 0.0
        total_discounts_inr = safe_round(
            delivered["discount_amount"].sum() if "discount_amount" in delivered.columns else 0.0, 2
        )

        # Take Rate & Commission Revenue
        commission_revenue_inr: Optional[float] = None
        take_rate_pct: Optional[float] = None
        if (
            not restaurants.empty
            and "restaurant_id" in delivered.columns
            and "restaurant_id" in restaurants.columns
            and "commission_percentage" in restaurants.columns
        ):
            comm_df = delivered.merge(
                restaurants[["restaurant_id", "commission_percentage"]].drop_duplicates("restaurant_id"),
                on="restaurant_id",
                how="left",
            )
            comm_df["_comm"] = (
                pd.to_numeric(comm_df["order_amount"], errors="coerce").fillna(0.0)
                * pd.to_numeric(comm_df["commission_percentage"], errors="coerce").fillna(0.0)
                / 100.0
            )
            commission_revenue_inr = safe_round(comm_df["_comm"].sum(), 2)
            take_rate_pct = safe_round((commission_revenue_inr / gmv_inr) * 100.0, 2) if gmv_inr > 0 else 0.0
        elif not orders_eng.empty and "commission_revenue" in orders_eng.columns:
            deliv_eng_comm = (
                orders_eng[orders_eng["order_status"] == "Delivered"]
                if "order_status" in orders_eng.columns
                else orders_eng
            )
            commission_revenue_inr = safe_round(deliv_eng_comm["commission_revenue"].sum(), 2)
            take_rate_pct = safe_round((commission_revenue_inr / gmv_inr) * 100.0, 2) if gmv_inr > 0 else 0.0
        else:
            data_gaps.append("restaurants/commission_percentage unavailable: Take Rate and Commission Revenue omitted")

        # Realized Profit & Contribution Margin
        realized_profit_inr: Optional[float] = None
        contribution_margin_pct: Optional[float] = None
        if not orders_eng.empty and "estimated_profit" in orders_eng.columns:
            deliv_eng = (
                orders_eng[orders_eng["order_status"] == "Delivered"]
                if "order_status" in orders_eng.columns
                else orders_eng[orders_eng["order_id"].isin(set(delivered["order_id"]))]
                if "order_id" in orders_eng.columns
                else orders_eng
            )
            realized_profit_inr = safe_round(deliv_eng["estimated_profit"].sum(), 2)
            contribution_margin_pct = (
                safe_round((realized_profit_inr / net_revenue_inr) * 100.0, 2) if net_revenue_inr > 0 else 0.0
            )
        else:
            data_gaps.append("orders_engineered unavailable: Realized Profit and Contribution Margin omitted")

        # Revenue leakage screening (strictly unconfirmed!)
        leakage_df, leakage_src, leakage_gap = self._analyze_leakage(
            orders, restaurants, orders_eng, leakage_raw, city_filter
        )
        if leakage_gap:
            data_gaps.append(leakage_gap)

        leakage_flagged_orders = int(len(leakage_df)) if not leakage_df.empty else 0
        leakage_amount_col = (
            "potential_leakage_amount"
            if (not leakage_df.empty and "potential_leakage_amount" in leakage_df.columns)
            else "leakage_amount"
        )
        potential_leakage_inr = (
            safe_round(pd.to_numeric(leakage_df[leakage_amount_col], errors="coerce").fillna(0.0).sum(), 2)
            if (not leakage_df.empty and leakage_amount_col in leakage_df.columns)
            else 0.0
        )
        critical_leakage_orders = (
            int((leakage_df["risk_level"] == "Critical Leakage").sum())
            if (not leakage_df.empty and "risk_level" in leakage_df.columns)
            else 0
        )

        # Payments & Promotions context
        promo_budget_inr = 0.0
        if not promotions.empty and "campaign_budget" in promotions.columns:
            promo_budget_inr = safe_round(
                pd.to_numeric(promotions["campaign_budget"], errors="coerce").fillna(0.0).sum(), 2
            )

        payment_failed_count = 0
        if not payments_raw.empty and "payment_status" in payments_raw.columns:
            scoped_pay = (
                payments_raw[payments_raw["order_id"].isin(set(orders["order_id"]))]
                if ("order_id" in payments_raw.columns and city_filter)
                else payments_raw
            )
            payment_failed_count = int(
                scoped_pay["payment_status"].astype(str).str.lower().isin({"failed", "refunded"}).sum()
            )

        # Build Facts & Metrics
        kpi_suffix = None if city_filter else "KPI-01"
        facts: List[GroundedFact] = [
            GroundedFact(
                label="Gross Merchandise Value (GMV)",
                value=gmv_inr,
                unit="INR",
                kpi_id=kpi_suffix,
                source=f"{data_source_label}:orders",
                formula="SUM(order_amount) WHERE order_status != 'Cancelled'",
            ),
            GroundedFact(
                label="Net Revenue (Platform Inflow)",
                value=net_revenue_inr,
                unit="INR",
                kpi_id=None if city_filter else "KPI-02",
                source=f"{data_source_label}:orders",
                formula="SUM(final_amount) WHERE order_status = 'Delivered'",
            ),
            GroundedFact(
                label="Average Order Value (Net AOV)",
                value=net_aov_inr,
                unit="INR",
                kpi_id=None if city_filter else "KPI-03",
                source=f"{data_source_label}:orders",
            ),
            GroundedFact(
                label="Gross AOV",
                value=gross_aov_inr,
                unit="INR",
                source=f"{data_source_label}:orders",
            ),
            GroundedFact(
                label="Completed Orders",
                value=completed_orders,
                unit="orders",
                kpi_id=None if city_filter else "KPI-06",
                source=f"{data_source_label}:orders",
            ),
            GroundedFact(
                label="Total Orders Placed",
                value=total_orders,
                unit="orders",
                kpi_id=None if city_filter else "KPI-05",
                source=f"{data_source_label}:orders",
            ),
        ]

        metrics: Dict[str, Any] = {
            "gmv_inr": gmv_inr,
            "net_revenue_inr": net_revenue_inr,
            "net_aov_inr": net_aov_inr,
            "gross_aov_inr": gross_aov_inr,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_discounts_inr": total_discounts_inr,
            "promo_campaign_budget_inr": promo_budget_inr,
            "payment_failed_or_refunded": payment_failed_count,
            "leakage_flagged_orders": leakage_flagged_orders,
            "critical_leakage_orders": critical_leakage_orders,
            "potential_leakage_inr": potential_leakage_inr,
        }

        if take_rate_pct is not None and commission_revenue_inr is not None:
            metrics["take_rate_pct"] = take_rate_pct
            metrics["commission_revenue_inr"] = commission_revenue_inr
            facts.append(
                GroundedFact(
                    label="Take Rate",
                    value=take_rate_pct,
                    unit="%",
                    kpi_id=None if city_filter else "KPI-04",
                    source=f"{data_source_label}:orders+restaurants",
                )
            )
            facts.append(
                GroundedFact(
                    label="Commission Revenue",
                    value=commission_revenue_inr,
                    unit="INR",
                    source=f"{data_source_label}:orders+restaurants",
                )
            )

        if realized_profit_inr is not None and contribution_margin_pct is not None:
            metrics["realized_profit_inr"] = realized_profit_inr
            metrics["contribution_margin_pct"] = contribution_margin_pct
            facts.append(
                GroundedFact(
                    label="Contribution Margin %",
                    value=contribution_margin_pct,
                    unit="%",
                    kpi_id=None if city_filter else "KPI-12",
                    source=f"{data_source_label}:orders_engineered",
                )
            )
            facts.append(
                GroundedFact(
                    label="Realized Operating Profit",
                    value=realized_profit_inr,
                    unit="INR",
                    kpi_id=None if city_filter else "KPI-13",
                    source=f"{data_source_label}:orders_engineered",
                )
            )

        if not leakage_df.empty:
            facts.append(
                GroundedFact(
                    label="Potential Leakage Screening Exposure (Unconfirmed)",
                    value=potential_leakage_inr,
                    unit="INR",
                    source=leakage_src,
                    is_confirmed=False,
                    is_confirmed_loss=False,
                )
            )
            facts.append(
                GroundedFact(
                    label="Leakage Screening Flagged Orders",
                    value=leakage_flagged_orders,
                    unit="orders",
                    source=leakage_src,
                    is_confirmed=False,
                    is_confirmed_loss=False,
                )
            )
            facts.append(
                GroundedFact(
                    label="Critical Leakage Screening Orders",
                    value=critical_leakage_orders,
                    unit="orders",
                    source=leakage_src,
                    is_confirmed=False,
                    is_confirmed_loss=False,
                )
            )

        # Charts & Table Rows by intent (or SQL override if sql_trace exists)
        monthly_rows = self._compute_monthly_trends(delivered, non_cancelled)
        city_rows = self._compute_city_financials(delivered, non_cancelled, restaurants)
        charts: List[ChartSpec] = []
        if monthly_rows:
            charts.append(
                ChartSpec(
                    chart_type="line",
                    title="Monthly Net Revenue & GMV Trend",
                    x_key="month",
                    y_key="net_revenue_inr",
                    data=monthly_rows[:36],
                )
            )
        if city_rows:
            charts.append(
                ChartSpec(
                    chart_type="bar",
                    title="Net Revenue by City (Delivered Orders)",
                    x_key="city",
                    y_key="net_revenue_inr",
                    data=city_rows[:15],
                )
            )

        table_rows: List[Dict[str, Any]]
        if sql_rows:
            table_rows = sql_rows
        elif intent == "revenue_trends":
            table_rows = monthly_rows
        elif intent == "financial_anomalies" and not leakage_df.empty:
            grp_col = "leakage_reason" if "leakage_reason" in leakage_df.columns else "risk_level"
            if grp_col in leakage_df.columns and leakage_amount_col in leakage_df.columns:
                grp = (
                    leakage_df.groupby(grp_col, as_index=False)
                    .agg(
                        flagged_orders=("order_id", "count"),
                        potential_leakage_inr=(leakage_amount_col, "sum"),
                    )
                    .sort_values("potential_leakage_inr", ascending=False)
                )
                grp["potential_leakage_inr"] = grp["potential_leakage_inr"].round(2)
                table_rows = df_to_table_rows(grp, max_rows=20)
            else:
                table_rows = df_to_table_rows(leakage_df, max_rows=20)
        elif intent == "financial_comparison" and city_rows:
            table_rows = city_rows
        else:
            table_rows = city_rows or monthly_rows

        caveats = [
            ModelCaveat(
                model_name="revenue_leakage_screening",
                domain="financial",
                validation_status="EXPERIMENTAL_HEURISTIC",
                metric_summary=(
                    f"flagged_orders={leakage_flagged_orders}, "
                    f"potential_exposure_inr={potential_leakage_inr:.2f}"
                ),
                warning=(
                    "Revenue leakage figures are unconfirmed heuristic screening estimates "
                    "(is_confirmed_loss=False). Source data lacks platform-vs-merchant promo-funding split."
                ),
                is_production_ready=False,
            )
        ]

        recommendations: List[ActionRecommendation] = []
        if critical_leakage_orders > 0:
            recommendations.append(
                ActionRecommendation(
                    title="Audit Discount & Subsidy Exposure (Unconfirmed Screening)",
                    target_type="Revenue Operations",
                    entity_id="promotions_and_orders",
                    evidence=(
                        f"{critical_leakage_orders} orders flagged as Critical Leakage across "
                        f"{leakage_flagged_orders} screening candidates (₹{potential_leakage_inr:,.2f} "
                        "unconfirmed screening exposure, is_confirmed_loss=False)."
                    ),
                    expected_impact="Requires promo cost-sharing ledger attribution before estimating net recovery.",
                    confidence="Heuristic Screening (No Verified Funding Split)",
                    action="Verify whether high discounts were co-funded by restaurant partners vs platform.",
                    priority="High",
                    recommendation_id="REC-REV-LEAK-AUD",
                    business_problem="Critical discount and fee subsidies exceeding unit order commission.",
                    proposed_action="Enforce 20% discount cap and audit merchant co-funding split ledger.",
                    expected_benefit="Prevent negative order contribution margin across subsidized baskets.",
                    implementation_cost=25000.0,
                    net_financial_impact=round(potential_leakage_inr * 0.30 - 25000.0, 2),
                    risk_and_uncertainty="Disclosed as unconfirmed screening until merchant ledger reconciliation.",
                    confidence_tier="OPERATIONAL_GATED",
                    measurement_period="30 days",
                    success_metric="Zero unconfirmed subsidy orders with negative net margin.",
                    lifecycle_status="Proposed",
                    human_approval_required=True,
                    is_simulation_projection=True,
                )
            )

        provenance: List[DataProvenance] = [
            make_provenance(data_source_label, "orders", orders, filters_applied=filters_desc),
        ]
        if not orders_eng.empty:
            provenance.append(make_provenance(data_source_label, "orders_engineered", orders_eng, filters_applied=filters_desc))
        if not restaurants.empty:
            provenance.append(make_provenance(data_source_label, "restaurants", restaurants))
        if not payments_raw.empty:
            provenance.append(make_provenance(data_source_label, "payments", payments_raw))
        if not promotions.empty:
            provenance.append(make_provenance(data_source_label, "promotions", promotions))
        if not leakage_df.empty:
            provenance.append(
                make_provenance(
                    data_source_label,
                    "revenue_leakage",
                    leakage_df,
                    filters_applied=filters_desc,
                    is_confirmed_loss=False,
                )
            )

        # Compose verified summary & narrative strictly from grounded facts
        city_scope = f" for city '{city_filter}'" if city_filter else " platform-wide"
        take_rate_txt = f", Take Rate {take_rate_pct:.2f}%" if take_rate_pct is not None else ""
        profit_txt = (
            f", Realized Operating Profit ₹{realized_profit_inr:,.2f} "
            f"({contribution_margin_pct:.2f}% contribution margin)"
            if realized_profit_inr is not None and contribution_margin_pct is not None
            else ""
        )
        summary = (
            f"Financial intelligence{city_scope}: GMV ₹{gmv_inr:,.2f}, "
            f"Net Revenue ₹{net_revenue_inr:,.2f}, Net AOV ₹{net_aov_inr:,.2f} "
            f"(Gross AOV ₹{gross_aov_inr:,.2f}){take_rate_txt}{profit_txt} across "
            f"{completed_orders:,} delivered orders ({total_orders:,} placed)."
        )
        narrative_parts = [
            f"Order fulfillment covers {completed_orders:,} delivered orders out of {total_orders:,} placed.",
        ]
        if commission_revenue_inr is not None and take_rate_pct is not None:
            narrative_parts.append(
                f"Commission revenue totals ₹{commission_revenue_inr:,.2f} ({take_rate_pct:.2f}% effective take rate)."
            )
        if not leakage_df.empty:
            narrative_parts.append(
                f"Screening detected {leakage_flagged_orders:,} flagged leakage candidate orders "
                f"({critical_leakage_orders:,} critical) representing ₹{potential_leakage_inr:,.2f} "
                f"in unconfirmed exposure (is_confirmed_loss=False; promo-funding split not verified)."
            )
        if data_gaps:
            narrative_parts.append(f"Data gaps observed: {'; '.join(data_gaps)}.")

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
            is_confirmed_loss=False,
            data_gaps=data_gaps,
        )


__all__ = ["FinancialAgent"]
