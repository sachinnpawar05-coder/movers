import streamlit as st
from common import show

c = st.session_state["ctx"]

t1, t2, t3 = st.tabs([
    f"Top {c['n']} Gainers",
    f"Up {c['lo']:g} to {c['hi']:g}% ({len(c['rng_up'])})",
    f"{c['thr']:g}%+ Up ({len(c['up_thr'])})",
])
with t1:
    show(c["top_up"], c["compact"])
with t2:
    show(c["rng_up"], c["compact"])
with t3:
    show(c["up_thr"], c["compact"])
