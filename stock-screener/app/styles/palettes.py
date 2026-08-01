"""Color palettes for dark and light themes.

Both palettes expose the same keys so consumer code can do
`P = get_palette(theme)` without caring which theme is active.
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


PALETTES: dict[str, Palette] = {
    "dark": {
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
    },
    "light": {
        "bg": "#f2f6fb", "bg2": "#ffffff", "bg3": "#e6eef7",
        "surface": "#ffffff", "border": "#c5d5e8",
        "text": "#162030", "text_muted": "#4a6080", "text_faint": "#8aa0b8",
        "accent": "#1565c0", "accent2": "#2e7d32",
        "hero_a": "#1565c0", "hero_b": "#1976d2", "hero_c": "#1e88e5",
        "metric_val": "#1565c0",
        "dist_lo_bg": "#c8f0d8", "dist_lo_fg": "#1b5e20",
        "dist_mid_bg": "#fff8e1", "dist_mid_fg": "#e65100",
        "dist_hi_bg": "#fce4ec", "dist_hi_fg": "#b71c1c",
        "err_bg": "#fce4ec", "err_border": "#e57373", "err_fg": "#b71c1c",
        "badge_bg": "#c8f0d8", "badge_fg": "#1b5e20",
        "footer_border": "#c5d5e8", "btn_text": "#ffffff",
        "input_bg": "#ffffff", "input_border": "#c5d5e8",
        "profit_bg": "#d0f0dc", "profit_fg": "#1b5e20",
        "loss_bg":   "#fce4ec", "loss_fg":   "#b71c1c",
        "card_buy":  "#e8f5e9", "card_sell": "#fce4ec",
        "label": "☀️ Light",
    },
}


def get_palette(name: str) -> Palette:
    """Return the palette for `name`, falling back to dark if unknown."""
    return PALETTES.get(name, PALETTES["dark"])
