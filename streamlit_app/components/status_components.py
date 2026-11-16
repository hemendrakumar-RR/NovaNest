"""
NovaNest Status & Section Indicators
------------------------------------
Provides section dividers, callouts, and clean data tables.
"""

from typing import Optional
import pandas as pd
import streamlit as st

def render_section_header(title: str, tag: str = ""):
    """Renders a sleek section divider with optional uppercase category tag."""
    tag_html = f'<span class="nn-section-tag">{tag}</span>' if tag else ""
    header_html = f"""
    <div class="nn-section-header">
        <h3 class="nn-section-title">{title}</h3>
        {tag_html}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def render_callout(title: str, message: str, level: str = "info"):
    """
    Renders an alert callout box.
    levels: 'info', 'success', 'warning', 'danger'
    """
    callout_html = f"""
    <div class="nn-callout {level}">
        <div>
            <div class="nn-callout-title">{title}</div>
            <div class="nn-callout-body">{message}</div>
        </div>
    </div>
    """
    st.markdown(callout_html, unsafe_allow_html=True)

def render_data_table(df: pd.DataFrame, max_rows: int = 100):
    """Renders an interactive Streamlit dataframe with standard container styling."""
    if df.empty:
        st.info("No records to display.")
        return
    st.dataframe(df.head(max_rows), width="stretch", hide_index=True)
