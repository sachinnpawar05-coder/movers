import streamlit as st
from common import show

c = st.session_state["ctx"]
df = c["df"]

st.markdown("##### RSI Scanner")
c1, c2 = st.columns(2)
rsi_min = c1.number_input("RSI min", 0.0, 100.0, 60.0, 1.0, key="rsi_min")
rsi_max = c2.number_input("RSI max", 0.0, 100.0, 100.0, 1.0, key="rsi_max")
side = st.radio("Stocks", ["All", "Up", "Down"],
                horizontal=True, key="rsi_side")
st.caption("Tip: overbought = 70-100, oversold = 0-30, strong trend = 60-100")

m = (df["RSI"] >= rsi_min) & (df["RSI"] <= rsi_max)
if side == "Up":
    m &= df["Chg%"] > 0
elif side == "Down":
    m &= df["Chg%"] < 0

res = df[m].sort_values("RSI", ascending=False)
st.caption(f"{len(res)} stocks mile · RSI {rsi_min:g} se {rsi_max:g}, side: {side}")
show(res, c["compact"])
