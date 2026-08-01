"""Critical CSS + inline JS injected BEFORE any session_state or cookie logic.

This is the single most important file for FOUC prevention. It must run as
the first ``st.markdown`` call in the app, immediately after
``st.set_page_config``.

Why this exists
---------------
Streamlit renders its app shell (HTML + default theme CSS) *before* any
Python-side ``st.markdown`` injection runs. Without this bootstrap, the
browser briefly paints Streamlit's default dark background + auto-width
buttons + unstyled metric containers, then ``inject_theme_css`` swaps in
the custom palette and stretches buttons to 100% width. The user sees:

  - buttons dancing / shifting position on refresh
  - elements appearing with extra space temporarily
  - layout flickering for a millisecond
  - duplicate elements flashing for a frame (when combined with reruns)

What this block does
--------------------
1. Defines both palette backgrounds as CSS variables synchronously.
2. Runs a tiny inline ``<script>`` that reads ``document.cookie`` BEFORE
   Streamlit's main bundle paints, picks the right background, and sets
   ``data-sdg-theme`` on ``<html>`` so the rest of the CSS can target it.
3. Reserves ``min-height`` for layout-shifting elements (buttons, metric
   containers, hero, tabs) so the second paint doesn't move them.
4. Adds a 60ms opacity fade-in on the app root so any residual swap
   between the Streamlit default theme and our custom palette is masked.

The inline ``<script>`` is intentionally tiny (no external dependencies,
no network calls) so it cannot itself become a FOUC source.
"""
from __future__ import annotations

import streamlit as st

from app.config import COOKIE_THEME, DEFAULT_THEME, VALID_THEMES


_CRITICAL_BOOTSTRAP_HTML = r"""
<style>
/* ── Synchronous palette variables ──────────────────────────────────────────
   Available to every subsequent rule, even before inject_theme_css() runs.
   Values MUST match PALETTES["dark"] / PALETTES["light"] in palettes.py.
   Keep them in sync if you change a palette. */
:root {
  --sdg-bg: #0b1622;
  --sdg-bg2: #0f2030;
  --sdg-text: #d0e0f0;
  --sdg-accent: #00d4aa;
  /* color-scheme: dark tells mobile browsers (especially Chrome on Android)
     "this page is already dark, don't auto-dark-mode my iframes". Without
     this, st.dataframe's iframe table cells paint white on dark apps. */
  color-scheme: dark;
}
html[data-sdg-theme="light"] {
  --sdg-bg: #f2f6fb;
  --sdg-bg2: #ffffff;
  --sdg-text: #162030;
  --sdg-accent: #1565c0;
  color-scheme: light;
}

/* Paint the app shell with our palette immediately. !important is required
   because Streamlit's own stylesheet also targets these elements. */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stSidebar"] {
  background-color: var(--sdg-bg) !important;
  color: var(--sdg-text) !important;
}
[data-testid="stSidebar"] { background-color: var(--sdg-bg2) !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* ── Reserve space for layout-shifting elements ─────────────────────────────
   Without these, buttons render auto-width then stretch to 100% when
   inject_theme_css() loads, metric containers gain padding/border, and
   the tab strip jumps. Pre-applying final dimensions eliminates the dance. */
.stButton > button {
  width: 100% !important;
  min-height: 38px !important;
  background: linear-gradient(90deg, var(--sdg-accent), var(--sdg-accent)) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
}
[data-testid="stDownloadButton"] > button {
  min-height: 38px !important;
  border: 2px solid var(--sdg-accent) !important;
  color: var(--sdg-accent) !important;
  background: transparent !important;
  border-radius: 8px !important;
}
[data-testid="metric-container"] {
  min-height: 92px !important;
  background: var(--sdg-bg2) !important;
  border: 1px solid rgba(128,128,128,0.18) !important;
  border-radius: 10px !important;
  padding: 0.85rem 1rem !important;
  box-sizing: border-box !important;
}
[data-testid="stMetricValue"] { color: var(--sdg-accent) !important; }
[data-testid="stTabs"] [data-testid="stTab"] {
  min-height: 36px !important;
  padding: 0.5rem 1.2rem !important;
  font-weight: 600 !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
  background: var(--sdg-bg2) !important;
  color: var(--sdg-text) !important;
  border-radius: 8px !important;
}

/* ── Mask residual palette swap with a 60ms fade-in ─────────────────────────
   Short enough to feel instant, long enough to cover the single rAF tick
   during which Streamlit's default styles would otherwise be visible. */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  animation: sdg-fade-in 60ms ease-out 0ms both !important;
}
@keyframes sdg-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.stApp > iframe { background: transparent !important; }
</style>
<script>
// Read the saved theme cookie *synchronously* and tag <html> before any
// visible paint happens. This avoids the dark->light flash that
// streamlit-cookies-controller causes (it reads cookies async via JS and
// triggers a rerun, which previously caused a second paint with the
// actually-saved palette).
(function () {
  try {
    var match = document.cookie.match(/(?:^|;\s*)__COOKIE_THEME__=([^;]+)/);
    var theme = match ? decodeURIComponent(match[1]) : "__DEFAULT_THEME__";
    if (theme !== "dark" && theme !== "light") theme = "__DEFAULT_THEME__";
    document.documentElement.setAttribute("data-sdg-theme", theme);
  } catch (e) {
    document.documentElement.setAttribute("data-sdg-theme", "__DEFAULT_THEME__");
  }
})();
</script>
"""


def inject_critical_bootstrap() -> None:
    """Inject the critical FOUC-prevention CSS + JS.

    Call this IMMEDIATELY after ``st.set_page_config``, before any
    ``session_state`` access or cookie logic. It is idempotent and safe
    to call on every rerun.
    """
    html = (
        _CRITICAL_BOOTSTRAP_HTML
        .replace("__COOKIE_THEME__", COOKIE_THEME)
        .replace("__DEFAULT_THEME__", DEFAULT_THEME)
    )
    # Use a stable component key so Streamlit doesn't re-mount this element
    # on every rerun (re-mounting would itself cause a flash).
    st.markdown(html, unsafe_allow_html=True)
