"""
NovaNest Monthly Cohort Retention Analysis Engine
Tracks customer lifecycle retention curves across monthly acquisition cohorts (Month 0 to Month 12).
Strictly separates monthly cohort retention decay from overall lifetime repeat-purchase rates.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Dynamic path discovery
BASE_DIR = Path(__file__).resolve().parents[2]
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
ANALYTICS_DIR = BASE_DIR / "datasets" / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def compute_cohort_retention_matrix(orders_df: pd.DataFrame = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Computes monthly cohort retention matrices (counts and percentages).
    Returns (retention_percentage_df, cohort_counts_df, summary_stats).
    """
    if orders_df is None:
        orders_df = pd.read_csv(CLEANED_DIR / "orders.csv")

    df = orders_df[orders_df["order_status"] != "Cancelled"].copy()
    df["order_datetime"] = pd.to_datetime(df["order_datetime"])
    df["order_month"] = df["order_datetime"].dt.to_period("M")

    # 1. First Order Month = Acquisition Cohort
    first_orders = df.groupby("customer_id")["order_month"].min().reset_index()
    first_orders.rename(columns={"order_month": "cohort_month"}, inplace=True)

    df = df.merge(first_orders, on="customer_id")

    # 2. Elapsed Months = Cohort Index (0, 1, 2, ...)
    df["cohort_index"] = (
        (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12 +
        (df["order_month"].dt.month - df["cohort_month"].dt.month)
    )

    # 3. Monthly Active Users per Cohort & Index
    cohort_grouped = df.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique().reset_index()
    counts_matrix = cohort_grouped.pivot(index="cohort_month", columns="cohort_index", values="customer_id")

    # 4. Cohort Sizes (Month 0 Base)
    cohort_sizes = counts_matrix.iloc[:, 0]

    # 5. Percentage Retention Matrix
    retention_matrix = counts_matrix.divide(cohort_sizes, axis=0) * 100.0

    # Format column names as 'Month 0', 'Month 1', etc.
    counts_matrix.columns = [f"Month {int(col)}" for col in counts_matrix.columns]
    retention_matrix.columns = [f"Month {int(col)}" for col in retention_matrix.columns]

    # Convert period index to string for serialization
    counts_matrix.index = counts_matrix.index.astype(str)
    retention_matrix.index = retention_matrix.index.astype(str)

    # 6. Overall Metrics & Summary Statistics
    total_customers = df["customer_id"].nunique()
    repeat_customers = (df.groupby("customer_id")["order_id"].count() > 1).sum()
    repeat_purchase_rate = round((repeat_customers / total_customers) * 100.0, 2)

    # Average retention at Month 1, Month 3, Month 6 across valid cohorts
    m1_avg = round(retention_matrix["Month 1"].dropna().mean(), 2) if "Month 1" in retention_matrix else 0.0
    m3_avg = round(retention_matrix["Month 3"].dropna().mean(), 2) if "Month 3" in retention_matrix else 0.0
    m6_avg = round(retention_matrix["Month 6"].dropna().mean(), 2) if "Month 6" in retention_matrix else 0.0

    summary_stats = {
        "total_acquired_customers": int(total_customers),
        "repeat_customers_lifetime": int(repeat_customers),
        "repeat_purchase_rate_pct": float(repeat_purchase_rate),
        "avg_month_1_retention_pct": float(m1_avg),
        "avg_month_3_retention_pct": float(m3_avg),
        "avg_month_6_retention_pct": float(m6_avg),
        "total_cohorts": len(cohort_sizes)
    }

    # 7. Export Artifacts
    counts_matrix.to_csv(ANALYTICS_DIR / "monthly_cohort_counts.csv")
    retention_matrix.round(2).to_csv(ANALYTICS_DIR / "monthly_cohort_matrix.csv")

    return retention_matrix, counts_matrix, summary_stats


def run_cohort_analysis():
    print("=" * 65)
    print("📅 NOVANEST MONTHLY COHORT RETENTION ENGINE")
    print("=" * 65)

    retention_matrix, counts_matrix, stats = compute_cohort_retention_matrix()

    print(f"Total Cohorts Analyzed:      {stats['total_cohorts']}")
    print(f"Total Acquired Customers:    {stats['total_acquired_customers']:,}")
    print(f"Lifetime Repeat Purchase Rate: {stats['repeat_purchase_rate_pct']}% (Customers ordering >1 time)")
    print(f"Average Month 1 Retention:   {stats['avg_month_1_retention_pct']}%")
    print(f"Average Month 3 Retention:   {stats['avg_month_3_retention_pct']}%")
    print(f"Average Month 6 Retention:   {stats['avg_month_6_retention_pct']}%\n")

    print("Retention Matrix Preview (% Retained):")
    cols_to_show = [c for c in retention_matrix.columns if int(c.split()[1]) <= 6]
    preview = retention_matrix[cols_to_show].head(6).fillna("-")
    print(preview.to_string())

    print("-" * 65)
    print("Artifacts saved:")
    print(f"- Cohort Retention Matrix (%): {ANALYTICS_DIR / 'monthly_cohort_matrix.csv'}")
    print(f"- Cohort Headcount Matrix:     {ANALYTICS_DIR / 'monthly_cohort_counts.csv'}")
    print("=" * 65)


if __name__ == "__main__":
    run_cohort_analysis()

