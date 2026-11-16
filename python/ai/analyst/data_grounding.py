"""
NovaNest Data Grounding & Analytics Context Resolver
Extracts verified business metrics directly from loaded datasets and analytics engines.
Prevents hallucination by supplying verified figures, dynamic schemas, and provenance to the AI layer.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


def clean_num(val: Any, default: Optional[float] = 0.0) -> Optional[float]:
    """Safely coerce numeric values while avoiding NaN/Inf leakage."""
    if val is None or pd.isna(val):
        return default
    try:
        fval = float(val)
        if np.isinf(fval) or np.isnan(fval):
            return default
        return fval
    except (TypeError, ValueError):
        return default


def _resolve_column(df: Optional[pd.DataFrame], candidates: List[str]) -> Optional[str]:
    """Return the first column name in `candidates` present on `df`."""
    if df is None or df.empty:
        return None
    col_map = {str(c).lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in col_map:
            return col_map[cand.lower()]
    return None


def _extract_domains(q: str) -> List[str]:
    """Identify one or more matching business domains without first-match blind spots."""
    matched: List[str] = []

    has_leakage = any(
        k in q
        for k in [
            "leakage",
            "subsidy",
            "subsidies",
            "coupon",
            "margin deficit",
            "excessive discount",
            "discount burn",
            "revenue burn",
            "drain",
        ]
    )
    has_cancellations = any(k in q for k in ["cancel", "cancellation", "rejected", "failed order"])
    has_financial = any(
        k in q
        for k in [
            "revenue",
            "gmv",
            "profit",
            "profitability",
            "sales",
            "margin",
            "income",
            "aov",
            "financial",
            "earnings",
            "commission",
        ]
    )
    has_customers = any(
        k in q for k in ["churn", "retention", "clv", "lifetime value", "rfm", "customer", "customers", "vip"]
    )
    has_restaurants = any(
        k in q for k in ["restaurant", "restaurants", "partner", "merchant", "kitchen", "rating", "cuisine"]
    )
    has_operations = any(
        k in q
        for k in [
            "delivery",
            "deliveries",
            "eta",
            "rider",
            "riders",
            "fleet",
            "delay",
            "delays",
            "dispatch",
            "duration",
            "speed",
            "operational",
            "operations",
            "sla",
            "logistics",
        ]
    )
    has_overview = any(
        k in q
        for k in [
            "overview",
            "summary",
            "how is business",
            "how is my business",
            "how is our business",
            "analyze my business",
            "analyse my business",
            "analyze business",
            "business performance",
            "overall performance",
            "company performance",
            "platform performance",
            "our metrics",
            "novanest data",
            "all metrics",
            "business health",
            "executive summary",
        ]
    )

    if has_leakage:
        matched.append("financial_leakage")
    if has_cancellations:
        matched.append("cancellations")
    if has_financial and not (has_leakage and "revenue leakage" in q and not has_operations and not has_overview):
        # Do not treat the phrase "revenue leakage" alone as a second standalone financial domain
        matched.append("financial")
    if has_customers:
        matched.append("customers")
    if has_restaurants:
        matched.append("restaurants")
    if has_operations:
        matched.append("operations")
    if has_overview and not matched:
        matched.append("business_overview")
    elif has_overview and len(matched) == 1:
        # Broad business performance queries benefit from full overview synthesis
        matched = ["business_overview"]

    # Preserve order while deduplicating
    deduped: List[str] = []
    for item in matched:
        if item not in deduped:
            deduped.append(item)

    # Disambiguate narrow single-intent phrases that contain overlapping vocabulary
    if (
        "financial" in deduped
        and "operations" in deduped
        and not any(w in q for w in ["compare", "both", "and operational", "and delivery", "and financial", "vs"])
    ):
        # e.g., "delivery fee revenue" -> prioritize financial if specifically fee revenue without comparison
        if "delivery fee" in q and "sla" not in q and "eta" not in q and "delay" not in q:
            deduped = [d for d in deduped if d != "operations"]

    return deduped


def _compute_baseline_financials(
    orders: pd.DataFrame, orders_eng: pd.DataFrame, restaurants: pd.DataFrame
) -> Dict[str, Any]:
    """Compute certified Phase 04 financial metrics strictly from loaded data."""
    total_orders = len(orders)
    has_status = not orders.empty and "order_status" in orders.columns
    non_cancelled = orders[orders["order_status"] != "Cancelled"] if has_status else orders
    delivered = orders[orders["order_status"] == "Delivered"] if has_status else orders

    total_gmv = (
        float(non_cancelled["order_amount"].sum())
        if not non_cancelled.empty and "order_amount" in non_cancelled.columns
        else 0.0
    )
    delivered_count = len(delivered) if has_status else total_orders
    net_revenue = (
        float(delivered["final_amount"].sum())
        if not delivered.empty and "final_amount" in delivered.columns
        else total_gmv
    )
    aov = (net_revenue / delivered_count) if delivered_count > 0 else 0.0
    cancelled_count = int((orders["order_status"] == "Cancelled").sum()) if has_status else 0
    cancellation_rate = (cancelled_count / total_orders * 100.0) if total_orders > 0 else 0.0
    fulfillment_rate = (delivered_count / total_orders * 100.0) if total_orders > 0 else None

    realized_profit: Optional[float] = None
    margin_pct: Optional[float] = None

    if not orders_eng.empty and "estimated_profit" in orders_eng.columns:
        deliv_eng = (
            orders_eng[orders_eng["order_status"] == "Delivered"]
            if "order_status" in orders_eng.columns
            else orders_eng
        )
        realized_profit = float(deliv_eng["estimated_profit"].sum())
        margin_pct = (realized_profit / net_revenue * 100.0) if net_revenue > 0 else 0.0
    elif (
        not delivered.empty
        and not restaurants.empty
        and {"restaurant_id", "commission_percentage"}.issubset(restaurants.columns)
        and {"order_amount", "delivery_fee", "discount_amount"}.issubset(delivered.columns)
    ):
        merged_comm = delivered.merge(
            restaurants[["restaurant_id", "commission_percentage"]],
            on="restaurant_id",
            how="left",
        )
        comm_pct = merged_comm["commission_percentage"].fillna(0.0) / 100.0
        comm_rev = float((merged_comm["order_amount"] * comm_pct).sum())
        fee_sum = float(merged_comm["delivery_fee"].sum())
        disc_sum = float(merged_comm["discount_amount"].sum())
        realized_profit = comm_rev + fee_sum - disc_sum
        margin_pct = (realized_profit / net_revenue * 100.0) if net_revenue > 0 else 0.0

    return {
        "total_orders": total_orders,
        "non_cancelled_orders": non_cancelled,
        "delivered_orders": delivered,
        "delivered_count": delivered_count,
        "cancelled_count": cancelled_count,
        "cancellation_rate": cancellation_rate,
        "fulfillment_rate": fulfillment_rate,
        "total_gmv": total_gmv,
        "net_revenue": net_revenue,
        "aov": aov,
        "realized_profit": realized_profit,
        "margin_pct": margin_pct,
    }


def _build_cancellations_domain(
    base: Dict[str, Any], orders: pd.DataFrame, restaurants: pd.DataFrame, source_name: str
) -> Dict[str, Any]:
    total_orders = base["total_orders"]
    cancelled_count = base["cancelled_count"]
    cancellation_rate = base["cancellation_rate"]
    fulfillment_rate = base["fulfillment_rate"]

    metrics = [
        {"label": "Total Orders", "value": f"{total_orders:,}", "provenance": source_name},
        {"label": "Cancelled Orders", "value": f"{cancelled_count:,}", "provenance": source_name},
        {"label": "Platform Cancellation Rate", "value": f"{cancellation_rate:.2f}%", "provenance": source_name},
        {
            "label": "Fulfillment Rate",
            "value": f"{fulfillment_rate:.2f}%" if fulfillment_rate is not None else "N/A",
            "provenance": source_name,
        },
    ]

    table_data: List[Dict[str, Any]] = []
    suggested_chart = None
    if not orders.empty and not restaurants.empty and {"restaurant_id", "city"}.issubset(restaurants.columns):
        merged = orders.merge(restaurants[["restaurant_id", "city"]], on="restaurant_id", how="left")
        city_cancels = (
            merged.groupby("city", dropna=True)
            .agg(
                total=("order_id", "count"),
                cancelled=("order_status", lambda s: int((s == "Cancelled").sum())),
            )
            .reset_index()
        )
        city_cancels["cancel_rate"] = (city_cancels["cancelled"] / city_cancels["total"] * 100).round(2)
        city_cancels = city_cancels.sort_values(by="cancel_rate", ascending=False)
        table_data = city_cancels.to_dict(orient="records")
        suggested_chart = {
            "type": "bar",
            "title": "Cancellation Rate by Metropolitan Region (%)",
            "x_key": "city",
            "y_key": "cancel_rate",
            "data": city_cancels[["city", "cancel_rate"]].to_dict(orient="records"),
        }

    if table_data:
        worst_city = str(table_data[0]["city"])
        worst_rate = float(table_data[0]["cancel_rate"])
        territory_note = f"Across cities, {worst_city} exhibits the highest cancellation rate at {worst_rate:.2f}%."
    else:
        territory_note = "City-level cancellation breakdown is unavailable in the loaded dataset slice."

    summary = (
        f"The verified platform cancellation rate is {cancellation_rate:.2f}% "
        f"({cancelled_count:,} out of {total_orders:,} placed orders). {territory_note}"
    )

    return {
        "domain": "cancellations",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def _build_financial_domain(
    base: Dict[str, Any], restaurants: pd.DataFrame, source_name: str
) -> Dict[str, Any]:
    total_gmv = base["total_gmv"]
    net_revenue = base["net_revenue"]
    aov = base["aov"]
    delivered_count = base["delivered_count"]
    total_orders = base["total_orders"]
    margin_pct = base["margin_pct"]
    realized_profit = base["realized_profit"]
    non_cancelled_orders = base["non_cancelled_orders"]

    metrics = [
        {"label": "Gross Merchandise Value (GMV)", "value": f"₹{total_gmv/10000000:.2f} Cr", "provenance": source_name},
        {"label": "Net Revenue (Platform Inflow)", "value": f"₹{net_revenue/10000000:.2f} Cr", "provenance": source_name},
        {"label": "Average Order Value (Net AOV)", "value": f"₹{aov:.2f}", "provenance": source_name},
        {
            "label": "Realized Contribution Margin",
            "value": f"{margin_pct:.2f}%" if margin_pct is not None else "N/A",
            "provenance": source_name,
        },
    ]
    if realized_profit is not None:
        metrics.append(
            {"label": "Estimated Realized Profit", "value": f"₹{realized_profit/100000:.2f}L", "provenance": source_name}
        )

    table_data: List[Dict[str, Any]] = []
    suggested_chart = None
    top_city_note = "City breakdown is unavailable because restaurant location metadata was not joined."

    if (
        not non_cancelled_orders.empty
        and not restaurants.empty
        and {"restaurant_id", "city"}.issubset(restaurants.columns)
        and "order_amount" in non_cancelled_orders.columns
    ):
        merged = non_cancelled_orders.merge(restaurants[["restaurant_id", "city"]], on="restaurant_id", how="left")
        city_rev = merged.groupby("city", dropna=True)["order_amount"].sum().reset_index()
        city_rev = city_rev.sort_values(by="order_amount", ascending=False)
        city_rev["revenue_in_lakhs"] = (city_rev["order_amount"] / 100000).round(2)
        table_data = city_rev.to_dict(orient="records")
        suggested_chart = {
            "type": "bar",
            "title": "Gross Revenue Contribution by City (₹ Lakhs)",
            "x_key": "city",
            "y_key": "revenue_in_lakhs",
            "data": city_rev[["city", "revenue_in_lakhs"]].to_dict(orient="records"),
        }
        if not city_rev.empty:
            top_city = str(city_rev.iloc[0]["city"])
            top_lakhs = float(city_rev.iloc[0]["revenue_in_lakhs"])
            top_city_note = f"The leading revenue-generating territory is {top_city} at ₹{top_lakhs:.2f} Lakhs GMV."

    margin_phrase = f"{margin_pct:.2f}%" if margin_pct is not None else "N/A"
    summary = (
        f"Verified GMV (non-cancelled orders) is ₹{total_gmv/10000000:.2f} Crores across {delivered_count:,} completed "
        f"deliveries ({total_orders:,} total orders), with Net Revenue (Delivered) at ₹{net_revenue/10000000:.2f} Crores, "
        f"Net AOV of ₹{aov:.2f}, and Realized Contribution Margin of {margin_phrase}. {top_city_note}"
    )

    return {
        "domain": "financial",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def _build_customers_domain(
    base: Dict[str, Any], customers: pd.DataFrame, churn_df: pd.DataFrame, source_name: str
) -> Dict[str, Any]:
    total_customers = len(customers)
    total_orders = base["total_orders"]
    churn_col = _resolve_column(churn_df, ["Churn_Risk", "churn_risk_level", "churn_risk"])
    prob_col = _resolve_column(churn_df, ["Churn_Probability", "churn_probability"])

    high_churn_count = 0
    medium_churn_count = 0
    low_churn_count = 0
    churn_pct: Optional[float] = None
    avg_prob: Optional[float] = None
    table_data: List[Dict[str, Any]] = []
    suggested_chart = None

    if not churn_df.empty and churn_col is not None:
        normalized = churn_df[churn_col].astype(str).str.strip().str.lower()
        high_churn_count = int(normalized.isin(["high", "high risk"]).sum())
        medium_churn_count = int(normalized.isin(["medium", "medium risk"]).sum())
        low_churn_count = int(normalized.isin(["low", "low risk"]).sum())
        tot_scored = len(churn_df)
        churn_pct = (high_churn_count / tot_scored * 100.0) if tot_scored > 0 else 0.0
        if prob_col is not None:
            avg_prob = clean_num(churn_df[prob_col].mean(), default=None)

        dist = churn_df[churn_col].value_counts().reset_index()
        dist.columns = ["risk_level", "count"]
        dist["share_pct"] = (dist["count"] / tot_scored * 100.0).round(2) if tot_scored > 0 else 0.0
        table_data = dist.to_dict(orient="records")
        suggested_chart = {
            "type": "pie",
            "title": "Customer Churn Risk Distribution",
            "x_key": "risk_level",
            "y_key": "count",
            "data": dist[["risk_level", "count"]].to_dict(orient="records"),
        }

    order_velocity = (total_orders / total_customers) if total_customers > 0 else None
    metrics = [
        {"label": "Active Customer Base", "value": f"{total_customers:,}", "provenance": source_name},
        {
            "label": "High Churn Risk Customers",
            "value": f"{high_churn_count:,}" if churn_col is not None else "N/A",
            "provenance": source_name,
        },
        {
            "label": "High Risk Proportion",
            "value": f"{churn_pct:.2f}%" if churn_pct is not None else "N/A",
            "provenance": source_name,
        },
        {
            "label": "Average Order Velocity",
            "value": f"{order_velocity:.2f} orders/user" if order_velocity is not None else "N/A",
            "provenance": source_name,
        },
    ]
    if churn_col is not None:
        metrics.append(
            {
                "label": "Medium / Low Risk Split",
                "value": f"{medium_churn_count:,} Medium / {low_churn_count:,} Low",
                "provenance": source_name,
            }
        )
    if avg_prob is not None:
        metrics.append(
            {
                "label": "Mean Experimental Churn Probability",
                "value": f"{avg_prob * 100:.2f}%",
                "provenance": f"{source_name} (NEEDS_MORE_DATA)",
            }
        )

    if churn_col is not None and churn_pct is not None:
        churn_sentence = (
            f"The experimental churn scoring dataset flags {high_churn_count:,} customers ({churn_pct:.2f}%) as High Risk, "
            f"{medium_churn_count:,} as Medium Risk, and {low_churn_count:,} as Low Risk. "
            f"Note: Phase 05 chronological validation scored Customer Churn v2 at ROC-AUC = 0.5161 "
            f"(NEEDS_MORE_DATA — treat churn probabilities as heuristic triage rather than strong predictive certainty)."
        )
    else:
        churn_sentence = "Customer churn scoring columns are unavailable in the active dataset."

    summary = f"NovaNest serves {total_customers:,} registered customers. {churn_sentence}"
    return {
        "domain": "customers",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def _build_restaurants_domain(
    base: Dict[str, Any], orders: pd.DataFrame, restaurants: pd.DataFrame, source_name: str
) -> Dict[str, Any]:
    total_merchants = len(restaurants)
    rating_col = _resolve_column(restaurants, ["avg_rating", "rating", "restaurant_rating"])
    avg_rating = (
        clean_num(restaurants[rating_col].mean(), default=None)
        if not restaurants.empty and rating_col is not None
        else None
    )
    low_rated_count = (
        int((restaurants[rating_col] < 3.8).sum())
        if not restaurants.empty and rating_col is not None
        else None
    )

    metrics = [
        {"label": "Active Merchants", "value": f"{total_merchants:,}", "provenance": source_name},
        {
            "label": "Average Store Rating",
            "value": f"{avg_rating:.2f} / 5.0" if avg_rating is not None else "N/A",
            "provenance": source_name,
        },
    ]
    if low_rated_count is not None:
        metrics.append(
            {"label": "Merchants Rated < 3.8", "value": f"{low_rated_count:,}", "provenance": source_name}
        )

    table_data: List[Dict[str, Any]] = []
    suggested_chart = None
    top_partner_name = "Unavailable"
    top_partner_gmv_str = "N/A"
    non_cancelled = base["non_cancelled_orders"]

    if not orders.empty and not restaurants.empty and "restaurant_id" in orders.columns:
        gmv_source = non_cancelled if not non_cancelled.empty else orders
        gmv_agg = (
            gmv_source.groupby("restaurant_id")
            .agg(
                non_cancelled_orders=("order_id", "count"),
                gmv=("order_amount", "sum"),
            )
            .reset_index()
        )
        all_agg = (
            orders.groupby("restaurant_id")
            .agg(
                total_orders=("order_id", "count"),
                cancelled_orders=("order_status", lambda s: int((s == "Cancelled").sum()))
                if "order_status" in orders.columns
                else ("order_id", lambda s: 0),
            )
            .reset_index()
        )
        rest_agg = restaurants.merge(gmv_agg, on="restaurant_id", how="left").merge(
            all_agg, on="restaurant_id", how="left"
        )
        rest_agg["gmv"] = rest_agg["gmv"].fillna(0.0)
        rest_agg["non_cancelled_orders"] = rest_agg["non_cancelled_orders"].fillna(0).astype(int)
        rest_agg["total_orders"] = rest_agg["total_orders"].fillna(0).astype(int)
        rest_agg["cancelled_orders"] = rest_agg["cancelled_orders"].fillna(0).astype(int)
        rest_agg["cancel_rate_pct"] = np.where(
            rest_agg["total_orders"] > 0,
            rest_agg["cancelled_orders"] / rest_agg["total_orders"] * 100.0,
            0.0,
        ).round(2)

        top_5 = rest_agg.sort_values(by="gmv", ascending=False).head(5)
        if not top_5.empty:
            top_row = top_5.iloc[0]
            top_partner_name = str(top_row.get("restaurant_name", top_row.get("restaurant_id", "Partner")))
            top_partner_gmv_str = f"₹{float(top_row['gmv']):,.0f} (₹{float(top_row['gmv'])/100000:.2f}L)"
            metrics.extend(
                [
                    {"label": "Top Partner GMV (Non-Cancelled)", "value": top_partner_gmv_str, "provenance": source_name},
                    {"label": "Top Merchant", "value": f"{top_partner_name} ({top_row.get('city', 'N/A')})", "provenance": source_name},
                ]
            )
            chart_data = []
            for _, r in top_5.iterrows():
                chart_data.append(
                    {
                        "name": str(r.get("restaurant_name", r["restaurant_id"])),
                        "city": str(r.get("city", "N/A")),
                        "revenue_lakhs": round(float(r["gmv"]) / 100000.0, 2),
                        "orders": int(r["non_cancelled_orders"]),
                        "avg_rating": round(float(r[rating_col]), 2) if rating_col and pd.notna(r.get(rating_col)) else None,
                        "cancel_rate_pct": float(r["cancel_rate_pct"]),
                    }
                )
            table_data = chart_data
            suggested_chart = {
                "type": "bar",
                "title": "Top 5 Restaurant Partners by Non-Cancelled GMV (₹ Lakhs)",
                "x_key": "name",
                "y_key": "revenue_lakhs",
                "data": chart_data,
            }

    rating_phrase = f"{avg_rating:.2f} / 5.0" if avg_rating is not None else "unavailable"
    low_phrase = f" ({low_rated_count:,} partners rated below 3.8)" if low_rated_count is not None else ""
    summary = (
        f"The network comprises {total_merchants:,} partner kitchens with an average rating of {rating_phrase}{low_phrase}. "
        f"The leading partner by non-cancelled GMV is {top_partner_name} at {top_partner_gmv_str}."
    )

    return {
        "domain": "restaurants",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def _build_operations_domain(
    deliveries: pd.DataFrame,
    riders: pd.DataFrame,
    alloc_df: pd.DataFrame,
    orders: pd.DataFrame,
    restaurants: pd.DataFrame,
    source_name: str,
) -> Dict[str, Any]:
    total_deliveries = len(deliveries)
    has_duration = not deliveries.empty and "delivery_duration" in deliveries.columns
    avg_duration = clean_num(deliveries["delivery_duration"].mean(), default=None) if has_duration else None
    sla_breach_count = int((deliveries["delivery_duration"] > 45).sum()) if has_duration else None
    sla_breach_rate = (sla_breach_count / total_deliveries * 100.0) if (has_duration and total_deliveries > 0) else None
    ontime_rate = (
        float((deliveries["delivery_duration"] <= 45).sum() / total_deliveries * 100.0)
        if (has_duration and total_deliveries > 0)
        else None
    )
    active_fleet = len(riders)

    metrics = [
        {"label": "Dispatches Completed", "value": f"{total_deliveries:,}", "provenance": source_name},
        {
            "label": "Average Delivery ETA",
            "value": f"{avg_duration:.2f} mins" if avg_duration is not None else "N/A",
            "provenance": source_name,
        },
        {
            "label": "On-Time SLA Compliance (<=45m)",
            "value": f"{ontime_rate:.2f}%" if ontime_rate is not None else "N/A",
            "provenance": source_name,
        },
        {
            "label": "SLA Breaches (>45m)",
            "value": f"{sla_breach_count:,} ({sla_breach_rate:.2f}%)" if sla_breach_count is not None and sla_breach_rate is not None else "N/A",
            "provenance": source_name,
        },
        {"label": "Active Courier Fleet", "value": f"{active_fleet:,} riders", "provenance": source_name},
    ]

    table_data: List[Dict[str, Any]] = []
    suggested_chart = None

    city_col = _resolve_column(alloc_df, ["order_city", "city", "rider_city"])
    rider_col = _resolve_column(alloc_df, ["recommended_rider_id", "rider_id"])
    tier_col = _resolve_column(alloc_df, ["workload_tier"])
    score_col = _resolve_column(alloc_df, ["allocation_score"])

    if not alloc_df.empty and city_col is not None:
        agg_kwargs: Dict[str, Any] = {"recommended_assignments": (city_col, "count")}
        if rider_col is not None:
            agg_kwargs["unique_recommended_riders"] = (rider_col, "nunique")
        if score_col is not None:
            agg_kwargs["avg_allocation_score"] = (score_col, "mean")

        alloc_summary = alloc_df.groupby(city_col, dropna=True).agg(**agg_kwargs).reset_index()
        alloc_summary = alloc_summary.rename(columns={city_col: "city"})
        if tier_col is not None:
            mode_tiers = (
                alloc_df.groupby(city_col)[tier_col]
                .agg(lambda s: str(s.mode().iloc[0]) if not s.mode().empty else "Unknown")
                .reset_index()
                .rename(columns={city_col: "city", tier_col: "workload_tier"})
            )
            alloc_summary = alloc_summary.merge(mode_tiers, on="city", how="left")
        if "avg_allocation_score" in alloc_summary.columns:
            alloc_summary["avg_allocation_score"] = alloc_summary["avg_allocation_score"].round(2)
        alloc_summary = alloc_summary.sort_values(by="recommended_assignments", ascending=False)
        table_data = alloc_summary.to_dict(orient="records")
        suggested_chart = {
            "type": "bar",
            "title": "Rider Allocation Recommendations by City",
            "x_key": "city",
            "y_key": "recommended_assignments",
            "data": table_data,
        }
        metrics.append(
            {
                "label": "Rider Allocation Sampled Orders",
                "value": f"{len(alloc_df):,} assignments",
                "provenance": source_name,
            }
        )
    elif not deliveries.empty and not orders.empty and not restaurants.empty and {"order_id", "restaurant_id"}.issubset(orders.columns):
        merged_ops = deliveries.merge(orders[["order_id", "restaurant_id"]], on="order_id", how="left").merge(
            restaurants[["restaurant_id", "city"]], on="restaurant_id", how="left"
        )
        if "city" in merged_ops.columns and "delivery_duration" in merged_ops.columns:
            city_ops = (
                merged_ops.groupby("city", dropna=True)
                .agg(
                    deliveries=("delivery_duration", "count"),
                    avg_eta_min=("delivery_duration", "mean"),
                    sla_breach_pct=("delivery_duration", lambda s: float((s > 45).mean() * 100.0)),
                )
                .reset_index()
                .round(2)
                .sort_values(by="avg_eta_min", ascending=False)
            )
            table_data = city_ops.to_dict(orient="records")
            suggested_chart = {
                "type": "bar",
                "title": "Average Delivery Duration by City (mins)",
                "x_key": "city",
                "y_key": "avg_eta_min",
                "data": table_data,
            }

    eta_phrase = f"{avg_duration:.2f} minutes" if avg_duration is not None else "unavailable"
    sla_phrase = (
        f"{ontime_rate:.2f}% ({sla_breach_count:,} breaches >45m, or {sla_breach_rate:.2f}%)"
        if ontime_rate is not None and sla_breach_count is not None and sla_breach_rate is not None
        else "unavailable"
    )
    alloc_phrase = ""
    if table_data and "workload_tier" in table_data[0]:
        top_alloc = table_data[0]
        alloc_phrase = (
            f" Rider allocation records cover {len(alloc_df):,} dispatch assignments across "
            f"{len(table_data)} cities, led by {top_alloc['city']} ({top_alloc['recommended_assignments']:,} assignments, "
            f"dominant workload tier: {top_alloc['workload_tier']})."
        )

    summary = (
        f"Platform fulfilled {total_deliveries:,} deliveries with an average delivery duration of {eta_phrase}. "
        f"On-time delivery SLA compliance (<=45 mins) is {sla_phrase}, supported by an active courier fleet of {active_fleet:,} riders."
        f"{alloc_phrase}"
    )

    return {
        "domain": "operations",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def _build_leakage_domain(leakage_df: pd.DataFrame, source_name: str) -> Dict[str, Any]:
    amt_col = _resolve_column(leakage_df, ["potential_leakage_amount", "leakage_amount"])
    type_col = _resolve_column(leakage_df, ["leakage_type", "leakage_reason", "detection_category"])
    risk_col = _resolve_column(leakage_df, ["risk_level", "severity"])

    has_valid_leakage = not leakage_df.empty and amt_col is not None
    total_leakage = clean_num(leakage_df[amt_col].sum(), default=None) if has_valid_leakage else None
    flagged_count = len(leakage_df) if not leakage_df.empty else 0
    critical_count = (
        int(leakage_df[risk_col].astype(str).str.contains("critical", case=False, na=False).sum())
        if not leakage_df.empty and risk_col is not None
        else None
    )

    table_data: List[Dict[str, Any]] = []
    top_category = "Unavailable"

    if has_valid_leakage and type_col is not None:
        agg = (
            leakage_df.groupby(type_col, dropna=False)
            .agg(
                flagged_orders=("order_id", "count") if "order_id" in leakage_df.columns else (amt_col, "count"),
                potential_leakage_inr=(amt_col, "sum"),
            )
            .reset_index()
            .rename(columns={type_col: "category"})
            .sort_values(by="potential_leakage_inr", ascending=False)
        )
        agg["potential_leakage_inr"] = agg["potential_leakage_inr"].round(2)
        agg["amount_lakhs"] = (agg["potential_leakage_inr"] / 100000.0).round(2)
        agg["classification"] = "Investigation Candidate (Unverified)"
        agg["is_confirmed_loss"] = False
        table_data = agg.to_dict(orient="records")
        if not agg.empty:
            top_category = str(agg.iloc[0]["category"])

    metrics = [
        {
            "label": "Potential Revenue Leakage Exposure (Unverified)",
            "value": f"₹{total_leakage:,.2f} (₹{total_leakage/100000:.2f}L)" if total_leakage is not None else "N/A",
            "provenance": source_name,
        },
        {"label": "Flagged Investigation Candidates", "value": f"{flagged_count:,} orders", "provenance": source_name},
        {
            "label": "Critical Risk Candidates",
            "value": f"{critical_count:,}" if critical_count is not None else "N/A",
            "provenance": source_name,
        },
        {"label": "Primary Exposure Category", "value": top_category, "provenance": source_name},
    ]

    suggested_chart = (
        {
            "type": "bar",
            "title": "Potential Revenue Leakage Exposure by Type (₹ Lakhs — Unverified)",
            "x_key": "category",
            "y_key": "amount_lakhs",
            "data": table_data,
        }
        if table_data
        else None
    )

    if total_leakage is not None:
        cat_desc = "; ".join(
            [f"{row['category']}: ₹{row['potential_leakage_inr']:,.2f} ({row['flagged_orders']:,} flags)" for row in table_data]
        )
        summary = (
            f"Audited potential revenue leakage exposure totals ₹{total_leakage:,.2f} (₹{total_leakage/100000:.2f} Lakhs) "
            f"across {flagged_count:,} flagged orders ({cat_desc}). "
            f"IMPORTANT: These figures represent heuristic investigation candidates (is_confirmed_loss=False), "
            f"not confirmed net accounting losses, because merchant vs. platform discount funding splits require reconciliation."
        )
    else:
        summary = "Revenue leakage audit dataset is unavailable in the active workspace."

    return {
        "domain": "financial_leakage",
        "is_confirmed_loss": False,
        "classification": "Investigation Candidate",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def _build_business_overview_domain(
    base: Dict[str, Any],
    customers: pd.DataFrame,
    restaurants: pd.DataFrame,
    deliveries: pd.DataFrame,
    churn_df: pd.DataFrame,
    leakage_df: pd.DataFrame,
    source_name: str,
) -> Dict[str, Any]:
    total_gmv = base["total_gmv"]
    net_revenue = base["net_revenue"]
    total_orders = base["total_orders"]
    cancellation_rate = base["cancellation_rate"]
    margin_pct = base["margin_pct"]

    total_deliveries = len(deliveries)
    avg_eta = (
        clean_num(deliveries["delivery_duration"].mean(), default=None)
        if not deliveries.empty and "delivery_duration" in deliveries.columns
        else None
    )
    sla_breach_pct = (
        float((deliveries["delivery_duration"] > 45).sum() / total_deliveries * 100.0)
        if total_deliveries > 0 and "delivery_duration" in deliveries.columns
        else None
    )

    churn_col = _resolve_column(churn_df, ["Churn_Risk", "churn_risk_level", "churn_risk"])
    high_churn_count = (
        int(churn_df[churn_col].astype(str).str.strip().str.lower().isin(["high", "high risk"]).sum())
        if not churn_df.empty and churn_col is not None
        else None
    )

    rating_col = _resolve_column(restaurants, ["avg_rating", "rating"])
    avg_rating = (
        clean_num(restaurants[rating_col].mean(), default=None)
        if not restaurants.empty and rating_col is not None
        else None
    )

    amt_col = _resolve_column(leakage_df, ["potential_leakage_amount", "leakage_amount"])
    potential_leakage = (
        clean_num(leakage_df[amt_col].sum(), default=None)
        if not leakage_df.empty and amt_col is not None
        else None
    )

    metrics = [
        {"label": "Gross Merchandise Value (GMV)", "value": f"₹{total_gmv/10000000:.2f} Cr", "provenance": source_name},
        {"label": "Net Revenue (Delivered)", "value": f"₹{net_revenue/10000000:.2f} Cr", "provenance": source_name},
        {"label": "Total Orders", "value": f"{total_orders:,}", "provenance": source_name},
        {"label": "Platform Cancellation Rate", "value": f"{cancellation_rate:.2f}%", "provenance": source_name},
        {
            "label": "Realized Contribution Margin",
            "value": f"{margin_pct:.2f}%" if margin_pct is not None else "N/A",
            "provenance": source_name,
        },
        {
            "label": "Average Delivery ETA",
            "value": f"{avg_eta:.2f} mins ({sla_breach_pct:.2f}% >45m)"
            if avg_eta is not None and sla_breach_pct is not None
            else "N/A",
            "provenance": source_name,
        },
        {
            "label": "Active Customers / High Risk (Heuristic)",
            "value": f"{len(customers):,} / {high_churn_count:,}" if high_churn_count is not None else f"{len(customers):,}",
            "provenance": source_name,
        },
        {
            "label": "Merchant Partners / Avg Rating",
            "value": f"{len(restaurants):,} / {avg_rating:.2f}" if avg_rating is not None else f"{len(restaurants):,}",
            "provenance": source_name,
        },
    ]

    # Build cross-city scorecard table for charts & table output
    table_data: List[Dict[str, Any]] = []
    suggested_chart = None
    non_cancelled = base["non_cancelled_orders"]
    if not non_cancelled.empty and not restaurants.empty and {"restaurant_id", "city"}.issubset(restaurants.columns):
        merged = non_cancelled.merge(restaurants[["restaurant_id", "city"]], on="restaurant_id", how="left")
        city_gmv = (
            merged.groupby("city", dropna=True)
            .agg(completed_orders=("order_id", "count"), gmv=("order_amount", "sum"))
            .reset_index()
            .sort_values(by="gmv", ascending=False)
        )
        city_gmv["gmv_lakhs"] = (city_gmv["gmv"] / 100000.0).round(2)
        table_data = city_gmv.to_dict(orient="records")
        suggested_chart = {
            "type": "bar",
            "title": "Executive GMV Performance by City (₹ Lakhs)",
            "x_key": "city",
            "y_key": "gmv_lakhs",
            "data": table_data,
        }

    eta_str = f"{avg_eta:.2f} mins avg ETA with {sla_breach_pct:.2f}% SLA breaches (>45m)" if avg_eta is not None and sla_breach_pct is not None else "delivery telemetry unavailable"
    leak_str = f" Potential unverified leakage exposure stands at ₹{potential_leakage:,.2f} across {len(leakage_df):,} flagged orders (investigation candidates)." if potential_leakage is not None else ""
    margin_str = f"{margin_pct:.2f}%" if margin_pct is not None else "N/A"
    summary = (
        f"NovaNest serves {len(customers):,} registered customers across {len(restaurants):,} partner restaurants, "
        f"recording ₹{total_gmv/10000000:.2f} Cr in non-cancelled GMV and ₹{net_revenue/10000000:.2f} Cr in delivered Net Revenue "
        f"over {total_orders:,} total orders (cancellation rate: {cancellation_rate:.2f}%, contribution margin: {margin_str}). "
        f"Operations report {eta_str}.{leak_str}"
    )

    return {
        "domain": "business_overview",
        "verified_metrics": metrics,
        "table_data": table_data,
        "suggested_chart": suggested_chart,
        "context_summary": summary,
    }


def retrieve_grounded_business_context(
    query: str, data: Dict[str, pd.DataFrame], source_name: str = "CSV File Store"
) -> Dict[str, Any]:
    """
    Analyze user intent and extract verified business metrics across one or more domains.
    Never supplies fabricated numbers or unconfirmed loss assertions as confirmed accounting facts.
    """
    q = (query or "").lower()

    orders = data.get("orders", pd.DataFrame())
    customers = data.get("customers", pd.DataFrame())
    restaurants = data.get("restaurants", pd.DataFrame())
    deliveries = data.get("deliveries", pd.DataFrame())
    riders = data.get("riders", pd.DataFrame())
    orders_eng = data.get("orders_engineered", pd.DataFrame())
    churn_df = data.get("customer_churn_predictions", pd.DataFrame())
    leakage_df = data.get("revenue_leakage", pd.DataFrame())
    alloc_df = data.get("rider_allocation", pd.DataFrame())

    context: Dict[str, Any] = {
        "domain": "general",
        "domains": [],
        "is_multi_domain": False,
        "is_confirmed_loss": False,
        "verified_metrics": [],
        "context_summary": "",
        "domain_summaries": {},
        "provenance": {
            "data_source": source_name,
            "period": f"Full Historical Cycle ({len(orders):,} Orders)",
            "records_analyzed": len(orders),
        },
        "table_data": [],
        "suggested_chart": None,
    }

    domains = _extract_domains(q)
    if not domains:
        return context

    base = _compute_baseline_financials(orders, orders_eng, restaurants)

    def build_single(dom: str) -> Dict[str, Any]:
        if dom == "cancellations":
            return _build_cancellations_domain(base, orders, restaurants, source_name)
        if dom == "financial":
            return _build_financial_domain(base, restaurants, source_name)
        if dom == "customers":
            return _build_customers_domain(base, customers, churn_df, source_name)
        if dom == "restaurants":
            return _build_restaurants_domain(base, orders, restaurants, source_name)
        if dom == "operations":
            return _build_operations_domain(deliveries, riders, alloc_df, orders, restaurants, source_name)
        if dom == "financial_leakage":
            return _build_leakage_domain(leakage_df, source_name)
        if dom == "business_overview":
            return _build_business_overview_domain(
                base, customers, restaurants, deliveries, churn_df, leakage_df, source_name
            )
        return {"domain": "general", "verified_metrics": [], "table_data": [], "suggested_chart": None, "context_summary": ""}

    if len(domains) == 1:
        res = build_single(domains[0])
        context["domain"] = res["domain"]
        context["domains"] = [res["domain"]]
        context["is_multi_domain"] = False
        context["verified_metrics"] = res["verified_metrics"]
        context["table_data"] = res["table_data"]
        context["suggested_chart"] = res["suggested_chart"]
        context["context_summary"] = res["context_summary"]
        context["domain_summaries"] = {res["domain"]: res["context_summary"]}
        if "is_confirmed_loss" in res:
            context["is_confirmed_loss"] = res["is_confirmed_loss"]
        if "classification" in res:
            context["classification"] = res["classification"]
        return context

    # Multi-domain aggregation (e.g., "Compare financial and operational performance.")
    combined_metrics: List[Dict[str, Any]] = []
    seen_labels = set()
    domain_summaries: Dict[str, str] = {}
    chosen_table: List[Dict[str, Any]] = []
    chosen_chart = None

    for dom in domains:
        part = build_single(dom)
        domain_summaries[dom] = part["context_summary"]
        for m in part["verified_metrics"]:
            if m["label"] not in seen_labels:
                combined_metrics.append(m)
                seen_labels.add(m["label"])
        if not chosen_table and part.get("table_data"):
            chosen_table = part["table_data"]
        if chosen_chart is None and part.get("suggested_chart") is not None:
            chosen_chart = part["suggested_chart"]

    # When both financial and operations are compared, build an aligned city scorecard if available
    if "financial" in domains and "operations" in domains and not base["non_cancelled_orders"].empty and not restaurants.empty:
        merged_fin = base["non_cancelled_orders"].merge(
            restaurants[["restaurant_id", "city"]], on="restaurant_id", how="left"
        )
        city_cmp = (
            merged_fin.groupby("city", dropna=True)
            .agg(non_cancelled_orders=("order_id", "count"), gmv=("order_amount", "sum"))
            .reset_index()
        )
        if not deliveries.empty and not orders.empty and {"order_id", "delivery_duration"}.issubset(deliveries.columns):
            merged_ops = deliveries.merge(orders[["order_id", "restaurant_id"]], on="order_id", how="left").merge(
                restaurants[["restaurant_id", "city"]], on="restaurant_id", how="left"
            )
            city_ops = (
                merged_ops.groupby("city", dropna=True)
                .agg(
                    avg_eta_min=("delivery_duration", "mean"),
                    sla_breach_pct=("delivery_duration", lambda s: float((s > 45).mean() * 100.0)),
                )
                .reset_index()
            )
            city_cmp = city_cmp.merge(city_ops, on="city", how="left")
        city_cmp["gmv_lakhs"] = (city_cmp["gmv"] / 100000.0).round(2)
        if "avg_eta_min" in city_cmp.columns:
            city_cmp["avg_eta_min"] = city_cmp["avg_eta_min"].round(2)
            city_cmp["sla_breach_pct"] = city_cmp["sla_breach_pct"].round(2)
        city_cmp = city_cmp.sort_values(by="gmv", ascending=False)
        chosen_table = city_cmp.to_dict(orient="records")
        chosen_chart = {
            "type": "bar",
            "title": "Financial GMV (₹ Lakhs) Across Cities Alongside Delivery Operations",
            "x_key": "city",
            "y_key": "gmv_lakhs",
            "data": chosen_table,
        }

    combined_summary = "\n\n".join(
        [f"**{dom.replace('_', ' ').title()}:** {summary}" for dom, summary in domain_summaries.items() if summary]
    )

    context["domain"] = "multi_domain"
    context["domains"] = domains
    context["is_multi_domain"] = True
    context["verified_metrics"] = combined_metrics
    context["table_data"] = chosen_table
    context["suggested_chart"] = chosen_chart
    context["context_summary"] = combined_summary
    context["domain_summaries"] = domain_summaries
    return context
