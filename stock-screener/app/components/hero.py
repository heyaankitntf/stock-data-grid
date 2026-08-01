"""Hero banner fragment."""
from __future__ import annotations

import streamlit as st


def render_hero() -> None:
    """Render the gradient hero banner at the top of the main content area."""
    st.markdown("""
<div class="hero">
  <h1>📈 CAR + DMA Super Breakout Scanner</h1>
  <p>NSE stocks above 30 / 50 / 200 DMA with monotonically rising CAR — plus mock trading with live P&amp;L.</p>
</div>
""", unsafe_allow_html=True)
