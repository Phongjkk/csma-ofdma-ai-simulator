"""Page 1 — Project overview, goals, KPIs."""
import streamlit as st

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
st.title("🏠 Project Overview")

st.markdown("""
## CSMA/OFDMA AI Network Simulator

This project simulates IEEE 802.11 wireless network access mechanisms and applies AI to predict performance in real time.

### Key Components

| Component | Description |
|-----------|-------------|
| **CSMA/CA Simulator** | DCF with binary exponential backoff, collision detection, ACK |
| **OFDMA Simulator** | Trigger Frame, Resource Unit allocation, parallel uplink TX |
| **Combined Mode** | Hybrid 802.11ax-style: CSMA/CA contention + OFDMA scheduling |
| **Real-time Monitor** | Sliding window metrics, threshold + z-score anomaly detection |
| **AI Prediction** | LSTM model forecasts 5-second performance horizon |

### 5 Core Metrics

| Metric | Description |
|--------|-------------|
| **Throughput** | Successfully delivered data (Mbps) |
| **Latency P99** | 99th percentile end-to-end delay (ms) |
| **Collision Rate** | Fraction of failed transmissions |
| **Fairness Index** | Jain's fairness index across stations |
| **Channel Utilization** | Fraction of time channel carries data |

### Technology Stack

- **Python 3.11+** — Simulator & AI
- **SimPy** — Discrete-event simulation
- **PyTorch** — LSTM model
- **Streamlit** — Dashboard
- **Plotly** — Interactive charts
""")

st.info("Use the sidebar to navigate to **Simulate** and run your first scenario.")
