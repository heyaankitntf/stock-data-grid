import io
import warnings
import logging
from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf

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

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b1622;
    color: #d0e0f0;
}
[data-testid="stHeader"] { background: transparent; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 14px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 1.9rem; font-weight: 800; margin: 0 0 .4rem; letter-spacing: -.5px; }
.hero p  { font-size: .9rem; opacity: .7; margin: 0; }

/* ── Scan button ── */
.stButton > button {
    background: linear-gradient(90deg, #00b09b, #96c93d) !important;
    color: #fff !important;
    font-weight: 700;
    border: none !important;
    border-radius: 8px;
    width: 100%;
}
.stButton > button:hover { filter: brightness(1.08); }

/* ── Progress bar ── */
.stProgress > div > div { background: linear-gradient(90deg, #00b09b, #96c93d) !important; }

/* ── Metric labels ── */
[data-testid="stMetricLabel"]  { color: #8ba8c4 !important; font-size: .78rem !important; }
[data-testid="stMetricValue"]  { color: #00d4aa !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Footer ── */
.footer {
    text-align: center; color: #3a5268; font-size: .75rem;
    margin-top: 2.5rem; padding-top: 1rem;
    border-top: 1px solid #1a2f42;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── NSE stock universe (210 symbols) ──────────────────────────────────────────
MY_STOCKS = [
    "360ONE.NS","ABB.NS","APLAPOLLO.NS","AUBANK.NS","ADANIENSOL.NS",
    "ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ADANIPOWER.NS","ABCAPITAL.NS",
    "ALKEM.NS","AMBER.NS","AMBUJACEM.NS","ANGELONE.NS","APOLLOHOSP.NS",
    "ASHOKLEY.NS","ASIANPAINT.NS","ASTRAL.NS","AUROPHARMA.NS","DMART.NS",
    "AXISBANK.NS","BSE.NS","BAJAJ-AUTO.NS","BAJFINANCE.NS","BAJAJFINSV.NS",
    "BAJAJHLDNG.NS","BANDHANBNK.NS","BANKBARODA.NS","BANKINDIA.NS","BDL.NS",
    "BEL.NS","BHARATFORG.NS","BHEL.NS","BPCL.NS","BHARTIARTL.NS",
    "BIOCON.NS","BLUESTARCO.NS","BOSCHLTD.NS","BRITANNIA.NS","CGPOWER.NS",
    "CANBK.NS","CDSL.NS","CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS",
    "COCHINSHIP.NS","COFORGE.NS","COLPAL.NS","CAMS.NS","CONCOR.NS",
    "CROMPTON.NS","CUMMINSIND.NS","DLF.NS","DABUR.NS","DALBHARAT.NS",
    "DELHIVERY.NS","DIVISLAB.NS","DIXON.NS","DRREDDY.NS","ETERNAL.NS",
    "EICHERMOT.NS","EXIDEIND.NS","FORCEMOT.NS","NYKAA.NS","FORTIS.NS",
    "GAIL.NS","GVT&D.NS","GMRAIRPORT.NS","GLENMARK.NS","GODFRYPHLP.NS",
    "GODREJCP.NS","GODREJPROP.NS","GRASIM.NS","HCLTECH.NS","HDFCAMC.NS",
    "HDFCBANK.NS","HDFCLIFE.NS","HAVELLS.NS","HEROMOTOCO.NS","HINDALCO.NS",
    "HAL.NS","HINDPETRO.NS","HINDUNILVR.NS","HINDZINC.NS","POWERINDIA.NS",
    "HYUNDAI.NS","ICICIBANK.NS","ICICIGI.NS","ICICIPRULI.NS","IDFCFIRSTB.NS",
    "ITC.NS","INDIANB.NS","IEX.NS","IOC.NS","IRFC.NS","IREDA.NS",
    "INDUSTOWER.NS","INDUSINDBK.NS","NAUKRI.NS","INFY.NS","INOXWIND.NS",
    "INDIGO.NS","JINDALSTEL.NS","JSWENERGY.NS","JSWSTEEL.NS","JIOFIN.NS",
    "JUBLFOOD.NS","KEI.NS","KPITTECH.NS","KALYANKJIL.NS","KAYNES.NS",
    "KFINTECH.NS","KOTAKBANK.NS","LTF.NS","LICHSGFIN.NS","LTM.NS",
    "LT.NS","LAURUSLABS.NS","LICI.NS","LODHA.NS","LUPIN.NS",
    "M&M.NS","MANAPPURAM.NS","MANKIND.NS","MARICO.NS","MARUTI.NS",
    "MFSL.NS","MAXHEALTH.NS","MAZDOCK.NS","MOTILALOFS.NS","MPHASIS.NS",
    "MCX.NS","MUTHOOTFIN.NS","NBCC.NS","NHPC.NS","NMDC.NS",
    "NTPC.NS","NATIONALUM.NS","NESTLEIND.NS","NAM-INDIA.NS","NUVAMA.NS",
    "OBEROIRLTY.NS","ONGC.NS","OIL.NS","PAYTM.NS","OFSS.NS",
    "POLICYBZR.NS","PGEL.NS","PIIND.NS","PNBHOUSING.NS","PAGEIND.NS",
    "PATANJALI.NS","PERSISTENT.NS","PETRONET.NS","PIDILITIND.NS","POLYCAB.NS",
    "PFC.NS","POWERGRID.NS","PREMIERENE.NS","PRESTIGE.NS","PNB.NS",
    "RBLBANK.NS","RECLTD.NS","RADICO.NS","RVNL.NS","RELIANCE.NS",
    "SBICARD.NS","SBILIFE.NS","SHREECEM.NS","SRF.NS","MOTHERSON.NS",
    "SHRIRAMFIN.NS","SIEMENS.NS","SOLARINDS.NS","SONACOMS.NS","SBIN.NS",
    "SAIL.NS","SUNPHARMA.NS","SUPREMEIND.NS","SUZLON.NS","SWIGGY.NS",
    "TATACONSUM.NS","TVSMOTOR.NS","TCS.NS","TATAELXSI.NS","TMPV.NS",
    "TATAPOWER.NS","TATASTEEL.NS","TECHM.NS","FEDERALBNK.NS","INDHOTEL.NS",
    "PHOENIXLTD.NS","TITAN.NS","TORNTPHARM.NS","TRENT.NS","TIINDIA.NS",
    "UNOMINDA.NS","UPL.NS","ULTRACEMCO.NS","UNIONBANK.NS","UNITDSPR.NS",
    "VBL.NS","VEDL.NS","VMM.NS","IDEA.NS","VOLTAS.NS",
    "WAAREEENER.NS","WIPRO.NS","YESBANK.NS","ZYDUSLIFE.NS",
]


# ── Helpers ────────────────────────────────────────────────────────────────────
def to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Breakout Stocks")
    return buf.getvalue()


def scan_stock(ticker: str) -> dict | None:
    """Return a result dict if the stock meets all 4 breakout criteria, else None."""
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if data.empty or len(data) < 200:
            return None

        close = data["Close"].squeeze()
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


# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in [("df_results", None), ("last_scan", None), ("scanned", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <h1>📈 CAR + DMA Super Breakout Scanner</h1>
  <p>
    NSE stocks simultaneously above their 30‑day, 50‑day &amp; 200‑day moving averages,
    with a Cumulative Average Return (CAR) rising monotonically for the past 10 sessions.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Scanner Settings")
    st.markdown(f"**Universe:** {len(MY_STOCKS)} NSE stocks")
    st.markdown(
        "**Criteria (all 4 must pass):**\n"
        "1. CMP > 30 DMA\n"
        "2. CMP > 50 DMA\n"
        "3. CMP > 200 DMA\n"
        "4. CAR rising for 10 straight days"
    )
    st.divider()
    run_btn = st.button("🔍 Run Full Scan", use_container_width=True)
    if st.session_state.last_scan:
        st.caption(f"Last run: {st.session_state.last_scan}")

# Auto-trigger on very first load
trigger = run_btn or (not st.session_state.scanned)

# ── Scan ───────────────────────────────────────────────────────────────────────
if trigger:
    st.session_state.scanned = True
    with st.container():
        st.markdown("#### ⏳ Scanning — please wait (3–5 min for 200+ stocks)…")
        pbar   = st.progress(0)
        status = st.empty()
        df     = run_scanner(MY_STOCKS, pbar, status)
        pbar.progress(1.0)
        status.empty()

    st.session_state.df_results = df
    st.session_state.last_scan  = datetime.now().strftime("%d-%m-%Y  %H:%M")
    st.rerun()

# ── Display results ────────────────────────────────────────────────────────────
df = st.session_state.df_results

if df is not None:
    n      = len(df)
    total  = len(MY_STOCKS)
    rate   = f"{n / total * 100:.1f}%" if total else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Stocks Scanned",   total)
    c2.metric("🟢 Breakouts Found",  n)
    c3.metric("🎯 Hit Rate",         rate)
    c4.metric("🕐 Scanned At",       st.session_state.last_scan or "—")

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

        # ── Colour-code the distance column ───────────────────────────────────
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
            .format(
                {
                    "CMP (₹)"        : "₹{:.2f}",
                    "30 DMA"         : "₹{:.2f}",
                    "50 DMA"         : "₹{:.2f}",
                    "200 DMA"        : "₹{:.2f}",
                    "200 DMA Dist %" : "{:.2f}%",
                }
            )
            .hide(axis="index")
        )

        st.dataframe(styled, use_container_width=True, height=min(80 + n * 38, 680))

        # ── Download ──────────────────────────────────────────────────────────
        st.download_button(
            label     = "⬇️  Download Excel",
            data      = to_excel(df),
            file_name = f"Breakout_Stocks_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
elif not trigger:
    st.info("Open the sidebar (top-left ›) and click **Run Full Scan** to begin.", icon="👈")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">'
    "Data via Yahoo Finance · Not financial advice · For educational purposes only"
    "</div>",
    unsafe_allow_html=True,
)
