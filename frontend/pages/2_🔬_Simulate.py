"""Page 2 — Interactive simulation runner."""
import streamlit as st

st.set_page_config(page_title="Simulate", page_icon="🔬", layout="wide")
st.title("🔬 Run Simulation")

with st.sidebar:
    st.header("Simulation Parameters")
    mode = "combined"  # CSMA/CA + OFDMA kết hợp (IEEE 802.11ax)
    n_stations = st.slider("Number of Stations", 1, 100, 10)
    traffic_load = st.slider("Traffic Load", 0.1, 1.0, 0.5, 0.05)
    sim_time = st.slider("Simulation Time (s)", 5.0, 60.0, 30.0, 5.0)
    pattern = st.selectbox("Traffic Pattern", ["poisson", "cbr", "ramp", "spike", "oscillate"])
    seed = st.number_input("Random Seed", 0, 9999, 42)
    run_btn = st.button("▶ Run Simulation", type="primary")

if run_btn:
    with st.spinner("Running simulation..."):
        try:
            from simulator.config import SimConfig
            from simulator.core.simulator import Simulator

            cfg = SimConfig(
                n_stations=n_stations,
                traffic_load=traffic_load,
                sim_time=sim_time,
                traffic_pattern=pattern,
                seed=int(seed),
            )
            sim = Simulator(cfg, mode=mode)
            sim.run()
            result = sim.get_results()
            st.session_state["last_result"] = result
            st.session_state["last_time_series"] = sim.time_series
            st.success("Simulation complete!")
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    s = result["summary"]
    st.subheader("Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Throughput", f"{s['throughput_mbps']:.3f} Mbps")
    col2.metric("Latency P99", f"{s['latency_p99_ms']:.2f} ms")
    col3.metric("Collision Rate", f"{s['collision_rate']:.3f}")
    col4.metric("Fairness Index", f"{s['fairness_index']:.3f}")
    col5.metric("Channel Util", f"{s['channel_util']:.3f}")

    if result.get("time_series"):
        try:
            import plotly.graph_objects as go
            ts = result["time_series"]
            times = [x["time"] for x in ts]

            st.subheader("Time Series")
            metric_sel = st.selectbox("Metric", ["throughput_mbps", "latency_p99_ms",
                                                  "collision_rate", "channel_util"])
            vals = [x[metric_sel] for x in ts]
            fig = go.Figure(go.Scatter(x=times, y=vals, mode="lines", name=metric_sel))
            fig.update_layout(xaxis_title="Time (s)", yaxis_title=metric_sel, height=350)
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for charts: pip install plotly")

    st.subheader("Raw Config")
    st.json(result["config"])
else:
    st.info("Configure parameters in the sidebar and click **Run Simulation**.")
