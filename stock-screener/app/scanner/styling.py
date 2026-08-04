"""Dataframe styling helpers for the scanner results table."""
from __future__ import annotations

import pandas as pd

from app.styles.palettes import Palette
from app.styles.tables import table_styles
from app.market import market_currency


def dist_colour(val, p: Palette) -> str:
    """Return inline CSS for a 200-DMA-distance cell, colour-banded by range."""
    if isinstance(val, (int, float)):
        if val < 5:
            return f"background-color:{p['dist_lo_bg']}; color:{p['dist_lo_fg']}"
        if val < 15:
            return f"background-color:{p['dist_mid_bg']}; color:{p['dist_mid_fg']}"
        return f"background-color:{p['dist_hi_bg']}; color:{p['dist_hi_fg']}"
    return ""


def style_breakout_df(df: pd.DataFrame, p: Palette, market: str = "NSE") -> pd.io.formats.style.Styler:
    """Apply distance colour-banding + currency formatting to the breakout dataframe.

    Also bakes dark-theme table styles directly into the table HTML via
    ``set_table_styles()``. This is critical on mobile Chrome (Android),
    where the browser auto-dark-modes iframe content and otherwise paints
    the dataframe cells white. See app/styles/tables.py for full rationale.
    """
    cur = market_currency(market)
    # Find the CMP column dynamically (it contains the currency symbol)
    cmp_col = next((c for c in df.columns if c.startswith("CMP")), "CMP (₹)")
    fmt = {
        cmp_col: f"{cur}{{:.2f}}",
        "30 DMA": f"{cur}{{:.2f}}",
        "50 DMA": f"{cur}{{:.2f}}",
        "200 DMA": f"{cur}{{:.2f}}",
        "200 DMA Dist %": "{:.2f}%",
    }
    return (
        df.style
        .map(lambda v: dist_colour(v, p), subset=["200 DMA Dist %"])
        .format(fmt)
        .hide(axis="index")
        .set_table_styles(table_styles(p), overwrite=False)
    )
