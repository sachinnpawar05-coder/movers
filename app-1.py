import io
import time
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Nifty 500 Movers", layout="wide")

NSE_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
COLS = ["LTP", "Chg%", "PDC", "Open", "High", "Low"]


@st.cache_data(ttl=6 * 3600)
def get_symbols():
    r = requests.get(NSE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))["Symbol"].tolist()


@st.cache_data(ttl=60)
def get_data(symbols):
    tickers = [s + ".NS" for s in symbols]
    raw = yf.download(tickers, period="5d", interval="1d",
                      progress=False, threads=True)
    df = pd.DataFrame({
        "PDC": raw["Close"].iloc[-2],
        "Open": raw["Open"].iloc[-1],
        "High": raw["High"].iloc[-1],
        "Low": raw["Low"].iloc[-1],
        "LTP": raw["Close"].iloc[-1],
    }).dropna()
    df["Chg%"] = (df.LTP / df.PDC - 1) * 100
    df = df.round(2).sort_values("Chg%", ascending=False)
    df.index = df.index.str.replace(".NS", "", regex=False)
    df.index.name = "Stock"
    return df[COLS], raw.index[-1].date()


def show(df):
    if compact:
        df = df[["LTP", "Chg%"]]
    styled = df.style.map(
        lambda v: "color: #0a8f3c" if v > 0 else "color: #d13438" if v < 0 else "",
        subset=["Chg%"],
    ).format("{:.2f}")
    cfg = {c: st.column_config.NumberColumn(width="small") for c in df.columns}
    st.dataframe(styled, use_container_width=True, column_config=cfg,
                 height=min(750, 40 + 35 * len(df)))


st.markdown("### Nifty 500 Movers")

# Sidebar
compact = st.sidebar.checkbox("Compact view (LTP & Chg% only)", value=False)
n = st.sidebar.slider("Top N stocks", 5, 50, 10)
thr = st.sidebar.number_input("Movement % (up/down)", 0.1, 10.0, 1.0, 0.1)
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

up_n = int((df["Chg%"] >= thr).sum())
down_n = int((df["Chg%"] <= -thr).sum())
st.markdown(
    f"**{last_day}** · {len(df)} stocks · "
    f":green[{thr:g}%+ Up: {up_n}] · :red[{thr:g}%+ Down: {down_n}]"
)
st.caption("Chg% = (LTP / PDC - 1) x 100. Table ko side me swipe karke Open/High/Low dekho.")

t1, t2, t3, t4, t5 = st.tabs(
    ["Top Gainers", "Top Losers", f"{thr:g}%+ Up", f"{thr:g}%+ Down", "All"]
)
with t1:
    show(df.head(n))
with t2:
    show(df.tail(n).iloc[::-1])
with t3:
    show(df[df["Chg%"] >= thr])
with t4:
    show(df[df["Chg%"] <= -thr].iloc[::-1])
with t5:
    show(df)
    st.download_button("Download CSV", df.to_csv().encode(), "nifty500_movers.csv")

if auto:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
