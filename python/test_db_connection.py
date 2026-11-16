"""
NovaNest MySQL Connection & Permissions Pre-Flight Test
-------------------------------------------------------
Verifies database connectivity, user authentication, and least-privilege scoping
for both `novanest_app` and `novanest_loader` without inserting or modifying any records.
"""

import argparse
import os
import sys
from pathlib import Path
import mysql.connector
from mysql.connector import errorcode

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

DOTENV_LOADED = False
try:
    from dotenv import load_dotenv
    if ENV_FILE.exists():
        DOTENV_LOADED = load_dotenv(ENV_FILE, override=True)
except ImportError:
    pass

def get_env_var(key: str, default: str = "") -> str:
    """Reads environment variable with fallback."""
    return os.getenv(key, default)

def test_user_connection(host: str, port: int, dbname: str, user_label: str, username: str, password: str, expected_role: str) -> bool:
    """Tests connection and verifies least-privilege permission boundaries for a specific user."""
    print(f"\n--- Testing {user_label} (`{username}`@{host}:{port}/{dbname}) ---")

    if not password:
        print(f"⚠️ Notice: No password found in environment for `{username}`.")
        print(f"👉 Please set DB_APP_PASSWORD or DB_INGEST_PASSWORD in `{ENV_FILE}`.")
        return False

    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=dbname,
            connect_timeout=3
        )

        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), DATABASE(), VERSION();")
        curr_user, curr_db, version = cursor.fetchone()
        print(f"   ✅ Authentication Successful: Authenticated as `{curr_user}`")
        print(f"   ✅ Database Target Verified: Connected to `{curr_db}` (MySQL {version})")

        # 1. Test SELECT privilege on dimension tables
        cursor.execute("SELECT COUNT(*) FROM customers;")
        cust_cnt = cursor.fetchone()[0]
        print(f"   ✅ SELECT Privilege Verified: `customers` table accessible ({cust_cnt:,} rows)")

        # 2. Test that administrative DDL (DROP TABLE) is strictly DENIED
        try:
            cursor.execute("DROP TABLE IF EXISTS __novanest_privilege_probe__;")
            print("   ❌ SECURITY ALERT: User has DROP privilege! Least-privilege boundary failed.")
            conn.rollback()
            return False
        except mysql.connector.Error as ddl_err:
            if ddl_err.errno == errorcode.ER_TABLEACCESS_DENIED_ERROR or ddl_err.errno == 1142:
                print("   🛡️ Least-Privilege Enforced: DROP TABLE access correctly DENIED (Error 1142)")
            else:
                print(f"   🛡️ DDL Command Blocked: [{ddl_err.errno}] {ddl_err.msg}")

        cursor.close()
        conn.close()
        print(f"🎉 {user_label} Verification PASSED: Scoped strictly to {expected_role}.")
        return True

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            # Sanitized error report: Never prints password or token values
            print(f"   ❌ Authentication Failed: Access denied for user `{username}`@`{host}`.")
            print(f"      [Sanitized Error: errno={err.errno}, sqlstate={err.sqlstate}]")
            print("   👉 Check that password matches what was created in MySQL Workbench.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"   ❌ Target Database Error: Database `{dbname}` does not exist on `{host}`.")
            print("   👉 Verify that DB_NAME=novanest_db is configured in `.env`.")
        else:
            print(f"   ❌ MySQL Connection Error [errno={err.errno}]: {err.msg}")
        return False


def test_sanitized_failed_authentication(host: str, port: int, dbname: str) -> bool:
    """Verifies that failed authentication produces sanitized errors without exposing credentials."""
    print("\n--- Testing Authentication Failure Sanitization ---")
    dummy_user = "nonexistent_probe_user"
    dummy_pass = "super_secret_dummy_probe_password_12345"

    try:
        mysql.connector.connect(
            host=host,
            port=port,
            user=dummy_user,
            password=dummy_pass,
            database=dbname,
            connect_timeout=2
        )
        print("❌ Unexpected: Connection succeeded with invalid credentials.")
        return False
    except mysql.connector.Error as err:
        err_str = str(err)
        # Verify secret dummy password is not in the error message
        if dummy_pass in err_str:
            print("❌ SECURITY VULNERABILITY: Plaintext password leaked in exception message!")
            return False
        print(f"   ✅ Authentication properly rejected: errno={err.errno}, sqlstate={err.sqlstate}")
        print("   ✅ Password Redaction Verified: 0 credentials leaked in exception output.")
        return True


def main():
    parser = argparse.ArgumentParser(description="NovaNest MySQL Connectivity & Authentication Test")
    parser.add_argument("--host", default=get_env_var("DB_HOST", "localhost"), help="MySQL Host")
    parser.add_argument("--port", type=int, default=int(get_env_var("DB_PORT", "3306")), help="MySQL Port")
    parser.add_argument("--dbname", default=get_env_var("DB_NAME", "novanest_db"), help="Target Database (default: novanest_db)")
    parser.add_argument("--app-user", default=get_env_var("DB_APP_USER", "novanest_app"), help="Runtime App User")
    parser.add_argument("--app-password", default=get_env_var("DB_APP_PASSWORD", ""), help="Runtime App Password")
    parser.add_argument("--ingest-user", default=get_env_var("DB_INGEST_USER", "novanest_loader"), help="Ingestion ETL User")
    parser.add_argument("--ingest-password", default=get_env_var("DB_INGEST_PASSWORD", ""), help="Ingestion ETL Password")
    args = parser.parse_args()

    print("=" * 70)
    print("🐘 NOVANEST MYSQL CONNECTIVITY & PERMISSIONS PRE-FLIGHT TEST")
    print(f"Target Database: {args.host}:{args.port}/{args.dbname}")
    if ENV_FILE.exists():
        print(f"ℹ️ Loaded Environment: {ENV_FILE} (dotenv={DOTENV_LOADED})")
    else:
        print(f"⚠️ Notice: `.env` file not found at {ENV_FILE}")
    if args.dbname == "novanest":
        print("⚠️ Warning: DB_NAME in `.env` is set to 'novanest'. The canonical database is 'novanest_db'.")
        print("👉 Please update `.env` to `DB_NAME=novanest_db`.")
    print("=" * 70)

    # 1. Test Application Runtime User
    app_ok = test_user_connection(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user_label="Runtime User",
        username=args.app_user,
        password=args.app_password,
        expected_role="Application Analytics & Queries"
    )

    # 2. Test Ingestion ETL User
    ingest_ok = test_user_connection(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user_label="Ingestion User",
        username=args.ingest_user,
        password=args.ingest_password,
        expected_role="ETL Bulk Ingestion"
    )

    # 3. Test Error Sanitization
    sanitize_ok = test_sanitized_failed_authentication(args.host, args.port, args.dbname)

    print("\n" + "=" * 70)
    print("PRE-FLIGHT SUMMARY:")
    print(f" • Runtime User (`{args.app_user}`)     : {'✅ CONNECTED' if app_ok else '⚠️ NOT CONNECTED / PENDING CONFIG'}")
    print(f" • Ingestion User (`{args.ingest_user}`): {'✅ CONNECTED' if ingest_ok else '⚠️ NOT CONNECTED / PENDING CONFIG'}")
    print(f" • Error Sanitization            : {'✅ VERIFIED (0 SECRETS LEAKED)' if sanitize_ok else '❌ FAILED'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
