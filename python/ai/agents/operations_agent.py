"""
NovaNest Operations Intelligence Agent (Phase 06.2)
---------------------------------------------------
Specializes in Delivery Performance (KPI-09), SLA Breach Analysis (KPI-08),
Rider Efficiency & Allocation (KPI-10), ETA Prediction Evaluation,
Demand Forecasting & Hotspots, Operational Anomaly Detection, and City Comparisons.

Strict Grounding & Security Rules:
- Permitted SQL tables: `deliveries`, `riders`, `orders`.
- Never presents Phase 05 experimental ETA (`R2 = -0.0002`, `BASELINE_ONLY`) or
  per-city Demand Forecast models (`per-city R2 < 0`) as production-ready.
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
    sanitize_text,
)


SLA_BREACH_THRESHOLD_MINS = 45.0


def _infer_operations_intent(request: AgentRequest) -> str:
    if request.intent:
        return request.intent.strip().lower()
    q = request.user_query.lower()
    if any(k in q for k in ("forecast", "heatmap", "hotspot", "demand")):
        return "demand_forecasting"
    if any(k in q for k in ("anomal", "alert", "outlier", "spike")):
        return "operational_anomalies"
    if any(k in q for k in ("rider", "fleet", "allocation", "workload")):
        return "rider_performance"
    if any(k in q for k in ("eta", "sla", "breach", "delay", "latency", "city", "compare")):
        return "delivery_sla_eta"
    return "operations_overview"


def _build_eta_caveat() -> ModelCaveat:
    try:
        from python.ai.agents.base import make_model_caveat_from_registry
        return make_model_caveat_from_registry("eta_prediction", "operations")
    except Exception:
        j = load_model_v2_json("eta_prediction/eta_metrics_v2.json")
        model = str(j.get("selected_model", "HistGradientBoosting"))
        mae = safe_round(j.get("MAE_minutes", 11.5186), 4, default=11.5186)
        rmse = safe_round(j.get("RMSE_minutes", 13.3158), 4, default=13.3158)
        r2 = safe_round(j.get("R2_Score", -0.0002), 4, default=-0.0002)
        return ModelCaveat(
            model_name=f"eta_prediction_v2 ({model})",
            domain="operations",
            validation_status="BASELINE_ONLY",
            metric_summary=f"mae_min={mae}, rmse_min={rmse}, r2={r2}",
            warning=(
                "Experimental ETA model performs equivalently to predicting the mean due to missing GPS, "
                "traffic, weather, and kitchen-prep telemetry; NOT production-ready for live customer ETAs."
            ),
            is_production_ready=False,
        )


def _build_demand_caveat() -> ModelCaveat:
    try:
        from python.ai.agents.base import make_model_caveat_from_registry
        return make_model_caveat_from_registry("demand_forecast", "operations")
    except Exception:
        j = load_model_v2_json("demand_forecast/demand_metrics_v2.json")
        model = str(j.get("Model_Type", "OLS_LinearRegression"))
        mae = safe_round(j.get("MAE", 4.3889), 4, default=4.3889)
        r2 = safe_round(j.get("R2_Score", 0.7707), 4, default=0.7707)
        lag7_mae = safe_round(j.get("Baseline_SeasonalNaive_Lag7_MAE", 6.2794), 4, default=6.2794)
        return ModelCaveat(
            model_name=f"demand_forecast_v2 ({model})",
            domain="operations",
            validation_status="BASELINE_ONLY",
            metric_summary=f"pooled_mae={mae}, pooled_r2={r2}, lag7_naive_mae={lag7_mae}",
            warning=(
                "Pooled R2 is inflated by static city-volume scale differences while within-city demand R2 < 0 "
                "across cities; treat forecasts strictly as directional experimental baselines."
            ),
            is_production_ready=False,
        )


def _build_anomaly_caveat() -> ModelCaveat:
    try:
        from python.ai.agents.base import make_model_caveat_from_registry
        return make_model_caveat_from_registry("anomaly_detection", "operations")
    except Exception:
        j = load_model_v2_json("anomaly_detection/anomaly_metrics_v2.json")
        audit = j.get("Statistical_Anomaly_Audit", {}) if isinstance(j.get("Statistical_Anomaly_Audit"), dict) else {}
        total_anom = int(audit.get("total_statistical_anomalies", 2184))
        rate = safe_round(audit.get("anomaly_rate_pct", 4.371), 3, default=4.371)
        return ModelCaveat(
            model_name="anomaly_detection_v2 (Dual Z-Score & Tukey IQR)",
            domain="operations",
            validation_status="EXPERIMENTAL",
            metric_summary=f"statistical_anomalies={total_anom}, rate_pct={rate}",
            warning=(
                "Unsupervised statistical Z-Score/IQR screening without ground-truth fraud or outage labels; "
                "requires operator triage before attributing root failure."
            ),
            is_production_ready=False,
        )


class OperationsAgent(BaseDomainAgent):
    """Domain intelligence agent for delivery SLA, ETA, riders, demand, and anomalies."""

    AGENT_ID = "operations_agent"
    DOMAIN = AgentDomain.OPERATIONS
    VERSION = "1.0.0"
    DESCRIPTION = (
        "Analyzes delivery latency (KPI-09), SLA breach rates (KPI-08), rider efficiency (KPI-10), "
        "demand hotspots, operational anomalies, and experimental ETA/demand model limits."
    )
    CAPABILITIES = (
        "delivery_performance",
        "eta_evaluation",
        "sla_breach_analysis",
        "rider_performance_allocation",
        "demand_forecast_hotspots",
        "operational_anomaly_detection",
        "city_operations_comparison",
    )
    SUPPORTED_INTENTS = (
        "operations_overview",
        "delivery_sla_eta",
        "rider_performance",
        "demand_forecasting",
        "operational_anomalies",
        "sql",
    )
    ALLOWED_TABLES = ("deliveries", "riders", "orders")
    ALLOWED_DATASETS = (
        "deliveries",
        "riders",
        "orders",
        "orders_engineered",
        "eta_predictions",
        "demand_forecasts",
        "demand_heatmap",
        "rider_allocation",
        "operational_anomalies",
        "operational_alerts",
    )
    REQUIRED_SCOPES = ("read",)

    def _compute_city_delivery_rows(
        self,
        deliveries: pd.DataFrame,
        riders: pd.DataFrame,
        heatmap_df: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        if not deliveries.empty and not riders.empty and "rider_id" in deliveries.columns and "city" in riders.columns:
            joined = deliveries.merge(
                riders[["rider_id", "city"]].drop_duplicates("rider_id"),
                on="rider_id",
                how="left",
            )
            joined["city"] = joined["city"].fillna("Unknown")
            joined["_sla_breach"] = (
                pd.to_numeric(joined["delivery_duration"], errors="coerce") > SLA_BREACH_THRESHOLD_MINS
            ).astype(int)
            grp = (
                joined.groupby("city", as_index=False)
                .agg(
                    deliveries=("delivery_id", "count") if "delivery_id" in joined.columns else ("order_id", "count"),
                    avg_delivery_mins=("delivery_duration", "mean"),
                    avg_distance_km=("distance_km", "mean") if "distance_km" in joined.columns else ("delivery_duration", "count"),
                    sla_breaches=("_sla_breach", "sum"),
                )
            )
            grp["sla_breach_rate_pct"] = grp.apply(
                lambda r: round((r["sla_breaches"] / r["deliveries"]) * 100.0, 2) if r["deliveries"] > 0 else 0.0,
                axis=1,
            )
            grp["avg_delivery_mins"] = grp["avg_delivery_mins"].round(2)
            if "avg_distance_km" in grp.columns and "distance_km" in joined.columns:
                grp["avg_distance_km"] = grp["avg_distance_km"].round(2)
            grp = grp.sort_values("sla_breach_rate_pct", ascending=False)
            return df_to_table_rows(grp, max_rows=20)
        if not heatmap_df.empty:
            return df_to_table_rows(heatmap_df, max_rows=20)
        return []

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
        intent = _infer_operations_intent(request)
        city_filter = request.filters.get("city")
        filters_desc = [f"city={city_filter}"] if city_filter else []

        deliveries_raw = data.get("deliveries", pd.DataFrame())
        riders_raw = data.get("riders", pd.DataFrame())
        orders_raw = data.get("orders", pd.DataFrame())
        eta_raw = data.get("eta_predictions", pd.DataFrame())
        forecasts_raw = data.get("demand_forecasts", pd.DataFrame())
        heatmap_raw = data.get("demand_heatmap", pd.DataFrame())
        rider_alloc_raw = data.get("rider_allocation", pd.DataFrame())
        anomalies_raw = data.get("operational_anomalies", pd.DataFrame())
        alerts_raw = data.get("operational_alerts", pd.DataFrame())

        if deliveries_raw.empty and orders_raw.empty:
            return AgentResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                agent_id=self.AGENT_ID,
                domain=self.DOMAIN,
                status=AgentStatus.BLOCKED,
                summary="Both 'deliveries' and 'orders' datasets are empty; operations intelligence blocked.",
                provenance=[make_provenance(data_source_label, "deliveries", deliveries_raw)],
                errors=[
                    AgentError(
                        code="MISSING_PRIMARY_DATASET",
                        message="Deliveries or orders dataset is required for operations intelligence.",
                        agent_id=self.AGENT_ID,
                        recoverable=True,
                        severity=SeverityLevel.ERROR,
                    )
                ],
                data_gaps=["deliveries and orders datasets missing or empty"],
            )

        riders = filter_df_by_city(riders_raw, city_filter) if city_filter else riders_raw
        deliveries = deliveries_raw
        orders = orders_raw
        if city_filter:
            if "city" in deliveries_raw.columns:
                deliveries = filter_df_by_city(deliveries_raw, city_filter)
            elif not riders.empty and "rider_id" in deliveries_raw.columns and "rider_id" in riders.columns:
                deliveries = deliveries_raw[deliveries_raw["rider_id"].isin(set(riders["rider_id"]))].copy()
            if not orders_raw.empty:
                if "city" in orders_raw.columns:
                    orders = filter_df_by_city(orders_raw, city_filter)
                elif not deliveries.empty and "order_id" in orders_raw.columns and "order_id" in deliveries.columns:
                    orders = orders_raw[orders_raw["order_id"].isin(set(deliveries["order_id"]))].copy()
                elif not riders.empty and "rider_id" in orders_raw.columns and "rider_id" in riders.columns:
                    orders = orders_raw[orders_raw["rider_id"].isin(set(riders["rider_id"]))].copy()

        data_gaps: List[str] = []
        facts: List[GroundedFact] = []
        metrics: Dict[str, Any] = {"sla_threshold_mins": SLA_BREACH_THRESHOLD_MINS}

        # 1. Delivery & SLA KPIs (KPI-08, KPI-09)
        total_deliveries = int(len(deliveries))
        if deliveries.empty or "delivery_duration" not in deliveries.columns:
            data_gaps.append("deliveries dataset or delivery_duration missing: SLA breach & avg delivery time omitted")
            avg_delivery_mins: Optional[float] = None
            sla_breach_rate_pct: Optional[float] = None
            sla_breach_count: int = 0
        else:
            durations = pd.to_numeric(deliveries["delivery_duration"], errors="coerce").dropna()
            avg_delivery_mins = safe_round(durations.mean(), 2) if not durations.empty else 0.0
            sla_breach_count = int((durations > SLA_BREACH_THRESHOLD_MINS).sum())
            sla_breach_rate_pct = safe_round((sla_breach_count / total_deliveries) * 100.0, 2) if total_deliveries > 0 else 0.0
            metrics["total_deliveries"] = total_deliveries
            metrics["avg_delivery_time_mins"] = avg_delivery_mins
            metrics["sla_breach_count"] = sla_breach_count
            metrics["sla_breach_rate_pct"] = sla_breach_rate_pct
            facts.extend(
                [
                    GroundedFact(
                        label="Total Deliveries",
                        value=total_deliveries,
                        unit="deliveries",
                        source=f"{data_source_label}:deliveries",
                    ),
                    GroundedFact(
                        label="Average Delivery Time",
                        value=avg_delivery_mins,
                        unit="minutes",
                        kpi_id=None if city_filter else "KPI-09",
                        source=f"{data_source_label}:deliveries",
                    ),
                    GroundedFact(
                        label="Delivery SLA Breach Rate",
                        value=sla_breach_rate_pct,
                        unit="%",
                        kpi_id=None if city_filter else "KPI-08",
                        source=f"{data_source_label}:deliveries",
                    ),
                    GroundedFact(
                        label="SLA Breached Deliveries (>45m)",
                        value=sla_breach_count,
                        unit="deliveries",
                        source=f"{data_source_label}:deliveries",
                    ),
                ]
            )
            if "distance_km" in deliveries.columns:
                avg_dist = safe_round(pd.to_numeric(deliveries["distance_km"], errors="coerce").dropna().mean(), 2)
                metrics["avg_distance_km"] = avg_dist
                facts.append(
                    GroundedFact(
                        label="Average Delivery Distance",
                        value=avg_dist,
                        unit="km",
                        source=f"{data_source_label}:deliveries",
                    )
                )

        # 2. Order fulfillment & Rider Efficiency (KPI-10)
        total_orders = int(len(orders))
        metrics["total_orders"] = total_orders
        if total_orders > 0:
            facts.append(
                GroundedFact(
                    label="Total Orders Evaluated",
                    value=total_orders,
                    unit="orders",
                    kpi_id=None if city_filter else "KPI-05",
                    source=f"{data_source_label}:orders",
                )
            )
        if not riders.empty:
            num_riders = int(len(riders))
            orders_for_ratio = total_orders if total_orders > 0 else total_deliveries
            rider_efficiency = safe_round(orders_for_ratio / num_riders, 2) if num_riders > 0 else 0.0
            metrics["active_riders"] = num_riders
            metrics["rider_efficiency_orders_per_rider"] = rider_efficiency
            facts.extend(
                [
                    GroundedFact(
                        label="Active Riders",
                        value=num_riders,
                        unit="riders",
                        source=f"{data_source_label}:riders",
                    ),
                    GroundedFact(
                        label="Rider Efficiency Ratio",
                        value=rider_efficiency,
                        unit="orders/rider",
                        kpi_id=None if city_filter else "KPI-10",
                        source=f"{data_source_label}:orders+riders",
                    ),
                ]
            )
        else:
            data_gaps.append("riders dataset missing or empty: Rider Efficiency Ratio (KPI-10) omitted")

        # Contextual rider-specific lookup if specified in filters
        rider_id_filter = request.filters.get("rider_id")
        target_rider_match = None
        if rider_id_filter and not deliveries_raw.empty and "rider_id" in deliveries_raw.columns:
            r_str = str(rider_id_filter).strip().upper()
            r_delivs = deliveries_raw[deliveries_raw["rider_id"].astype(str).str.upper() == r_str]
            if not r_delivs.empty:
                r_count = int(len(r_delivs))
                r_dur = safe_round(pd.to_numeric(r_delivs["delivery_duration"], errors="coerce").dropna().mean(), 2)
                r_breaches = int((pd.to_numeric(r_delivs["delivery_duration"], errors="coerce") > SLA_BREACH_THRESHOLD_MINS).sum())
                target_rider_match = {
                    "rider_id": r_str,
                    "deliveries": r_count,
                    "avg_duration_mins": r_dur,
                    "sla_breaches": r_breaches,
                }
                facts.append(
                    GroundedFact(
                        label=f"Total Deliveries for Rider {r_str}",
                        value=r_count,
                        unit="deliveries",
                        source=f"{data_source_label}:deliveries",
                    )
                )
                facts.append(
                    GroundedFact(
                        label=f"Average Delivery Duration for Rider {r_str}",
                        value=r_dur,
                        unit="minutes",
                        source=f"{data_source_label}:deliveries",
                    )
                )
                metrics["target_rider_id"] = r_str
                metrics["target_rider_deliveries"] = r_count
                metrics["target_rider_avg_duration_mins"] = r_dur
                metrics["target_rider_sla_breaches"] = r_breaches

        rider_rows: List[Dict[str, Any]] = []
        if not rider_alloc_raw.empty:
            alloc_scoped = filter_df_by_city(rider_alloc_raw, city_filter) if city_filter else rider_alloc_raw
            if "workload_tier" in alloc_scoped.columns:
                tier_grp = alloc_scoped.groupby("workload_tier", as_index=False).agg(
                    allocations=("order_id", "count"),
                    avg_score=("allocation_score", "mean")
                    if "allocation_score" in alloc_scoped.columns
                    else ("order_id", "count"),
                )
                if "avg_score" in tier_grp.columns:
                    tier_grp["avg_score"] = tier_grp["avg_score"].round(2)
                rider_rows = df_to_table_rows(tier_grp, max_rows=10)
        elif not deliveries.empty and not riders.empty:
            try:
                from python.intelligence.operations.rider_allocation import calculate_rider_workload

                rw_df = calculate_rider_workload(deliveries, riders)
                rider_rows = df_to_table_rows(rw_df, max_rows=20)
            except Exception as exc:
                data_gaps.append(f"Rider workload analysis skipped: {exc}")

        # 3. ETA Prediction diagnostics (strictly experimental baseline)
        if not eta_raw.empty and "abs_eta_error" in eta_raw.columns:
            eta_scoped = eta_raw
            if city_filter and not deliveries.empty and "order_id" in deliveries.columns and "order_id" in eta_raw.columns:
                eta_scoped = eta_raw[eta_raw["order_id"].isin(set(deliveries["order_id"]))]
            if not eta_scoped.empty:
                eta_mae = safe_round(pd.to_numeric(eta_scoped["abs_eta_error"], errors="coerce").dropna().mean(), 2)
                metrics["eta_empirical_mae_mins"] = eta_mae
                facts.append(
                    GroundedFact(
                        label="ETA Empirical Mean Absolute Error (Experimental Baseline)",
                        value=eta_mae,
                        unit="minutes",
                        source=f"{data_source_label}:eta_predictions",
                        is_confirmed=False,
                    )
                )

        # 4. Demand Heatmap & Experimental Demand Forecast
        forecast_rows: List[Dict[str, Any]] = []
        heatmap_scoped = filter_df_by_city(heatmap_raw, city_filter) if (city_filter and not heatmap_raw.empty) else heatmap_raw
        if heatmap_scoped.empty and not orders.empty and "order_datetime" in orders.columns:
            try:
                from python.intelligence.operations.demand_heatmap import generate_demand_hotspots

                heatmap_scoped = generate_demand_hotspots(orders, pd.DataFrame())
            except Exception:
                pass
        if not heatmap_scoped.empty:
            forecast_rows = df_to_table_rows(heatmap_scoped, max_rows=20)

        if not forecasts_raw.empty and "predicted_orders" in forecasts_raw.columns:
            f_scoped = filter_df_by_city(forecasts_raw, city_filter) if city_filter else forecasts_raw
            if not f_scoped.empty:
                metrics["forecast_window_days"] = int(len(f_scoped))
                metrics["mean_predicted_daily_orders"] = safe_round(
                    pd.to_numeric(f_scoped["predicted_orders"], errors="coerce").dropna().mean(), 2
                )
                if intent == "demand_forecasting":
                    forecast_rows = df_to_table_rows(f_scoped, max_rows=30)

        # 5. Operational Anomalies & Alerts
        anomaly_rows: List[Dict[str, Any]] = []
        anom_scoped = pd.DataFrame()
        if not anomalies_raw.empty:
            anom_scoped = anomalies_raw
        elif not orders.empty and not deliveries.empty:
            try:
                from python.intelligence.operations.anomaly_detection import detect_operational_anomalies_with_audit

                anom_scoped, _ = detect_operational_anomalies_with_audit(orders, deliveries)
            except Exception as exc:
                data_gaps.append(f"Operational anomaly engine skipped: {exc}")

        if not anom_scoped.empty:
            total_anomalies = int(len(anom_scoped))
            metrics["operational_anomalies_count"] = total_anomalies
            facts.append(
                GroundedFact(
                    label="Operational Statistical Anomalies Flagged",
                    value=total_anomalies,
                    unit="records",
                    source=f"{data_source_label}:operational_anomalies",
                    is_confirmed=False,
                )
            )
            if "Severity" in anom_scoped.columns:
                sev_grp = anom_scoped.groupby("Severity", as_index=False).size().rename(columns={"size": "count"})
                anomaly_rows = df_to_table_rows(sev_grp, max_rows=10)
            else:
                anomaly_rows = df_to_table_rows(anom_scoped, max_rows=20)

        alerts_count = int(len(alerts_raw)) if not alerts_raw.empty else 0
        metrics["active_operational_alerts"] = alerts_count

        city_rows = self._compute_city_delivery_rows(deliveries, riders, heatmap_scoped)

        charts: List[ChartSpec] = []
        if city_rows and "sla_breach_rate_pct" in city_rows[0]:
            charts.append(
                ChartSpec(
                    chart_type="bar",
                    title="SLA Breach Rate (%) by City",
                    x_key="city",
                    y_key="sla_breach_rate_pct",
                    data=city_rows[:15],
                )
            )
        if forecast_rows and "predicted_orders" in forecast_rows[0]:
            charts.append(
                ChartSpec(
                    chart_type="line",
                    title="Experimental Daily Demand Forecast vs Actuals",
                    x_key="date",
                    y_key="predicted_orders",
                    data=forecast_rows[:30],
                )
            )

        if sql_rows:
            table_rows = sql_rows
        elif intent == "rider_performance" and rider_rows:
            table_rows = rider_rows
        elif intent == "demand_forecasting" and forecast_rows:
            table_rows = forecast_rows
        elif intent == "operational_anomalies" and anomaly_rows:
            table_rows = anomaly_rows
        else:
            table_rows = city_rows or rider_rows or anomaly_rows or forecast_rows

        caveats = [_build_eta_caveat(), _build_demand_caveat(), _build_anomaly_caveat()]
        recommendations: List[ActionRecommendation] = []
        if target_rider_match is not None:
            r_str = target_rider_match["rider_id"]
            r_count = target_rider_match["deliveries"]
            r_dur = target_rider_match["avg_duration_mins"]
            r_breaches = target_rider_match["sla_breaches"]
            recommendations.append(
                ActionRecommendation(
                    title=f"Rider Profile & Performance ({r_str})",
                    target_type="Rider",
                    entity_id=r_str,
                    evidence=f"{r_count} deliveries completed with {r_dur} mins average latency and {r_breaches} SLA breaches.",
                    expected_impact="Optimize route assignment and dispatch scheduling.",
                    confidence="Deterministic delivery records lookup",
                    action=f"Review dispatch zone assignments and delivery latency for rider {r_str}.",
                    priority="Medium",
                    recommendation_id=f"REC-RDR-{r_str[:12]}",
                    business_problem="Individual rider dispatch latency and route efficiency.",
                    proposed_action=f"Audit dispatch cluster and vehicle suitability for rider {r_str}.",
                    expected_benefit="Improve unit delivery duration by 3-5 minutes.",
                    implementation_cost=0.0,
                    net_financial_impact=500.0,
                    risk_and_uncertainty="Traffic and weather fluctuations.",
                    confidence_tier="MODERATE",
                    measurement_period="14 days",
                    success_metric="Zero SLA breaches on next 20 dispatches.",
                    lifecycle_status="Proposed",
                    human_approval_required=True,
                    is_simulation_projection=True,
                )
            )
        if sla_breach_rate_pct is not None and sla_breach_rate_pct > 25.0:
            recommendations.append(
                ActionRecommendation(
                    title="Mitigate High Delivery SLA Breach Rate via Zone Dispatch Balancing",
                    target_type="Operations & Logistics",
                    entity_id=city_filter or "all_cities",
                    evidence=(
                        f"SLA breach rate is {sla_breach_rate_pct:.2f}% ({sla_breach_count:,} deliveries exceeding "
                        f"{SLA_BREACH_THRESHOLD_MINS:.0f} mins)."
                    ),
                    expected_impact="Target reduction in >45m delivery tail once traffic/prep telemetry is instrumented.",
                    confidence="Validated Delivery Telemetry (ETA ML remains BASELINE_ONLY)",
                    action="Instrument real-time prep/GPS telemetry and rebalance riders in peak breach zones.",
                    priority="High",
                    recommendation_id="REC-OPS-SLA-SYS",
                    business_problem=f"Elevated SLA breach rate ({sla_breach_rate_pct:.2f}%) degrades customer retention.",
                    proposed_action="Rebalance dispatch zone radii (max 6 km during peak surge) and deploy peak incentive pools.",
                    expected_benefit="Projected 25% reduction in SLA breaches; saving ~₹56,000 in credits.",
                    implementation_cost=45000.0,
                    net_financial_impact=11000.0,
                    risk_and_uncertainty="Batch historical telemetry used; live real-time GPS required for dynamic control.",
                    confidence_tier="OPERATIONAL_GATED",
                    measurement_period="30 days",
                    success_metric="SLA breach rate drops below 24.0%.",
                    lifecycle_status="Proposed",
                    human_approval_required=True,
                    is_simulation_projection=True,
                )
            )

        provenance: List[DataProvenance] = []
        if not deliveries.empty:
            provenance.append(make_provenance(data_source_label, "deliveries", deliveries, filters_applied=filters_desc))
        if not riders.empty:
            provenance.append(make_provenance(data_source_label, "riders", riders, filters_applied=filters_desc))
        if not orders.empty:
            provenance.append(make_provenance(data_source_label, "orders", orders, filters_applied=filters_desc))
        if not anomalies_raw.empty:
            provenance.append(make_provenance(data_source_label, "operational_anomalies", anomalies_raw))

        scope_label = f" for city '{city_filter}'" if city_filter else " platform-wide"
        deliv_txt = (
            f"avg delivery time {avg_delivery_mins:.2f} mins, SLA breach rate {sla_breach_rate_pct:.2f}% "
            f"({sla_breach_count:,}/{total_deliveries:,} deliveries > {SLA_BREACH_THRESHOLD_MINS:.0f} mins)"
            if avg_delivery_mins is not None and sla_breach_rate_pct is not None
            else "delivery timing data unavailable"
        )
        rider_txt = (
            f", rider efficiency {metrics['rider_efficiency_orders_per_rider']:.2f} orders/rider"
            if "rider_efficiency_orders_per_rider" in metrics
            else ""
        )
        summary = f"Operations intelligence{scope_label}: {deliv_txt}{rider_txt}."
        narrative_parts = [
            "Experimental ML disclosures: ETA prediction (BASELINE_ONLY, zero GPS/traffic features) and "
            "per-city demand forecasting are NOT production-ready for live SLA commitments.",
        ]
        if "operational_anomalies_count" in metrics:
            narrative_parts.append(
                f"Statistical screening flagged {metrics['operational_anomalies_count']:,} operational anomalies."
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


__all__ = ["OperationsAgent"]
