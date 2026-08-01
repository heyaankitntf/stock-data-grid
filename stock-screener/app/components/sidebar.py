"""Sidebar fragment: user info, scanner controls, theme toggle, stock universe."""
from __future__ import annotations

import streamlit as st

from app.auth import do_logout
from app.config import COOKIE_THEME
from app.scanner import load_stocks, save_stocks
from app.styles.palettes import PALETTES


def _save_stock_universe(raw_text: str) -> None:
    tokens = [
        t.strip() for chunk in raw_text.replace("\n", ",").split(",")
        for t in [chunk.strip()] if t.strip()
    ]
    cleaned = list(dict.fromkeys(
        sym.upper() if sym.upper().endswith(".NS") else sym.upper() + ".NS"
        for sym in tokens
    ))
    save_stocks(cleaned)
    st.session_state.df_results = None
    st.session_state.last_scan  = None
    st.session_state.scanned    = False
    st.success(f"✅ Saved {len(cleaned)} symbols.")


def render_sidebar() -> str:
    """Render the sidebar. Returns the current theme name.

    The theme toggle is the only sidebar control that calls ``st.rerun()``
    — and it does so only when the theme actually changes. All other
    interactions (save stocks, reload) are handled inline without rerun
    to avoid the duplicate-render flash.
    """
    p = PALETTES[st.session_state.theme]

    with st.sidebar:
        st.markdown("👤 **admin**")
        if st.button("🚪 Logout", width="stretch"):
            do_logout()
            st.rerun()

        st.divider()

        st.markdown("### 🔍 Scanner")
        my_stocks = load_stocks()
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

        st.divider()

        st.markdown("### 🎨 Appearance")
        chosen_theme = st.radio(
            "Theme", options=["dark", "light"],
            format_func=lambda x: PALETTES[x]["label"],
            index=0 if st.session_state.theme == "dark" else 1,
            horizontal=True, label_visibility="collapsed",
        )
        if chosen_theme != st.session_state.theme:
            st.session_state.theme = chosen_theme
            try:
                from app.auth import get_cookie_controller
                get_cookie_controller().set(COOKIE_THEME, chosen_theme, max_age=365 * 24 * 3600)
            except Exception:
                pass
            st.rerun()

        st.divider()

        st.markdown("### 🗂️ Stock Universe")
        st.caption("One per line or comma-separated. `.NS` auto-added.")
        current_stocks = load_stocks()
        raw_text = st.text_area(
            "symbols",
            value=", ".join(current_stocks),
            height=200,
            label_visibility="collapsed",
        )
        sc, rc = st.columns(2)
        with sc:
            if st.button("💾 Save", width="stretch"):
                _save_stock_universe(raw_text)
        with rc:
            if st.button("↩️ Reload", width="stretch"):
                st.rerun()
        st.markdown(
            f'<div class="stock-badge">📋 {len(current_stocks)} symbols</div>',
            unsafe_allow_html=True,
        )

    return st.session_state.theme
