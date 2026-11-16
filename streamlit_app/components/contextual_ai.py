"""
NovaNest Contextual AI Components for Streamlit Dashboards
---------------------------------------------------------
Enables launching multi-agent AI analysis directly from any Streamlit
KPI card, chart, or data table row while preserving structured context.

Provides architectural parity with the React `ContextualAIButton` and `ContextualAIAction`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st

from utils.api_client import get_streamlit_ai_client, ApiClientError
from components.telemetry_components import render_agent_telemetry_card


def build_contextual_payload(
    dashboard_name: str,
    kpi_or_chart_id: str,
    selected_metric: str,
    metric_value: Optional[Any] = None,
    active_filters: Optional[Dict[str, Any]] = None,
    city: Optional[str] = None,
    date_range: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    entity_name: Optional[str] = None,
    source_component: Optional[str] = None,
    suggested_prompt: Optional[str] = None,
    auto_submit: bool = True,
) -> Dict[str, Any]:
    """
    Constructs a standardized contextual AI payload matching the React contract.
    Strictly adheres to the Untrusted Client Metric Principle:
    metric_value is included only for display/logging, never trusted for calculation.
    """
    prompt = suggested_prompt
    if not prompt:
        territory = f" in {city}" if city and city != "All" else ""
        if entity_name:
            prompt = f"Analyze performance and risk drivers for {entity_name}{territory}."
        elif selected_metric:
            prompt = f"Analyze {selected_metric}{territory} and explain the underlying performance drivers."
        else:
            prompt = f"Analyze business performance{territory}."

    return {
        "dashboard_name": str(dashboard_name)[:100],
        "kpi_or_chart_id": str(kpi_or_chart_id)[:100],
        "selected_metric": str(selected_metric)[:100],
        "metric_value": metric_value,
        "active_filters": active_filters or {},
        "city": str(city)[:100] if city else None,
        "date_range": str(date_range)[:100] if date_range else None,
        "entity_type": str(entity_type)[:32] if entity_type else None,
        "entity_id": str(entity_id)[:64] if entity_id else None,
        "entity_name": str(entity_name)[:100] if entity_name else None,
        "source_component": str(source_component)[:100] if source_component else "streamlit_dashboard",
        "suggested_prompt": prompt,
        "auto_submit": bool(auto_submit),
    }


def render_contextual_ai_button(
    payload: Dict[str, Any],
    key: str,
    label: str = "✨ Ask AI",
    help_text: str = "Launch NovaNest Multi-Agent AI analysis with this context",
    use_container_width: bool = False,
    width: Optional[str] = None,
) -> bool:
    """
    Renders an interactive contextual AI launcher button.
    When clicked, preloads the structured context and navigates to Ask NovaNest.
    """
    btn_width = width if width is not None else ("stretch" if use_container_width else "content")
    clicked = st.button(
        label,
        key=key,
        help=help_text,
        width=btn_width,
    )
    if clicked:
        st.session_state["contextual_ai_preloaded"] = payload
        st.session_state["ask_novanest_preloaded_prompt"] = payload.get("suggested_prompt")
        st.session_state["ask_novanest_auto_submit"] = payload.get("auto_submit", True)
        try:
            st.switch_page("pages/07_Ask_NovaNest.py")
        except Exception:
            # Fallback for environments where switch_page is not available (e.g. non-interactive tests)
            st.session_state["active_page"] = "pages/07_Ask_NovaNest.py"
    return clicked


def render_contextual_ai_inline(
    payload: Dict[str, Any],
    key: str,
    label: str = "✨ Quick AI Analysis",
) -> None:
    """
    Renders an inline expandable analysis card directly inside the dashboard.
    Enables users to run in-place multi-agent analysis without leaving the view.
    """
    metric_label = payload.get("selected_metric", "Metric")
    with st.expander(f"✨ Quick AI Analysis: {metric_label}", expanded=False):
        prompt = payload.get("suggested_prompt", f"Analyze {metric_label}")
        st.markdown(f"**Target Inquiry:** *\"{prompt}\"*")

        col1, col2 = st.columns([2, 1])
        with col1:
            run_btn = st.button("Run Multi-Agent Analysis", key=f"btn_run_{key}")
        with col2:
            if st.button("Open in Ask NovaNest →", key=f"btn_open_{key}"):
                st.session_state["contextual_ai_preloaded"] = payload
                st.session_state["ask_novanest_preloaded_prompt"] = prompt
                st.session_state["ask_novanest_auto_submit"] = True
                try:
                    st.switch_page("pages/07_Ask_NovaNest.py")
                except Exception:
                    st.session_state["active_page"] = "pages/07_Ask_NovaNest.py"

        if run_btn:
            client = get_streamlit_ai_client()
            session_id = st.session_state.get("ask_novanest_session_id", "st_inline_session")
            with st.spinner("Executing MasterOrchestrator across domain intelligence agents..."):
                try:
                    resp = client.ask_ai(
                        question=prompt,
                        session_id=session_id,
                        city_filter=payload.get("city"),
                        filters=payload.get("active_filters"),
                        contextual_data=payload,
                    )
                    render_agent_telemetry_card(
                        telemetry=resp.get("telemetry"),
                        verification_outcome=resp.get("verification_outcome", "verified"),
                        request_id=resp.get("request_id"),
                    )
                    st.markdown(resp.get("answer", ""))
                except ApiClientError as err:
                    st.error(f"Analysis failed: {err.message}")
                except Exception as exc:
                    st.error(f"Unexpected error: {str(exc)}")

