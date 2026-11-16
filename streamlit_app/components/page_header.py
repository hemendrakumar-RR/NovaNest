"""
NovaNest Page Header Component
-------------------------------
Renders standardized top-level executive headers with category tags,
descriptive subtitles, and live data telemetry indicators.
"""

import datetime
import streamlit as st

def render_page_header(
    title: str,
    subtitle: str,
    category: str = "NOVANEST INTELLIGENCE",
    data_source: str = "CSV File Store",
    record_count: int = None
):
    """
    Renders the unified enterprise page header banner.
    """
    is_mysql = "MySQL" in data_source
    time_str = datetime.datetime.now().strftime("%I:%M %p")
    dot_class = "online" if is_mysql else "fallback"
    source_label = "MySQL DB" if is_mysql else "Cleaned Data Store"
    record_text = f" • {record_count:,} Records" if record_count is not None else ""

    header_html = f"""
    <div class="nn-header-container">
        <div class="nn-header-left">
            <span class="nn-header-badge">{category}</span>
            <h1 class="nn-header-title">{title}</h1>
            <p class="nn-header-subtitle">{subtitle}</p>
        </div>
        <div class="nn-telemetry-badge">
            <span class="nn-pulse-dot {dot_class}"></span>
            <div class="nn-telemetry-text">
                <span class="nn-telemetry-value">{source_label}</span>{record_text}
                <div style="font-size: 0.68rem; color: #64748B; font-weight: 500;">Last Sync: {time_str}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
