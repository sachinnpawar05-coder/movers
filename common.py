import io
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

NSE_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
COLS = ["LTP", "Chg%", "Gap%", "RSI", "ADX", "ADXp", "PDC", "Open", "High", "Low"]


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
    adx = calc_adx(high, low, close)
    df = pd.DataFrame({
        "PDC": close.iloc[-2],
        "Open": raw["Open"].iloc[-1],
        "High": high.iloc[-1],
        "Low": low.iloc[-1],
        "LTP": close.iloc[-1],
        "RSI": calc_rsi(close).iloc[-1],
        "ADX": adx.iloc[-1],
        "ADXp": adx.iloc[-2],
    }).dropna(subset=["PDC", "Open", "High", "Low", "LTP"])
    df["Chg%"] = (df.LTP / df.PDC - 1) * 100
    df["Gap%"] = (df.Open / df.PDC - 1) * 100
    df = df.round(2).sort_values("Chg%", ascending=False)
    df.index = df.index.str.replace(".NS", "", regex=False)
    df.index.name = "Stock"
    fetched = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M:%S")
    return df[COLS], raw.index[-1].date(), fetched


def show(df, compact=False):
    if compact:
        df = df[["LTP", "Chg%", "RSI", "ADX"]]
    styled = df.style.map(
        lambda v: "color: #0a8f3c" if v > 0 else "color: #d13438" if v < 0 else "",
        subset=[c for c in ["Chg%", "Gap%"] if c in df.columns],
    ).format("{:.2f}", na_rep="-")
    cfg = {c: st.column_config.NumberColumn(width="small") for c in df.columns}
    st.dataframe(styled, use_container_width=True, column_config=cfg,
                 height=min(750, 40 + 35 * len(df)))
