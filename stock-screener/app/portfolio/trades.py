"""Trade execution logic."""
from __future__ import annotations

import uuid

from app.portfolio.store import compute_holdings, load_portfolio, save_portfolio
from app.market import market_currency, now_tz


def execute_trade(
    ticker: str,
    stock: str,
    action: str,
    qty: int,
    price: float,
    market: str = "NSE",
) -> tuple[bool, str]:
    """Execute a BUY or SELL. Returns ``(success, message)``."""
    cur  = market_currency(market)
    port = load_portfolio(market=market)
    holdings = compute_holdings(port["trades"], market=market)
    value = qty * price

    if action == "BUY":
        if port["balance"] < value:
            return False, f"Insufficient balance. Need {cur}{value:,.0f}, have {cur}{port['balance']:,.0f}."
        port["balance"] -= value
    elif action == "SELL":
        if ticker not in holdings or holdings[ticker]["qty"] < qty:
            have = holdings.get(ticker, {}).get("qty", 0)
            return False, f"Not enough shares. Trying to sell {qty}, holding {have}."
        port["balance"] += value
    else:
        return False, f"Unknown action: {action}"

    port["trades"].append({
        "id":        str(uuid.uuid4())[:8],
        "ticker":    ticker,
        "stock":     stock,
        "action":    action,
        "qty":       qty,
        "price":     price,
        "value":     round(value, 2),
        "timestamp": now_tz(market).strftime("%d-%m-%Y %H:%M"),
    })
    save_portfolio(port, market=market)
    return True, f"{action} {qty} × {stock} @ {cur}{price:,.2f} → {cur}{value:,.0f}"
