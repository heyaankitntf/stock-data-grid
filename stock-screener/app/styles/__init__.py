"""Theme palettes, CSS injection, and FOUC-prevention bootstrap."""
from app.styles.palettes import PALETTES, get_palette
from app.styles.bootstrap import inject_critical_bootstrap
from app.styles.css import inject_theme_css

__all__ = [
    "PALETTES",
    "get_palette",
    "inject_critical_bootstrap",
    "inject_theme_css",
]
