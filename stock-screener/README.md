# CAR + DMA Super Breakout Scanner

A Streamlit stock screener for NSE stocks breaking out above key moving averages
(30/50/200 DMA) with monotonically rising Cumulative Average Return (CAR).
Includes a mock trading module with live P&L tracking.

## Quick start

### Option A — Run locally with Python

```bash
cd stock-screener
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Default login: `admin` / `admin123` (change in production).

### Option B — Run with Docker

```bash
# Build the image (run from repo root)
docker build -t stock-scanner:latest ./stock-screener

# Run on http://localhost:8501 with persistent data volume
docker run --rm -p 8501:8501 \
  -v scanner-data:/app/data \
  stock-scanner:latest
```

Detached run with custom admin password:

```bash
docker run -d --name scanner -p 8501:8501 \
  -v scanner-data:/app/data \
  stock-scanner:latest
```

Useful commands:

```bash
docker logs -f scanner                # tail logs
docker stop scanner                   # graceful stop
docker volume rm scanner-data         # wipe portfolio/session data
docker compose -f docker-compose.yml up   # if using compose (see below)
```

The Docker image:
- Is built on `python:3.12-slim` (≈ 450 MB)
- Runs as non-root user `appuser` (uid 1001)
- Uses `tini` as PID 1 for proper signal handling
- Has a healthcheck polling `/_stcore/health`
- Persists `portfolio.json` + `session.json` into the mounted volume via the entrypoint shim

## Project structure

```
stock-screener/
├── app.py                      ← thin entry point
├── Dockerfile                  ← container build
├── docker-entrypoint.sh        ← data-volume wiring + CMD handoff
├── .dockerignore               ← excluded from build context
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
└── portfolio.json              ← trade data (gitignored, persisted to /app/data in Docker)
```

> The `docker-compose.yml` at the repo root is a convenience wrapper around the `docker run` command — see the Docker quick start above.

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
