"""
Phase 5 / 6.0 — AI Business Insights
-------------------------------------
Generates data-grounded executive insights aligned strictly with certified
Phase 04 KPI definitions (GMV on non-cancelled orders; Net Revenue and Net AOV
on Delivered orders).
"""

import pandas as pd


def generate_business_insights(orders_df: pd.DataFrame, customers_df: pd.DataFrame) -> list:
    """
    Analyzes order and customer datasets using certified Phase 04 revenue filters
    and returns a list of executive insight strings.
    """
    insights = []

    if orders_df is not None and not orders_df.empty:
        total_orders = len(orders_df)
        has_status = "order_status" in orders_df.columns
        non_cancelled = orders_df[orders_df["order_status"] != "Cancelled"] if has_status else orders_df
        delivered = orders_df[orders_df["order_status"] == "Delivered"] if has_status else orders_df
        cancelled_count = int((orders_df["order_status"] == "Cancelled").sum()) if has_status else 0

        amt_col = "order_amount" if "order_amount" in non_cancelled.columns else "final_amount"
        net_col = "final_amount" if "final_amount" in delivered.columns else "order_amount"

        gmv = float(non_cancelled[amt_col].sum()) if (not non_cancelled.empty and amt_col in non_cancelled.columns) else 0.0
        net_revenue = float(delivered[net_col].sum()) if (not delivered.empty and net_col in delivered.columns) else gmv
        delivered_count = len(delivered) if has_status else total_orders
        net_aov = (net_revenue / delivered_count) if delivered_count > 0 else 0.0
        cancel_rate = (cancelled_count / total_orders * 100.0) if total_orders > 0 else 0.0

        insights.append(
            f"💰 **Revenue Intelligence (Certified KPIs)**: Non-cancelled GMV is ₹{gmv:,.2f} "
            f"and delivered Net Revenue is ₹{net_revenue:,.2f} across {delivered_count:,} fulfilled orders "
            f"({total_orders:,} total placed; {cancel_rate:.2f}% cancellation rate). Net AOV stands at ₹{net_aov:,.2f}."
        )

        fee_source = delivered if not delivered.empty else non_cancelled
        if "delivery_fee" in fee_source.columns and not fee_source.empty:
            avg_fee = float(fee_source["delivery_fee"].mean())
            insights.append(
                f"🛵 **Operations**: The average delivery fee collected on fulfilled orders is ₹{avg_fee:,.2f}."
            )

    if customers_df is not None and not customers_df.empty:
        total_customers = len(customers_df)
        insights.append(
            f"👥 **Customer Growth**: NovaNest currently serves {total_customers:,} registered customers."
        )

    if not insights:
        insights.append("Not enough data to generate business insights at this time.")

    return insights
