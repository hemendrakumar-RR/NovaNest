"""
NovaNest RFM Customer Segmentation Engine
Calculates Recency, Frequency, Monetary (RFM) scores and classifies customers
into evidence-based behavioral segments for targeted retention marketing.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Dynamic path discovery
BASE_DIR = Path(__file__).resolve().parents[2]
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
ANALYTICS_DIR = BASE_DIR / "datasets" / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_rfm_segments(orders_df: pd.DataFrame = None, customers_df: pd.DataFrame = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute customer-level RFM scores and business segments.
    Excludes cancelled orders to reflect true economic engagement.
    """
    if orders_df is None:
        orders_df = pd.read_csv(CLEANED_DIR / "orders.csv")
    if customers_df is None:
        customers_df = pd.read_csv(CLEANED_DIR / "customers.csv")

    # 1. Filter valid transactional orders
    valid_orders = orders_df[orders_df["order_status"] != "Cancelled"].copy()
    valid_orders["order_datetime"] = pd.to_datetime(valid_orders["order_datetime"])

    # 2. Reference timestamp: Max order date + 1 day
    ref_date = valid_orders["order_datetime"].max() + pd.Timedelta(days=1)

    # 3. Base RFM Aggregations
    rfm = valid_orders.groupby("customer_id").agg(
        last_order_date=("order_datetime", "max"),
        recency=("order_datetime", lambda x: int((ref_date - x.max()).days)),
        frequency=("order_id", "count"),
        monetary=("final_amount", "sum")
    ).reset_index()

    # Handle customers with zero non-cancelled orders (edge-case safety)
    missing_custs = customers_df[~customers_df["customer_id"].isin(rfm["customer_id"])]
    if not missing_custs.empty:
        filler = pd.DataFrame({
            "customer_id": missing_custs["customer_id"],
            "last_order_date": pd.NaT,
            "recency": 999,
            "frequency": 0,
            "monetary": 0
        })
        rfm = pd.concat([rfm, filler], ignore_index=True)

    # 4. Quantile-Based Scoring (1 to 5)
    # Recency: Lower days = Higher Score (Inverted)
    rfm["r_score"] = pd.qcut(rfm["recency"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    # Frequency: Higher count = Higher Score
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    # Monetary: Higher spend = Higher Score
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_cell"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)
    rfm["rfm_combined_score"] = ((rfm["r_score"] + rfm["f_score"] + rfm["m_score"]) / 3.0).round(2)

    # 5. Segment Assignment Rules
    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r == 1 and f >= 4 and m >= 4:
            return "Cannot Lose Them"
        if r <= 2 and f >= 3 and m >= 3:
            return "At Risk"
        if r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        if r >= 4 and f in [2, 3]:
            return "Potential Loyalists"
        if r >= 4 and f == 1:
            return "New Customers"
        if r == 3 and f in [1, 2]:
            return "Promising"
        if r == 3 and f == 3:
            return "Need Attention"
        if r <= 2 and f <= 2:
            return "Hibernating / Lost"
        return "Occasional"

    rfm["segment"] = rfm.apply(assign_segment, axis=1)

    # 6. Merge Demographic and Metadata
    cust_meta = customers_df[["customer_id", "customer_name", "city", "persona", "subscription_type"]]
    rfm = rfm.merge(cust_meta, on="customer_id", how="left")

    # Reorder columns
    col_order = [
        "customer_id", "customer_name", "city", "persona", "subscription_type",
        "last_order_date", "recency", "frequency", "monetary",
        "r_score", "f_score", "m_score", "rfm_cell", "rfm_combined_score", "segment"
    ]
    rfm = rfm[col_order]

    # 7. Generate Segment Summary Statistics
    summary = rfm.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum")
    ).reset_index()

    total_customers = len(rfm)
    total_rev = rfm["monetary"].sum()

    summary["customer_pct"] = ((summary["customer_count"] / total_customers) * 100).round(2)
    summary["revenue_pct"] = ((summary["total_revenue"] / total_rev) * 100).round(2)
    summary["avg_recency"] = summary["avg_recency"].round(1)
    summary["avg_frequency"] = summary["avg_frequency"].round(1)
    summary["avg_monetary"] = summary["avg_monetary"].round(2)
    summary["total_revenue"] = summary["total_revenue"].round(2)

    summary = summary.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

    # 8. Export Artifacts
    customer_export_path = ANALYTICS_DIR / "customer_rfm_segments.csv"
    summary_export_path = ANALYTICS_DIR / "rfm_segment_summary.csv"
    rfm.to_csv(customer_export_path, index=False)
    summary.to_csv(summary_export_path, index=False)

    return rfm, summary


def run_rfm_analysis():
    print("=" * 65)
    print("🎯 NOVANEST RFM CUSTOMER SEGMENTATION ENGINE")
    print("=" * 65)

    rfm, summary = calculate_rfm_segments()
    print(f"✅ Evaluated {len(rfm):,} customers across {len(summary)} segments.\n")
    print(f"| {'Segment Name':<22} | {'Customers':<9} | {'Cust %':<7} | {'Avg Recency':<11} | {'Avg Freq':<8} | {'Avg Spend (₹)':<13} | {'Rev %':<6} |")
    print("|" + "-"*24 + "|" + "-"*11 + "|" + "-"*9 + "|" + "-"*13 + "|" + "-"*10 + "|" + "-"*15 + "|" + "-"*8 + "|")
    for _, row in summary.iterrows():
        print(f"| {row['segment']:<22} | {row['customer_count']:<9} | {row['customer_pct']:<6}% | {row['avg_recency']:<11} | {row['avg_frequency']:<8} | ₹{row['avg_monetary']:<12,.2f} | {row['revenue_pct']:<5}% |")

    print("-" * 65)
    print(f"Artifacts saved:")
    print(f"- Customer Details: {ANALYTICS_DIR / 'customer_rfm_segments.csv'}")
    print(f"- Segment Summary:  {ANALYTICS_DIR / 'rfm_segment_summary.csv'}")
    print("=" * 65)


if __name__ == "__main__":
    run_rfm_analysis()
