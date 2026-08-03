"""Dark-only color palette.

The app uses a single dark palette. Light mode has been removed entirely
so the UI is always consistent regardless of the system theme.
"""
from __future__ import annotations

from typing import TypedDict


class Palette(TypedDict):
    bg: str
    bg2: str
    bg3: str
    surface: str
    border: str
    text: str
    text_muted: str
    text_faint: str
    accent: str
    accent2: str
    hero_a: str
    hero_b: str
    hero_c: str
    metric_val: str
    dist_lo_bg: str
    dist_lo_fg: str
    dist_mid_bg: str
    dist_mid_fg: str
    dist_hi_bg: str
    dist_hi_fg: str
    err_bg: str
    err_border: str
    err_fg: str
    badge_bg: str
    badge_fg: str
    footer_border: str
    btn_text: str
    input_bg: str
    input_border: str
    profit_bg: str
    profit_fg: str
    loss_bg: str
    loss_fg: str
    card_buy: str
    card_sell: str
    label: str


DARK: Palette = {
    "bg": "#0b1622", "bg2": "#0f2030", "bg3": "#162840",
    "surface": "#122035", "border": "#1e3a55",
    "text": "#d0e0f0", "text_muted": "#8ba8c4", "text_faint": "#3a5268",
    "accent": "#00d4aa", "accent2": "#96c93d",
    "hero_a": "#0f2027", "hero_b": "#203a43", "hero_c": "#2c5364",
    "metric_val": "#00d4aa",
    "dist_lo_bg": "#0d3322", "dist_lo_fg": "#00d464",
    "dist_mid_bg": "#2e2800", "dist_mid_fg": "#ffc800",
    "dist_hi_bg": "#2e1200", "dist_hi_fg": "#ff7755",
    "err_bg": "#2e1215", "err_border": "#7a1f28", "err_fg": "#ff7070",
    "badge_bg": "#0d3322", "badge_fg": "#00d464",
    "footer_border": "#1a2f42", "btn_text": "#ffffff",
    "input_bg": "#0f2030", "input_border": "#1e3a55",
    "profit_bg": "#0d3322", "profit_fg": "#00d464",
    "loss_bg":   "#2e1200", "loss_fg":   "#ff7755",
    "card_buy":  "#0d2e1a", "card_sell": "#2e1200",
    "label": "🌙 Dark",
}


def get_palette() -> Palette:
    """Return the dark palette (the only palette)."""
    return DARK
