"""Trading tab fragment: portfolio overview, holdings, trade form, history."""
from __future__ import annotations

from datetime import datetime

import streamlit as st
import pandas as pd

from app.config import INITIAL_BALANCE
from app.portfolio import compute_holdings, execute_trade, load_portfolio, save_portfolio
from app.scanner import load_stocks
from app.styles.palettes import Palette
from app.trading import fetch_cmp_bulk, fetch_cmp_single


def _pnl_style(val, p: Palette) -> str:
    if not isinstance(val, (int, float)):
        return ""
    if val > 0:
        return f"background-color:{p['profit_bg']};color:{p['profit_fg']};font-weight:700"
    if val < 0:
        return f"background-color:{p['loss_bg']};color:{p['loss_fg']};font-weight:700"
    return ""


def _action_style(val, p: Palette) -> str:
    if val == "BUY":
        return f"background-color:{p['profit_bg']};color:{p['profit_fg']};font-weight:700"
    return f"background-color:{p['loss_bg']};color:{p['loss_fg']};font-weight:700"


def _render_portfolio_overview(port: dict, holdings: dict, cached_prices: dict, p: Palette) -> dict:
    """Render the metrics row + refresh/reset buttons. Returns updated prices."""
    held_tickers = list(holdings.keys())

    # Auto-fetch on first open if holdings exist and cache is empty
    if held_tickers and not any(t in cached_prices for t in held_tickers):
        with st.spinner("Fetching live prices…"):
            fresh = fetch_cmp_bulk(held_tickers)
            st.session_state.portfolio_prices = {**cached_prices, **fresh}
            cached_prices = st.session_state.portfolio_prices

    total_invested    = sum(h["invested"] for h in holdings.values())
    total_current_val = sum(
        holdings[tk]["qty"] * cached_prices.get(tk, holdings[tk]["avg_price"])
        for tk in holdings
    )
    overall_pnl     = total_current_val - total_invested
    overall_pnl_pct = (overall_pnl / total_invested * 100) if total_invested else 0
    portfolio_value = port["balance"] + total_current_val

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💰 Cash Balance",   f"₹{port['balance']:,.0f}")
    m2.metric("📥 Invested",       f"₹{total_invested:,.0f}")
    m3.metric("📈 Current Value",  f"₹{total_current_val:,.0f}",
              delta=f"₹{overall_pnl:+,.0f}" if total_invested else None)
    m4.metric("💹 Overall P&L",    f"₹{overall_pnl:+,.0f}",
              delta=f"{overall_pnl_pct:+.2f}%" if total_invested else None)
    m5.metric("🏦 Portfolio Value", f"₹{portfolio_value:,.0f}")

    ref_col, _, reset_col = st.columns([1, 3, 1])
    with ref_col:
        if st.button("🔄 Refresh Prices", width="stretch"):
            if held_tickers:
                with st.spinner("Fetching live prices…"):
                    fresh = fetch_cmp_bulk(held_tickers)
                    st.session_state.portfolio_prices = {**cached_prices, **fresh}
                st.rerun()
    with reset_col:
        if st.button("🗑️ Reset Portfolio", width="stretch"):
            st.session_state["_confirm_reset"] = True

    if st.session_state.get("_confirm_reset"):
        st.warning("This will wipe all trades and restore ₹10,00,000 balance. Are you sure?")
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button("✅ Yes, Reset", width="stretch"):
                save_portfolio({
                    "initial_balance": INITIAL_BALANCE,
                    "balance": INITIAL_BALANCE,
                    "trades": [],
                })
                st.session_state.portfolio_prices = {}
                st.session_state.pop("_confirm_reset", None)
                st.rerun()
        with no_col:
            if st.button("❌ Cancel", width="stretch"):
                st.session_state.pop("_confirm_reset", None)
                st.rerun()

    return cached_prices


def _render_holdings(holdings: dict, cached_prices: dict, p: Palette) -> None:
    st.markdown("### 📋 Holdings")
    if not holdings:
        st.info("No open positions yet. Place your first trade below.", icon="📭")
        return

    rows = []
    for tk, h in holdings.items():
        cmp_live   = cached_prices.get(tk, None)
        cur_val    = h["qty"] * cmp_live if cmp_live else None
        pnl        = (cur_val - h["invested"]) if cur_val is not None else None
        pnl_pct    = (pnl / h["invested"] * 100) if (pnl is not None and h["invested"]) else None
        rows.append({
            "Stock":        h["stock"],
            "Qty":          h["qty"],
            "Avg Buy (₹)":  h["avg_price"],
            "Live CMP (₹)": cmp_live if cmp_live else "—",
            "Invested (₹)": round(h["invested"], 2),
            "Cur Value (₹)": round(cur_val, 2) if cur_val else "—",
            "P&L (₹)":      round(pnl, 2) if pnl is not None else "—",
            "P&L %":        round(pnl_pct, 2) if pnl_pct is not None else "—",
        })
    h_df = pd.DataFrame(rows)

    fmt = {"Avg Buy (₹)": "₹{:.2f}", "Invested (₹)": "₹{:,.0f}"}
    for col in ["Live CMP (₹)", "Cur Value (₹)", "P&L (₹)"]:
        if h_df[col].apply(lambda x: isinstance(x, (int, float))).all():
            fmt[col] = "₹{:,.2f}"
    if h_df["P&L %"].apply(lambda x: isinstance(x, (int, float))).all():
        fmt["P&L %"] = "{:+.2f}%"

    styled_h = (
        h_df.style
        .map(lambda v: _pnl_style(v, p), subset=["P&L (₹)", "P&L %"])
        .format(fmt, na_rep="—")
        .hide(axis="index")
    )
    st.dataframe(styled_h, width="stretch",
                 height=min(80 + len(rows) * 40, 500))


def _render_trade_form(port: dict, my_stocks: list[str], p: Palette) -> None:
    st.markdown("### 🛒 Place a Trade")
    stock_options = my_stocks if my_stocks else ["—"]
    trade_col, preview_col = st.columns([1, 1], gap="large")

    with trade_col:
        st.markdown('<div class="trade-card"><h4>📝 Order Details</h4>', unsafe_allow_html=True)
        selected_ticker = st.selectbox(
            "Select Stock",
            options=stock_options,
            format_func=lambda x: x.replace(".NS", "") if x != "—" else "—",
        )
        action = st.radio("Action", ["BUY", "SELL"], horizontal=True,
                          format_func=lambda x: f"🟢 {x}" if x == "BUY" else f"🔴 {x}")
        qty    = st.number_input("Quantity (shares)", min_value=1, max_value=100000,
                                 value=1, step=1)
        fetch_btn = st.button("📡 Get Live Price", width="stretch")
        if fetch_btn and selected_ticker != "—":
            with st.spinner(f"Fetching CMP for {selected_ticker.replace('.NS','')}…"):
                price = fetch_cmp_single(selected_ticker)
            if price:
                st.session_state.trade_preview = {
                    "ticker": selected_ticker,
                    "stock":  selected_ticker.replace(".NS", ""),
                    "price":  price,
                    "qty":    qty,
                    "action": action,
                    "ts":     datetime.now().strftime("%H:%M:%S"),
                }
            else:
                st.error("Could not fetch price. Check ticker or try again.")
                st.session_state.trade_preview = None
        st.markdown('</div>', unsafe_allow_html=True)

    with preview_col:
        tp = st.session_state.trade_preview
        if tp and (tp.get("ticker") == selected_ticker):
            tp["qty"]    = qty
            tp["action"] = action

        if tp and tp.get("ticker") == selected_ticker:
            total_val = tp["price"] * tp["qty"]
            is_buy    = tp["action"] == "BUY"
            card_bg   = p["card_buy"] if is_buy else p["card_sell"]
            action_lbl = "🟢 BUY" if is_buy else "🔴 SELL"

            st.markdown(f"""
<div style="background:{card_bg};border:1px solid {p['border']};border-radius:12px;
     padding:1.2rem 1.4rem;margin-bottom:1rem;">
  <div style="font-size:1.05rem;font-weight:800;color:{p['text']};margin-bottom:.6rem;">
    {action_lbl} · {tp['stock']}
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:.88rem;color:{p['text']};">
    <tr><td style="padding:3px 0;color:{p['text_muted']}">Live CMP</td>
        <td style="text-align:right;font-weight:700;">₹{tp['price']:,.2f}</td></tr>
    <tr><td style="padding:3px 0;color:{p['text_muted']}">Quantity</td>
        <td style="text-align:right;font-weight:700;">{tp['qty']}</td></tr>
    <tr><td style="padding:3px 0;color:{p['text_muted']}">Total Value</td>
        <td style="text-align:right;font-weight:700;">₹{total_val:,.0f}</td></tr>
    <tr><td style="padding:3px 0;color:{p['text_muted']}">Cash Balance</td>
        <td style="text-align:right;">₹{port['balance']:,.0f}</td></tr>
    <tr><td style="padding:3px 0;color:{p['text_muted']}">Fetched at</td>
        <td style="text-align:right;">{tp['ts']}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

            if st.button(f"✅ Confirm {action_lbl}", width="stretch"):
                ok, msg = execute_trade(tp["ticker"], tp["stock"],
                                        tp["action"], tp["qty"], tp["price"])
                if ok:
                    st.success(f"✅ {msg}")
                    st.session_state.trade_preview    = None
                    st.session_state.portfolio_prices = {}
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
        else:
            st.markdown(f"""
<div style="background:{p['surface']};border:1px dashed {p['border']};border-radius:12px;
     padding:2rem;text-align:center;color:{p['text_muted']};">
  <div style="font-size:2rem;margin-bottom:.5rem;">📡</div>
  <div>Select a stock and click<br><strong>Get Live Price</strong> to see the order preview.</div>
</div>
""", unsafe_allow_html=True)


def _render_trade_history(port: dict, p: Palette) -> None:
    trades = port.get("trades", [])
    with st.expander(f"📜 Trade History ({len(trades)} trades)", expanded=False):
        if not trades:
            st.caption("No trades yet.")
            return

        hist_rows = []
        for t in reversed(trades):
            hist_rows.append({
                "Date / Time":  t["timestamp"],
                "Stock":        t["stock"],
                "Action":       t["action"],
                "Qty":          t["qty"],
                "Price (₹)":    t["price"],
                "Value (₹)":    t["value"],
            })
        hist_df = pd.DataFrame(hist_rows)
        styled_hist = (
            hist_df.style
            .map(lambda v: _action_style(v, p), subset=["Action"])
            .format({"Price (₹)": "₹{:,.2f}", "Value (₹)": "₹{:,.0f}"})
            .hide(axis="index")
        )
        st.dataframe(styled_hist, width="stretch",
                     height=min(80 + len(hist_rows) * 38, 420))
        st.download_button(
            label="⬇️ Export Trade History",
            data=hist_df.to_csv(index=False).encode(),
            file_name=f"Trade_History_{datetime.now().strftime('%d-%m-%Y')}.csv",
            mime="text/csv",
        )


def render_trading_tab(p: Palette) -> None:
    """Render the Mock Trading tab."""
    port      = load_portfolio()
    holdings  = compute_holdings(port["trades"])
    my_stocks = load_stocks()

    st.markdown("### 💼 Portfolio Overview")
    cached_prices: dict[str, float] = st.session_state.portfolio_prices
    cached_prices = _render_portfolio_overview(port, holdings, cached_prices, p)

    st.divider()
    _render_holdings(holdings, cached_prices, p)
    st.divider()
    _render_trade_form(port, my_stocks, p)
    st.divider()
    _render_trade_history(port, p)
