"""Trade execution logic."""
from __future__ import annotations

from datetime import datetime
import uuid

from app.portfolio.store import compute_holdings, load_portfolio, save_portfolio


def execute_trade(
    ticker: str,
    stock: str,
    action: str,
    qty: int,
    price: float,
) -> tuple[bool, str]:
    """Execute a BUY or SELL. Returns ``(success, message)``."""
    port = load_portfolio()
    holdings = compute_holdings(port["trades"])
    value = qty * price

    if action == "BUY":
        if port["balance"] < value:
            return False, f"Insufficient balance. Need ₹{value:,.0f}, have ₹{port['balance']:,.0f}."
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
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M"),
    })
    save_portfolio(port)
    return True, f"{action} {qty} × {stock} @ ₹{price:,.2f} → ₹{value:,.0f}"
