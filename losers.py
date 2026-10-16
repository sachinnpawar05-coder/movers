import streamlit as st
from common import show

c = st.session_state["ctx"]

t1, t2, t3 = st.tabs([
    f"Top {c['n']} Losers",
    f"Down -{c['lo']:g} to -{c['hi']:g}% ({len(c['rng_down'])})",
    f"{c['thr']:g}%+ Down ({len(c['down_thr'])})",
])
with t1:
    show(c["top_down"], c["compact"])
with t2:
    show(c["rng_down"], c["compact"])
with t3:
    show(c["down_thr"], c["compact"])
