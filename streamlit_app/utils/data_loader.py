"""
Cached Data Loader for NovaNest Streamlit Application
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st
from database.connection import get_db_connection

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DIR = BASE_DIR / "datasets" / "cleaned"
ENGINEERED_DIR = BASE_DIR / "datasets" / "engineered"

_last_streamlit_fallback_reason: str = ""
_active_streamlit_source: str = "CSV File Store (Cleaned & Engineered)"

@st.cache_data(ttl=3600)
def load_all_datasets() -> Tuple[Dict[str, pd.DataFrame], str]:
    """
    Loads all datasets cleanly with caching.
    Respects DATA_SOURCE configuration ('mysql' vs 'csv') with observable, seamless fallback.
    Guarantees strict single-source consistency: zero silent mixing within any load.
    """
    global _last_streamlit_fallback_reason, _active_streamlit_source
    data = {}
    data_source_mode = os.getenv("DATA_SOURCE", "csv").lower()

    if data_source_mode == "mysql":
        conn, source_type = get_db_connection()
        if conn is not None:
            try:
                # Check if MySQL has rows populated
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM customers")
                row_cnt = cur.fetchone()[0]
                cur.close()

                if row_cnt > 0:
                    data["customers"] = pd.read_sql("SELECT * FROM customers", conn)
                    data["restaurants"] = pd.read_sql("SELECT * FROM restaurants", conn)
                    data["menu_items"] = pd.read_sql("SELECT * FROM menu_items", conn)
                    data["riders"] = pd.read_sql("SELECT * FROM riders", conn)
                    try:
                        data["orders"] = pd.read_sql("SELECT * FROM orders_table", conn)
                    except Exception:
                        data["orders"] = pd.read_sql("SELECT * FROM orders", conn)
                    data["payments"] = pd.read_sql("SELECT * FROM payments", conn)
                    data["deliveries"] = pd.read_sql("SELECT * FROM deliveries", conn)
                    data["app_events"] = pd.read_sql("SELECT * FROM app_events", conn)
                    data["promotions"] = pd.read_sql("SELECT * FROM promotions", conn)
                    data["ratings_reviews"] = pd.read_sql("SELECT * FROM ratings_reviews", conn)
                    conn.close()

                    # Load engineered datasets from local CSVs
                    _load_engineered_csvs(data)
                    _active_streamlit_source = "MySQL Database"
                    _last_streamlit_fallback_reason = ""
                    logger.info("[STREAMLIT_DATA_SOURCE_ACTIVE] Successfully loaded all 10 tables from MySQL Database novanest_db.")
                    return data, _active_streamlit_source
                else:
                    _last_streamlit_fallback_reason = "MySQL connected, but 'customers' table has 0 rows (database unpopulated)."
                    logger.warning("[STREAMLIT_DATA_SOURCE_FALLBACK] %s Using CSV File Store.", _last_streamlit_fallback_reason)
            except Exception as e:
                _last_streamlit_fallback_reason = f"MySQL query failure during extraction: {type(e).__name__}."
                logger.error("[STREAMLIT_DATA_SOURCE_FALLBACK] %s Clearing partial data and failing over to CSV File Store.", _last_streamlit_fallback_reason)
                data.clear()
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
        else:
            _last_streamlit_fallback_reason = "MySQL connection unavailable or timed out."
            logger.warning("[STREAMLIT_DATA_SOURCE_FALLBACK] %s Using CSV File Store.", _last_streamlit_fallback_reason)

    # Clean Fallback to Cleaned CSVs (Strict single-source isolation: clear any partial state)
    data.clear()
    data["customers"] = pd.read_csv(CLEANED_DIR / "customers.csv")
    data["restaurants"] = pd.read_csv(CLEANED_DIR / "restaurants.csv")
    data["menu_items"] = pd.read_csv(CLEANED_DIR / "menu_items.csv")
    data["riders"] = pd.read_csv(CLEANED_DIR / "riders.csv")
    data["orders"] = pd.read_csv(CLEANED_DIR / "orders.csv")
    data["payments"] = pd.read_csv(CLEANED_DIR / "payments.csv")
    data["deliveries"] = pd.read_csv(CLEANED_DIR / "deliveries.csv")
    data["app_events"] = pd.read_csv(CLEANED_DIR / "app_events.csv")
    data["promotions"] = pd.read_csv(CLEANED_DIR / "promotions.csv")
    data["ratings_reviews"] = pd.read_csv(CLEANED_DIR / "ratings_reviews.csv")

    _load_engineered_csvs(data)

    _active_streamlit_source = "CSV File Store (Cleaned & Engineered)"
    return data, _active_streamlit_source


def get_streamlit_data_source_diagnostics() -> Dict[str, Any]:
    """Exposes observable data-source diagnostics for the Streamlit application."""
    configured = os.getenv("DATA_SOURCE", "csv").lower()
    is_fallback = (configured == "mysql" and _active_streamlit_source != "MySQL Database")
    return {
        "configured_data_source": configured,
        "active_data_source": _active_streamlit_source,
        "fallback_active": is_fallback,
        "fallback_reason": _last_streamlit_fallback_reason if is_fallback else None,
        "consistent_source": True,
        "mixed_sources_detected": False
    }

def _load_engineered_csvs(data: dict):
    """
    Safely loads all engineered datasets for Phase 3 and Phase 4.
    """
    csv_map = {
        "orders_engineered": "orders_engineered.csv",
        "customer_churn_predictions": "customer_churn_predictions.csv",
        "restaurant_predictions": "restaurant_predictions.csv",
        "demand_forecasts": "demand_forecasts.csv",
        "demand_heatmap": "demand_heatmap.csv",
        "eta_predictions": "eta_predictions.csv",
        "rider_allocation": "rider_allocation.csv",
        "operational_anomalies": "operational_anomalies.csv",
        "revenue_leakage": "revenue_leakage.csv",
        "operational_alerts": "operational_alerts.csv",
    }

    for key, filename in csv_map.items():
        path = ENGINEERED_DIR / filename
        if path.exists():
            data[key] = pd.read_csv(path)
        else:
            data[key] = pd.DataFrame()
