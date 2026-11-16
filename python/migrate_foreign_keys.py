"""
NovaNest Foreign-Key & Index Migration Runner
Executes or generates ALTER TABLE statements to add 11 foreign-key constraints
and 19 secondary performance indexes to novanest_db safely without data loss.
"""

import os
import sys
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_WORKBENCH_SAFE_FILE = BASE_DIR / "mysql" / "02_safe_workbench_migration.sql"
SQL_IDEMPOTENT_FILE = BASE_DIR / "mysql" / "02_add_foreign_keys_and_indexes.sql"
SQL_DIRECT_FILE = BASE_DIR / "mysql" / "02_add_foreign_keys_direct.sql"

load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "novanest_db")


def check_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=3
        )
        return conn
    except mysql.connector.Error:
        return None


def run_migration():
    print("=" * 70)
    print("NOVANEST FOREIGN KEY & INDEX MIGRATION RUNNER")
    print("=" * 70)

    conn = check_connection()
    if conn is None:
        print("⚠️ MySQL CLI Connection is not currently available (errno=1045).")
        print("👉 Recommended Action: Execute the safe staged migration in MySQL Workbench:")
        print(f"   ⭐ Recommended Workbench Script: {SQL_WORKBENCH_SAFE_FILE}")
        print(f"   ℹ️ Alternative Idempotent Script: {SQL_IDEMPOTENT_FILE}")
        print(f"   ℹ️ Direct DDL Script (Single-Run): {SQL_DIRECT_FILE}")
        print("\nPlease open '02_safe_workbench_migration.sql' in MySQL Workbench as root@localhost.")
        print("=" * 70)
        return False

    cursor = conn.cursor()
    try:
        print("🔍 Checking pre-migration foreign keys...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL;
        """, (DB_NAME,))
        pre_count = cursor.fetchone()[0]
        print(f"   Existing registered foreign keys: {pre_count}")

        print("🚀 Applying migration DDL...")
        sql_content = SQL_DIRECT_FILE.read_text(encoding="utf-8")
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        for stmt in statements:
            if stmt.upper().startswith("USE") or stmt.upper().startswith("SELECT"):
                continue
            try:
                cursor.execute(stmt)
            except mysql.connector.Error as exec_err:
                # 1061 = Duplicate key name (Index exists), 1826 = Duplicate foreign key constraint
                if exec_err.errno in (1061, 1826):
                    print(f"   ℹ️ Already exists (skipped): {exec_err.msg}")
                else:
                    raise exec_err

        conn.commit()
        print("✅ Migration statements applied successfully.")

        print("🔍 Verifying post-migration foreign keys...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL;
        """, (DB_NAME,))
        post_count = cursor.fetchone()[0]
        print(f"   Registered foreign keys after migration: {post_count}")

        if post_count == 11:
            print("🎉 SUCCESS: All 11 canonical foreign keys are verified in novanest_db!")
            return True
        else:
            print(f"⚠️ Warning: Expected 11 foreign keys, found {post_count}.")
            return False

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"❌ Migration Error [{err.errno}]: {err.msg}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_migration()

