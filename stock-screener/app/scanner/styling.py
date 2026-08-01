"""Dataframe styling helpers for the scanner results table."""
from __future__ import annotations

import pandas as pd

from app.styles.palettes import Palette


def dist_colour(val, p: Palette) -> str:
    """Return inline CSS for a 200-DMA-distance cell, colour-banded by range."""
    if isinstance(val, (int, float)):
        if val < 5:
            return f"background-color:{p['dist_lo_bg']}; color:{p['dist_lo_fg']}"
        if val < 15:
            return f"background-color:{p['dist_mid_bg']}; color:{p['dist_mid_fg']}"
        return f"background-color:{p['dist_hi_bg']}; color:{p['dist_hi_fg']}"
    return ""


def style_breakout_df(df: pd.DataFrame, p: Palette) -> pd.io.formats.style.Styler:
    """Apply distance colour-banding + ₹ formatting to the breakout dataframe."""
    return (
        df.style
        .map(lambda v: dist_colour(v, p), subset=["200 DMA Dist %"])
        .format({
            "CMP (₹)": "₹{:.2f}", "30 DMA": "₹{:.2f}",
            "50 DMA": "₹{:.2f}",  "200 DMA": "₹{:.2f}",
            "200 DMA Dist %": "{:.2f}%",
        })
        .hide(axis="index")
    )
