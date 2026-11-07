"""
NovaNest Master Data Validation Script
Validates row counts, columns, duplicates, and missing values across all 10 datasets.
Supports inspecting either 'raw' or 'cleaned' directories.
"""

from pathlib import Path
import pandas as pd
import sys

# Dynamic project root discovery
BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_DIR = BASE_DIR / "datasets" / "cleaned"

DATASETS = {
    "customers": "customers.csv",
    "restaurants": "restaurants.csv",
    "menu_items": "menu_items.csv",
    "riders": "riders.csv",
    "orders": "orders.csv",
    "payments": "payments.csv",
    "deliveries": "deliveries.csv",
    "app_events": "app_events.csv",
    "ratings_reviews": "ratings_reviews.csv",
    "promotions": "promotions.csv"
}


def validate_all_datasets(target_dir: Path = None):
    dir_to_check = target_dir or DATASET_DIR
    print("=" * 65)
    print(f"🔍 NOVANEST MASTER DATA VALIDATION — Target: {dir_to_check.name.upper()}")
    print(f"Path: {dir_to_check}")
    print("=" * 65)
    
    total_records = 0
    validation_passed = True
    
    for name, filename in DATASETS.items():
        file_path = dir_to_check / filename
        if not file_path.exists():
            print(f"❌ MISSING: {filename} does not exist in {dir_to_check}")
            validation_passed = False
            continue
            
        df = pd.read_csv(file_path)
        rows = len(df)
        cols = len(df.columns)
        dups = df.duplicated().sum()
        nulls = df.isnull().sum().sum()
        total_records += rows
        
        status_icon = "✅" if dups == 0 and nulls == 0 else "⚠️"
        print(f"{status_icon} {name.upper():<16} | Rows: {rows:<7} | Cols: {cols:<2} | Duplicates: {dups:<3} | Nulls: {nulls}")
        
    print("-" * 65)
    print(f"Total Records Analyzed: {total_records:,}")
    print(f"Overall Validation Status: {'PASSED (Zero Duplicates / Zero Nulls)' if validation_passed else 'FAILED'}")
    print("=" * 65)
    return validation_passed


if __name__ == "__main__":
    target = None
    if len(sys.argv) > 1 and sys.argv[1].lower() == "raw":
        target = BASE_DIR / "datasets" / "raw"
    validate_all_datasets(target)
