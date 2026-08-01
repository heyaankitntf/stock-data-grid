"""Reusable UI fragments (sidebar, hero, scanner tab, trading tab).

Each fragment is a self-contained function that takes its data as arguments
and renders via Streamlit. Fragments are wrapped in ``st.fragment`` where
appropriate so that local interactions (button clicks) only re-run the
fragment, not the whole script — this eliminates the duplicate-render
flash that occurs when a long-running operation triggers a full rerun.
"""
from app.components.sidebar import render_sidebar
from app.components.hero import render_hero
from app.components.scanner_tab import render_scanner_tab
from app.components.trading_tab import render_trading_tab

__all__ = [
    "render_hero",
    "render_scanner_tab",
    "render_sidebar",
    "render_trading_tab",
]
