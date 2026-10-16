import io
import time
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Nifty 500 Movers", layout="wide")

NSE_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
COLS = ["LTP", "Chg%", "RSI", "ADX", "PDC", "Open", "High", "Low"]


def calc_rsi(close, n=14):
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + gain / loss)


def calc_adx(high, low, close, n=14):
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    pc = close.shift()
    tr = np.maximum(np.maximum(high - low, (high - pc).abs()), (low - pc).abs())
    w = dict(alpha=1 / n, adjust=False, min_periods=n)
    atr = tr.ewm(**w).mean()
    plus_di = 100 * plus_dm.ewm(**w).mean() / atr
    minus_di = 100 * minus_dm.ewm(**w).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(**w).mean()


@st.cache_data(ttl=6 * 3600)
def get_symbols():
    r = requests.get(NSE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))["Symbol"].tolist()


@st.cache_data(ttl=60)
def get_data(symbols):
    tickers = [s + ".NS" for s in symbols]
    raw = yf.download(tickers, period="6mo", interval="1d",
                      progress=False, threads=True)
    close, high, low = raw["Close"], raw["High"], raw["Low"]
    df = pd.DataFrame({
        "PDC": close.iloc[-2],
        "Open": raw["Open"].iloc[-1],
        "High": high.iloc[-1],
        "Low": low.iloc[-1],
        "LTP": close.iloc[-1],
        "RSI": calc_rsi(close).iloc[-1],
        "ADX": calc_adx(high, low, close).iloc[-1],
    }).dropna(subset=["PDC", "Open", "High", "Low", "LTP"])
    df["Chg%"] = (df.LTP / df.PDC - 1) * 100
    df = df.round(2).sort_values("Chg%", ascending=False)
    df.index = df.index.str.replace(".NS", "", regex=False)
    df.index.name = "Stock"
    return df[COLS], raw.index[-1].date()


def show(df):
    if compact:
        df = df[["LTP", "Chg%", "RSI", "ADX"]]
    styled = df.style.map(
        lambda v: "color: #0a8f3c" if v > 0 else "color: #d13438" if v < 0 else "",
        subset=["Chg%"],
    ).format("{:.2f}", na_rep="-")
    cfg = {c: st.column_config.NumberColumn(width="small") for c in df.columns}
    st.dataframe(styled, use_container_width=True, column_config=cfg,
                 height=min(750, 40 + 35 * len(df)))


st.markdown("### Nifty 500 Movers")

# Sidebar
compact = st.sidebar.checkbox("Compact view (LTP, Chg%, RSI, ADX)", value=False)
n = st.sidebar.slider("Top N stocks", 5, 50, 10)
thr = st.sidebar.number_input("Movement % (up/down)", 0.1, 10.0, 1.0, 0.1)

st.sidebar.markdown("**Range filter**")
lo = st.sidebar.number_input("Min % (se zyada)", 0.0, 20.0, 1.0, 0.1)
hi = st.sidebar.number_input("Max % (se kam)", 0.1, 20.0, 2.0, 0.1)
side = st.sidebar.radio("Direction", ["Up", "Down", "Both"], horizontal=True)
min_adx = st.sidebar.number_input("Min ADX (optional)", 0.0, 100.0, 0.0, 1.0)

auto = st.sidebar.checkbox("Auto refresh (60 sec)")
if st.sidebar.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()

# Symbols (NSE list, fallback to uploaded CSV)
try:
    symbols = get_symbols()
except Exception:
    st.warning("NSE se list nahi aayi. Nifty 500 CSV (Symbol column) upload karo.")
    up = st.file_uploader("ind_nifty500list.csv", type="csv")
    if up is None:
        st.stop()
    symbols = pd.read_csv(up)["Symbol"].tolist()

with st.spinner("Data la raha hu..."):
    df, last_day = get_data(tuple(symbols))

# Range filter
chg = df["Chg%"]
if side == "Up":
    m = (chg >= lo) & (chg < hi)
elif side == "Down":
    m = (chg <= -lo) & (chg > -hi)
else:
    m = (chg.abs() >= lo) & (chg.abs() < hi)
if min_adx > 0:
    m &= df["ADX"] >= min_adx
rng = df[m]
if side == "Down":
    rng = rng.sort_values("Chg%")

up_n = int((chg >= thr).sum())
down_n = int((chg <= -thr).sum())
st.markdown(
    f"**{last_day}** · {len(df)} stocks · "
    f":green[{thr:g}%+ Up: {up_n}] · :red[{thr:g}%+ Down: {down_n}]"
)
st.caption("Chg% = (LTP / PDC - 1) x 100. RSI/ADX: 14 period daily. "
           "Table ko side me swipe karke baaki columns dekho.")

t1, t2, t3, t4, t5, t6 = st.tabs([
    "Top Gainers", "Top Losers",
    f"Range {lo:g}-{hi:g}% ({len(rng)})",
    f"{thr:g}%+ Up", f"{thr:g}%+ Down", "All",
])
with t1:
    show(df.head(n))
with t2:
    show(df.tail(n).iloc[::-1])
with t3:
    show(rng)
with t4:
    show(df[chg >= thr])
with t5:
    show(df[chg <= -thr].iloc[::-1])
with t6:
    show(df)
    st.download_button("Download CSV", df.to_csv().encode(), "nifty500_movers.csv")

if auto:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
