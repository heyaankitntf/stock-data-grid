"""JSON-backed portfolio store + holdings computation."""
from __future__ import annotations

import json
import logging

from app.config import INITIAL_BALANCE, INITIAL_BALANCE_US, PORTFOLIO_FILE, US_PORTFOLIO_FILE
from app.market import market_initial_balance, ticker_display


def load_portfolio(market: str = "NSE") -> dict:
    """Load portfolio from disk, seeding with initial balance on first run."""
    file = US_PORTFOLIO_FILE if market == "US" else PORTFOLIO_FILE
    try:
        return json.loads(file.read_text())
    except Exception:
        seed = {
            "initial_balance": market_initial_balance(market),
            "balance": market_initial_balance(market),
            "trades": [],
        }
        save_portfolio(seed, market=market)
        return seed


def save_portfolio(data: dict, market: str = "NSE") -> None:
    """Persist portfolio to disk."""
    file = US_PORTFOLIO_FILE if market == "US" else PORTFOLIO_FILE
    try:
        file.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logging.error("Failed to save portfolio: %s", e)


def compute_holdings(trades: list[dict], market: str = "NSE") -> dict:
    """Return ``{ticker: {qty, avg_price, invested, stock}}`` from trade log."""
    h: dict[str, dict] = {}
    for t in trades:
        tk = t["ticker"]
        if tk not in h:
            h[tk] = {"qty": 0, "total_cost": 0.0}
        if t["action"] == "BUY":
            h[tk]["qty"]        += t["qty"]
            h[tk]["total_cost"] += t["qty"] * t["price"]
        elif t["action"] == "SELL":
            h[tk]["qty"]        -= t["qty"]
            h[tk]["total_cost"] -= t["qty"] * t["price"]
    return {
        tk: {
            "qty":       v["qty"],
            "avg_price": round(v["total_cost"] / v["qty"], 2) if v["qty"] > 0 else 0,
            "invested":  round(v["total_cost"], 2),
            "stock":     ticker_display(tk, market),
        }
        for tk, v in h.items() if v["qty"] > 0
    }
