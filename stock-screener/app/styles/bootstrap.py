"""Critical FOUC-prevention CSS (runs before any other Streamlit widget).

Why this exists:
    Streamlit renders its app shell (HTML + default theme CSS) *before* any
    Python-generated HTML hits the DOM. With base="dark" in config.toml,
    the shell is already dark, but widgets appear unstyled for a frame:
    buttons + unstyled metric containers, then ``inject_theme_css`` swaps in
    the custom palette and stretches buttons to 100% width. The user sees:
      1. Streamlit's dark shell (no custom colours yet)
      2. ~60 ms later: our palette fades in smoothly

What this module does:
    1. Defines the dark palette background as CSS variables synchronously.
    2. Paints the app shell with our palette immediately via !important.
    3. Pre-reserves min-height on buttons, metrics, tabs, inputs so the
       layout doesn't jump when inject_theme_css() adds padding/borders.
    4. Applies a 60ms fade-in so the brief gap between the Streamlit
       default theme and our custom palette is masked.
"""
from __future__ import annotations

import streamlit as st


_CRITICAL_CSS = """
<style>
/* ── Dark palette variables (always active) ──────────────────────────────── */
:root {
    --sdg-bg: #0b1622;
    --sdg-bg2: #0f2030;
    --sdg-bg3: #162840;
    --sdg-surface: #122035;
    --sdg-border: #1e3a55;
    --sdg-text: #d0e0f0;
    --sdg-text-muted: #8ba8c4;
    --sdg-accent: #00d4aa;
    --sdg-accent2: #96c93d;
}

/* Paint the app shell with our palette immediately. !important is required
   to beat Streamlit's own inline styles. */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--sdg-bg) !important;
    color: var(--sdg-text) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
    background-color: var(--sdg-bg2) !important;
    border-right: 1px solid var(--sdg-border) !important;
}

/* ── Pre-reserve min-height so layout doesn't jump ──────────────────────── */
/* When inject_theme_css() loads, metric containers gain padding/border, and
   buttons stretch to 100% width. Pre-reserving min-height avoids the
   visible layout shift. */
.stButton > button { min-height: 42px !important; }
[data-testid="metric-container"] { min-height: 72px !important; }
[data-testid="stTab"] { min-height: 36px !important; }
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input { min-height: 38px !important; }

/* ── Mask residual palette swap with a 60ms fade-in ─────────────────────────
   The app's custom CSS (inject_theme_css) is injected via st.markdown,
   which means there's a brief window where Streamlit's default dark theme
   colours are visible before our palette overrides kick in. The 60ms
   fade-in masks this gap. */
[data-testid="stAppViewContainer"] {
    animation: sdg-fade-in 60ms ease-out;
}
@keyframes sdg-fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
}
</style>
"""


def inject_critical_bootstrap() -> None:
    """Inject the critical FOUC-prevention CSS. Must run before any widget."""
    st.markdown(_CRITICAL_CSS, unsafe_allow_html=True)
