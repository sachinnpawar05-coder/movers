import streamlit as st
from common import show

c = st.session_state["ctx"]
df = c["df"]

st.markdown("##### ADX Scanner")
c1, c2 = st.columns(2)
adx_min = c1.number_input("ADX min", 0.0, 100.0, 20.0, 1.0, key="adx_min")
adx_max = c2.number_input("ADX max", 0.0, 100.0, 100.0, 1.0, key="adx_max")
trend = st.radio("ADX trend", ["Rising", "Falling", "Any"],
                 horizontal=True, key="adx_trend")
side = st.radio("Stocks", ["All", "Up", "Down"],
                horizontal=True, key="adx_side")

m = (df["ADX"] >= adx_min) & (df["ADX"] <= adx_max)
if trend == "Rising":
    m &= df["ADX"] > df["ADXp"]
elif trend == "Falling":
    m &= df["ADX"] < df["ADXp"]
if side == "Up":
    m &= df["Chg%"] > 0
elif side == "Down":
    m &= df["Chg%"] < 0

res = df[m].sort_values("ADX", ascending=False)
st.caption(f"{len(res)} stocks mile · ADX {adx_min:g} se {adx_max:g}, "
           f"trend: {trend}, side: {side}")
show(res, c["compact"])
