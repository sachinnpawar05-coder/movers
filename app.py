import time
import pandas as pd
import streamlit as st
from common import get_symbols, get_data

st.set_page_config(page_title="Nifty 500 Movers", layout="wide")

st.markdown("### Nifty 500 Movers")

# Refresh button on main screen (clears cache, page reruns with fresh data)
if st.button("🔄 Refresh", use_container_width=True):
    st.cache_data.clear()

# ---------------- Sidebar (sab pages par same) ----------------
compact = st.sidebar.checkbox("Compact view (LTP, Chg%, RSI, ADX)", value=False)
n = st.sidebar.slider("Top N stocks", 5, 50, 10)
thr = st.sidebar.number_input("Movement % (up/down)", 0.1, 10.0, 1.0, 0.1)

st.sidebar.markdown("**Range filter**")
lo = st.sidebar.number_input("Min % (se zyada)", 0.0, 20.0, 1.0, 0.1)
hi = st.sidebar.number_input("Max % (se kam)", 0.1, 20.0, 2.0, 0.1)
min_adx = st.sidebar.number_input("Min ADX (optional, dono range par)", 0.0, 100.0, 0.0, 1.0)
gap_max = st.sidebar.number_input("Avoid gap up/down > % (0 = off)", 0.0, 20.0, 2.0, 0.1)
gap_all = st.sidebar.checkbox("Gap filter sabhi tabs me lagao", value=False)

st.sidebar.markdown("**ADX rising**")
adx_lvl = st.sidebar.number_input("ADX above", 0.0, 100.0, 20.0, 1.0)
adx_rise_all = st.sidebar.checkbox("ADX rising filter range tabs me bhi lagao", value=False)

auto = st.sidebar.checkbox("Auto refresh (60 sec)")
if st.sidebar.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()

# ---------------- Symbols (NSE list, fallback to uploaded CSV) ----------------
try:
    symbols = get_symbols()
except Exception:
    st.warning("NSE se list nahi aayi. Nifty 500 CSV (Symbol column) upload karo.")
    up = st.file_uploader("ind_nifty500list.csv", type="csv")
    if up is None:
        st.stop()
    symbols = pd.read_csv(up)["Symbol"].tolist()

with st.spinner("Data la raha hu..."):
    df, last_day, fetched = get_data(tuple(symbols))

# ---------------- Filters ----------------
# Gap filter: gap = (Open / PDC - 1) x 100
gap_ok = (df["Gap%"].abs() <= gap_max) if gap_max > 0 else True
if gap_all and gap_max > 0:
    df = df[gap_ok]
    gap_ok = True

chg = df["Chg%"]
adx_ok = (df["ADX"] >= min_adx) if min_adx > 0 else True
# ADX rising = aaj ka ADX pichle din se zyada, aur level ke upar
adx_rise = (df["ADX"] > df["ADXp"]) & (df["ADX"] > adx_lvl)
if adx_rise_all:
    adx_ok = adx_ok & adx_rise

# Pages ke liye shared data
st.session_state["ctx"] = dict(
    compact=compact, n=n, thr=thr, lo=lo, hi=hi, adx_lvl=adx_lvl,
    df=df,
    top_up=df.head(n),
    top_down=df.tail(n).iloc[::-1],
    up_thr=df[chg >= thr],
    down_thr=df[chg <= -thr].iloc[::-1],
    rng_up=df[(chg >= lo) & (chg < hi) & adx_ok & gap_ok],
    rng_down=df[(chg <= -lo) & (chg > -hi) & adx_ok & gap_ok].sort_values("Chg%"),
)

st.markdown(
    f"🕒 **{fetched} IST** · {last_day} · {len(df)} stocks · "
    f":green[{thr:g}%+ Up: {int((chg >= thr).sum())}] · "
    f":red[{thr:g}%+ Down: {int((chg <= -thr).sum())}]"
)
st.caption("Chg% = (LTP / PDC - 1) x 100. Gap% = (Open / PDC - 1) x 100. "
           "RSI/ADX: 14 period daily, ADXp = pichle din ka ADX. "
           "Table ko side me swipe karke baaki columns dekho.")

# ---------------- Pages ----------------
pg = st.navigation(
    [
        st.Page("gainers.py", title="Gainers", icon="📈", default=True),
        st.Page("losers.py", title="Losers", icon="📉"),
        st.Page("adx_scan.py", title="ADX", icon="📊"),
        st.Page("rsi_scan.py", title="RSI", icon="🔎"),
        st.Page("all_stocks.py", title="All", icon="📋"),
    ],
    position="top",
)
pg.run()

if auto:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
