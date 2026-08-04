"""Market context helpers: currency, suffix, display, timezone, index data."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
import yfinance as yf

from app.config import INITIAL_BALANCE, INITIAL_BALANCE_US, DOW_JONES_DEFAULT


def market_currency(market: str) -> str:
    """Return the currency symbol for the given market."""
    return "$" if market == "US" else "₹"


def market_suffix(market: str) -> str:
    """Return the yfinance ticker suffix for the given market."""
    return "" if market == "US" else ".NS"


def ticker_display(ticker: str, market: str) -> str:
    """Return a human-readable ticker (strip .NS for NSE)."""
    return ticker if market == "US" else ticker.replace(".NS", "")


def market_initial_balance(market: str) -> float:
    """Return the virtual starting balance for the given market."""
    return INITIAL_BALANCE_US if market == "US" else INITIAL_BALANCE


def now_tz(market: str) -> datetime:
    """Return the current datetime in the market's local timezone."""
    tz = ZoneInfo("Asia/Kolkata") if market == "NSE" else ZoneInfo("America/New_York")
    return datetime.now(tz)


def fetch_index(market: str) -> dict | None:
    """Fetch live index data for NIFTY 50 (NSE) or Dow Jones (US), cached per session."""
    cache_key = f"index_data_{market}"
    if st.session_state.get(cache_key):
        return st.session_state[cache_key]

    ticker = "^NSEI" if market == "NSE" else "^DJI"
    name   = "NIFTY 50" if market == "NSE" else "DOW JONES"
    try:
        info  = yf.Ticker(ticker).fast_info
        price = float(info.last_price)
        prev  = float(info.previous_close)
        change     = price - prev
        change_pct = (change / prev) * 100
        result = {"name": name, "price": price, "change": change, "change_pct": change_pct}
        st.session_state[cache_key] = result
        return result
    except Exception:
        return None
