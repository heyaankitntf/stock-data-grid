"""Centralised constants and paths for the Stock Screener app."""
from __future__ import annotations

import hashlib
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
# Resolves to stock-screener/ regardless of CWD.
APP_DIR: Path = Path(__file__).resolve().parents[2]
SETTINGS_FILE: Path = APP_DIR / "settings.json"
PORTFOLIO_FILE: Path = APP_DIR / "portfolio.json"
SESSION_FILE: Path = APP_DIR / "session.json"
US_SETTINGS_FILE: Path = APP_DIR / "us_stocks.json"
US_PORTFOLIO_FILE: Path = APP_DIR / "portfolio_us.json"

# ── Auth ──────────────────────────────────────────────────────────────────────
ADMIN_USERNAME: str = "admin"
ADMIN_PASSWORD: str = "admin123"
COOKIE_AUTH: str = "screener_auth_v1"
COOKIE_TOKEN: str = hashlib.sha256(b"screener_admin_nilesh_2026").hexdigest()
COOKIE_MARKET: str = "screener_market_v1"
SESSION_EXPIRY_DAYS: int = 30

# ── Trading ───────────────────────────────────────────────────────────────────
INITIAL_BALANCE: int = 1_000_000  # ₹10,00,000 virtual capital
INITIAL_BALANCE_US: int = 100_000  # $100,000 virtual capital

# ── Scanner ───────────────────────────────────────────────────────────────────
SCAN_WORKERS: int = 10
SCAN_PERIOD: str = "2y"
SCAN_INTERVAL: str = "1d"
DMA_SHORT: int = 30
DMA_MID: int = 50
DMA_LONG: int = 200
CAR_WINDOW: int = 10
MIN_BARS_REQUIRED: int = 200

# ── US Market ─────────────────────────────────────────────────────────────────
DOW_JONES_DEFAULT: list[str] = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "CSCO", "IBM", "INTC", "VZ", "CRM",
    "GS", "JPM", "V", "AXP", "TRV", "UNH", "AMGN", "JNJ", "MRK", "CAT",
    "BA", "HON", "MMM", "DOW", "SHW", "WMT", "HD", "PG", "KO", "MCD",
]
