"""Theme palettes, CSS injection, and FOUC-prevention bootstrap."""
from app.styles.palettes import DARK, get_palette
from app.styles.bootstrap import inject_critical_bootstrap
from app.styles.css import inject_theme_css
from app.styles.tables import apply_dark_table, table_styles

__all__ = [
    "DARK",
    "get_palette",
    "inject_critical_bootstrap",
    "inject_theme_css",
    "apply_dark_table",
    "table_styles",
]
