"""Sidebar fragment: user info, scanner controls, stock universe, market selector."""
from __future__ import annotations

import streamlit as st

from app.auth import do_logout
from app.scanner import load_stocks, save_stocks
from app.config import COOKIE_MARKET
from app.market import market_suffix, ticker_display


def _save_stock_universe(raw_text: str, market: str = "NSE") -> None:
    """Parse, clean, and save the stock universe for the given market."""
    tokens = [
        t.strip() for chunk in raw_text.replace("\n", ",").split(",")
        for t in [chunk.strip()] if t.strip()
    ]
    suffix = market_suffix(market)
    if market == "NSE":
        cleaned = list(dict.fromkeys(
            sym.upper() if sym.upper().endswith(".NS") else sym.upper() + ".NS"
            for sym in tokens
        ))
    else:
        # US tickers: just uppercase, no suffix
        cleaned = list(dict.fromkeys(sym.upper() for sym in tokens))

    save_stocks(cleaned, market=market)
    st.session_state.df_results = None
    st.session_state.last_scan  = None
    st.session_state.scanned    = False
    st.success(f"✅ Saved {len(cleaned)} symbols.")


def render_sidebar(cookies=None) -> None:
    """Render the sidebar with market selector. No theme toggle — dark mode is always active."""
    market = st.session_state.get("market", "NSE")

    with st.sidebar:
        st.markdown("👤 **admin**")
        if st.button("🚪 Logout", width="stretch"):
            do_logout()
            st.rerun()

        st.divider()

        # ── Market selector ──
        st.markdown("### 🌍 Market")
        new_market = st.radio(
            "Select Market",
            options=["NSE", "US"],
            index=0 if market == "NSE" else 1,
            horizontal=True,
            format_func=lambda x: "🇮🇳 NSE" if x == "NSE" else "🇺🇸 US",
            key="market_selector",
        )
        if new_market != market:
            st.session_state.market = new_market
            # Reset scan + trade state on market switch
            st.session_state.df_results      = None
            st.session_state.last_scan        = None
            st.session_state.scanned          = False
            st.session_state.trade_preview    = None
            st.session_state.portfolio_prices = {}
            # Save market preference to cookie
            if cookies is not None:
                try:
                    cookies.set(COOKIE_MARKET, new_market, max_age=365 * 24 * 3600)
                except Exception:
                    pass
            st.rerun()

        market = st.session_state.market  # update local ref

        st.divider()

        st.markdown("### 🔍 Scanner")
        my_stocks = load_stocks(market=market)
        st.markdown(f"**Universe:** {len(my_stocks)} stocks")
        st.markdown(
            "**Criteria (all 4):**\n"
            "- CMP > 30 DMA\n"
            "- CMP > 50 DMA\n"
            "- CMP > 200 DMA\n"
            "- CAR rising 10 days"
        )
        if st.session_state.last_scan:
            st.caption(f"Last run: {st.session_state.last_scan}")

        st.markdown("### 🗂️ Stock Universe")
        if market == "NSE":
            st.caption("One per line or comma-separated. `.NS` auto-added.")
        else:
            st.caption("One per line or comma-separated. US tickers (no suffix needed).")
        current_stocks = load_stocks(market=market)
        display_stocks = [ticker_display(s, market) for s in current_stocks]
        raw_text = st.text_area(
            "symbols",
            value=", ".join(display_stocks),
            height=200,
            label_visibility="collapsed",
        )
        sc, rc = st.columns(2)
        with sc:
            if st.button("💾 Save", width="stretch"):
                _save_stock_universe(raw_text, market=market)
        with rc:
            if st.button("↩️ Reload", width="stretch"):
                st.rerun()
        st.markdown(
            f'<div class="stock-badge">📋 {len(current_stocks)} symbols</div>',
            unsafe_allow_html=True,
        )
