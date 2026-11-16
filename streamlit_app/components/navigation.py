"""
NovaNest Navigation & Sidebar Control System
--------------------------------------------
Provides unified sidebar branding, system telemetry badges,
and global analytical filters stored across st.session_state.
"""

import streamlit as st
from config.settings import CITIES, PERSONAS, ORDER_STATUSES
from utils.validation import get_data_quality_status

def render_sidebar(data_source: str = "CSV File Store"):
    """
    Renders the consistent platform sidebar across all NovaNest pages.
    Returns the active dictionary of global filters.
    """
    with st.sidebar:
        # Platform Branding
        st.markdown("""
        <div style="padding: 0.5rem 0 1.25rem 0;">
            <div style="display: flex; align-items: center; gap: 0.65rem;">
                <div style="width: 34px; height: 34px; border-radius: 8px; background: linear-gradient(135deg, #2563EB, #1D4ED8); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; box-shadow: 0 4px 12px rgba(37,99,235,0.4);">
                    ⚡
                </div>
                <div>
                    <h2 style="font-size: 1.3rem; font-weight: 800; margin: 0; color: #FFFFFF; letter-spacing: -0.02em;">NovaNest</h2>
                    <span style="font-size: 0.68rem; font-weight: 700; color: #60A5FA; text-transform: uppercase; letter-spacing: 0.08em;">Enterprise Intelligence</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1px; background: rgba(255,255,255,0.08); margin: 0.5rem 0 1rem 0;'></div>", unsafe_allow_html=True)

        # Global Analytical Filters Expander
        with st.expander("🎛️ **ANALYTICAL SCOPE FILTERS**", expanded=False):
            default_city = st.session_state.get("global_city", "All")
            city_idx = CITIES.index(default_city) if default_city in CITIES else 0
            selected_city = st.selectbox("Market / City", CITIES, index=city_idx, key="sb_city")
            st.session_state["global_city"] = selected_city

            default_persona = st.session_state.get("global_persona", "All")
            persona_idx = PERSONAS.index(default_persona) if default_persona in PERSONAS else 0
            selected_persona = st.selectbox("Customer Segment", PERSONAS, index=persona_idx, key="sb_persona")
            st.session_state["global_persona"] = selected_persona

            default_status = st.session_state.get("global_status", "All")
            status_idx = ORDER_STATUSES.index(default_status) if default_status in ORDER_STATUSES else 0
            selected_status = st.selectbox("Order Fulfillment", ORDER_STATUSES, index=status_idx, key="sb_status")
            st.session_state["global_status"] = selected_status

        # System Telemetry & Engine Health
        quality_score, health_status, health_msg = get_data_quality_status()
        is_mysql = "MySQL" in data_source

        st.markdown(f"""
        <div style="margin-top: 1.5rem; background: rgba(17, 24, 39, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.85rem;">
            <div style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #94A3B8; margin-bottom: 0.65rem;">Platform Telemetry</div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.76rem;">
                <span style="color: #94A3B8;">Data Source:</span>
                <span style="font-weight: 600; color: {'#34D399' if is_mysql else '#60A5FA'};">{'MySQL Online' if is_mysql else 'CSV Engine'}</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.76rem;">
                <span style="color: #94A3B8;">Integrity Score:</span>
                <span style="font-weight: 700; color: #34D399;">{quality_score:.0f}% Valid</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.76rem;">
                <span style="color: #94A3B8;">Digital Twin:</span>
                <span style="font-weight: 600; color: #A78BFA;">Operational</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 1.5rem; font-size: 0.7rem; color: #64748B; text-align: center;'>NovaNest Analytics v2.0 • Clean Slate</div>", unsafe_allow_html=True)

    return {
        "city": st.session_state.get("global_city", "All"),
        "persona": st.session_state.get("global_persona", "All"),
        "status": st.session_state.get("global_status", "All")
    }
