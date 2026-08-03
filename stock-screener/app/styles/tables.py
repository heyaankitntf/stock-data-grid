"""Reusable pandas-Styler table styles for dark-only theme.

Why this exists
---------------
Tables are rendered via ``st.markdown(html, unsafe_allow_html=True)`` using
the pandas Styler's ``.to_html()`` output. This avoids the ``st.dataframe()``
iframe problem where Streamlit's internal theme (light/dark) takes over and
ignores our custom dark palette.

The Styler's ``set_table_styles()`` bakes the dark colours directly into the
table's inline ``<style>`` block, so they always render correctly regardless
of the browser or OS theme.
"""
from __future__ import annotations

import pandas as pd

from app.styles.palettes import Palette


def table_styles(p: Palette) -> list[dict]:
    """Return a ``set_table_styles()``-compatible style list for the dark palette.

    Styles every part of the table so it always looks dark:
      - the table itself (background, text colour, border, border-radius)
      - headers (``<th>``)
      - data cells (``<td>``)
      - hover state (subtle highlight)
    """
    hover_bg = p.get("bg3", p["bg2"])

    return [
        # ── Table-wide ───────────────────────────────────────────────────
        {
            "selector": "table",
            "props": [
                ("background-color", p["bg2"]),
                ("color", p["text"]),
                ("border-color", p["border"]),
                ("border-collapse", "collapse"),
                ("width", "100%"),
                ("border-radius", "10px"),
                ("overflow", "hidden"),
                ("font-size", "0.88rem"),
                ("margin", "0"),
            ],
        },
        # ── All cells ───────────────────────────────────────────────────
        {
            "selector": "thead, tbody, tr, th, td",
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
                ("padding", "10px 12px"),
            ],
        },
        # ── Data cells ───────────────────────────────────────────────────
        {
            "selector": "tbody td",
            "props": [
                ("background-color", p["bg2"]),
                ("color", p["text"]),
                ("border-top", f"1px solid {p['border']}"),
                ("padding", "8px 12px"),
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
                ("padding", "8px 12px"),
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
    ]


def apply_dark_table(styler: pd.io.formats.style.Styler, p: Palette) -> pd.io.formats.style.Styler:
    """Apply dark table styles to a pandas Styler.

    Usage:
        styled = df.style.format({...}).hide(axis="index")
        st.markdown(apply_dark_table(styled, p).to_html(), unsafe_allow_html=True)

    This is idempotent and safe to chain with other Styler methods.
    """
    return styler.set_table_styles(table_styles(p), overwrite=False)
