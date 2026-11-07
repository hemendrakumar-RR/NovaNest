"""
NovaNest Feature Engineering Pipeline
Enriches cleaned orders with temporal, geospatial, economic, and operational features.
Produces datasets/engineered/orders_engineered.csv and datasets/engineered/orders_geo_temporal_enriched.csv.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Dynamic project root discovery
BASE_DIR = Path(__file__).resolve().parent.parent
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
ENGINEERED_DIR = BASE_DIR / "datasets" / "engineered"
ENGINEERED_DIR.mkdir(parents=True, exist_ok=True)


def load_cleaned_datasets():
    """Load required cleaned relational tables for feature joining."""
    orders = pd.read_csv(CLEANED_DIR / "orders.csv")
    restaurants = pd.read_csv(CLEANED_DIR / "restaurants.csv")
    customers = pd.read_csv(CLEANED_DIR / "customers.csv")
    riders = pd.read_csv(CLEANED_DIR / "riders.csv")
    deliveries = pd.read_csv(CLEANED_DIR / "deliveries.csv")
    return orders, restaurants, customers, riders, deliveries


def engineer_features(orders_df: pd.DataFrame,
                       restaurants_df: pd.DataFrame,
                       customers_df: pd.DataFrame,
                       riders_df: pd.DataFrame,
                       deliveries_df: pd.DataFrame) -> pd.DataFrame:
    """Enrich orders dataset with 26 additional business intelligence features (38 columns total)."""
    df = orders_df.copy()
    
    # 1. Parse Datetime Features
    dt = pd.to_datetime(df["order_datetime"])
    df["order_date"] = dt.dt.strftime("%Y-%m-%d")
    df["order_year"] = dt.dt.year
    df["order_month"] = dt.dt.month
    df["order_month_name"] = dt.dt.strftime("%B")
    df["hour"] = dt.dt.hour
    df["day_of_week"] = dt.dt.day_name()
    
    # 2. Operational & Temporal Flags
    df["peak_hour_flag"] = np.where(
        df["hour"].between(12, 14) | df["hour"].between(18, 21), 1, 0
    )
    df["weekend_flag"] = np.where(dt.dt.dayofweek >= 5, 1, 0)
    df["cancellation_flag"] = np.where(df["order_status"] == "Cancelled", 1, 0)
    
    # 3. Pricing & Value Metrics
    df["net_order_value"] = df["order_amount"] - df["discount_amount"]
    df["discount_percentage"] = (
        (df["discount_amount"] / df["order_amount"]) * 100
    ).round(2)
    
    # 4. Join Restaurant Intelligence (City & Commission)
    rest_subset = restaurants_df[["restaurant_id", "city", "commission_percentage"]].rename(
        columns={"city": "restaurant_city"}
    )
    df = df.merge(rest_subset, on="restaurant_id", how="left")
    
    # 5. Financial & Margin Metrics
    df["commission_revenue"] = (
        (df["order_amount"] * df["commission_percentage"]) / 100
    ).round(2)
    # Unit Economics: Commission + Delivery Fee - Delivery Cost (₹30 baseline payout)
    df["estimated_profit"] = (
        df["commission_revenue"] + df["delivery_fee"] - 30.0
    ).round(2)
    df["profit_margin_pct"] = (
        (df["estimated_profit"] / df["final_amount"]) * 100
    ).round(2)
    
    # 6. Order Size Classification
    df["order_size"] = pd.cut(
        df["final_amount"],
        bins=[-np.inf, 400, 900, np.inf],
        labels=["Small", "Medium", "Large"]
    )
    
    # 7. Join Delivery Performance (Distance & Duration)
    deliv_subset = deliveries_df[["order_id", "distance_km", "delivery_duration"]]
    df = df.merge(deliv_subset, on="order_id", how="left")
    
    # Speed & SLA Delay (Threshold: > 45 minutes)
    df["delivery_speed_kph"] = (
        df["distance_km"] / (df["delivery_duration"] / 60.0)
    ).round(2)
    df["delivery_delay_flag"] = np.where(df["delivery_duration"] > 45, 1, 0)
    
    # 8. Join Customer & Rider Geospatial / Lifecycle Data
    cust_subset = customers_df[["customer_id", "city", "signup_date"]].rename(
        columns={"city": "customer_city"}
    )
    rider_subset = riders_df[["rider_id", "city"]].rename(
        columns={"city": "rider_city"}
    )
    df = df.merge(cust_subset, on="customer_id", how="left")
    df = df.merge(rider_subset, on="rider_id", how="left")
    
    # 9. Geo-Temporal Integrity Flags
    df["cross_city_flag"] = np.where(
        df["customer_city"] != df["restaurant_city"], 1, 0
    )
    df["pre_signup_order_flag"] = np.where(
        pd.to_datetime(df["order_datetime"]) < pd.to_datetime(df["signup_date"]), 1, 0
    )
    
    # Verify Exact Column Sequence Matching Power BI & Downstream Schema
    expected_cols = [
        "order_id", "customer_id", "restaurant_id", "item_id", "rider_id",
        "order_datetime", "quantity", "order_amount", "discount_amount",
        "delivery_fee", "final_amount", "order_status", "order_date",
        "order_year", "order_month", "order_month_name", "hour", "day_of_week",
        "peak_hour_flag", "weekend_flag", "cancellation_flag", "net_order_value",
        "discount_percentage", "commission_percentage", "restaurant_city",
        "commission_revenue", "estimated_profit", "profit_margin_pct",
        "order_size", "distance_km", "delivery_duration", "delivery_speed_kph",
        "delivery_delay_flag", "customer_city", "signup_date", "rider_city",
        "cross_city_flag", "pre_signup_order_flag"
    ]
    df = df[expected_cols]
    return df


def run_feature_engineering():
    """Main execution entrypoint for feature engineering pipeline."""
    print("=" * 65)
    print("🚀 NOVANEST FEATURE ENGINEERING PIPELINE")
    print("=" * 65)
    
    orders, restaurants, customers, riders, deliveries = load_cleaned_datasets()
    print(f"Loaded {len(orders):,} base orders from cleaned dataset.")
    
    engineered_df = engineer_features(orders, restaurants, customers, riders, deliveries)
    
    output_path = ENGINEERED_DIR / "orders_engineered.csv"
    engineered_df.to_csv(output_path, index=False)
    print(f"✅ Saved engineered dataset: {output_path}")
    print(f"   Shape: {engineered_df.shape[0]:,} rows x {engineered_df.shape[1]} columns")
    
    # Also save dedicated geo-temporal enriched artifact for models
    geo_path = ENGINEERED_DIR / "orders_geo_temporal_enriched.csv"
    engineered_df.to_csv(geo_path, index=False)
    print(f"✅ Saved geo-temporal enriched dataset: {geo_path}")
    
    print("-" * 65)
    print("Key Feature Distributions:")
    print(f"- Peak Hour Orders: {engineered_df['peak_hour_flag'].sum():,} ({engineered_df['peak_hour_flag'].mean()*100:.1f}%)")
    print(f"- Weekend Orders: {engineered_df['weekend_flag'].sum():,} ({engineered_df['weekend_flag'].mean()*100:.1f}%)")
    print(f"- Delivery Delays (>45 min): {engineered_df['delivery_delay_flag'].sum():,} ({engineered_df['delivery_delay_flag'].mean()*100:.1f}%)")
    print(f"- Cross-City Orders: {engineered_df['cross_city_flag'].sum():,} ({engineered_df['cross_city_flag'].mean()*100:.1f}%)")
    print(f"- Pre-Signup Orders: {engineered_df['pre_signup_order_flag'].sum():,} ({engineered_df['pre_signup_order_flag'].mean()*100:.1f}%)")
    print(f"- Mean Estimated Profit per Order: ₹{engineered_df['estimated_profit'].mean():.2f}")
    print(f"- Mean Profit Margin: {engineered_df['profit_margin_pct'].mean():.2f}%")
    print("=" * 65)
    return engineered_df


if __name__ == "__main__":
    run_feature_engineering()
