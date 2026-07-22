import io
import json
import warnings
import logging
import hashlib
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_cookies_controller import CookieController

# ── Silence noisy loggers ──────────────────────────────────────────────────────
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CAR + DMA Breakout Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auth constants ─────────────────────────────────────────────────────────────
ADMIN_USERNAME  = "admin"
ADMIN_PASSWORD  = "admin123"
COOKIE_NAME     = "screener_auth_v1"
COOKIE_TOKEN    = hashlib.sha256(b"screener_admin_nilesh_2026").hexdigest()
SETTINGS_FILE   = Path(__file__).parent / "settings.json"

# ── Cookie controller (must be created before any other st calls) ──────────────
cookies = CookieController()

# ── Settings helpers ───────────────────────────────────────────────────────────
def load_stocks() -> list[str]:
    try:
        data = json.loads(SETTINGS_FILE.read_text())
        return [s.strip() for s in data.get("stocks", []) if s.strip()]
    except Exception:
        return []

def save_stocks(stocks: list[str]):
    SETTINGS_FILE.write_text(json.dumps({"stocks": stocks}, indent=2))

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b1622;
    color: #d0e0f0;
}
[data-testid="stHeader"] { background: transparent; }

/* ── Login card ── */
.login-wrap {
    display: flex; justify-content: center;
    align-items: center; min-height: 80vh;
}
.login-card {
    background: linear-gradient(145deg, #0f2030, #162840);
    border: 1px solid #1e3a55;
    border-radius: 18px;
    padding: 2.8rem 3rem;
    width: 100%; max-width: 420px;
    box-shadow: 0 20px 60px rgba(0,0,0,.5);
}
.login-card h2 {
    font-size: 1.55rem; font-weight: 800;
    margin: 0 0 .25rem; color: #e8f4ff;
}
.login-card p { font-size: .85rem; opacity: .55; margin: 0 0 1.8rem; }
.login-error {
    background: #2e1215; border: 1px solid #7a1f28;
    border-radius: 8px; padding: .65rem 1rem;
    color: #ff7070; font-size: .88rem; margin-top: .8rem;
}

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 14px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 1.9rem; font-weight: 800; margin: 0 0 .4rem; letter-spacing: -.5px; }
.hero p  { font-size: .9rem; opacity: .7; margin: 0; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(90deg, #00b09b, #96c93d) !important;
    color: #fff !important; font-weight: 700;
    border: none !important; border-radius: 8px; width: 100%;
}
.stButton > button:hover { filter: brightness(1.08); }

/* ── Progress bar ── */
.stProgress > div > div { background: linear-gradient(90deg, #00b09b, #96c93d) !important; }

/* ── Metrics ── */
[data-testid="stMetricLabel"]  { color: #8ba8c4 !important; font-size: .78rem !important; }
[data-testid="stMetricValue"]  { color: #00d4aa !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Sidebar settings ── */
.settings-header {
    font-size: 1rem; font-weight: 700; color: #00d4aa;
    margin-bottom: .4rem;
}
.stock-count-badge {
    display: inline-block;
    background: #0d3322; color: #00d464;
    border-radius: 6px; padding: 2px 10px;
    font-size: .82rem; font-weight: 600;
    margin-bottom: .8rem;
}

/* ── Footer ── */
.footer {
    text-align: center; color: #3a5268; font-size: .75rem;
    margin-top: 2.5rem; padding-top: 1rem;
    border-top: 1px solid #1a2f42;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH LAYER
# ══════════════════════════════════════════════════════════════════════════════

def check_cookie_auth() -> bool:
    """Return True if the remember-me cookie is valid."""
    try:
        val = cookies.get(COOKIE_NAME)
        return val == COOKIE_TOKEN
    except Exception:
        return False

def do_login(username: str, password: str, remember: bool) -> bool:
    if username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        if remember:
            cookies.set(COOKIE_NAME, COOKIE_TOKEN,
                        max_age=30 * 24 * 3600)   # 30 days
        return True
    return False

def do_logout():
    st.session_state.authenticated = False
    st.session_state.df_results    = None
    st.session_state.last_scan     = None
    st.session_state.scanned       = False
    try:
        cookies.remove(COOKIE_NAME)
    except Exception:
        pass

# Initialise session auth from cookie if not already set
if "authenticated" not in st.session_state:
    st.session_state.authenticated = check_cookie_auth()

# ── Login page ─────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 📈 CAR + DMA Breakout Scanner")
        st.markdown("##### Admin Login")
        st.markdown("---")

        with st.form("login_form", clear_on_submit=False):
            username  = st.text_input("Username", placeholder="admin")
            password  = st.text_input("Password", type="password", placeholder="••••••••")
            remember  = st.checkbox("Remember me for 30 days")
            submitted = st.form_submit_button("🔐 Sign In", use_container_width=True)

        if submitted:
            if do_login(username, password, remember):
                st.rerun()
            else:
                st.error("❌ Incorrect username or password.", icon="🚫")

        st.markdown(
            '<div class="footer">Authorised access only · Not financial advice</div>',
            unsafe_allow_html=True,
        )
    st.stop()   # Nothing below renders until authenticated


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP  (only reached when authenticated)
# ══════════════════════════════════════════════════════════════════════════════

# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in [("df_results", None), ("last_scan", None), ("scanned", False),
                     ("settings_open", False), ("stocks_saved_msg", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>📈 CAR + DMA Super Breakout Scanner</h1>
  <p>
    NSE stocks simultaneously above their 30‑day, 50‑day &amp; 200‑day moving averages,
    with a Cumulative Average Return (CAR) rising monotonically for the past 10 sessions.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── User header ──
    st.markdown("👤 **Signed in as admin**")
    if st.button("🚪 Logout", use_container_width=True):
        do_logout()
        st.rerun()

    st.divider()

    # ── Scanner controls ──
    st.markdown("### ⚙️ Scanner")
    MY_STOCKS = load_stocks()
    st.markdown(f"**Universe:** {len(MY_STOCKS)} NSE stocks")
    st.markdown(
        "**Criteria (all 4 must pass):**\n"
        "1. CMP > 30 DMA\n"
        "2. CMP > 50 DMA\n"
        "3. CMP > 200 DMA\n"
        "4. CAR rising for 10 straight days"
    )
    run_btn = st.button("🔍 Run Full Scan", use_container_width=True)
    if st.session_state.last_scan:
        st.caption(f"Last run: {st.session_state.last_scan}")

    st.divider()

    # ── Settings ──────────────────────────────────────────────────────────────
    st.markdown("### 🗂️ Stock Universe Settings")
    st.caption("Add or remove NSE symbols (e.g. RELIANCE.NS). One per line or comma-separated.")

    current_stocks = load_stocks()
    # Display as comma-separated in a text area
    raw_text = st.text_area(
        "Stock Symbols",
        value=", ".join(current_stocks),
        height=260,
        help="Comma-separated list of NSE ticker symbols with .NS suffix.",
        label_visibility="collapsed",
    )

    save_col, reset_col = st.columns(2)
    with save_col:
        if st.button("💾 Save", use_container_width=True):
            # Parse: split by comma OR newline, strip whitespace
            raw_tokens = [t.strip() for token in raw_text.replace("\n", ",").split(",")
                          for t in [token.strip()] if t.strip()]
            # Auto-append .NS if missing
            cleaned = []
            for sym in raw_tokens:
                sym = sym.upper()
                if not sym.endswith(".NS"):
                    sym += ".NS"
                cleaned.append(sym)
            cleaned = list(dict.fromkeys(cleaned))  # deduplicate, preserve order
            save_stocks(cleaned)
            # Reset scan so results reflect new universe
            st.session_state.df_results = None
            st.session_state.last_scan  = None
            st.session_state.scanned    = False
            st.success(f"✅ Saved {len(cleaned)} symbols. Re-run the scan to update results.")

    with reset_col:
        if st.button("↩️ Reload", use_container_width=True):
            st.rerun()

    st.markdown(
        f'<div class="stock-count-badge">📋 {len(current_stocks)} symbols loaded</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SCANNER LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Breakout Stocks")
    return buf.getvalue()


def scan_stock(ticker: str) -> dict | None:
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if data.empty or len(data) < 200:
            return None

        close   = data["Close"].squeeze()
        dma_30  = close.rolling(30).mean().iloc[-1]
        dma_50  = close.rolling(50).mean().iloc[-1]
        dma_200 = close.rolling(200).mean().iloc[-1]
        cmp     = close.iloc[-1]
        dist_200 = ((cmp - dma_200) / dma_200) * 100

        high_date = data.tail(252)["High"].squeeze().idxmax()
        car_data  = close.loc[high_date:]
        if len(car_data) < 10:
            return None

        car_rising = car_data.expanding().mean().tail(10).is_monotonic_increasing

        if cmp > dma_30 and cmp > dma_50 and cmp > dma_200 and car_rising:
            return {
                "Date"           : datetime.now().strftime("%d-%m-%Y"),
                "Stock"          : ticker.replace(".NS", ""),
                "CMP (₹)"        : round(float(cmp), 2),
                "30 DMA"         : round(float(dma_30), 2),
                "50 DMA"         : round(float(dma_50), 2),
                "200 DMA"        : round(float(dma_200), 2),
                "200 DMA Dist %" : round(float(dist_200), 2),
                "CAR Status"     : "✅ Positive",
                "Signal"         : "🟢 Breakout",
            }
    except Exception:
        pass
    return None


def run_scanner(ticker_list, progress_bar, status_placeholder):
    results = []
    total   = len(ticker_list)
    for i, ticker in enumerate(ticker_list, 1):
        label = ticker.replace(".NS", "")
        status_placeholder.caption(f"Scanning {label} ({i} / {total})…")
        progress_bar.progress(i / total)
        row = scan_stock(ticker)
        if row:
            results.append(row)
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("200 DMA Dist %", ascending=True).reset_index(drop=True)
    return df


# Auto-trigger on very first load
MY_STOCKS = load_stocks()
trigger   = run_btn or (not st.session_state.scanned)

if trigger:
    if not MY_STOCKS:
        st.warning("⚠️ No stocks configured. Add symbols in the Settings panel on the sidebar.")
    else:
        st.session_state.scanned = True
        with st.container():
            st.markdown(f"#### ⏳ Scanning — please wait ({len(MY_STOCKS)} stocks)…")
            pbar   = st.progress(0)
            status = st.empty()
            df     = run_scanner(MY_STOCKS, pbar, status)
            pbar.progress(1.0)
            status.empty()
        st.session_state.df_results = df
        st.session_state.last_scan  = datetime.now().strftime("%d-%m-%Y  %H:%M")
        st.rerun()


# ── Display results ─────────────────────────────────────────────────────────────
df = st.session_state.df_results

if df is not None:
    n     = len(df)
    total = len(MY_STOCKS)
    rate  = f"{n / total * 100:.1f}%" if total else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Stocks Scanned",  total)
    c2.metric("🟢 Breakouts Found", n)
    c3.metric("🎯 Hit Rate",        rate)
    c4.metric("🕐 Scanned At",      st.session_state.last_scan or "—")

    st.divider()

    if df.empty:
        st.info(
            "**No breakout stocks found today.**  \n"
            "All 4 criteria were not met by any stock in the current universe. "
            "Markets may be consolidating — try again after the session closes.",
            icon="🔎",
        )
    else:
        st.markdown(f"### 🟢 Breakout Stocks — {n} found")
        st.caption("Sorted by distance from 200 DMA (ascending — closest first)")

        def dist_colour(val):
            if isinstance(val, (int, float)):
                if val < 5:
                    return "background-color:#0d3322; color:#00d464"
                if val < 15:
                    return "background-color:#2e2800; color:#ffc800"
                return "background-color:#2e1200; color:#ff7755"
            return ""

        styled = (
            df.style
            .map(dist_colour, subset=["200 DMA Dist %"])
            .format({
                "CMP (₹)"        : "₹{:.2f}",
                "30 DMA"         : "₹{:.2f}",
                "50 DMA"         : "₹{:.2f}",
                "200 DMA"        : "₹{:.2f}",
                "200 DMA Dist %" : "{:.2f}%",
            })
            .hide(axis="index")
        )

        st.dataframe(styled, use_container_width=True, height=min(80 + n * 38, 680))

        st.download_button(
            label     = "⬇️  Download Excel",
            data      = to_excel(df),
            file_name = f"Breakout_Stocks_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
elif not trigger:
    st.info("Open the sidebar (top-left ›) and click **Run Full Scan** to begin.", icon="👈")

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">'
    "Data via Yahoo Finance · Not financial advice · For educational purposes only"
    "</div>",
    unsafe_allow_html=True,
)
