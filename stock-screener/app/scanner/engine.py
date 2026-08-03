"""Scanner engine: yfinance download + technical analysis.

Each stock is evaluated against four criteria (all must be true):
  1. CMP > 30 DMA
  2. CMP > 50 DMA
  3. CMP > 200 DMA
  4. CAR (cumulative average return) monotonically rising over 10 days
"""
from __future__ import annotations

import logging
import time
from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf

from app.config import (
    CAR_WINDOW,
    DMA_LONG,
    DMA_MID,
    DMA_SHORT,
    MIN_BARS_REQUIRED,
    SCAN_INTERVAL,
    SCAN_PERIOD,
)


def scan_stock(ticker: str) -> dict | None:
    """Scan a single ticker. Returns a result row dict, or None if no breakout."""
    try:
        data = yf.download(ticker, period=SCAN_PERIOD, interval=SCAN_INTERVAL, progress=False)
        if data.empty or len(data) < MIN_BARS_REQUIRED:
            return None
        close    = data["Close"].squeeze()
        dma_30   = close.rolling(DMA_SHORT).mean().iloc[-1]
        dma_50   = close.rolling(DMA_MID).mean().iloc[-1]
        dma_200  = close.rolling(DMA_LONG).mean().iloc[-1]
        cmp      = close.iloc[-1]
        dist_200 = ((cmp - dma_200) / dma_200) * 100
        high_date  = data.tail(252)["High"].squeeze().idxmax()
        car_data   = close.loc[high_date:]
        if len(car_data) < CAR_WINDOW:
            return None
        car_rising = car_data.expanding().mean().tail(CAR_WINDOW).is_monotonic_increasing
        if cmp > dma_30 and cmp > dma_50 and cmp > dma_200 and car_rising:
            return {
                "Date": datetime.now().strftime("%d-%m-%Y"),
                "Stock": ticker.replace(".NS", ""),
                "CMP (₹)": round(float(cmp), 2),
                "30 DMA": round(float(dma_30), 2),
                "50 DMA": round(float(dma_50), 2),
                "200 DMA": round(float(dma_200), 2),
                "200 DMA Dist %": round(float(dist_200), 2),
                "CAR Status": "✅ Positive",
                "Signal": "🟢 Breakout",
            }
    except Exception as e:
        logging.debug("Scan failed for %s: %s", ticker, e)
    return None


def run_scanner(ticker_list: list[str], pbar, status) -> pd.DataFrame:
    """Scan all tickers sequentially, updating ``pbar`` / ``status`` as we go.

    Sequential scanning is used instead of ThreadPoolExecutor because yfinance
    downloads are not thread-safe — concurrent requests to Yahoo Finance cause
    rate-limiting and throttling, producing different (missing) results on
    every run. A small inter-request delay avoids triggering Yahoo's rate
    limiter while keeping the scan reliable and deterministic.
    """
    results: list[dict] = []
    total = len(ticker_list)

    for i, ticker in enumerate(ticker_list, 1):
        status.caption(f"Scanning {ticker.replace('.NS','')} ({i}/{total})…")
        pbar.progress(i / total)
        row = scan_stock(ticker)
        if row:
            results.append(row)
        # Small delay to avoid Yahoo Finance rate-limiting
        if i < total:
            time.sleep(0.15)

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("200 DMA Dist %", ascending=True).reset_index(drop=True)
    return df
