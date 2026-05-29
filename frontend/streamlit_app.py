"""Streamlit multi-page app entry point."""
import streamlit as st

st.set_page_config(
    page_title="CSMA/OFDMA AI Simulator",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📡 CSMA/OFDMA AI Simulator")
st.markdown("""
Welcome to the **IEEE 802.11 CSMA/CA & OFDMA Network Performance Simulator** with AI-based prediction.

Use the sidebar to navigate between pages:
- **Simulate** — Run a single simulation scenario
- **Results** — View detailed per-run metrics
- **Compare** — Compare CSMA/CA vs OFDMA vs Combined modes
- **Live Monitor** — Real-time monitoring dashboard
- **AI Prediction** — LSTM overload forecasting
- **Model Evaluation** — Compare AI model accuracy
""")

st.sidebar.success("Select a page above.")
