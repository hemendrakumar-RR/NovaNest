"""
NovaNest Marketing & Conversion Funnel Analytics Engine
Analyzes clickstream app event funnels from App Open to Order Complete.
Evaluates event volume, unique user reach, step-by-step conversion, and drop-off leakage.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Dynamic path discovery
BASE_DIR = Path(__file__).resolve().parents[2]
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
ANALYTICS_DIR = BASE_DIR / "datasets" / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

# Standard E-Commerce Food Delivery Funnel Hierarchy
FUNNEL_STAGES = [
    "App Open",
    "Restaurant View",
    "Menu View",
    "Add To Cart",
    "Checkout",
    "Order Complete"
]


def analyze_marketing_funnel(events_df: pd.DataFrame = None) -> tuple[pd.DataFrame, dict]:
    """
    Evaluates marketing funnel progression, stage-wise conversion rates, and leakages.
    Returns (funnel_summary_df, diagnostic_stats).
    """
    if events_df is None:
        events_df = pd.read_csv(CLEANED_DIR / "app_events.csv")

    total_events_in_db = len(events_df)
    total_unique_customers = events_df["customer_id"].nunique()

    # 1. Aggregate stage metrics
    stage_data = []
    for idx, stage in enumerate(FUNNEL_STAGES):
        sub = events_df[events_df["event_type"] == stage]
        stage_data.append({
            "stage_order": idx + 1,
            "stage_name": stage,
            "total_events": len(sub),
            "unique_users": sub["customer_id"].nunique()
        })

    funnel_df = pd.DataFrame(stage_data)

    # 2. Benchmark against Top-of-Funnel (Stage 1: App Open)
    base_events = funnel_df.loc[0, "total_events"]
    base_users = funnel_df.loc[0, "unique_users"]

    # 3. Cumulative & Step Conversions
    funnel_df["event_share_pct"] = ((funnel_df["total_events"] / total_events_in_db) * 100.0).round(2)
    funnel_df["user_reach_pct"] = ((funnel_df["unique_users"] / 5000.0) * 100.0).round(2)

    # Event Step Conversion & Drop-off
    prev_events = funnel_df["total_events"].shift(1).fillna(base_events)
    funnel_df["event_step_conversion_pct"] = ((funnel_df["total_events"] / prev_events) * 100.0).round(2)
    funnel_df["event_dropoff_volume"] = (prev_events - funnel_df["total_events"]).astype(int)

    # 4. User Full Funnel Completion Check
    user_stage_pivot = events_df.pivot_table(
        index="customer_id",
        columns="event_type",
        aggfunc="size",
        fill_value=0
    )
    users_with_all_stages = (user_stage_pivot[FUNNEL_STAGES] > 0).all(axis=1).sum()
    full_completion_rate = round((users_with_all_stages / total_unique_customers) * 100.0, 2)

    # Largest Leakage Stage based on step drop-off volume
    leakage_stages = funnel_df.iloc[1:].sort_values(by="event_dropoff_volume", ascending=False)
    largest_leakage = leakage_stages.iloc[0]["stage_name"] if not leakage_stages.empty else "None"

    diagnostic_stats = {
        "total_clickstream_events": int(total_events_in_db),
        "total_active_app_users": int(total_unique_customers),
        "users_completing_all_stages": int(users_with_all_stages),
        "full_funnel_user_completion_rate_pct": float(full_completion_rate),
        "largest_leakage_stage": str(largest_leakage)
    }

    # 5. Export Summary Artifact
    export_path = ANALYTICS_DIR / "app_funnel_summary.csv"
    funnel_df.to_csv(export_path, index=False)

    return funnel_df, diagnostic_stats


def run_funnel_analysis():
    print("=" * 65)
    print("📲 NOVANEST MARKETING & CONVERSION FUNNEL ENGINE")
    print("=" * 65)

    funnel_df, stats = analyze_marketing_funnel()

    print(f"Total Funnel Events:        {stats['total_clickstream_events']:,}")
    print(f"Total App Users Tracked:    {stats['total_active_app_users']:,}")
    print(f"Users with All 6 Stages:    {stats['users_completing_all_stages']:,} ({stats['full_funnel_user_completion_rate_pct']}%)")
    print(f"Largest Leakage Transition:  {stats['largest_leakage_stage']}\n")

    print("| Stage | Funnel Stage Name   | Total Events | Event Share | Unique Users | User Reach % |")
    print("|-------|---------------------|--------------|-------------|--------------|--------------|")
    for _, row in funnel_df.iterrows():
        print(f"| {row['stage_order']:<5} | {row['stage_name']:<19} | {row['total_events']:<12,} | {row['event_share_pct']:<10}% | {row['unique_users']:<12,} | {row['user_reach_pct']:<11}% |")

    print("-" * 65)
    print(f"Artifact saved: {ANALYTICS_DIR / 'app_funnel_summary.csv'}")
    print("=" * 65)


if __name__ == "__main__":
    run_funnel_analysis()
