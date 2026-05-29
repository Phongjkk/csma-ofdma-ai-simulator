"""Page 5 — Realtime monitoring dashboard (auto-refresh)."""
import streamlit as st
import time

st.set_page_config(page_title="Live Monitor", page_icon="📡", layout="wide")
st.title("📡 Live Monitor")

with st.sidebar:
    st.header("Simulation Config")
    n_stations = st.slider("Stations", 5, 50, 20)
    traffic_load = st.slider("Load", 0.1, 1.0, 0.7, 0.05)
    mode = "combined"  # CSMA/CA + OFDMA kết hợp
    pattern = st.selectbox("Pattern", ["poisson", "ramp", "spike", "oscillate"])
    start_btn = st.button("▶ Start Live Demo", type="primary")

if start_btn:
    from simulator.config import SimConfig
    from simulator.core.simulator import Simulator
    from monitoring.monitor import RealtimeMonitor

    cfg = SimConfig(n_stations=n_stations, traffic_load=traffic_load,
                    traffic_pattern=pattern, sim_time=30.0, seed=42)
    sim = Simulator(cfg, mode=mode)

    with st.spinner("Running simulation..."):
        sim.run()

    monitor = RealtimeMonitor(buffer_maxlen=300)
    alerts = []
    monitor.on_alert(alerts.append)
    for s in sim.time_series:
        monitor.push(s)

    st.session_state["monitor_samples"] = sim.time_series
    st.session_state["monitor_alerts"] = alerts
    st.success(f"Loaded {len(sim.time_series)} metric samples.")

if "monitor_samples" in st.session_state:
    samples = st.session_state["monitor_samples"]
    fired_alerts = st.session_state.get("monitor_alerts", [])

    times = [s.time for s in samples]
    metrics_map = {
        "throughput_mbps": [s.throughput_mbps for s in samples],
        "latency_p99_ms": [s.latency_p99_ms for s in samples],
        "collision_rate": [s.collision_rate for s in samples],
        "channel_util": [s.channel_util for s in samples],
    }

    latest = samples[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Throughput", f"{latest.throughput_mbps:.3f} Mbps")
    c2.metric("Latency P99", f"{latest.latency_p99_ms:.2f} ms")
    c3.metric("Collision Rate", f"{latest.collision_rate:.3f}")
    c4.metric("Channel Util", f"{latest.channel_util:.3f}")

    try:
        import plotly.graph_objects as go

        metric_sel = st.selectbox("Metric to display",
                                  list(metrics_map.keys()))
        fig = go.Figure(go.Scatter(x=times, y=metrics_map[metric_sel],
                                   mode="lines", name=metric_sel,
                                   line=dict(color="#00CC96")))
        fig.update_layout(height=300, xaxis_title="Time (s)", yaxis_title=metric_sel)
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass

    if fired_alerts:
        st.subheader(f"Alerts ({len(fired_alerts)})")
        for a in fired_alerts[-10:]:
            color = "red" if a.severity.value == "CRITICAL" else "orange"
            st.markdown(f":{color}[**{a.severity.value}** @ t={a.timestamp:.1f}s — {a.message}]")
    else:
        st.success("No anomalies detected.")
else:
    st.info("Click **Start Live Demo** to run the monitoring simulation.")
