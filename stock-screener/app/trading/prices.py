"""Live price fetching via yfinance.

``fetch_cmp_bulk`` is optimised for the common case of fetching many tickers
at once (used by the portfolio overview). ``fetch_cmp_single`` is faster for
a single ticker (used by the trade preview).
"""
from __future__ import annotations

import logging

import yfinance as yf


def fetch_cmp_single(ticker: str) -> float | None:
    """Fetch latest close for one ticker quickly via ``fast_info``."""
    try:
        info = yf.Ticker(ticker).fast_info
        p = info.last_price
        return round(float(p), 2) if p else None
    except Exception as e:
        logging.debug("fetch_cmp_single failed for %s: %s", ticker, e)
        return None


def fetch_cmp_bulk(tickers: list[str]) -> dict[str, float]:
    """Fetch latest close for multiple tickers in one yfinance call."""
    if not tickers:
        return {}
    try:
        if len(tickers) == 1:
            data = yf.download(tickers[0], period="5d", interval="1d", progress=False)
            if not data.empty:
                return {tickers[0]: round(float(data["Close"].dropna().iloc[-1]), 2)}
            return {}
        raw = yf.download(" ".join(tickers), period="5d", interval="1d", progress=False)
        closes = raw["Close"]
        result: dict[str, float] = {}
        for tk in tickers:
            try:
                result[tk] = round(float(closes[tk].dropna().iloc[-1]), 2)
            except Exception:
                pass
        return result
    except Exception as e:
        logging.error("fetch_cmp_bulk failed: %s", e)
        return {}
