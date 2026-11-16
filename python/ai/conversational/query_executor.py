"""
Phase 5 — AI Query Executor
---------------------------
Executes AST-validated read-only SQL queries safely and returns tabular results.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import pandas as pd

from python.ai.analyst.sql_agent import validate_and_sanitize_sql

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent / "streamlit_app"))
try:
    from database.connection import get_db_connection
except ImportError:
    get_db_connection = None

logger = logging.getLogger(__name__)


def execute_query(sql_query: str) -> pd.DataFrame:
    """
    Validates SQL strictly via AST schema whitelist and executes read-only query.
    Returns an empty DataFrame if validation fails or database is unavailable.
    """
    if not sql_query:
        return pd.DataFrame()

    is_valid, sanitized_sql, reason = validate_and_sanitize_sql(sql_query)
    if not is_valid:
        logger.warning("Blocked unsafe SQL in execute_query: %s", reason)
        return pd.DataFrame()

    try:
        if get_db_connection:
            conn, _ = get_db_connection()
            if conn:
                try:
                    # Enforce session read-only mode on MySQL connection before executing query
                    cursor = conn.cursor()
                    try:
                        cursor.execute("SET SESSION TRANSACTION READ ONLY")
                        cursor.execute("SET SESSION max_execution_time = 2000")
                    except Exception:
                        pass
                    finally:
                        cursor.close()
                    return pd.read_sql(sanitized_sql, conn)
                finally:
                    conn.close()

        logger.warning("Database connection unavailable for AI SQL execution.")
        return pd.DataFrame()
    except Exception as exc:
        logger.error("Failed to execute AI SQL query: %s", exc)
        return pd.DataFrame()
