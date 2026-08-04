"""Stock universe persistence (settings.json / us_stocks.json)."""
from __future__ import annotations

import json
import logging

from app.config import SETTINGS_FILE, US_SETTINGS_FILE, DOW_JONES_DEFAULT


def load_stocks(market: str = "NSE") -> list[str]:
    """Return the list of configured ticker symbols for the given market."""
    file = US_SETTINGS_FILE if market == "US" else SETTINGS_FILE
    try:
        data = json.loads(file.read_text())
        return [s.strip() for s in data.get("stocks", []) if s.strip()]
    except Exception:
        if market == "US":
            return DOW_JONES_DEFAULT.copy()
        return []


def save_stocks(stocks: list[str], market: str = "NSE") -> None:
    """Persist the ticker list to disk for the given market."""
    file = US_SETTINGS_FILE if market == "US" else SETTINGS_FILE
    try:
        file.write_text(json.dumps({"stocks": stocks}, indent=2))
    except Exception as e:
        logging.error("Failed to save stocks: %s", e)
