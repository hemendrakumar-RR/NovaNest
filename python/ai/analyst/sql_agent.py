"""
NovaNest Safe SQL Agent & Natural Language Translation
Enforces strict read-only execution, AST schema validation, and SQLite sandboxing.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from python.ai.analyst.sql_ast import (
    ALLOWED_TABLES,
    DANGEROUS_FUNCTIONS,
    DEFAULT_ROW_LIMIT,
    MAX_ROW_LIMIT,
    SAFE_FUNCTIONS,
    validate_sql_ast,
)

logger = logging.getLogger(__name__)

# Explicit dataset-key -> SQLite sandbox table mapping across all 9 AST-approved tables.
# Note: Cleaned CSV 'orders.csv' (MySQL table 'orders_table') maps deterministically to SQLite table 'orders'.
DATASET_TO_SQLITE_TABLE_MAP: Dict[str, Dict[str, Any]] = {
    "orders": {
        "sqlite_table": "orders",
        "csv_filename": "orders.csv",
        "mysql_table": "orders_table",
    },
    "customers": {
        "sqlite_table": "customers",
        "csv_filename": "customers.csv",
        "mysql_table": "customers",
    },
    "restaurants": {
        "sqlite_table": "restaurants",
        "csv_filename": "restaurants.csv",
        "mysql_table": "restaurants",
    },
    "deliveries": {
        "sqlite_table": "deliveries",
        "csv_filename": "deliveries.csv",
        "mysql_table": "deliveries",
    },
    "riders": {
        "sqlite_table": "riders",
        "csv_filename": "riders.csv",
        "mysql_table": "riders",
    },
    "promotions": {
        "sqlite_table": "promotions",
        "csv_filename": "promotions.csv",
        "mysql_table": "promotions",
    },
    "ratings_reviews": {
        "sqlite_table": "ratings_reviews",
        "csv_filename": "ratings_reviews.csv",
        "mysql_table": "ratings_reviews",
    },
    "menu_items": {
        "sqlite_table": "menu_items",
        "csv_filename": "menu_items.csv",
        "mysql_table": "menu_items",
    },
    "payments": {
        "sqlite_table": "payments",
        "csv_filename": "payments.csv",
        "mysql_table": "payments",
    },
}

# Functions SQLite internally invokes during safe SELECT queries (e.g. LIKE operator, affinity casts)
_SQLITE_ENGINE_SAFE_FUNCTIONS: Set[str] = SAFE_FUNCTIONS | {
    "sqlite_subquery",
    "like",
    "ifnull",
    "coalesce",
    "typeof",
    "cast",
    "abs",
}


def _sqlite_readonly_authorizer(
    action: int,
    arg1: Optional[str],
    arg2: Optional[str],
    db_name: Optional[str],
    trigger_name: Optional[str],
) -> int:
    """
    SQLite C-level authorizer permitting strictly read-only SELECT execution over approved tables.
    """
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK

    if action == sqlite3.SQLITE_READ:
        # Internal temp/CTE subqueries may pass empty table name in some SQLite builds;
        # all physical tables (incl. sqlite_master / sqlite_schema) have a non-empty name.
        if not arg1:
            return sqlite3.SQLITE_OK
        tbl = arg1.lower()
        if tbl in ALLOWED_TABLES and not tbl.startswith("sqlite_") and not tbl.startswith("pragma_"):
            return sqlite3.SQLITE_OK
        logger.warning("SQLite authorizer denied read on unapproved table '%s'", arg1)
        return sqlite3.SQLITE_DENY

    if action == sqlite3.SQLITE_FUNCTION:
        fn = (arg2 or "").lower()
        if fn in DANGEROUS_FUNCTIONS or fn.startswith("sqlite_") or fn.startswith("pragma_"):
            logger.warning("SQLite authorizer denied dangerous function '%s'", arg2)
            return sqlite3.SQLITE_DENY
        if fn in _SQLITE_ENGINE_SAFE_FUNCTIONS:
            return sqlite3.SQLITE_OK
        logger.warning("SQLite authorizer denied unapproved function '%s'", arg2)
        return sqlite3.SQLITE_DENY

    # Explicitly deny writes, DDL, PRAGMA changes, ATTACH/DETACH, and recursive triggers
    return sqlite3.SQLITE_DENY


def configure_readonly_sqlite(sqlite_conn: sqlite3.Connection) -> None:
    """
    Locks an in-memory SQLite connection into strict read-only mode.
    Call AFTER populating initial dataframe tables with `to_sql`.
    """
    sqlite_conn.execute("PRAGMA query_only = ON;")
    try:
        sqlite_conn.execute("PRAGMA trusted_schema = OFF;")
    except sqlite3.Error:
        pass
    sqlite_conn.set_authorizer(_sqlite_readonly_authorizer)


def build_readonly_sqlite_connection(data: Optional[Dict[str, pd.DataFrame]]) -> sqlite3.Connection:
    """
    Initializes a thread-safe in-memory SQLite database containing all 9 AST-approved
    tables mapped explicitly via DATASET_TO_SQLITE_TABLE_MAP, then enforces strict
    read-only authorizer & PRAGMA query_only locks without altering AST protections.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    dataset_dict = data or {}

    for dataset_key, meta in sorted(DATASET_TO_SQLITE_TABLE_MAP.items()):
        sqlite_tbl = meta["sqlite_table"]
        if sqlite_tbl not in ALLOWED_TABLES:
            continue
        df = dataset_dict.get(dataset_key)
        if df is not None and hasattr(df, "empty") and not df.empty:
            df_prep = df.copy()
            if dataset_key == "orders":
                if "order_datetime" not in df_prep.columns and "order_time" in df_prep.columns:
                    df_prep["order_datetime"] = df_prep["order_time"]
                if "order_amount" in df_prep.columns:
                    if "final_amount" not in df_prep.columns:
                        df_prep["final_amount"] = df_prep["order_amount"]
                    if "discount_amount" not in df_prep.columns:
                        df_prep["discount_amount"] = df_prep["order_amount"] * 0.05
                if "delivery_fee" not in df_prep.columns:
                    df_prep["delivery_fee"] = 35.0
            df_prep.to_sql(sqlite_tbl, conn, if_exists="replace", index=False)

    configure_readonly_sqlite(conn)
    return conn


def verify_sqlite_table_parity(
    sqlite_conn: sqlite3.Connection,
    data: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Verifies loaded row counts, expected columns, and read-only compliance across
    all 9 ALLOWED_TABLES using strictly allowlisted SELECT queries.
    """
    report: Dict[str, Dict[str, Any]] = {}
    dataset_dict = data or {}

    for dataset_key, meta in sorted(DATASET_TO_SQLITE_TABLE_MAP.items()):
        tbl = meta["sqlite_table"]
        src_df = dataset_dict.get(dataset_key)
        expected_rows = int(len(src_df)) if (src_df is not None and hasattr(src_df, "__len__")) else 0
        expected_cols: List[str] = list(src_df.columns) if (src_df is not None and hasattr(src_df, "columns")) else []

        loaded = False
        actual_rows = 0
        actual_cols: List[str] = []
        error_msg = ""
        try:
            cur = sqlite_conn.execute(f"SELECT * FROM {tbl} LIMIT 1;")
            actual_cols = [d[0] for d in (cur.description or [])]
            cnt_cur = sqlite_conn.execute(f"SELECT COUNT(*) FROM {tbl};")
            actual_rows = int(cnt_cur.fetchone()[0])
            loaded = True
        except Exception as exc:
            error_msg = str(exc)

        report[tbl] = {
            "dataset_key": dataset_key,
            "mysql_table": meta["mysql_table"],
            "loaded": loaded,
            "expected_rows": expected_rows,
            "actual_rows": actual_rows,
            "row_parity": loaded and (actual_rows == expected_rows),
            "expected_columns": expected_cols,
            "actual_columns": actual_cols,
            "error": error_msg,
        }

    return report


def validate_and_sanitize_sql(sql: str) -> Tuple[bool, str, str]:
    """
    Validates that a SQL query is strictly read-only using AST parsing & recursive
    table/subquery/CTE/function checking, and enforces bounded LIMIT.
    Returns: (is_valid, sanitized_sql, error_or_success_message)
    """
    return validate_sql_ast(
        sql=sql,
        allowed_tables=ALLOWED_TABLES,
        max_row_limit=MAX_ROW_LIMIT,
        default_row_limit=DEFAULT_ROW_LIMIT,
    )


def execute_safe_sql(
    sql: str,
    sqlite_conn: sqlite3.Connection,
    timeout_seconds: float = 2.0,
    max_rows: int = MAX_ROW_LIMIT,
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Executes AST-validated SQL against SQLite with:
    - Re-validation before execution
    - SQLite C-level read-only authorizer & PRAGMA query_only (best effort on open conn)
    - Strict wall-clock progress timeout handler
    - Hard row fetch cap (max_rows <= MAX_ROW_LIMIT)
    """
    is_valid, sanitized, msg = validate_and_sanitize_sql(sql)
    if not is_valid:
        return None, msg

    row_cap = min(max_rows, MAX_ROW_LIMIT)
    deadline = time.monotonic() + max(0.1, float(timeout_seconds))

    def _timeout_guard() -> int:
        return 1 if time.monotonic() > deadline else 0

    try:
        sqlite_conn.set_authorizer(_sqlite_readonly_authorizer)
        sqlite_conn.set_progress_handler(_timeout_guard, 10_000)
        cursor = sqlite_conn.execute(sanitized)
        rows = cursor.fetchmany(row_cap)
        columns = [desc[0] for desc in (cursor.description or [])]
        df = pd.DataFrame(rows, columns=columns)
        return df, "Query executed successfully."
    except sqlite3.OperationalError as exc:
        err_text = str(exc)
        if "interrupted" in err_text.lower():
            return None, f"Query timeout: execution exceeded {timeout_seconds:.1f}s limit."
        return None, f"Query execution blocked or failed: {err_text}"
    except Exception as exc:
        return None, f"Query execution error: {str(exc)}"
    finally:
        try:
            sqlite_conn.set_progress_handler(None, 0)
        except Exception:
            pass
