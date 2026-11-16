"""
NovaNest Strategic Insight & Decision Components
------------------------------------------------
Renders actionable Next-Best-Action cards with real approval workflows
and strategic insight summaries.
"""

from typing import List, Optional
import streamlit as st

def render_action_card(
    target: str,
    title: str,
    condition: str,
    recommended_action: str,
    reason: str,
    priority: str = "High",
    action_id: str = "act_1"
):
    """
    Renders an action card with an actual Streamlit interactive button.
    Supports approval / dispatch states via st.session_state.
    """
    state_key = f"action_approved_{action_id}"
    is_approved = st.session_state.get(state_key, False)

    priority_lower = priority.lower()
    if "high" in priority_lower or "critical" in priority_lower:
        pill_class = "high"
    elif "medium" in priority_lower:
        pill_class = "medium"
    else:
        pill_class = "low"

    card_html = f"""
    <div class="nn-action-card">
        <div class="nn-action-header">
            <span class="nn-action-target">{target}</span>
            <span class="nn-priority-pill {pill_class}">{priority} Priority</span>
        </div>
        <div class="nn-action-title">{title}</div>
        <div class="nn-action-desc">
            <strong style="color: #94A3B8;">Condition:</strong> {condition}<br>
            <strong style="color: #94A3B8;">Rationale:</strong> {reason}
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); padding: 0.65rem 0.85rem; border-radius: 6px; font-size: 0.82rem; margin-bottom: 0.75rem;">
            <span style="color: #60A5FA; font-weight: 700;">Proposed Action:</span>
            <span style="color: #F8FAFC;"> {recommended_action}</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        if is_approved:
            st.button(f"✓ Approved", key=f"btn_{action_id}", disabled=True)
        else:
            if st.button("Authorize Action", key=f"btn_{action_id}"):
                st.session_state[state_key] = True
                st.rerun()
    with col2:
        if is_approved:
            st.caption("⚡ Intervention dispatched to execution queue.")
        else:
            st.caption("Requires executive authorization before execution.")

def render_insight_summary(title: str, points: List[str], category: str = "AI STRATEGIC VERDICT"):
    """Renders a structured executive AI verdict."""
    bullets_html = "".join([f"<li style='margin-bottom: 0.45rem; color: #CBD5E1;'>{p}</li>" for p in points])
    verdict_html = f"""
    <div style="background: var(--nn-bg-card); border: 1px solid var(--nn-border); border-left: 4px solid var(--nn-accent-blue); border-radius: var(--nn-radius-md); padding: 1.25rem; margin-bottom: 1.25rem;">
        <div style="font-size: 0.72rem; font-weight: 700; color: #60A5FA; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.35rem;">{category}</div>
        <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.65rem;">{title}</div>
        <ul style="padding-left: 1.25rem; margin: 0; font-size: 0.85rem; line-height: 1.5;">
            {bullets_html}
        </ul>
    </div>
    """
    st.markdown(verdict_html, unsafe_allow_html=True)
