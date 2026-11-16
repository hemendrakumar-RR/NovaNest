"""
NovaNest Standardized Chart Components
--------------------------------------
Generates unified Plotly visualizations matching the official NovaNest Enterprise design system.
"""

from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

COLOR_PALETTE = ["#2563EB", "#F97316", "#0EA5E9", "#16A34A", "#F59E0B", "#DC2626", "#8B5CF6", "#64748B"]

def style_figure(fig: go.Figure, height: int = 380) -> go.Figure:
    """Applies the official NovaNest Enterprise design system styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1E293B", size=12),
        margin=dict(l=16, r=16, t=44, b=16),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#475569"),
            bgcolor="rgba(0,0,0,0)"
        ),
        title=dict(
            font=dict(size=14, color="#1E293B", weight=700),
            x=0.01,
            y=0.96
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#E2E8F0",
        linecolor="#CBD5E1",
        zeroline=False,
        tickfont=dict(color="#64748B")
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#E2E8F0",
        linecolor="#CBD5E1",
        zeroline=False,
        tickfont=dict(color="#64748B")
    )
    return fig

def render_line_chart(df: pd.DataFrame, x: str, y: str, title: str, color: Optional[str] = None, height: int = 360):
    """Renders a smooth time-series or trend line chart."""
    if df.empty:
        st.info("No data available to display chart.")
        return
    fig = px.line(df, x=x, y=y, color=color, title=title, color_discrete_sequence=COLOR_PALETTE)
    fig.update_traces(line=dict(width=2.5))
    fig = style_figure(fig, height=height)
    st.plotly_chart(fig, width="stretch")

def render_bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: Optional[str] = None, horizontal: bool = False, height: int = 360):
    """Renders a modern bar chart."""
    if df.empty:
        st.info("No data available to display chart.")
        return
    orientation = "h" if horizontal else "v"
    fig = px.bar(df, x=x, y=y, color=color, title=title, orientation=orientation, color_discrete_sequence=COLOR_PALETTE)
    fig.update_traces(marker_line_width=0, opacity=0.9)
    fig = style_figure(fig, height=height)
    st.plotly_chart(fig, width="stretch")

def render_donut_chart(df: pd.DataFrame, names: str, values: str, title: str, height: int = 340):
    """Renders a sleek donut distribution chart."""
    if df.empty:
        st.info("No data available to display chart.")
        return
    fig = px.pie(df, names=names, values=values, title=title, hole=0.6, color_discrete_sequence=COLOR_PALETTE)
    fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#0B0F17", width=2)))
    fig = style_figure(fig, height=height)
    st.plotly_chart(fig, width="stretch")

def render_scatter_chart(df: pd.DataFrame, x: str, y: str, title: str, color: Optional[str] = None, size: Optional[str] = None, height: int = 380):
    """Renders an analytical scatter plot with hover diagnostics."""
    if df.empty:
        st.info("No data available to display chart.")
        return
    fig = px.scatter(df, x=x, y=y, color=color, size=size, title=title, color_discrete_sequence=COLOR_PALETTE, opacity=0.75)
    fig = style_figure(fig, height=height)
    st.plotly_chart(fig, width="stretch")
