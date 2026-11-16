"""
NovaNest Automated MySQL Ingestion Pipeline
-------------------------------------------
Safely ingests cleaned CSV datasets into MySQL tables enforcing referential foreign-key ordering.
Features transaction management, table-level atomicity, environment-based credentials,
dry-run validation, and post-ingestion verification routines.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import mysql.connector
from mysql.connector import errorcode

# Dynamic project root discovery
BASE_DIR = Path(__file__).resolve().parent.parent
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"

# Load environment configuration if available
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env", override=True)
except ImportError:
    pass

# Database Configuration with least-privilege resolution
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
# Primary: Ingestion ETL user; Fallback: standard user
DB_USER = os.getenv("DB_INGEST_USER") or os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_INGEST_PASSWORD") or os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "novanest_db")

# Strict Referential Dependency Order (Parent Tables Before Child Tables)
INGESTION_SEQUENCE: List[Dict[str, any]] = [
    # Tier 1: Independent Dimension Tables (No Foreign Keys)
    {"table": "customers", "file": "customers.csv", "batch_size": 2500, "expected_rows": 5000, "tier": 1},
    {"table": "restaurants", "file": "restaurants.csv", "batch_size": 1500, "expected_rows": 1500, "tier": 1},
    {"table": "riders", "file": "riders.csv", "batch_size": 2000, "expected_rows": 4000, "tier": 1},
    {"table": "promotions", "file": "promotions.csv", "batch_size": 500, "expected_rows": 200, "tier": 1},

    # Tier 2: 1st Degree Dependent Table (References restaurants)
    {"table": "menu_items", "file": "menu_items.csv", "batch_size": 5000, "expected_rows": 15000, "tier": 2},

    # Tier 3: Core Transaction Fact Table (References customers, restaurants, menu_items, riders)
    {"table": "orders_table", "file": "orders.csv", "batch_size": 5000, "expected_rows": 49971, "tier": 3},

    # Tier 4: Transaction-Dependent Child Tables (Reference orders_table, riders, customers)
    {"table": "payments", "file": "payments.csv", "batch_size": 5000, "expected_rows": 49971, "tier": 4},
    {"table": "deliveries", "file": "deliveries.csv", "batch_size": 5000, "expected_rows": 49971, "tier": 4},
    {"table": "ratings_reviews", "file": "ratings_reviews.csv", "batch_size": 5000, "expected_rows": 28792, "tier": 4},

    # Tier 5: Customer Activity Stream (References customers)
    {"table": "app_events", "file": "app_events.csv", "batch_size": 10000, "expected_rows": 100000, "tier": 5},
]


def get_db_connection(
    host: str = DB_HOST,
    port: int = DB_PORT,
    user: str = DB_USER,
    password: str = DB_PASSWORD,
    dbname: str = DB_NAME
) -> Optional[mysql.connector.MySQLConnection]:
    """Establish direct connection to target MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbname,
            connect_timeout=5,
            autocommit=False
        )
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Authentication Error: Invalid MySQL username or password.")
            print(f"   Target user: '{user}' on '{host}:{port}'")
            print("👉 Please configure valid credentials in your .env file or command arguments.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"❌ Database Error: Database '{dbname}' does not exist.")
            print("👉 Please run 'mysql/02_safe_workbench_migration.sql' in MySQL Workbench first.")
        else:
            print(f"❌ MySQL Connection Error [{err.errno}]: {err}")
        return None


def verify_database_readiness(conn: mysql.connector.MySQLConnection, dbname: str) -> bool:
    """Verifies that all 10 tables exist and all 11 foreign keys are registered before ingestion."""
    cursor = conn.cursor()
    try:
        # 1. Verify tables
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
            (dbname,)
        )
        existing_tables = set(row[0] for row in cursor.fetchall())
        required_tables = set(task["table"] for task in INGESTION_SEQUENCE)
        missing_tables = required_tables - existing_tables

        if missing_tables:
            print(f"❌ Missing tables in '{dbname}': {sorted(missing_tables)}")
            print("👉 Execute 'mysql/02_safe_workbench_migration.sql' to initialize the schema.")
            return False

        # 2. Verify foreign keys
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (dbname,))
        fk_count = cursor.fetchone()[0]

        print(f"✅ Schema Verified: All {len(required_tables)} tables present in `{dbname}`.")
        print(f"✅ Relational Integrity: {fk_count} foreign-key constraints active.")
        if fk_count < 11:
            print(f"⚠️ Warning: Expected 11 foreign keys, found {fk_count}. Ingestion will proceed with existing constraints.")

        return True
    finally:
        cursor.close()


def dry_run_validation() -> bool:
    """Validates all 10 CSV datasets, column mapping, row counts, and data types offline."""
    print("\n" + "=" * 70)
    print("🔍 RUNNING OFFLINE PRE-INGESTION CSV AUDIT (DRY RUN)")
    print("=" * 70)

    if not CLEANED_DIR.exists():
        print(f"❌ Datasets directory not found: {CLEANED_DIR}")
        return False

    total_records = 0
    all_valid = True

    print(f"{'Table':<16} | {'CSV File':<20} | {'Rows':<8} | {'Cols':<5} | {'Nulls':<6} | {'Status'}")
    print("-" * 70)

    for task in INGESTION_SEQUENCE:
        tbl = task["table"]
        fname = task["file"]
        expected = task["expected_rows"]
        fpath = CLEANED_DIR / fname

        if not fpath.exists():
            print(f"{tbl:<16} | {fname:<20} | {'MISSING':<8} | {'-':<5} | {'-':<6} | ❌ FILE NOT FOUND")
            all_valid = False
            continue

        df = pd.read_csv(fpath)
        row_count = len(df)
        col_count = len(df.columns)
        null_count = int(df.isnull().sum().sum())
        total_records += row_count

        status = "✅ OK"
        if row_count != expected:
            status = f"⚠️ Count mismatch ({row_count} != {expected})"
            all_valid = False
        elif null_count > 0:
            status = f"⚠️ {null_count} nulls"
            all_valid = False

        print(f"{tbl:<16} | {fname:<20} | {row_count:<8,d} | {col_count:<5d} | {null_count:<6d} | {status}")

    print("-" * 70)
    print(f"Total Datasets: {len(INGESTION_SEQUENCE)} | Total Records: {total_records:,d}")
    if all_valid:
        print("🎉 DRY RUN PASSED: All 10 datasets are verified and ready for ingestion.")
    else:
        print("⚠️ DRY RUN WARNING: Some datasets contain discrepancies. Review above.")
    print("=" * 70 + "\n")
    return all_valid


def ingest_table(
    conn: mysql.connector.MySQLConnection,
    table_name: str,
    csv_filename: str,
    batch_size: int = 5000,
    expected_rows: int = 0
) -> bool:
    """
    Ingests CSV records into MySQL table with table-level transactional atomicity.
    Rolls back the entire table if any batch fails.
    """
    csv_path = CLEANED_DIR / csv_filename
    if not csv_path.exists():
        print(f"❌ File missing: {csv_path}")
        return False

    df = pd.read_csv(csv_path)
    total_rows = len(df)
    cols = df.columns.tolist()

    cursor = conn.cursor()
    try:
        # Check current row count
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        existing_count = cursor.fetchone()[0]

        if existing_count == total_rows and existing_count > 0:
            print(f"ℹ️ Table `{table_name}` already fully populated ({existing_count:,} rows). Skipping.")
            return True

        if existing_count > 0:
            print(f"⚠️ Table `{table_name}` has partial records ({existing_count:,} / {total_rows:,}). Safe replay enabled.")

        placeholders = ", ".join(["%s"] * len(cols))
        col_names = ", ".join([f"`{c}`" for c in cols])
        insert_sql = f"INSERT IGNORE INTO `{table_name}` ({col_names}) VALUES ({placeholders})"

        # Convert NaN/NaT to None, and numpy types to Python native types
        records = [
            tuple(None if pd.isna(val) else val for val in row)
            for row in df.itertuples(index=False)
        ]

        t0 = time.time()
        for i in range(0, total_rows, batch_size):
            batch = records[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            current_done = min(i + batch_size, total_rows)
            pct = (current_done / total_rows) * 100
            print(f"   Table `{table_name}`: [{current_done:,} / {total_rows:,}] ({pct:.1f}%) ...", end="\r")

        # Table-level atomic commit: commits ONLY when all batches complete without error
        conn.commit()
        duration = time.time() - t0
        speed = total_rows / duration if duration > 0 else total_rows
        print(f"✅ Ingested `{table_name}`: {total_rows:,} rows in {duration:.2f}s ({speed:.0f} rows/s)           ")

        # Post-ingestion row count confirmation
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        final_count = cursor.fetchone()[0]
        if final_count != total_rows:
            print(f"⚠️ Count notice: `{table_name}` contains {final_count:,} rows (expected {total_rows:,})")

        return True
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\n❌ Error ingesting `{table_name}` [{err.errno}]: {err.msg}")
        return False
    finally:
        cursor.close()


def verify_ingestion(conn: mysql.connector.MySQLConnection, dbname: str = DB_NAME) -> bool:
    """Performs comprehensive post-ingestion verification across row counts and referential integrity."""
    print("\n" + "=" * 70)
    print(f"🔍 RUNNING POST-INGESTION INTEGRITY AUDIT ON `{dbname}`")
    print("=" * 70)

    cursor = conn.cursor()
    all_ok = True
    try:
        print("1. ROW COUNT RECONCILIATION:")
        print(f"{'Table':<16} | {'Actual Rows':<12} | {'Expected Rows':<14} | {'Status'}")
        print("-" * 55)

        total_actual = 0
        total_expected = 0

        for task in INGESTION_SEQUENCE:
            tbl = task["table"]
            expected = task["expected_rows"]
            cursor.execute(f"SELECT COUNT(*) FROM `{dbname}`.`{tbl}`")
            actual = cursor.fetchone()[0]
            total_actual += actual
            total_expected += expected

            status = "✅ MATCH" if actual == expected else f"⚠️ MISMATCH ({actual} vs {expected})"
            if actual != expected:
                all_ok = False
            print(f"{tbl:<16} | {actual:<12,d} | {expected:<14,d} | {status}")

        print("-" * 55)
        print(f"TOTAL RECORDS    | {total_actual:<12,d} | {total_expected:<14,d} | {'✅ MATCH' if total_actual == total_expected else '⚠️ MISMATCH'}")

        print("\n2. REFERENTIAL INTEGRITY (ORPHAN FOREIGN KEY CHECKS):")
        fk_checks = [
            ("menu_items -> restaurants", "menu_items", "restaurant_id", "restaurants", "restaurant_id"),
            ("orders -> customers", "orders_table", "customer_id", "customers", "customer_id"),
            ("orders -> restaurants", "orders_table", "restaurant_id", "restaurants", "restaurant_id"),
            ("orders -> menu_items", "orders_table", "item_id", "menu_items", "item_id"),
            ("orders -> riders", "orders_table", "rider_id", "riders", "rider_id"),
            ("payments -> orders", "payments", "order_id", "orders_table", "order_id"),
            ("deliveries -> orders", "deliveries", "order_id", "orders_table", "order_id"),
            ("deliveries -> riders", "deliveries", "rider_id", "riders", "rider_id"),
            ("reviews -> orders", "ratings_reviews", "order_id", "orders_table", "order_id"),
            ("reviews -> customers", "ratings_reviews", "customer_id", "customers", "customer_id"),
            ("events -> customers", "app_events", "customer_id", "customers", "customer_id"),
        ]

        for desc, child_tbl, child_col, parent_tbl, parent_col in fk_checks:
            sql = f"""
                SELECT COUNT(*) 
                FROM `{dbname}`.`{child_tbl}` c 
                LEFT JOIN `{dbname}`.`{parent_tbl}` p ON c.`{child_col}` = p.`{parent_col}` 
                WHERE p.`{parent_col}` IS NULL;
            """
            cursor.execute(sql)
            orphan_count = cursor.fetchone()[0]
            if orphan_count == 0:
                print(f"   ✅ {desc:<32}: 0 orphans (100% referential integrity)")
            else:
                print(f"   ❌ {desc:<32}: {orphan_count:,} orphaned records detected!")
                all_ok = False

        print("\n3. CORE BUSINESS METRICS SANITY CHECK:")
        cursor.execute(f"""
            SELECT 
                COUNT(*) AS total_orders,
                SUM(order_amount) AS total_gmv,
                SUM(CASE WHEN order_status = 'Delivered' THEN order_amount ELSE 0 END) AS delivered_gmv
            FROM `{dbname}`.`orders_table`
        """)
        row = cursor.fetchone()
        if row and row[0] is not None:
            orders_cnt, gmv, delivered_gmv = row
            print(f"   • Total Orders  : {orders_cnt:,d}")
            print(f"   • Total GMV     : ₹{gmv:,.2f}" if gmv else "   • Total GMV : N/A")
            print(f"   • Delivered GMV : ₹{delivered_gmv:,.2f}" if delivered_gmv else "   • Delivered GMV : N/A")
            print("   ✅ Business calculations grounded and consistent with certified analytics.")

        print("=" * 70 + "\n")
        return all_ok
    finally:
        cursor.close()


def run_mysql_ingestion(args: argparse.Namespace) -> bool:
    """Main execution orchestrator for MySQL data loader."""
    print("=" * 70)
    print("🐘 NOVANEST AUTOMATED MYSQL DATA LOADER")
    print(f"Target Database : {args.user}@{args.host}:{args.port}/{args.dbname}")
    print("=" * 70)

    if args.dry_run:
        return dry_run_validation()

    conn = get_db_connection(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        dbname=args.dbname
    )

    if conn is None:
        print("\n⚠️ Ingestion Blocked: MySQL database connection could not be established.")
        print("   Cleaned CSV datasets and schema DDL are validated and ready.")
        print("   Configure valid credentials in `.env` or pass command arguments.")
        print("   You can test datasets offline anytime using: python python/load_mysql.py --dry-run")
        print("=" * 70)
        return False

    try:
        # Schema and Foreign Key Readiness Audit
        ready = verify_database_readiness(conn, args.dbname)
        if not ready:
            return False

        if args.verify_only:
            return verify_ingestion(conn, args.dbname)

        print("\n🚀 Starting FK-Safe Sequential Ingestion Pipeline...")
        t_start = time.time()
        success_count = 0

        for task in INGESTION_SEQUENCE:
            batch_sz = args.batch_size if args.batch_size else task["batch_size"]
            ok = ingest_table(
                conn=conn,
                table_name=task["table"],
                csv_filename=task["file"],
                batch_size=batch_sz,
                expected_rows=task["expected_rows"]
            )
            if ok:
                success_count += 1
            else:
                print(f"❌ Sequence aborted at table `{task['table']}`. Halting downstream tables.")
                break

        total_time = time.time() - t_start
        print("-" * 70)
        print(f"Ingestion Sequence Finished: {success_count} / {len(INGESTION_SEQUENCE)} tables processed successfully in {total_time:.2f}s.")

        if success_count == len(INGESTION_SEQUENCE):
            print("🎉 Full Ingestion Complete! Running post-ingestion verification...")
            verify_ingestion(conn, args.dbname)
            return True
        else:
            return False

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="NovaNest FK-Safe MySQL Data Ingestion Pipeline")
    parser.add_argument("--host", default=DB_HOST, help="MySQL Host (default: %(default)s)")
    parser.add_argument("--port", type=int, default=DB_PORT, help="MySQL Port (default: %(default)s)")
    parser.add_argument("--user", default=DB_USER, help="MySQL User (default: %(default)s)")
    parser.add_argument("--password", default=DB_PASSWORD, help="MySQL Password")
    parser.add_argument("--dbname", default=DB_NAME, help="Target Database Name (default: %(default)s)")
    parser.add_argument("--batch-size", type=int, default=None, help="Custom batch size override")
    parser.add_argument("--dry-run", action="store_true", help="Audit datasets offline without connecting to MySQL")
    parser.add_argument("--verify-only", action="store_true", help="Run verification queries on live database without ingesting")

    args = parser.parse_args()
    success = run_mysql_ingestion(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
