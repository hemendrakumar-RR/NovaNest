"""
NovaNest Database Connector with Seamless CSV Fallback
"""

import logging
import os
from pathlib import Path
import threading
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
ENGINEERED_DIR = BASE_DIR / "datasets" / "engineered"

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

_pool = None
_pool_config = None
_pool_lock = threading.Lock()

def _get_secret_or_env(key: str, default: str = "") -> str:
    """Safely retrieves a configuration key from st.secrets (root or mysql section) or os.getenv."""
    try:
        if hasattr(st, "secrets"):
            # Check root level
            if key in st.secrets:
                val = st.secrets[key]
                if val is not None:
                    return str(val).strip()
            # Check [mysql] section
            if "mysql" in st.secrets:
                mysql_sec = st.secrets["mysql"]
                if hasattr(mysql_sec, "get"):
                    if key in mysql_sec:
                        return str(mysql_sec[key]).strip()
                    lower_key = key.lower().replace("db_", "")
                    if lower_key in mysql_sec:
                        return str(mysql_sec[lower_key]).strip()
    except Exception:
        pass
    env_val = os.getenv(key)
    return env_val.strip() if env_val is not None else default

def get_db_connection():
    """
    Attempts to establish MySQL database connection with connection pooling
    and fail-safe CSV fallback. Credentials are never logged.
    Supports local .env, environment variables, and Streamlit Community Cloud st.secrets.
    """
    global _pool, _pool_config
    db_host = _get_secret_or_env("DB_HOST", "localhost")
    try:
        db_port = int(_get_secret_or_env("DB_PORT", "3306"))
    except ValueError:
        db_port = 3306
    db_user = _get_secret_or_env("DB_APP_USER") or _get_secret_or_env("DB_USER", "root")
    db_pass = _get_secret_or_env("DB_APP_PASSWORD") or _get_secret_or_env("DB_PASSWORD", "")
    db_name = _get_secret_or_env("DB_NAME", "novanest_db")
    current_config = (db_host, db_port, db_user, db_name)

    try:
        import mysql.connector
        from mysql.connector import pooling

        # Initialize connection pool if possible and config matches
        with _pool_lock:
            if _pool is None or _pool_config != current_config:
                try:
                    _pool = pooling.MySQLConnectionPool(
                        pool_name="streamlit_pool",
                        pool_size=5,
                        pool_reset_session=True,
                        host=db_host,
                        port=db_port,
                        user=db_user,
                        password=db_pass,
                        database=db_name,
                        connect_timeout=3,
                    )
                    _pool_config = current_config
                except Exception as pool_err:
                    _pool = None
                    _pool_config = None
                    logger.debug("Streamlit MySQL pool init deferred: %s", type(pool_err).__name__)

        if _pool is not None:
            try:
                conn = _pool.get_connection()
                if conn.is_connected():
                    return conn, "MySQL Database"
            except Exception:
                pass

        # Direct connection attempt if pool is inactive
        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            database=db_name,
            connect_timeout=3,
        )
        if conn.is_connected():
            return conn, "MySQL Database"
    except Exception as exc:
        logger.debug("Database connection error: %s. Using CSV File Store.", type(exc).__name__)

    return None, "CSV File Store"
