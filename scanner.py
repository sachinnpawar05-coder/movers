import streamlit as st
from common import show

c = st.session_state["ctx"]
df = c["df"]

st.markdown("##### 🎯 Scanner")

a1, a2 = st.columns(2)
chg_min = a1.number_input("Chg% min", 0.0, 20.0, 1.0, 0.1, key="sc_chg_min")
chg_max = a2.number_input("Chg% max", 0.0, 20.0, 2.0, 0.1, key="sc_chg_max")
b1, b2 = st.columns(2)
rsi_min = b1.number_input("RSI min", 0.0, 100.0, 50.0, 1.0, key="sc_rsi_min")
rsi_max = b2.number_input("RSI max", 0.0, 100.0, 60.0, 1.0, key="sc_rsi_max")
d1, d2 = st.columns(2)
adx_min = d1.number_input("ADX min", 0.0, 100.0, 20.0, 1.0, key="sc_adx_min")
adx_max = d2.number_input("ADX max", 0.0, 100.0, 30.0, 1.0, key="sc_adx_max")

m = (
    (df["Chg%"] >= chg_min) & (df["Chg%"] <= chg_max)
    & (df["RSI"] > rsi_min) & (df["RSI"] < rsi_max)
    & (df["ADX"] > adx_min) & (df["ADX"] < adx_max)
    & (df["ADX"] > df["ADXp"])  # ADX rising
)
res = df[m].sort_values("Chg%", ascending=False)

st.caption(
    f"{len(res)} stocks mile · Chg {chg_min:g}-{chg_max:g}% · "
    f"RSI {rsi_min:g}-{rsi_max:g} · ADX {adx_min:g}-{adx_max:g} rising"
)
show(res, c["compact"])
