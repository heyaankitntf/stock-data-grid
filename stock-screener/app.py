import io
import json
import uuid
import warnings
import logging
import hashlib
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

# ── Constants ──────────────────────────────────────────────────────────────────
ADMIN_USERNAME  = "admin"
ADMIN_PASSWORD  = "admin123"
COOKIE_AUTH     = "screener_auth_v1"
COOKIE_THEME    = "screener_theme_v1"
COOKIE_TOKEN    = hashlib.sha256(b"screener_admin_nilesh_2026").hexdigest()
SETTINGS_FILE   = Path(__file__).parent / "settings.json"
PORTFOLIO_FILE  = Path(__file__).parent / "portfolio.json"
INITIAL_BALANCE = 1_000_000   # ₹10,00,000 virtual capital

# ── Cookie controller ──────────────────────────────────────────────────────────
cookies = CookieController()

# ══════════════════════════════════════════════════════════════════════════════
# THEME PALETTES
# ══════════════════════════════════════════════════════════════════════════════
PALETTES = {
    "dark": {
        "bg": "#0b1622", "bg2": "#0f2030", "bg3": "#162840",
        "surface": "#122035", "border": "#1e3a55",
        "text": "#d0e0f0", "text_muted": "#8ba8c4", "text_faint": "#3a5268",
        "accent": "#00d4aa", "accent2": "#96c93d",
        "hero_a": "#0f2027", "hero_b": "#203a43", "hero_c": "#2c5364",
        "metric_val": "#00d4aa",
        "dist_lo_bg": "#0d3322", "dist_lo_fg": "#00d464",
        "dist_mid_bg": "#2e2800", "dist_mid_fg": "#ffc800",
        "dist_hi_bg": "#2e1200", "dist_hi_fg": "#ff7755",
        "err_bg": "#2e1215", "err_border": "#7a1f28", "err_fg": "#ff7070",
        "badge_bg": "#0d3322", "badge_fg": "#00d464",
        "footer_border": "#1a2f42", "btn_text": "#ffffff",
        "input_bg": "#0f2030", "input_border": "#1e3a55",
        "profit_bg": "#0d3322", "profit_fg": "#00d464",
        "loss_bg":   "#2e1200", "loss_fg":   "#ff7755",
        "card_buy":  "#0d2e1a", "card_sell": "#2e1200",
        "label": "🌙 Dark",
    },
    "light": {
        "bg": "#f2f6fb", "bg2": "#ffffff", "bg3": "#e6eef7",
        "surface": "#ffffff", "border": "#c5d5e8",
        "text": "#162030", "text_muted": "#4a6080", "text_faint": "#8aa0b8",
        "accent": "#1565c0", "accent2": "#2e7d32",
        "hero_a": "#1565c0", "hero_b": "#1976d2", "hero_c": "#1e88e5",
        "metric_val": "#1565c0",
        "dist_lo_bg": "#c8f0d8", "dist_lo_fg": "#1b5e20",
        "dist_mid_bg": "#fff8e1", "dist_mid_fg": "#e65100",
        "dist_hi_bg": "#fce4ec", "dist_hi_fg": "#b71c1c",
        "err_bg": "#fce4ec", "err_border": "#e57373", "err_fg": "#b71c1c",
        "badge_bg": "#c8f0d8", "badge_fg": "#1b5e20",
        "footer_border": "#c5d5e8", "btn_text": "#ffffff",
        "input_bg": "#ffffff", "input_border": "#c5d5e8",
        "profit_bg": "#d0f0dc", "profit_fg": "#1b5e20",
        "loss_bg":   "#fce4ec", "loss_fg":   "#b71c1c",
        "card_buy":  "#e8f5e9", "card_sell": "#fce4ec",
        "label": "☀️ Light",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
def load_stocks() -> list[str]:
    try:
        data = json.loads(SETTINGS_FILE.read_text())
        return [s.strip() for s in data.get("stocks", []) if s.strip()]
    except Exception:
        return []

def save_stocks(stocks: list[str]):
    SETTINGS_FILE.write_text(json.dumps({"stocks": stocks}, indent=2))

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — PORTFOLIO
# ══════════════════════════════════════════════════════════════════════════════
def load_portfolio() -> dict:
    try:
        return json.loads(PORTFOLIO_FILE.read_text())
    except Exception:
        seed = {"initial_balance": INITIAL_BALANCE, "balance": INITIAL_BALANCE, "trades": []}
        PORTFOLIO_FILE.write_text(json.dumps(seed, indent=2))
        return seed

def save_portfolio(data: dict):
    PORTFOLIO_FILE.write_text(json.dumps(data, indent=2))

def compute_holdings(trades: list[dict]) -> dict:
    """Return {ticker: {qty, avg_price, total_invested}} from trade log."""
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
    # Remove zero/negative holdings, compute avg
    return {
        tk: {
            "qty":       v["qty"],
            "avg_price": round(v["total_cost"] / v["qty"], 2) if v["qty"] > 0 else 0,
            "invested":  round(v["total_cost"], 2),
            "stock":     tk.replace(".NS", ""),
        }
        for tk, v in h.items() if v["qty"] > 0
    }

def fetch_cmp_single(ticker: str) -> float | None:
    """Fetch latest close for one ticker quickly."""
    try:
        info = yf.Ticker(ticker).fast_info
        p = info.last_price
        return round(float(p), 2) if p else None
    except Exception:
        return None

def fetch_cmp_bulk(tickers: list[str]) -> dict[str, float]:
    """Fetch latest close for multiple tickers in one call."""
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
        result = {}
        for tk in tickers:
            try:
                result[tk] = round(float(closes[tk].dropna().iloc[-1]), 2)
            except Exception:
                pass
        return result
    except Exception:
        return {}

def execute_trade(ticker: str, stock: str, action: str, qty: int, price: float) -> tuple[bool, str]:
    """Execute a BUY or SELL, return (success, message)."""
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

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
def inject_css(p: dict):
    st.markdown(f"""
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background-color: {p['bg']} !important; color: {p['text']} !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebar"] {{
    background-color: {p['bg2']} !important;
    border-right: 1px solid {p['border']} !important;
}}
.block-container {{
    padding: 1.5rem 2rem 2rem !important; max-width: 1440px !important;
}}
@media (max-width: 768px) {{
    .block-container {{ padding: 1rem 0.75rem 1.5rem !important; }}
    [data-testid="stSidebar"] {{ width: 88vw !important; min-width: unset !important; }}
}}

/* ── Hero ── */
.hero {{
    background: linear-gradient(135deg,{p['hero_a']} 0%,{p['hero_b']} 50%,{p['hero_c']} 100%);
    border-radius: 14px; padding: 1.6rem 2rem; margin-bottom: 1.2rem;
}}
.hero h1 {{ font-size:1.7rem; font-weight:800; margin:0 0 .3rem; color:#fff; letter-spacing:-.4px; }}
.hero p  {{ font-size:.85rem; opacity:.82; margin:0; color:#e8f4ff; }}
@media (max-width:600px) {{
    .hero {{ padding:1.1rem 1rem; border-radius:10px; }}
    .hero h1 {{ font-size:1.15rem; }}
    .hero p  {{ font-size:.76rem; }}
}}

/* ── Tabs ── */
[data-testid="stTabs"] [data-testid="stTab"] {{
    font-weight: 600 !important; font-size: .92rem !important;
    padding: .5rem 1.2rem !important; border-radius: 8px 8px 0 0 !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {p['accent']} !important;
    border-bottom: 2px solid {p['accent']} !important;
}}
[data-testid="stTabContent"] {{ padding-top: 1.2rem !important; }}

/* ── Metrics ── */
[data-testid="stMetricLabel"]  {{ color:{p['text_muted']} !important; font-size:.78rem !important; }}
[data-testid="stMetricValue"]  {{ color:{p['metric_val']} !important; font-size:1.3rem !important; }}
[data-testid="metric-container"] {{
    background:{p['surface']}; border:1px solid {p['border']};
    border-radius:10px; padding:.85rem 1rem !important;
}}
@media (max-width:640px) {{
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        min-width:46% !important; flex:1 1 46% !important;
    }}
    [data-testid="stMetricValue"] {{ font-size:1rem !important; }}
}}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(90deg,{p['accent']},{p['accent2']}) !important;
    color:{p['btn_text']} !important; font-weight:700 !important;
    border:none !important; border-radius:8px !important; width:100%;
}}
.stButton > button:hover {{ filter:brightness(1.1); }}
[data-testid="stDownloadButton"] > button {{
    background:transparent !important; border:2px solid {p['accent']} !important;
    color:{p['accent']} !important; font-weight:600 !important;
}}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    background:{p['input_bg']} !important; border:1px solid {p['input_border']} !important;
    color:{p['text']} !important; border-radius:8px !important;
}}
[data-baseweb="select"] > div {{
    background:{p['input_bg']} !important; border-color:{p['input_border']} !important;
    color:{p['text']} !important;
}}
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stRadio"] label  {{ color:{p['text']} !important; }}
[data-testid="stCheckbox"] label {{ color:{p['text']} !important; }}

/* ── Progress ── */
.stProgress > div > div {{
    background: linear-gradient(90deg,{p['accent']},{p['accent2']}) !important;
}}

/* ── Trade card ── */
.trade-card {{
    background:{p['surface']}; border:1px solid {p['border']};
    border-radius:12px; padding:1.2rem 1.4rem; margin-bottom:1rem;
}}
.trade-card h4 {{ margin:0 0 .8rem; font-size:1rem; color:{p['text']}; font-weight:700; }}

/* ── P&L badge ── */
.pnl-profit {{
    display:inline-block; background:{p['profit_bg']}; color:{p['profit_fg']};
    border-radius:6px; padding:2px 10px; font-weight:700; font-size:.85rem;
}}
.pnl-loss {{
    display:inline-block; background:{p['loss_bg']}; color:{p['loss_fg']};
    border-radius:6px; padding:2px 10px; font-weight:700; font-size:.85rem;
}}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {{ border-radius:10px; overflow:hidden; }}
@media (max-width:768px) {{
    [data-testid="stDataFrame"] > div {{ overflow-x:auto !important; }}
}}

/* ── Misc ── */
hr {{ border-color:{p['border']} !important; opacity:.6; }}
[data-testid="stAlert"] {{
    border-radius:10px !important; background:{p['bg3']} !important;
    border-color:{p['border']} !important; color:{p['text']} !important;
}}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong {{ color:{p['text']} !important; }}
[data-testid="stCaptionContainer"] {{ color:{p['text_muted']} !important; }}
.stock-badge {{
    display:inline-block; background:{p['badge_bg']}; color:{p['badge_fg']};
    border-radius:6px; padding:3px 12px; font-size:.82rem; font-weight:600;
}}
.footer {{
    text-align:center; color:{p['text_faint']}; font-size:.75rem;
    margin-top:2.5rem; padding-top:1rem; border-top:1px solid {p['footer_border']};
}}
[data-testid="stRadio"] label {{ color:{p['text']} !important; }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# THEME BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════
if "theme" not in st.session_state:
    saved = cookies.get(COOKIE_THEME)
    st.session_state.theme = saved if saved in PALETTES else "dark"

P = PALETTES[st.session_state.theme]
inject_css(P)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
def do_login(username: str, password: str, remember: bool) -> bool:
    if username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        if remember:
            cookies.set(COOKIE_AUTH, COOKIE_TOKEN, max_age=30 * 24 * 3600)
        return True
    return False

def do_logout():
    for k in ("authenticated", "df_results", "last_scan", "scanned",
              "trade_preview", "portfolio_prices"):
        st.session_state.pop(k, None)
    try:
        cookies.remove(COOKIE_AUTH)
    except Exception:
        pass

# Read the cookie on every render — it returns None on the very first render
# (JS bridge hasn't fired yet) and the real value on every subsequent rerun.
_auth_cookie = cookies.get(COOKIE_AUTH)

# If cookie is valid but session says unauthenticated → promote immediately.
# This is what makes "Remember me" work on page refresh:
#   Render 1 → cookie = None → authenticated = False → login shown
#   Cookie component fires → Streamlit reruns
#   Render 2 → cookie = TOKEN → this block runs → authenticated = True → dashboard shown
if _auth_cookie == COOKIE_TOKEN and not st.session_state.get("authenticated", False):
    st.session_state.authenticated = True

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown(f"""
<style>
.block-container {{
    max-width:440px !important; margin:0 auto !important;
    padding-top:5rem !important; padding-left:1.2rem !important; padding-right:1.2rem !important;
}}
@media (max-width:480px) {{ .block-container {{ padding-top:2.5rem !important; }} }}
</style>
<div style="background:{P['bg2']};border:1px solid {P['border']};border-radius:16px;
    padding:2.2rem 2.4rem 1.6rem;box-shadow:0 16px 48px rgba(0,0,0,.22);margin-bottom:1.2rem;">
  <div style="font-size:1.5rem;font-weight:800;color:{P['text']};letter-spacing:-.4px;margin-bottom:.2rem;">
    📈 Breakout Scanner
  </div>
  <div style="font-size:.85rem;color:{P['text_muted']};">Sign in to access the dashboard</div>
</div>
""", unsafe_allow_html=True)
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
    st.markdown('<div class="footer">Authorised access only · Not financial advice</div>',
                unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("df_results", None), ("last_scan", None), ("scanned", False),
             ("trade_preview", None), ("portfolio_prices", {})]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("👤 **admin**")
    if st.button("🚪 Logout", use_container_width=True):
        do_logout()
        st.rerun()

    st.divider()

    st.markdown("### 🔍 Scanner")
    MY_STOCKS_SIDEBAR = load_stocks()
    st.markdown(f"**Universe:** {len(MY_STOCKS_SIDEBAR)} stocks")
    st.markdown("**Criteria (all 4):**\n- CMP > 30 DMA\n- CMP > 50 DMA\n- CMP > 200 DMA\n- CAR rising 10 days")
    run_btn = st.button("▶ Run Full Scan", use_container_width=True)
    if st.session_state.last_scan:
        st.caption(f"Last run: {st.session_state.last_scan}")

    st.divider()

    st.markdown("### 🎨 Appearance")
    chosen_theme = st.radio(
        "Theme", options=["dark", "light"],
        format_func=lambda x: PALETTES[x]["label"],
        index=0 if st.session_state.theme == "dark" else 1,
        horizontal=True, label_visibility="collapsed",
    )
    if chosen_theme != st.session_state.theme:
        st.session_state.theme = chosen_theme
        cookies.set(COOKIE_THEME, chosen_theme, max_age=365 * 24 * 3600)
        st.rerun()

    st.divider()

    st.markdown("### 🗂️ Stock Universe")
    st.caption("One per line or comma-separated. `.NS` auto-added.")
    current_stocks = load_stocks()
    raw_text = st.text_area("symbols", value=", ".join(current_stocks),
                            height=200, label_visibility="collapsed")
    sc, rc = st.columns(2)
    with sc:
        if st.button("💾 Save", use_container_width=True):
            tokens  = [t.strip() for chunk in raw_text.replace("\n", ",").split(",")
                       for t in [chunk.strip()] if t.strip()]
            cleaned = list(dict.fromkeys(
                sym.upper() if sym.upper().endswith(".NS") else sym.upper() + ".NS"
                for sym in tokens
            ))
            save_stocks(cleaned)
            st.session_state.df_results = None
            st.session_state.last_scan  = None
            st.session_state.scanned    = False
            st.success(f"✅ Saved {len(cleaned)} symbols.")
    with rc:
        if st.button("↩️ Reload", use_container_width=True):
            st.rerun()
    st.markdown(f'<div class="stock-badge">📋 {len(current_stocks)} symbols</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <h1>📈 CAR + DMA Super Breakout Scanner</h1>
  <p>NSE stocks above 30 / 50 / 200 DMA with monotonically rising CAR — plus mock trading with live P&amp;L.</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_scanner, tab_trading = st.tabs(["📊 Scanner", "💼 Mock Trading"])


# ════════════════════════════════════════════════════════════════════════
# TAB 1 — SCANNER
# ════════════════════════════════════════════════════════════════════════
with tab_scanner:

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
            close    = data["Close"].squeeze()
            dma_30   = close.rolling(30).mean().iloc[-1]
            dma_50   = close.rolling(50).mean().iloc[-1]
            dma_200  = close.rolling(200).mean().iloc[-1]
            cmp      = close.iloc[-1]
            dist_200 = ((cmp - dma_200) / dma_200) * 100
            high_date  = data.tail(252)["High"].squeeze().idxmax()
            car_data   = close.loc[high_date:]
            if len(car_data) < 10:
                return None
            car_rising = car_data.expanding().mean().tail(10).is_monotonic_increasing
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
        except Exception:
            pass
        return None

    def run_scanner(ticker_list, pbar, status):
        results = []
        total   = len(ticker_list)
        for i, ticker in enumerate(ticker_list, 1):
            status.caption(f"Scanning {ticker.replace('.NS','')} ({i}/{total})…")
            pbar.progress(i / total)
            row = scan_stock(ticker)
            if row:
                results.append(row)
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("200 DMA Dist %", ascending=True).reset_index(drop=True)
        return df

    MY_STOCKS = load_stocks()
    trigger   = run_btn or (not st.session_state.scanned)

    if trigger:
        if not MY_STOCKS:
            st.warning("⚠️ No stocks configured — add symbols in the sidebar.")
        else:
            st.session_state.scanned = True
            st.markdown(f"#### ⏳ Scanning {len(MY_STOCKS)} stocks — please wait…")
            pbar   = st.progress(0)
            status = st.empty()
            df     = run_scanner(MY_STOCKS, pbar, status)
            pbar.progress(1.0)
            status.empty()
            st.session_state.df_results = df
            st.session_state.last_scan  = datetime.now().strftime("%d-%m-%Y  %H:%M")
            st.rerun()

    df = st.session_state.df_results
    if df is not None:
        n     = len(df)
        total = len(MY_STOCKS)
        rate  = f"{n / total * 100:.1f}%" if total else "—"
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📊 Scanned",   total)
        c2.metric("🟢 Breakouts", n)
        c3.metric("🎯 Hit Rate",  rate)
        c4.metric("🕐 Last Scan", st.session_state.last_scan or "—")
        st.divider()

        if df.empty:
            st.info("**No breakout stocks found today.** Markets may be consolidating.", icon="🔎")
        else:
            st.markdown(f"### 🟢 Breakout Stocks — {n} found")
            st.caption("Sorted by distance from 200 DMA · closest first")

            def dist_colour(val):
                if isinstance(val, (int, float)):
                    if val < 5:
                        return f"background-color:{P['dist_lo_bg']}; color:{P['dist_lo_fg']}"
                    if val < 15:
                        return f"background-color:{P['dist_mid_bg']}; color:{P['dist_mid_fg']}"
                    return f"background-color:{P['dist_hi_bg']}; color:{P['dist_hi_fg']}"
                return ""

            styled = (
                df.style
                .map(dist_colour, subset=["200 DMA Dist %"])
                .format({
                    "CMP (₹)": "₹{:.2f}", "30 DMA": "₹{:.2f}",
                    "50 DMA": "₹{:.2f}",  "200 DMA": "₹{:.2f}",
                    "200 DMA Dist %": "{:.2f}%",
                })
                .hide(axis="index")
            )
            st.dataframe(styled, use_container_width=True, height=min(80 + n * 38, 680))
            st.download_button(
                label="⬇️  Download Excel", data=to_excel(df),
                file_name=f"Breakout_Stocks_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    elif not trigger:
        st.info("Open the sidebar (☰) and tap **Run Full Scan** to begin.", icon="👈")


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — MOCK TRADING
# ════════════════════════════════════════════════════════════════════════
with tab_trading:

    port      = load_portfolio()
    holdings  = compute_holdings(port["trades"])
    MY_STOCKS = load_stocks()

    # ── 1. PORTFOLIO SUMMARY ──────────────────────────────────────────────────
    st.markdown("### 💼 Portfolio Overview")

    # Fetch live prices for all holdings (cached in session state)
    held_tickers = list(holdings.keys())
    cached_prices: dict[str, float] = st.session_state.portfolio_prices

    # Auto-fetch on first open if holdings exist and cache is empty
    if held_tickers and not any(t in cached_prices for t in held_tickers):
        with st.spinner("Fetching live prices…"):
            fresh = fetch_cmp_bulk(held_tickers)
            st.session_state.portfolio_prices = {**cached_prices, **fresh}
            cached_prices = st.session_state.portfolio_prices

    # Compute totals
    total_invested    = sum(h["invested"] for h in holdings.values())
    total_current_val = sum(
        holdings[tk]["qty"] * cached_prices.get(tk, holdings[tk]["avg_price"])
        for tk in holdings
    )
    overall_pnl     = total_current_val - total_invested
    overall_pnl_pct = (overall_pnl / total_invested * 100) if total_invested else 0
    portfolio_value = port["balance"] + total_current_val   # cash + equity

    # Metrics row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💰 Cash Balance",   f"₹{port['balance']:,.0f}")
    m2.metric("📥 Invested",       f"₹{total_invested:,.0f}")
    m3.metric("📈 Current Value",  f"₹{total_current_val:,.0f}",
              delta=f"₹{overall_pnl:+,.0f}" if total_invested else None)
    m4.metric("💹 Overall P&L",    f"₹{overall_pnl:+,.0f}",
              delta=f"{overall_pnl_pct:+.2f}%" if total_invested else None)
    m5.metric("🏦 Portfolio Value", f"₹{portfolio_value:,.0f}")

    # Refresh + Reset row
    ref_col, _, reset_col = st.columns([1, 3, 1])
    with ref_col:
        if st.button("🔄 Refresh Prices", use_container_width=True):
            if held_tickers:
                with st.spinner("Fetching live prices…"):
                    fresh = fetch_cmp_bulk(held_tickers)
                    st.session_state.portfolio_prices = {**cached_prices, **fresh}
                st.rerun()
    with reset_col:
        if st.button("🗑️ Reset Portfolio", use_container_width=True):
            st.session_state["_confirm_reset"] = True

    if st.session_state.get("_confirm_reset"):
        st.warning("This will wipe all trades and restore ₹10,00,000 balance. Are you sure?")
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button("✅ Yes, Reset", use_container_width=True):
                save_portfolio({"initial_balance": INITIAL_BALANCE,
                                "balance": INITIAL_BALANCE, "trades": []})
                st.session_state.portfolio_prices = {}
                st.session_state.pop("_confirm_reset", None)
                st.rerun()
        with no_col:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.pop("_confirm_reset", None)
                st.rerun()

    st.divider()

    # ── 2. HOLDINGS TABLE ─────────────────────────────────────────────────────
    st.markdown("### 📋 Holdings")
    if not holdings:
        st.info("No open positions yet. Place your first trade below.", icon="📭")
    else:
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

        def pnl_style(val):
            if not isinstance(val, (int, float)):
                return ""
            if val > 0:
                return f"background-color:{P['profit_bg']};color:{P['profit_fg']};font-weight:700"
            if val < 0:
                return f"background-color:{P['loss_bg']};color:{P['loss_fg']};font-weight:700"
            return ""

        fmt = {
            "Avg Buy (₹)":   "₹{:.2f}", "Invested (₹)": "₹{:,.0f}",
        }
        # Only format numeric columns that exist as numbers
        for col in ["Live CMP (₹)", "Cur Value (₹)", "P&L (₹)"]:
            if h_df[col].apply(lambda x: isinstance(x, (int, float))).all():
                fmt[col] = "₹{:,.2f}"
        if h_df["P&L %"].apply(lambda x: isinstance(x, (int, float))).all():
            fmt["P&L %"] = "{:+.2f}%"

        styled_h = (
            h_df.style
            .map(pnl_style, subset=["P&L (₹)", "P&L %"])
            .format(fmt, na_rep="—")
            .hide(axis="index")
        )
        st.dataframe(styled_h, use_container_width=True,
                     height=min(80 + len(rows) * 40, 500))

    st.divider()

    # ── 3. TRADE FORM ─────────────────────────────────────────────────────────
    st.markdown("### 🛒 Place a Trade")

    stock_options = MY_STOCKS if MY_STOCKS else ["—"]
    trade_col, preview_col = st.columns([1, 1], gap="large")

    with trade_col:
        st.markdown(f'<div class="trade-card"><h4>📝 Order Details</h4>', unsafe_allow_html=True)

        selected_ticker = st.selectbox(
            "Select Stock",
            options=stock_options,
            format_func=lambda x: x.replace(".NS", "") if x != "—" else "—",
        )
        action = st.radio("Action", ["BUY", "SELL"], horizontal=True,
                          format_func=lambda x: f"🟢 {x}" if x == "BUY" else f"🔴 {x}")
        qty    = st.number_input("Quantity (shares)", min_value=1, max_value=100000,
                                 value=1, step=1)

        fetch_btn = st.button("📡 Get Live Price", use_container_width=True)
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
        # Sync qty/action into preview if user changed them
        if tp and (tp.get("ticker") == selected_ticker):
            tp["qty"]    = qty
            tp["action"] = action

        if tp and tp.get("ticker") == selected_ticker:
            total_val = tp["price"] * tp["qty"]
            is_buy    = tp["action"] == "BUY"
            card_bg   = P["card_buy"] if is_buy else P["card_sell"]
            action_lbl = "🟢 BUY" if is_buy else "🔴 SELL"

            st.markdown(f"""
<div style="background:{card_bg};border:1px solid {P['border']};border-radius:12px;
     padding:1.2rem 1.4rem;margin-bottom:1rem;">
  <div style="font-size:1.05rem;font-weight:800;color:{P['text']};margin-bottom:.6rem;">
    {action_lbl} · {tp['stock']}
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:.88rem;color:{P['text']};">
    <tr><td style="padding:3px 0;color:{P['text_muted']}">Live CMP</td>
        <td style="text-align:right;font-weight:700;">₹{tp['price']:,.2f}</td></tr>
    <tr><td style="padding:3px 0;color:{P['text_muted']}">Quantity</td>
        <td style="text-align:right;font-weight:700;">{tp['qty']}</td></tr>
    <tr><td style="padding:3px 0;color:{P['text_muted']}">Total Value</td>
        <td style="text-align:right;font-weight:700;">₹{total_val:,.0f}</td></tr>
    <tr><td style="padding:3px 0;color:{P['text_muted']}">Cash Balance</td>
        <td style="text-align:right;">₹{port['balance']:,.0f}</td></tr>
    <tr><td style="padding:3px 0;color:{P['text_muted']}">Fetched at</td>
        <td style="text-align:right;">{tp['ts']}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

            if st.button(f"✅ Confirm {action_lbl}", use_container_width=True):
                ok, msg = execute_trade(tp["ticker"], tp["stock"],
                                        tp["action"], tp["qty"], tp["price"])
                if ok:
                    st.success(f"✅ {msg}")
                    st.session_state.trade_preview    = None
                    st.session_state.portfolio_prices = {}  # force price refresh
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
        else:
            st.markdown(f"""
<div style="background:{P['surface']};border:1px dashed {P['border']};border-radius:12px;
     padding:2rem;text-align:center;color:{P['text_muted']};">
  <div style="font-size:2rem;margin-bottom:.5rem;">📡</div>
  <div>Select a stock and click<br><strong>Get Live Price</strong> to see the order preview.</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── 4. TRADE HISTORY ──────────────────────────────────────────────────────
    trades = port.get("trades", [])
    with st.expander(f"📜 Trade History ({len(trades)} trades)", expanded=False):
        if not trades:
            st.caption("No trades yet.")
        else:
            hist_rows = []
            running_balance = port["initial_balance"]
            for t in reversed(trades):   # newest first
                hist_rows.append({
                    "Date / Time":  t["timestamp"],
                    "Stock":        t["stock"],
                    "Action":       t["action"],
                    "Qty":          t["qty"],
                    "Price (₹)":    t["price"],
                    "Value (₹)":    t["value"],
                })

            hist_df = pd.DataFrame(hist_rows)

            def action_style(val):
                if val == "BUY":
                    return f"background-color:{P['profit_bg']};color:{P['profit_fg']};font-weight:700"
                return f"background-color:{P['loss_bg']};color:{P['loss_fg']};font-weight:700"

            styled_hist = (
                hist_df.style
                .map(action_style, subset=["Action"])
                .format({"Price (₹)": "₹{:,.2f}", "Value (₹)": "₹{:,.0f}"})
                .hide(axis="index")
            )
            st.dataframe(styled_hist, use_container_width=True,
                         height=min(80 + len(hist_rows) * 38, 420))

            st.download_button(
                label="⬇️ Export Trade History",
                data=hist_df.to_csv(index=False).encode(),
                file_name=f"Trade_History_{datetime.now().strftime('%d-%m-%Y')}.csv",
                mime="text/csv",
            )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">Data via Yahoo Finance · Mock trading only · Not financial advice · Educational use</div>',
    unsafe_allow_html=True,
)
