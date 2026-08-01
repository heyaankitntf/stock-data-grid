"""Stock universe persistence (settings.json)."""
from __future__ import annotations

import json
import logging

from app.config import SETTINGS_FILE


def load_stocks() -> list[str]:
    """Return the list of configured ticker symbols."""
    try:
        data = json.loads(SETTINGS_FILE.read_text())
        return [s.strip() for s in data.get("stocks", []) if s.strip()]
    except Exception:
        return []


def save_stocks(stocks: list[str]) -> None:
    """Persist the ticker list to disk."""
    try:
        SETTINGS_FILE.write_text(json.dumps({"stocks": stocks}, indent=2))
    except Exception as e:
        logging.error("Failed to save stocks: %s", e)
