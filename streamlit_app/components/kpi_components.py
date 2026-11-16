"""
NovaNest High-Legibility KPI Components
---------------------------------------
Renders crisp enterprise metric cards with accent top borders,
micro-badges, trend pills, and formatted values.
"""

from typing import List, Dict, Any, Optional
import streamlit as st

def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    delta: Optional[str] = None,
    delta_positive: Optional[bool] = None,
    accent: str = "blue"
):
    """
    Renders a single high-legibility KPI card.
    accents: 'blue', 'emerald', 'amber', 'crimson', 'violet', 'cyan'
    """
    pill_html = ""
    if delta:
        if delta_positive is True:
            pill_class = "positive"
            arrow = "▲"
        elif delta_positive is False:
            pill_class = "negative"
            arrow = "▼"
        else:
            pill_class = "neutral"
            arrow = "•"
        pill_html = f'<span class="nn-kpi-pill {pill_class}">{arrow} {delta}</span>'

    card_html = f"""
    <div class="nn-kpi-card accent-{accent}">
        <div class="nn-kpi-header">
            <span class="nn-kpi-label">{label}</span>
            {pill_html}
        </div>
        <div class="nn-kpi-value">{value}</div>
        <div class="nn-kpi-sub">{subtext}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_kpi_row(cards: List[Dict[str, Any]]):
    """
    Renders an evenly spaced row of KPI metric cards.
    Each item in cards should be a dict with keys:
    label, value, and optionally subtext, delta, delta_positive, accent, ai_payload
    """
    n = len(cards)
    if n == 0:
        return
    cols = st.columns(n)
    for idx, (col, card) in enumerate(zip(cols, cards)):
        with col:
            render_kpi_card(
                label=card.get("label", ""),
                value=card.get("value", ""),
                subtext=card.get("subtext", ""),
                delta=card.get("delta"),
                delta_positive=card.get("delta_positive"),
                accent=card.get("accent", "blue")
            )
            ai_payload = card.get("ai_payload")
            if ai_payload and isinstance(ai_payload, dict):
                from components.contextual_ai import render_contextual_ai_button
                clean_key = f"kpi_ai_{idx}_{card.get('label', 'metric').lower().replace(' ', '_')}"
                render_contextual_ai_button(
                    payload=ai_payload,
                    key=clean_key,
                    label="✨ Ask AI",
                    width="stretch",
                )
