"""Full decorative stylesheet for the dark-only palette.

Critical layout-stabilising CSS (body background, button min-height, metric
container padding, etc.) is already applied by ``bootstrap.py`` which runs
*before* this function. This module adds the decorative styles
(gradients, borders, colours) that are safe to apply slightly later because
they don't change element dimensions.
"""
from __future__ import annotations

import streamlit as st

from app.styles.palettes import Palette


_CSS_TEMPLATE = """
<style>
/* ── Force dark color-scheme on everything ──────────────────────────────── */
/* Prevents browsers from applying light-mode heuristics to iframes,
   especially Chrome on Android which auto-dark-modes unstyled content. */
:root, html, body {{
    color-scheme: dark !important;
}}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background-color: {bg} !important; color: {text} !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebar"] {{
    background-color: {bg2} !important;
    border-right: 1px solid {border} !important;
}}
.block-container {{
    padding: 1.5rem 2rem 2rem !important; max-width: 1440px !important;
}}
@media (max-width: 768px) {{
    .block-container {{ padding: 1rem 0.75rem 1.5rem !important; }}
    [data-testid="stSidebar"] {{ width: 88vw !important; min-width: unset !important; }}
}}

/* ── Hero ── */
.hero {{
    background: linear-gradient(135deg,{hero_a} 0%,{hero_b} 50%,{hero_c} 100%);
    border-radius: 14px; padding: 1.6rem 2rem; margin-bottom: 1.2rem;
    min-height: 96px;
}}
.hero h1 {{ font-size:1.7rem; font-weight:800; margin:0 0 .3rem; color:#fff; letter-spacing:-.4px; }}
.hero p  {{ font-size:.85rem; opacity:.82; margin:0; color:#e8f4ff; }}
@media (max-width:600px) {{
    .hero {{ padding:1.1rem 1rem; border-radius:10px; }}
    .hero h1 {{ font-size:1.15rem; }}
    .hero p  {{ font-size:.76rem; }}
}}

/* ── Tabs ── */
[data-testid="stTabs"] [data-testid="stTab"] {{
    font-weight: 600 !important; font-size: .92rem !important;
    padding: .5rem 1.2rem !important; border-radius: 8px 8px 0 0 !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {accent} !important;
    border-bottom: 2px solid {accent} !important;
}}
[data-testid="stTabContent"] {{ padding-top: 1.2rem !important; }}

/* ── Metrics ── */
[data-testid="stMetricLabel"]  {{ color:{text_muted} !important; font-size:.78rem !important; }}
[data-testid="stMetricValue"]  {{ color:{metric_val} !important; font-size:1.3rem !important; }}
[data-testid="metric-container"] {{
    background:{surface}; border:1px solid {border};
    border-radius:10px; padding:.85rem 1rem !important;
}}
@media (max-width:640px) {{
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        min-width:46% !important; flex:1 1 46% !important;
    }}
    [data-testid="stMetricValue"] {{ font-size:1rem !important; }}
}}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(90deg,{accent},{accent2}) !important;
    color:{btn_text} !important; font-weight:700 !important;
    border:none !important; border-radius:8px !important; width:100%;
}}
.stButton > button:hover {{ filter:brightness(1.1); }}
[data-testid="stDownloadButton"] > button {{
    background:transparent !important; border:2px solid {accent} !important;
    color:{accent} !important; font-weight:600 !important;
}}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    background:{input_bg} !important; border:1px solid {input_border} !important;
    color:{text} !important; border-radius:8px !important;
}}
[data-baseweb="select"] > div {{
    background:{input_bg} !important; border-color:{input_border} !important;
    color:{text} !important;
}}
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stRadio"] label  {{ color:{text} !important; }}
[data-testid="stCheckbox"] label {{ color:{text} !important; }}

/* ── Progress ── */
.stProgress > div > div {{
    background: linear-gradient(90deg,{accent},{accent2}) !important;
}}

/* ── Trade card ── */
.trade-card {{
    background:{surface}; border:1px solid {border};
    border-radius:12px; padding:1.2rem 1.4rem; margin-bottom:1rem;
}}
.trade-card h4 {{ margin:0 0 .8rem; font-size:1rem; color:{text}; font-weight:700; }}

/* ── P&L badge ── */
.pnl-profit {{
    display:inline-block; background:{profit_bg}; color:{profit_fg};
    border-radius:6px; padding:2px 10px; font-weight:700; font-size:.85rem;
}}
.pnl-loss {{
    display:inline-block; background:{loss_bg}; color:{loss_fg};
    border-radius:6px; padding:2px 10px; font-weight:700; font-size:.85rem;
}}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {{ border-radius:10px; overflow:hidden; }}
@media (max-width:768px) {{
    [data-testid="stDataFrame"] > div {{ overflow-x:auto !important; }}
}}
/* Force dark theme on ALL dataframe iframes so the table grid never
   shows white/light backgrounds regardless of system theme. */
[data-testid="stDataFrame"] iframe {{
    background-color: {bg2} !important;
}}
[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
    background-color: {bg2} !important;
}}
/* Target the inner scrollable container of the dataframe */
[data-testid="stDataFrame"] .stDataFrame {{
    background-color: {bg2} !important;
}}

/* ── Dividers ── */
hr,
[data-testid="stDivider"] {{
    border-color:{accent} !important; opacity:.6;
}}
[data-testid="stDivider"] > div {{
    background-color:{accent} !important;
    border-top-color:{accent} !important;
}}
/* Override Streamlit's default red selection indicator (rgb(255,75,75))
   to match the theme accent green. */
[class*="st-emotion-cache"][data-selected] .react-aria-SelectionIndicator {{
    background-color:{accent} !important;
}}

/* ── Misc ── */
[data-testid="stAlert"] {{
    border-radius:10px !important; background:{bg3} !important;
    border-color:{border} !important; color:{text} !important;
}}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong {{ color:{text} !important; }}
[data-testid="stCaptionContainer"] {{ color:{text_muted} !important; }}
.stock-badge {{
    display:inline-block; background:{badge_bg}; color:{badge_fg};
    border-radius:6px; padding:3px 12px; font-size:.82rem; font-weight:600;
}}
.footer {{
    text-align:center; color:{text_faint}; font-size:.75rem;
    margin-top:2.5rem; padding-top:1rem; border-top:1px solid {footer_border};
}}
[data-testid="stRadio"] label {{ color:{text} !important; }}

/* ── Index widget ── */
.index-widget {{
    display:flex; flex-direction:column; align-items:flex-end;
    justify-content:center; min-width:160px;
}}
.index-widget .idx-name {{
    font-size:.72rem; font-weight:700; letter-spacing:.8px;
    color:rgba(255,255,255,.55); text-transform:uppercase; margin-bottom:.15rem;
}}
.index-widget .idx-price {{
    font-size:1.35rem; font-weight:800; color:#fff; line-height:1.1;
}}
.index-widget .idx-change-up {{
    font-size:.82rem; font-weight:700; color:#00e87a;
    background:rgba(0,232,122,.12); border-radius:5px;
    padding:2px 8px; margin-top:.2rem; display:inline-block;
}}
.index-widget .idx-change-dn {{
    font-size:.82rem; font-weight:700; color:#ff6b6b;
    background:rgba(255,107,107,.12); border-radius:5px;
    padding:2px 8px; margin-top:.2rem; display:inline-block;
}}
@media (max-width:600px) {{
    .index-widget {{ align-items:flex-start; margin-top:.6rem; }}
    .index-widget .idx-price {{ font-size:1.05rem; }}
}}

/* ── Market pill ── */
.market-pill-nse {{
    display:inline-block; background:#0d3322; color:#00d464;
    border-radius:20px; padding:3px 14px; font-size:.82rem; font-weight:700;
    letter-spacing:.5px;
}}
.market-pill-us {{
    display:inline-block; background:#0d1f3c; color:#4db8ff;
    border-radius:20px; padding:3px 14px; font-size:.82rem; font-weight:700;
    letter-spacing:.5px;
}}
</style>
"""


def inject_theme_css(p: Palette) -> None:
    """Inject the dark-only stylesheet. Safe to call on every rerun."""
    st.markdown(
        _CSS_TEMPLATE.format(**p),
        unsafe_allow_html=True,
    )
