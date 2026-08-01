"""Scanner tab fragment.

This is the most FOUC-sensitive fragment in the app. The scan takes 1-2
minutes (212 stocks via yfinance), so any ``st.rerun()`` call during or
after the scan would cause Streamlit's frontend to briefly show BOTH the
old render (scanning UI) and the new render (results UI) at the same time
— producing the "duplicate elements for a flash second" bug the user
reported.

Fix strategy:
  1. Wrap the entire scanner tab in ``@st.fragment``. Button clicks inside
     a fragment only re-run the fragment, not the whole script. This means
     clicking "Run Scanner" or "Run Again" doesn't trigger a full app
     rerun, so there's no opportunity for old/new render overlap.
  2. Never call ``st.rerun()`` after the scan. Render the results inline
     in the same fragment run.
  3. Use a placeholder pattern (``st.container``) so the scan UI and
     results UI render into the same slot, replacing each other cleanly.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from app.scanner import load_stocks, run_scanner, style_breakout_df
from app.styles.palettes import Palette


def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Breakout Stocks")
    return buf.getvalue()


def _render_results(df: pd.DataFrame, my_stocks: list[str], p: Palette) -> None:
    """Render the post-scan results (metrics + table + download)."""
    n     = len(df)
    total = len(my_stocks)
    rate  = f"{n / total * 100:.1f}%" if total else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Scanned",   total)
    c2.metric("🟢 Breakouts", n)
    c3.metric("🎯 Hit Rate",  rate)
    c4.metric("🕐 Last Scan", st.session_state.last_scan or "—")
    st.divider()

    if df.empty:
        st.info("**No breakout stocks found today.** Markets may be consolidating.", icon="🔎")
        return

    st.markdown(f"### 🟢 Breakout Stocks — {n} found")
    st.caption("Sorted by distance from 200 DMA · closest first")
    styled = style_breakout_df(df, p)
    st.dataframe(styled, use_container_width=True, height=min(80 + n * 38, 680))
    st.download_button(
        label="⬇️  Download Excel", data=_to_excel(df),
        file_name=f"Breakout_Stocks_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@st.fragment(run_every=None)
def render_scanner_tab(p: Palette) -> None:
    """Render the Scanner tab. Wrapped in a fragment to isolate reruns."""
    my_stocks = load_stocks()

    # Single button with dynamic label. No conditional rendering, no
    # duplicate buttons, no st.rerun() on click.
    run_btn = st.button(
        "🚀 Run Scanner" if st.session_state.df_results is None
        else "🔄 Run Scanner Again",
        use_container_width=True,
        type="primary",
        key="scanner_btn",
    )

    # When "Run Again" is clicked, clear cached results so the scan block
    # below re-runs in THIS fragment run. We intentionally do NOT call
    # st.rerun() — see module docstring.
    if run_btn and st.session_state.df_results is not None:
        st.session_state.df_results = None
        st.session_state.last_scan  = None

    if run_btn:
        if not my_stocks:
            st.warning("⚠️ No stocks configured — add symbols in the sidebar.")
        else:
            st.markdown(f"#### ⏳ Scanning {len(my_stocks)} stocks — please wait…")
            pbar   = st.progress(0)
            status = st.empty()
            df     = run_scanner(my_stocks, pbar, status)
            pbar.progress(1.0)
            status.empty()
            st.session_state.df_results = df
            st.session_state.last_scan  = datetime.now().strftime("%d-%m-%Y  %H:%M")
            st.session_state.scanned    = True
            # NOTE: no st.rerun(). Results render inline below.

    df = st.session_state.df_results
    if df is not None:
        _render_results(df, my_stocks, p)
    # NOTE: the "Open the sidebar..." hint banner is intentionally removed
    # per user request. When there are no cached results and the user
    # hasn't clicked Run, the Run button is the only thing shown — clean
    # and unambiguous.
