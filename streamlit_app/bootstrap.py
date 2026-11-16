"""
NovaNest Platform Bootstrap & Runtime Environment
-------------------------------------------------
Establishes standardized project-root path resolution and injects
the Obsidian & Electric Sapphire design system CSS.
"""

import sys
from pathlib import Path
import streamlit as st

# Standardized Project Root Resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "python"))
if str(PROJECT_ROOT / "streamlit_app") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "streamlit_app"))

STYLES_DIR = CURRENT_DIR / "styles"

def load_css_file(filename: str) -> str:
    """Safely reads CSS content from styles directory."""
    css_path = STYLES_DIR / filename
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def inject_theme():
    """
    Injects the clean-slate design system CSS into the active Streamlit page.
    Loaded as raw HTML <style> block with high priority.
    """
    theme_css = load_css_file("theme.css")
    components_css = load_css_file("components.css")
    animations_css = load_css_file("animations.css")

    combined_css = f"""
    <style>
    {theme_css}
    {components_css}
    {animations_css}
    </style>
    """
    st.markdown(combined_css, unsafe_allow_html=True)
