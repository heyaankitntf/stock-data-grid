# CAR + DMA Super Breakout Scanner

A Streamlit stock screener for NSE stocks breaking out above key moving averages
(30/50/200 DMA) with monotonically rising Cumulative Average Return (CAR).
Includes a mock trading module with live P&L tracking.

## Quick start

```bash
cd stock-screener
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Default login: `admin` / `admin123` (change in production).

## Project structure

```
stock-screener/
├── app.py                      ← thin entry point
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         ← paths, constants, env
│   ├── styles/
│   │   ├── __init__.py
│   │   ├── palettes.py         ← dark/light colour palettes
│   │   ├── bootstrap.py        ← CRITICAL FOUC-prevention CSS (runs first)
│   │   └── css.py              ← decorative per-theme CSS
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── session.py          ← file-based session token
│   │   ├── cookies.py          ← CookieController singleton
│   │   └── login.py            ← login form + do_login/do_logout
│   ├── portfolio/
│   │   ├── __init__.py
│   │   ├── store.py            ← JSON portfolio + holdings calc
│   │   └── trades.py           ← execute_trade()
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── universe.py         ← settings.json stock list
│   │   ├── engine.py           ← yfinance scan + parallel runner
│   │   └── styling.py          ← dataframe colour-banding
│   ├── trading/
│   │   ├── __init__.py
│   │   └── prices.py           ← fetch_cmp_single / fetch_cmp_bulk
│   └── components/
│       ├── __init__.py
│       ├── sidebar.py          ← sidebar fragment
│       ├── hero.py             ← hero banner fragment
│       ├── scanner_tab.py      ← scanner tab (st.fragment-wrapped)
│       └── trading_tab.py      ← trading tab fragment
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── settings.json               ← stock universe (gitignored)
└── portfolio.json              ← trade data (gitignored)
```

## FOUC prevention

The app was previously affected by Flash of Unstyled Content (FOUC) — buttons
dancing, layout flickering, and duplicate elements flashing for a frame on
refresh. The fixes live in three places:

1. **`app/styles/bootstrap.py`** — runs as the first `st.markdown` call,
   immediately after `st.set_page_config`. Defines palette CSS variables
   synchronously, runs inline JS to detect the saved theme from cookies
   before Streamlit's bundle paints, pre-reserves `min-height` on
   buttons/metrics/tabs/inputs, and adds a 60ms fade-in to mask any
   residual palette swap.

2. **`app/components/scanner_tab.py`** — wrapped in `@st.fragment` so
   button clicks only re-run the fragment, not the whole script. This
   eliminates the duplicate-render flash that occurred when a 1-2 minute
   scan triggered a full `st.rerun()`.

3. **No `st.rerun()` after long operations** — the scan renders results
   inline in the same fragment run instead of calling `st.rerun()`.

## Screening criteria

A stock qualifies as a breakout when ALL of these are true:
1. CMP > 30 DMA
2. CMP > 50 DMA
3. CMP > 200 DMA
4. CAR (cumulative average return) monotonically rising over 10 days

## Disclaimer

For educational purposes only. Not financial advice.
