import io
import json
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
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
COOKIE_AUTH    = "screener_auth_v1"
COOKIE_THEME   = "screener_theme_v1"
COOKIE_TOKEN   = hashlib.sha256(b"screener_admin_nilesh_2026").hexdigest()
SETTINGS_FILE  = Path(__file__).parent / "settings.json"

# ── Cookie controller ──────────────────────────────────────────────────────────
cookies = CookieController()

# ── Theme palettes ─────────────────────────────────────────────────────────────
PALETTES = {
    "dark": {
        "bg":               "#0b1622",
        "bg2":              "#0f2030",
        "bg3":              "#162840",
        "surface":          "#122035",
        "border":           "#1e3a55",
        "text":             "#d0e0f0",
        "text_muted":       "#8ba8c4",
        "text_faint":       "#3a5268",
        "accent":           "#00d4aa",
        "accent2":          "#96c93d",
        "hero_a":           "#0f2027",
        "hero_b":           "#203a43",
        "hero_c":           "#2c5364",
        "metric_val":       "#00d4aa",
        "dist_lo_bg":       "#0d3322",  "dist_lo_fg":  "#00d464",
        "dist_mid_bg":      "#2e2800",  "dist_mid_fg": "#ffc800",
        "dist_hi_bg":       "#2e1200",  "dist_hi_fg":  "#ff7755",
        "err_bg":           "#2e1215",  "err_border":  "#7a1f28", "err_fg": "#ff7070",
        "badge_bg":         "#0d3322",  "badge_fg":    "#00d464",
        "footer_border":    "#1a2f42",
        "btn_text":         "#ffffff",
        "input_bg":         "#0f2030",
        "input_border":     "#1e3a55",
        "label":            "🌙 Dark",
    },
    "light": {
        "bg":               "#f2f6fb",
        "bg2":              "#ffffff",
        "bg3":              "#e6eef7",
        "surface":          "#ffffff",
        "border":           "#c5d5e8",
        "text":             "#162030",
        "text_muted":       "#4a6080",
        "text_faint":       "#8aa0b8",
        "accent":           "#1565c0",
        "accent2":          "#2e7d32",
        "hero_a":           "#1565c0",
        "hero_b":           "#1976d2",
        "hero_c":           "#1e88e5",
        "metric_val":       "#1565c0",
        "dist_lo_bg":       "#c8f0d8",  "dist_lo_fg":  "#1b5e20",
        "dist_mid_bg":      "#fff8e1",  "dist_mid_fg": "#e65100",
        "dist_hi_bg":       "#fce4ec",  "dist_hi_fg":  "#b71c1c",
        "err_bg":           "#fce4ec",  "err_border":  "#e57373", "err_fg": "#b71c1c",
        "badge_bg":         "#c8f0d8",  "badge_fg":    "#1b5e20",
        "footer_border":    "#c5d5e8",
        "btn_text":         "#ffffff",
        "input_bg":         "#ffffff",
        "input_border":     "#c5d5e8",
        "label":            "☀️ Light",
    },
}

# ── Settings helpers ───────────────────────────────────────────────────────────
def load_stocks() -> list[str]:
    try:
        data = json.loads(SETTINGS_FILE.read_text())
        return [s.strip() for s in data.get("stocks", []) if s.strip()]
    except Exception:
        return []

def save_stocks(stocks: list[str]):
    SETTINGS_FILE.write_text(json.dumps({"stocks": stocks}, indent=2))

# ── CSS injection ──────────────────────────────────────────────────────────────
def inject_css(p: dict):
    st.markdown(f"""
<style>
/* ═══════════════════════ RESET / GLOBAL ═══════════════════════ */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background-color: {p['bg']} !important;
    color: {p['text']} !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stSidebar"] {{
    background-color: {p['bg2']} !important;
    border-right: 1px solid {p['border']} !important;
}}
/* main block padding — tighter on mobile */
.block-container {{
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1400px !important;
}}
@media (max-width: 768px) {{
    .block-container {{ padding: 1rem 0.75rem 1.5rem !important; }}
    [data-testid="stSidebar"] {{ width: 88vw !important; min-width: unset !important; }}
}}

/* ═══════════════════════ LOGIN PAGE ═══════════════════════════ */
.login-outer {{
    min-height: 78vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 1.5rem 1rem;
}}
.login-card {{
    background: {p['bg2']};
    border: 1px solid {p['border']};
    border-radius: 18px;
    padding: 2.4rem 2.6rem;
    width: 100%; max-width: 400px;
    box-shadow: 0 16px 48px rgba(0,0,0,.25);
}}
@media (max-width: 480px) {{
    .login-card {{ padding: 1.8rem 1.4rem; border-radius: 14px; }}
}}
.login-title {{
    font-size: 1.5rem; font-weight: 800;
    color: {p['text']}; margin: 0 0 .2rem;
    letter-spacing: -.4px;
}}
.login-sub {{
    font-size: .85rem; color: {p['text_muted']}; margin: 0 0 1.4rem;
}}

/* ═══════════════════════ HERO ═════════════════════════════════ */
.hero {{
    background: linear-gradient(135deg, {p['hero_a']} 0%, {p['hero_b']} 50%, {p['hero_c']} 100%);
    border-radius: 14px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.4rem;
}}
.hero h1 {{
    font-size: 1.75rem; font-weight: 800;
    margin: 0 0 .35rem; letter-spacing: -.4px;
    color: #ffffff;
}}
.hero p {{ font-size: .88rem; opacity: .82; margin: 0; color: #e8f4ff; }}
@media (max-width: 600px) {{
    .hero {{ padding: 1.2rem 1.2rem; border-radius: 10px; }}
    .hero h1 {{ font-size: 1.2rem; }}
    .hero p  {{ font-size: .78rem; }}
}}

/* ═══════════════════════ METRICS ══════════════════════════════ */
[data-testid="stMetricLabel"] {{
    color: {p['text_muted']} !important; font-size: .78rem !important;
}}
[data-testid="stMetricValue"] {{
    color: {p['metric_val']} !important; font-size: 1.35rem !important;
}}
[data-testid="metric-container"] {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: .9rem 1rem !important;
}}
/* on very small screens let 4 metric columns wrap into 2×2 */
@media (max-width: 640px) {{
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        min-width: 46% !important;
        flex: 1 1 46% !important;
        flex-wrap: wrap !important;
    }}
    [data-testid="stMetricValue"] {{ font-size: 1.05rem !important; }}
}}

/* ═══════════════════════ BUTTONS ══════════════════════════════ */
.stButton > button {{
    background: linear-gradient(90deg, {p['accent']}, {p['accent2']}) !important;
    color: {p['btn_text']} !important; font-weight: 700 !important;
    border: none !important; border-radius: 8px !important;
    width: 100%;
}}
.stButton > button:hover {{ filter: brightness(1.1); }}

/* download button — keep it as an outline style */
[data-testid="stDownloadButton"] > button {{
    background: transparent !important;
    border: 2px solid {p['accent']} !important;
    color: {p['accent']} !important;
    font-weight: 600 !important;
}}

/* ═══════════════════════ FORM INPUTS ══════════════════════════ */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
    background: {p['input_bg']} !important;
    border: 1px solid {p['input_border']} !important;
    color: {p['text']} !important;
    border-radius: 8px !important;
}}
[data-baseweb="select"] > div {{
    background: {p['input_bg']} !important;
    border-color: {p['input_border']} !important;
    color: {p['text']} !important;
}}

/* ═══════════════════════ PROGRESS ═════════════════════════════ */
.stProgress > div > div {{
    background: linear-gradient(90deg, {p['accent']}, {p['accent2']}) !important;
}}

/* ═══════════════════════ DATAFRAME ════════════════════════════ */
[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}
/* horizontal scroll on mobile */
@media (max-width: 768px) {{
    [data-testid="stDataFrame"] > div {{ overflow-x: auto !important; }}
}}

/* ═══════════════════════ SIDEBAR ELEMENTS ═════════════════════ */
.sidebar-section {{
    background: {p['bg3']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: .9rem 1rem;
    margin-bottom: .75rem;
}}
.stock-badge {{
    display: inline-block;
    background: {p['badge_bg']}; color: {p['badge_fg']};
    border-radius: 6px; padding: 3px 12px;
    font-size: .82rem; font-weight: 600;
}}

/* ═══════════════════════ DIVIDER ══════════════════════════════ */
hr {{ border-color: {p['border']} !important; opacity: .6; }}

/* ═══════════════════════ ALERT / INFO ═════════════════════════ */
[data-testid="stAlert"] {{
    border-radius: 10px !important;
    background: {p['bg3']} !important;
    border-color: {p['border']} !important;
    color: {p['text']} !important;
}}

/* ═══════════════════════ CHECKBOX ═════════════════════════════ */
[data-testid="stCheckbox"] label {{ color: {p['text']} !important; }}

/* ═══════════════════════ MARKDOWN ═════════════════════════════ */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong {{
    color: {p['text']} !important;
}}
[data-testid="stCaptionContainer"] {{ color: {p['text_muted']} !important; }}

/* ═══════════════════════ FOOTER ═══════════════════════════════ */
.footer {{
    text-align: center; color: {p['text_faint']}; font-size: .75rem;
    margin-top: 2.5rem; padding-top: 1rem;
    border-top: 1px solid {p['footer_border']};
}}
@media (max-width: 480px) {{ .footer {{ font-size: .68rem; }} }}

/* ═══════════════════════ RADIO (theme toggle) ══════════════════ */
[data-testid="stRadio"] label {{ color: {p['text']} !important; }}
[data-testid="stRadio"] > div {{ gap: .4rem; }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# THEME BOOTSTRAP  (read cookie → session state)
# ══════════════════════════════════════════════════════════════════════════════
if "theme" not in st.session_state:
    saved = cookies.get(COOKIE_THEME)
    st.session_state.theme = saved if saved in PALETTES else "dark"

P = PALETTES[st.session_state.theme]   # active palette
inject_css(P)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def check_cookie_auth() -> bool:
    try:
        return cookies.get(COOKIE_AUTH) == COOKIE_TOKEN
    except Exception:
        return False

def do_login(username: str, password: str, remember: bool) -> bool:
    if username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        if remember:
            cookies.set(COOKIE_AUTH, COOKIE_TOKEN, max_age=30 * 24 * 3600)
        return True
    return False

def do_logout():
    for k in ("authenticated", "df_results", "last_scan", "scanned"):
        st.session_state.pop(k, None)
    try:
        cookies.remove(COOKIE_AUTH)
    except Exception:
        pass

if "authenticated" not in st.session_state:
    st.session_state.authenticated = check_cookie_auth()


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    # Narrow + centre the block container for the login page only
    st.markdown(f"""
<style>
.block-container {{
    max-width: 440px !important;
    margin: 0 auto !important;
    padding-top: 5rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
}}
@media (max-width: 480px) {{
    .block-container {{ padding-top: 2.5rem !important; }}
}}
</style>
<div style="
    background:{P['bg2']};
    border:1px solid {P['border']};
    border-radius:16px;
    padding:2.2rem 2.4rem 1.6rem;
    box-shadow:0 16px 48px rgba(0,0,0,.22);
    margin-bottom:1.2rem;
">
  <div style="font-size:1.5rem;font-weight:800;color:{P['text']};letter-spacing:-.4px;margin-bottom:.2rem;">
    📈 Breakout Scanner
  </div>
  <div style="font-size:.85rem;color:{P['text_muted']};margin-bottom:.2rem;">
    Sign in to access the dashboard
  </div>
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

    st.markdown(
        '<div class="footer">Authorised access only · Not financial advice</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("df_results", None), ("last_scan", None), ("scanned", False)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── User ──────────────────────────────────────────────────────────────────
    st.markdown(f"👤 **admin**")
    if st.button("🚪 Logout", use_container_width=True):
        do_logout()
        st.rerun()

    st.divider()

    # ── Scanner ───────────────────────────────────────────────────────────────
    st.markdown("### 🔍 Scanner")
    MY_STOCKS = load_stocks()
    st.markdown(f"**Universe:** {len(MY_STOCKS)} stocks")
    st.markdown(
        "**Criteria (all 4):**\n"
        "- CMP > 30 DMA\n- CMP > 50 DMA\n- CMP > 200 DMA\n- CAR rising 10 days"
    )
    run_btn = st.button("▶ Run Full Scan", use_container_width=True)
    if st.session_state.last_scan:
        st.caption(f"Last run: {st.session_state.last_scan}")

    st.divider()

    # ── Theme ─────────────────────────────────────────────────────────────────
    st.markdown("### 🎨 Appearance")
    chosen_theme = st.radio(
        "Theme",
        options=["dark", "light"],
        format_func=lambda x: PALETTES[x]["label"],
        index=0 if st.session_state.theme == "dark" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    if chosen_theme != st.session_state.theme:
        st.session_state.theme = chosen_theme
        cookies.set(COOKIE_THEME, chosen_theme, max_age=365 * 24 * 3600)
        st.rerun()

    st.divider()

    # ── Stock Settings ────────────────────────────────────────────────────────
    st.markdown("### 🗂️ Stock Universe")
    st.caption("One per line or comma-separated. `.NS` is added automatically.")

    current_stocks = load_stocks()
    raw_text = st.text_area(
        "symbols",
        value=", ".join(current_stocks),
        height=240,
        label_visibility="collapsed",
    )

    sc, rc = st.columns(2)
    with sc:
        if st.button("💾 Save", use_container_width=True):
            tokens = [t.strip()
                      for chunk in raw_text.replace("\n", ",").split(",")
                      for t in [chunk.strip()] if t.strip()]
            cleaned = []
            for sym in tokens:
                sym = sym.upper()
                if not sym.endswith(".NS"):
                    sym += ".NS"
                cleaned.append(sym)
            cleaned = list(dict.fromkeys(cleaned))
            save_stocks(cleaned)
            st.session_state.df_results = None
            st.session_state.last_scan  = None
            st.session_state.scanned    = False
            st.success(f"✅ Saved {len(cleaned)} symbols.")
    with rc:
        if st.button("↩️ Reload", use_container_width=True):
            st.rerun()

    st.markdown(
        f'<div class="stock-badge">📋 {len(current_stocks)} symbols</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <h1>📈 CAR + DMA Super Breakout Scanner</h1>
  <p>NSE stocks simultaneously above their 30‑day, 50‑day &amp; 200‑day moving averages,
  with a Cumulative Average Return (CAR) rising monotonically for the past 10 sessions.</p>
</div>
""", unsafe_allow_html=True)


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
        close    = data["Close"].squeeze()
        dma_30   = close.rolling(30).mean().iloc[-1]
        dma_50   = close.rolling(50).mean().iloc[-1]
        dma_200  = close.rolling(200).mean().iloc[-1]
        cmp      = close.iloc[-1]
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
        st.warning("⚠️ No stocks configured — add symbols in the sidebar Settings.")
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


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
df = st.session_state.df_results

if df is not None:
    n     = len(df)
    total = len(MY_STOCKS)
    rate  = f"{n / total * 100:.1f}%" if total else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Scanned",        total)
    c2.metric("🟢 Breakouts",      n)
    c3.metric("🎯 Hit Rate",       rate)
    c4.metric("🕐 Last Scan",      st.session_state.last_scan or "—")

    st.divider()

    if df.empty:
        st.info(
            "**No breakout stocks found today.** All 4 criteria were not met by any stock "
            "in the current universe. Markets may be consolidating.",
            icon="🔎",
        )
    else:
        st.markdown(f"### 🟢 Breakout Stocks &nbsp;—&nbsp; {n} found")
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
    st.info("Open the sidebar (☰ top-left) and tap **Run Full Scan** to begin.", icon="👈")

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">Data via Yahoo Finance · Not financial advice · Educational use only</div>',
    unsafe_allow_html=True,
)
