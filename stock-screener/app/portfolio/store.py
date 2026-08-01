"""JSON-backed portfolio store + holdings computation."""
from __future__ import annotations

import json
import logging

from app.config import INITIAL_BALANCE, PORTFOLIO_FILE


def load_portfolio() -> dict:
    """Load portfolio from disk, seeding with INITIAL_BALANCE on first run."""
    try:
        return json.loads(PORTFOLIO_FILE.read_text())
    except Exception:
        seed = {
            "initial_balance": INITIAL_BALANCE,
            "balance": INITIAL_BALANCE,
            "trades": [],
        }
        save_portfolio(seed)
        return seed


def save_portfolio(data: dict) -> None:
    """Persist portfolio to disk."""
    try:
        PORTFOLIO_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logging.error("Failed to save portfolio: %s", e)


def compute_holdings(trades: list[dict]) -> dict:
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
            "stock":     tk.replace(".NS", ""),
        }
        for tk, v in h.items() if v["qty"] > 0
    }
