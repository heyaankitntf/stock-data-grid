"""Sidebar fragment: user info, scanner controls, stock universe."""
from __future__ import annotations

import streamlit as st

from app.auth import do_logout
from app.scanner import load_stocks, save_stocks


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


def render_sidebar() -> None:
    """Render the sidebar. No theme toggle — dark mode is always active."""
    with st.sidebar:
        st.markdown("👤 **admin**")
        if st.button("🚪 Logout", width="stretch"):
            do_logout()
            st.rerun()

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
