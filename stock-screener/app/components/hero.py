"""Hero banner fragment with live index widget + market pill."""
from __future__ import annotations

import streamlit as st

from app.market import fetch_index, market_currency


def render_hero(market: str = "NSE") -> None:
    """Render the gradient hero banner with market pill and live index widget."""
    cur = market_currency(market)
    market_label = "NSE" if market == "NSE" else "US Markets"
    pill_class = "market-pill-nse" if market == "NSE" else "market-pill-us"

    # Fetch live index data
    idx = fetch_index(market)

    # Build index widget HTML
    if idx:
        change_cls = "idx-change-up" if idx["change"] >= 0 else "idx-change-dn"
        sign = "+" if idx["change"] >= 0 else ""
        index_html = f"""
        <div class="index-widget">
            <span class="idx-name">{idx['name']}</span>
            <span class="idx-price">{cur}{idx['price']:,.2f}</span>
            <span class="{change_cls}">{sign}{idx['change']:.2f} ({sign}{idx['change_pct']:.2f}%)</span>
        </div>"""
    else:
        index_name = "NIFTY 50" if market == "NSE" else "DOW JONES"
        index_html = f"""
        <div class="index-widget">
            <span class="idx-name">{index_name}</span>
            <span class="idx-price" style="opacity:.4">—</span>
        </div>"""

    description = (
        "NSE stocks above 30 / 50 / 200 DMA with monotonically rising CAR — plus mock trading with live P&L."
        if market == "NSE"
        else "US stocks above 30 / 50 / 200 DMA with monotonically rising CAR — plus mock trading with live P&L."
    )

    st.markdown(f"""
<div class="hero" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
  <div>
    <h1 style="margin:0">📈 CAR + DMA Super Breakout Scanner</h1>
    <p style="margin:.3rem 0 0">{description}</p>
    <span class="{pill_class}" style="margin-top:.4rem">{market_label}</span>
  </div>
  {index_html}
</div>
""", unsafe_allow_html=True)
