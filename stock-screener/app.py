"""CAR + DMA Super Breakout Scanner — Streamlit entry point.

Run with:
    streamlit run app.py

Architecture (industry-standard modular layout):
    app.py                      ← thin entry point (this file)
    app/
        __init__.py
        config/
            __init__.py
            settings.py         ← paths, constants, env
        styles/
            __init__.py
            palettes.py         ← dark-only colour palette
            bootstrap.py        ← CRITICAL FOUC-prevention CSS (runs first)
            css.py              ← decorative dark CSS
        auth/
            __init__.py
            session.py          ← file-based session token
            cookies.py          ← CookieController singleton
            login.py            ← login form + do_login/do_logout
        market.py               ← market context helpers (currency, suffix, index)
        portfolio/
            __init__.py
            store.py            ← JSON-backed portfolio + holdings calc
            trades.py           ← execute_trade()
        scanner/
            __init__.py
            universe.py         ← settings.json / us_stocks.json stock list
            engine.py           ← yfinance scan + sequential runner
            styling.py          ← dataframe colour-banding
        trading/
            __init__.py
            prices.py           ← fetch_cmp_single / fetch_cmp_bulk
        components/
            __init__.py
            sidebar.py          ← sidebar fragment
            hero.py             ← hero banner fragment
            scanner_tab.py      ← scanner tab fragment (st.fragment-wrapped)
            trading_tab.py      ← trading tab fragment

The app uses a single dark palette — no theme toggle. Streamlit's base
theme is forced to dark via .streamlit/config.toml so the UI is always
dark regardless of the OS/browser system theme.
"""
from __future__ import annotations

import logging
import warnings

import streamlit as st

# ── Silence noisy loggers (must run before any yfinance import) ──────────────
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

# ── Page config MUST be the first Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="CAR + DMA Breakout Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 1. Critical FOUC bootstrap (dark palette CSS vars) ───────────────────────
from app.styles import inject_critical_bootstrap, inject_theme_css, get_palette
from app.auth import is_authenticated, render_login_page, do_logout, get_cookie_controller

inject_critical_bootstrap()

# ── 2. Dark palette (always) ────────────────────────────────────────────────
P = get_palette()
inject_theme_css(P)


# ── 3. Auth gate ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = is_authenticated()

if not st.session_state.authenticated:
    render_login_page(P)


# ── 4. Session state defaults ────────────────────────────────────────────────
for k, v in [("df_results", None), ("last_scan", None), ("scanned", False),
             ("trade_preview", None), ("portfolio_prices", {})]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── 5. Market state management ──────────────────────────────────────────────
from app.config import COOKIE_MARKET
from app.market import market_currency

cookies = get_cookie_controller()

if "market" not in st.session_state:
    try:
        saved_market = cookies.get(COOKIE_MARKET)
    except Exception:
        saved_market = None
    st.session_state.market = saved_market if saved_market in ("NSE", "US") else "NSE"

MARKET = st.session_state.market


# ── 6. Sidebar ───────────────────────────────────────────────────────────────
from app.components import render_sidebar, render_hero, render_scanner_tab, render_trading_tab

render_sidebar(cookies=cookies)


# ── 7. Main content: hero + tabs ─────────────────────────────────────────────
render_hero(market=MARKET)

tab_scanner, tab_trading = st.tabs(["📊 Scanner", "💼 Mock Trading"])

with tab_scanner:
    render_scanner_tab(P, market=MARKET)

with tab_trading:
    render_trading_tab(P, market=MARKET)


# ── 8. Footer ────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">Data via Yahoo Finance · Mock trading only · Not financial advice · Educational use</div>',
    unsafe_allow_html=True,
)
