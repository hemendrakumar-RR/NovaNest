"""
NovaNest Marketing & Conversion Funnel Analytics Engine
Analyzes clickstream app event distributions, user stage reach, and event co-occurrence.

IMPORTANT ARCHITECTURAL & METHODOLOGICAL NOTE:
The `app_events.csv` dataset contains exactly three columns:
['event_id', 'customer_id', 'event_type'].
There is NO timestamp column and NO session_id in the clickstream event dataset.
Therefore, this engine analyzes:
1. Unique-User Stage Reach (User presence across event stages).
2. Event Frequency & Type Distribution.
3. Event-Presence Overlap & Co-occurrence across customer profiles.
This engine DOES NOT claim chronological sequence, temporal progression, or true
session-level funnel drop-off leakage, which require timestamped event sequences.
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


def analyze_marketing_funnel(events_df: pd.DataFrame = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Evaluates marketing event distribution, unique user stage reach, and stage overlap.
    Returns (funnel_summary_df, overlap_matrix_df, diagnostic_stats).
    """
    if events_df is None:
        events_df = pd.read_csv(CLEANED_DIR / "app_events.csv")

    if events_df.empty:
        empty_funnel = pd.DataFrame(columns=[
            "stage_order", "stage_name", "total_events", "unique_users",
            "event_share_pct", "user_reach_pct"
        ])
        empty_overlap = pd.DataFrame()
        empty_stats = {
            "total_clickstream_events": 0,
            "total_active_app_users": 0,
            "users_completing_all_stages": 0,
            "full_funnel_user_completion_rate_pct": 0.0,
            "has_timestamp": False,
            "methodology_limitation": "Empty dataset provided."
        }
        return empty_funnel, empty_overlap, empty_stats

    total_events_in_db = len(events_df)
    total_unique_customers = events_df["customer_id"].nunique()
    has_timestamp = "timestamp" in events_df.columns or "event_datetime" in events_df.columns

    # 1. Aggregate stage metrics (Unique User Reach and Event Share)
    stage_data = []
    for idx, stage in enumerate(FUNNEL_STAGES):
        sub = events_df[events_df["event_type"] == stage]
        stage_events = len(sub)
        stage_users = sub["customer_id"].nunique()
        event_share = round((stage_events / total_events_in_db) * 100.0, 2) if total_events_in_db > 0 else 0.0
        user_reach = round((stage_users / total_unique_customers) * 100.0, 2) if total_unique_customers > 0 else 0.0

        stage_data.append({
            "stage_order": idx + 1,
            "stage_name": stage,
            "total_events": stage_events,
            "unique_users": stage_users,
            "event_share_pct": event_share,
            "user_reach_pct": user_reach
        })

    funnel_df = pd.DataFrame(stage_data)

    # 2. User Stage-Presence Overlap Analysis
    user_stage_pivot = events_df.pivot_table(
        index="customer_id",
        columns="event_type",
        aggfunc="size",
        fill_value=0
    )
    # Ensure all funnel stages exist in pivot columns
    for st in FUNNEL_STAGES:
        if st not in user_stage_pivot.columns:
            user_stage_pivot[st] = 0

    # Binary presence flag
    presence_matrix = (user_stage_pivot[FUNNEL_STAGES] > 0).astype(int)
    distinct_stages_per_user = presence_matrix.sum(axis=1)

    # Pairwise co-occurrence overlap matrix
    overlap_matrix = presence_matrix.T.dot(presence_matrix)

    users_with_all_stages = int((distinct_stages_per_user == len(FUNNEL_STAGES)).sum())
    full_completion_rate = round((users_with_all_stages / total_unique_customers) * 100.0, 2) if total_unique_customers > 0 else 0.0

    # User stage coverage distribution
    coverage_counts = distinct_stages_per_user.value_counts().sort_index().to_dict()

    diagnostic_stats = {
        "total_clickstream_events": int(total_events_in_db),
        "total_active_app_users": int(total_unique_customers),
        "users_completing_all_stages": int(users_with_all_stages),
        "full_funnel_user_completion_rate_pct": float(full_completion_rate),
        "stage_coverage_distribution": coverage_counts,
        "has_timestamp_column": bool(has_timestamp),
        "data_architecture_note": (
            "app_events.csv lacks timestamps; events reflect uniform random sampling "
            "(~16.6% per event type). Analysis measures user presence, not temporal progression."
        )
    }

    # 3. Export Summary Artifacts
    export_path = ANALYTICS_DIR / "app_funnel_summary.csv"
    funnel_df.to_csv(export_path, index=False)

    overlap_path = ANALYTICS_DIR / "app_event_overlap_matrix.csv"
    overlap_matrix.to_csv(overlap_path)

    return funnel_df, overlap_matrix, diagnostic_stats


def run_funnel_analysis():
    print("=" * 65)
    print("📲 NOVANEST MARKETING & USER STAGE-REACH ENGINE")
    print("=" * 65)

    funnel_df, overlap_df, stats = analyze_marketing_funnel()

    print(f"Total Clickstream Events:    {stats['total_clickstream_events']:,}")
    print(f"Total Unique Users:          {stats['total_active_app_users']:,}")
    print(f"Users with All 6 Stages:     {stats['users_completing_all_stages']:,} ({stats['full_funnel_user_completion_rate_pct']}%)")
    print(f"Has Timestamps:              {stats['has_timestamp_column']} (Temporal funnel sequence disabled)")
    print(f"Note:                        {stats['data_architecture_note']}\n")

    print("Stage Distribution & User Reach Summary:")
    print(funnel_df.to_string(index=False))

    print("\nPairwise User Co-occurrence Matrix:")
    print(overlap_df.to_string())

    print("-" * 65)
    print("Artifacts saved:")
    print(f"- Funnel Summary:   {ANALYTICS_DIR / 'app_funnel_summary.csv'}")
    print(f"- Overlap Matrix:   {ANALYTICS_DIR / 'app_event_overlap_matrix.csv'}")
    print("=" * 65)


if __name__ == "__main__":
    run_funnel_analysis()
