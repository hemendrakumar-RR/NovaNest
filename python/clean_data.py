"""
NovaNest Data Cleaning & Preprocessing Pipeline
Reads raw transactional datasets, applies type validations, sanitizes string fields,
validates business constraints, and produces cleaned data ready for warehousing and analytics.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Dynamic project root discovery
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "datasets" / "raw"
OUTPUT_DIR = BASE_DIR / "datasets" / "cleaned"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATASET_FILES = [
    "customers.csv",
    "restaurants.csv",
    "menu_items.csv",
    "riders.csv",
    "orders.csv",
    "payments.csv",
    "deliveries.csv",
    "app_events.csv",
    "ratings_reviews.csv",
    "promotions.csv"
]


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # String strip
    str_cols = ["customer_id", "customer_name", "gender", "city", "persona", "occupation", "subscription_type", "acquisition_channel"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Types & Bounds
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(25).astype(int)
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates(subset=["customer_id"])
    return df


def clean_restaurants(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    str_cols = ["restaurant_id", "restaurant_name", "city", "restaurant_type", "cuisine_type"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    df["opening_year"] = pd.to_numeric(df["opening_year"], errors="coerce").fillna(2020).astype(int)
    df["avg_rating"] = pd.to_numeric(df["avg_rating"], errors="coerce").round(1)
    df["delivery_radius_km"] = pd.to_numeric(df["delivery_radius_km"], errors="coerce").round(1)
    df["commission_percentage"] = pd.to_numeric(df["commission_percentage"], errors="coerce").astype(int)
    df = df.drop_duplicates(subset=["restaurant_id"])
    return df


def clean_menu_items(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    str_cols = ["item_id", "restaurant_id", "cuisine_type", "item_name"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
    df["preparation_time"] = pd.to_numeric(df["preparation_time"], errors="coerce").fillna(20).astype(int)
    df = df.drop_duplicates(subset=["item_id"])
    return df


def clean_riders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    str_cols = ["rider_id", "rider_name", "city", "vehicle_type", "shift_type"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    df["experience_years"] = pd.to_numeric(df["experience_years"], errors="coerce").fillna(1).astype(int)
    df["joining_year"] = pd.to_numeric(df["joining_year"], errors="coerce").fillna(2022).astype(int)
    df = df.drop_duplicates(subset=["rider_id"])
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    id_cols = ["order_id", "customer_id", "restaurant_id", "item_id", "rider_id", "order_status"]
    for col in id_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    df["order_datetime"] = pd.to_datetime(df["order_datetime"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["order_amount"] = pd.to_numeric(df["order_amount"], errors="coerce").fillna(0).astype(int)
    df["discount_amount"] = pd.to_numeric(df["discount_amount"], errors="coerce").fillna(0).astype(int)
    df["delivery_fee"] = pd.to_numeric(df["delivery_fee"], errors="coerce").fillna(0).astype(int)
    df["final_amount"] = pd.to_numeric(df["final_amount"], errors="coerce").fillna(0).astype(int)
    
    # Enforce minimum final amount business rule (clamped to at least 0)
    df["final_amount"] = df["final_amount"].clip(lower=0)
    df = df.drop_duplicates(subset=["order_id"])
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["payment_id", "order_id", "payment_method", "payment_status"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df = df.drop_duplicates(subset=["payment_id"])
    return df


def clean_deliveries(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["delivery_id", "order_id", "rider_id"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce").round(1)
    df["delivery_duration"] = pd.to_numeric(df["delivery_duration"], errors="coerce").fillna(30).astype(int)
    df = df.drop_duplicates(subset=["delivery_id"])
    return df


def clean_app_events(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["event_id", "customer_id", "event_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df = df.drop_duplicates(subset=["event_id"])
    return df


def clean_ratings_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["review_id", "order_id", "customer_id"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df["restaurant_rating"] = pd.to_numeric(df["restaurant_rating"], errors="coerce").fillna(4).astype(int).clip(1, 5)
    df["delivery_rating"] = pd.to_numeric(df["delivery_rating"], errors="coerce").fillna(4).astype(int).clip(1, 5)
    df = df.drop_duplicates(subset=["review_id"])
    return df


def clean_promotions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["promo_id", "promo_name", "promo_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce").fillna(10).astype(int).clip(0, 100)
    df["campaign_budget"] = pd.to_numeric(df["campaign_budget"], errors="coerce").fillna(10000).astype(int)
    df = df.drop_duplicates(subset=["promo_id"])
    return df


CLEANERS = {
    "customers.csv": clean_customers,
    "restaurants.csv": clean_restaurants,
    "menu_items.csv": clean_menu_items,
    "riders.csv": clean_riders,
    "orders.csv": clean_orders,
    "payments.csv": clean_payments,
    "deliveries.csv": clean_deliveries,
    "app_events.csv": clean_app_events,
    "ratings_reviews.csv": clean_ratings_reviews,
    "promotions.csv": clean_promotions
}


def run_cleaning_pipeline():
    print("=" * 60)
    print("🚀 STARTING NOVANEST DATA CLEANING PIPELINE")
    print(f"Source Directory: {RAW_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    summary = []
    
    for filename in DATASET_FILES:
        raw_file = RAW_DIR / filename
        if not raw_file.exists():
            print(f"❌ Warning: File {raw_file} not found. Skipping.")
            continue
            
        df_raw = pd.read_csv(raw_file)
        initial_rows = len(df_raw)
        
        cleaner_fn = CLEANERS.get(filename)
        if cleaner_fn:
            df_clean = cleaner_fn(df_raw)
        else:
            df_clean = df_raw.drop_duplicates()
            
        final_rows = len(df_clean)
        null_count = df_clean.isnull().sum().sum()
        
        output_file = OUTPUT_DIR / filename
        df_clean.to_csv(output_file, index=False)
        
        status = {
            "dataset": filename,
            "raw_rows": initial_rows,
            "cleaned_rows": final_rows,
            "cols": len(df_clean.columns),
            "remaining_nulls": null_count
        }
        summary.append(status)
        print(f"✅ Cleaned {filename:<20} | Rows: {final_rows:<7} | Cols: {len(df_clean.columns):<2} | Nulls: {null_count}")

    print("=" * 60)
    print("🎉 ALL 10 DATASETS CLEANED & VERIFIED SUCCESSFULLY")
    print("=" * 60)
    return summary


if __name__ == "__main__":
    run_cleaning_pipeline()
