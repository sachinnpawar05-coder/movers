import streamlit as st
from common import show

c = st.session_state["ctx"]

show(c["df"], c["compact"])
st.download_button("Download CSV", c["df"].to_csv().encode(),
                   "nifty500_movers.csv")
