"""Reusable pandas-Styler table styles for dark/light themes.

Why this exists
---------------
Streamlit's ``st.dataframe()`` renders the table inside an ``<iframe>``.
CSS injected via ``st.markdown(..., unsafe_allow_html=True)`` in the parent
document **cannot reach inside that iframe** — so per-theme CSS in
``app/styles/css.py`` won't style the table cells.

On mobile browsers (especially Chrome on Android with dark mode enabled),
the browser applies its OWN dark-theme heuristics to iframe content that
doesn't explicitly opt out. The result: white table cells on a dark app
background, exactly the bug reported on phones.

Two-pronged fix
---------------
1. ``color-scheme: <dark|light>`` on ``<html>`` (set in ``bootstrap.py``)
   tells the browser "this page is already themed, don't auto-dark-mode
   my iframes".

2. ``pandas.io.formats.style.Styler.set_table_styles()`` bakes the dark
   colours directly into the table's inline ``<style>`` block, so they
   survive cross-iframe regardless of what the browser does.

This module provides the second part. Use it on every ``st.dataframe()``
call by chaining ``.set_table_styles(table_styles(p))`` on your Styler.
"""
from __future__ import annotations

import pandas as pd

from app.styles.palettes import Palette


def table_styles(p: Palette) -> list[dict]:
    """Return a ``set_table_styles()``-compatible style list for a palette.

    Styles every part of the table that mobile Chrome was painting white:
      - the table itself (background, text colour, border)
      - headers (``<th>``)
      - data cells (``<td>``)
      - the index column (the leftmost 0,1,2,... column)
      - hover state (subtle highlight)
      - selected row state
    """
    # Pick a slightly lighter shade of bg for hover, falls back to bg2.
    hover_bg = p.get("bg3", p["bg2"])

    return [
        # ── Table-wide ───────────────────────────────────────────────────
        {
            "selector": "table, thead, tbody, tr, th, td",
            "props": [
                ("background-color", p["bg2"]),
                ("color", p["text"]),
                ("border-color", p["border"]),
            ],
        },
        # ── Header row ───────────────────────────────────────────────────
        {
            "selector": "thead th",
            "props": [
                ("background-color", p["bg3"]),
                ("color", p["text"]),
                ("font-weight", "700"),
                ("border-bottom", f"2px solid {p['border']}"),
                ("text-align", "left"),
            ],
        },
        # ── Data cells ───────────────────────────────────────────────────
        {
            "selector": "tbody td",
            "props": [
                ("background-color", p["bg2"]),
                ("color", p["text"]),
                ("border-top", f"1px solid {p['border']}"),
            ],
        },
        # ── Index column (row numbers) ──────────────────────────────────
        {
            "selector": "tbody th, thead tr th:first-child",
            "props": [
                ("background-color", p["bg3"]),
                ("color", p["text_muted"]),
                ("font-weight", "600"),
                ("border-right", f"1px solid {p['border']}"),
            ],
        },
        # ── Hover state (desktop) ───────────────────────────────────────
        {
            "selector": "tbody tr:hover td",
            "props": [
                ("background-color", hover_bg),
            ],
        },
        # ── Selected row state ──────────────────────────────────────────
        {
            "selector": "tbody tr:selected td, tbody tr.odd.selected td",
            "props": [
                ("background-color", p["bg3"]),
            ],
        },
        # ── Caption / empty cells ───────────────────────────────────────
        {
            "selector": "caption",
            "props": [
                ("color", p["text_muted"]),
                ("caption-side", "bottom"),
                ("font-size", "0.8rem"),
                ("padding-top", "0.5rem"),
            ],
        },
        # ── Cell text alignment override (numbers right-aligned) ────────
        {
            "selector": "tbody td.text-right, th.text-right",
            "props": [("text-align", "right")],
        },
    ]


def apply_dark_table(styler: pd.io.formats.style.Styler, p: Palette) -> pd.io.formats.style.Styler:
    """Apply theme-aware table styles to a pandas Styler.

    Usage:
        styled = df.style.format({...}).hide(axis="index")
        st.dataframe(apply_dark_table(styled, p), ...)

    This is idempotent and safe to chain with other Styler methods.
    """
    return styler.set_table_styles(table_styles(p), overwrite=False)
