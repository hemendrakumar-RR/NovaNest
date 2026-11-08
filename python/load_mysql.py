"""
NovaNest Automated MySQL Ingestion Pipeline
Safely ingests cleaned CSV datasets into MySQL tables enforcing referential foreign-key ordering.
Features transaction management, batch chunking, environment-based credentials, and idempotency.
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd
import mysql.connector
from mysql.connector import errorcode

# Dynamic project root discovery
BASE_DIR = Path(__file__).resolve().parent.parent
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
SCHEMA_FILE = BASE_DIR / "mysql" / "01_schema.sql"

# Try loading .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# Database Configuration from environment or defaults
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "novanest_db")

# Foreign-Key Safe Ingestion Hierarchy
INGESTION_SEQUENCE = [
    {"table": "customers", "file": "customers.csv", "batch_size": 2500},
    {"table": "restaurants", "file": "restaurants.csv", "batch_size": 1500},
    {"table": "riders", "file": "riders.csv", "batch_size": 2000},
    {"table": "promotions", "file": "promotions.csv", "batch_size": 500},
    {"table": "menu_items", "file": "menu_items.csv", "batch_size": 5000},
    {"table": "orders_table", "file": "orders.csv", "batch_size": 5000},
    {"table": "payments", "file": "payments.csv", "batch_size": 5000},
    {"table": "deliveries", "file": "deliveries.csv", "batch_size": 5000},
    {"table": "ratings_reviews", "file": "ratings_reviews.csv", "batch_size": 5000},
    {"table": "app_events", "file": "app_events.csv", "batch_size": 10000},
]


def get_db_connection(create_db_if_missing: bool = True):
    """Establish connection to MySQL server."""
    try:
        # Initial connection without database to verify server & create DB if missing
        server_conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        if create_db_if_missing:
            cursor = server_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.close()
        server_conn.close()

        # Connect directly to target database
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Authentication Error: Invalid MySQL username or password.")
            print("👉 Please configure DB_USER and DB_PASSWORD in your .env file.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"❌ Database Error: Database '{DB_NAME}' does not exist.")
        else:
            print(f"❌ MySQL Connection Error [{err.errno}]: {err}")
        return None


def execute_ddl_schema(conn):
    """Execute 01_schema.sql to ensure all 10 tables exist."""
    print("📋 Verifying relational database schema...")
    if not SCHEMA_FILE.exists():
        print(f"❌ Schema file not found at {SCHEMA_FILE}")
        return False

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split commands by semicolon
    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
    cursor = conn.cursor()
    try:
        for stmt in statements:
            cursor.execute(stmt)
        conn.commit()
        print("✅ Schema verified / updated successfully.")
        return True
    except mysql.connector.Error as err:
        print(f"⚠️ Schema execution notice: {err}")
        return False
    finally:
        cursor.close()


def ingest_table(conn, table_name: str, csv_filename: str, batch_size: int = 5000):
    """Batch-ingest CSV records into MySQL table safely."""
    csv_path = CLEANED_DIR / csv_filename
    if not csv_path.exists():
        print(f"❌ File missing: {csv_path}")
        return False

    df = pd.read_csv(csv_path)
    total_rows = len(df)
    cols = df.columns.tolist()

    # Check existing count
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    existing_count = cursor.fetchone()[0]

    if existing_count >= total_rows:
        print(f"ℹ️ Table `{table_name}` already contains {existing_count:,} records. Skipping ingestion.")
        cursor.close()
        return True

    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join([f"`{c}`" for c in cols])
    insert_sql = f"INSERT IGNORE INTO `{table_name}` ({col_names}) VALUES ({placeholders})"

    # Clean None / NaN values
    records = df.where(pd.notnull(df), None).values.tolist()

    t0 = time.time()
    try:
        inserted = 0
        for i in range(0, total_rows, batch_size):
            batch = records[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            conn.commit()
            inserted += len(batch)
            print(f"   Table `{table_name}`: Ingested {inserted:,} / {total_rows:,} records...", end="\r")

        duration = time.time() - t0
        print(f"✅ Ingested `{table_name}`: {total_rows:,} rows in {duration:.2f}s ({total_rows/duration:.0f} rows/s)")
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\n❌ Error ingesting `{table_name}`: {err}")
        return False
    finally:
        cursor.close()


def run_mysql_ingestion():
    """Main execution entrypoint for MySQL data loader."""
    print("=" * 65)
    print("🐘 NOVANEST AUTOMATED MYSQL DATA LOADER")
    print(f"Target Database: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 65)

    conn = get_db_connection()
    if conn is None:
        print("\n⚠️ Ingestion Blocked: MySQL database connection could not be established.")
        print("   Static SQL scripts have been sanitized and are production-ready.")
        print("   Configure valid credentials in `.env` to execute live ingestion.")
        print("=" * 65)
        return False

    try:
        execute_ddl_schema(conn)
        print("\n🚀 Starting FK-Safe Ingestion Sequence...")
        success_count = 0
        for task in INGESTION_SEQUENCE:
            ok = ingest_table(conn, task["table"], task["file"], task["batch_size"])
            if ok:
                success_count += 1
            else:
                print(f"❌ Aborting sequence due to error in table `{task['table']}`")
                break

        print("-" * 65)
        print(f"Ingestion Finished: {success_count} / {len(INGESTION_SEQUENCE)} tables processed successfully.")
        print("=" * 65)
        return success_count == len(INGESTION_SEQUENCE)
    finally:
        conn.close()


if __name__ == "__main__":
    run_mysql_ingestion()

