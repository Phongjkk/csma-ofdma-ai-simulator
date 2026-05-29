"""Page 4 — Mode comparison across load profiles."""
import streamlit as st

st.set_page_config(page_title="Compare", page_icon="⚖️", layout="wide")
st.title("⚖️ Mode Comparison")

with st.sidebar:
    st.header("Comparison Settings")
    n_stations = st.slider("Number of Stations", 5, 100, 20)
    traffic_load = st.slider("Traffic Load", 0.1, 1.0, 0.7, 0.05)
    sim_time = st.slider("Sim Time (s)", 5.0, 30.0, 15.0, 5.0)
    pattern = st.selectbox("Traffic Pattern", ["poisson", "cbr", "ramp"])
    run_all = st.button("▶ Run Both Modes", type="primary")

if run_all:
    from simulator.config import SimConfig
    from simulator.modes.mode_su import run_su
    from simulator.modes.mode_ofdma import run_ofdma

    results = {}
    cfg = SimConfig(n_stations=n_stations, traffic_load=traffic_load,
                    sim_time=sim_time, traffic_pattern=pattern, seed=42)
    with st.spinner("Running CSMA/CA..."):
        results["CSMA/CA"] = run_su(cfg)["summary"]
    with st.spinner("Running OFDMA..."):
        results["OFDMA"] = run_ofdma(cfg)["summary"]
    st.session_state["compare_results"] = results
    st.success("Both modes complete!")

if "compare_results" in st.session_state:
    results = st.session_state["compare_results"]
    modes = list(results.keys())
    metrics = ["throughput_mbps", "latency_p99_ms", "collision_rate", "fairness_index", "channel_util"]
    labels = ["Throughput (Mbps)", "Latency P99 (ms)", "Collision Rate", "Fairness", "Channel Util"]

    st.subheader("Comparison Table")
    try:
        import pandas as pd
        rows = []
        for mode, s in results.items():
            rows.append({"Mode": mode, **{lbl: round(s[m], 4)
                                           for m, lbl in zip(metrics, labels)}})
        st.dataframe(pd.DataFrame(rows).set_index("Mode"), use_container_width=True)
    except ImportError:
        st.json(results)

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        st.subheader("Bar Charts")
        fig = make_subplots(rows=1, cols=len(metrics), subplot_titles=labels)
        colors = ["#636EFA", "#EF553B"]
        for j, (m, lbl) in enumerate(zip(metrics, labels)):
            for i, mode in enumerate(modes):
                fig.add_trace(
                    go.Bar(name=mode, x=[mode], y=[results[mode][m]],
                           marker_color=colors[i], showlegend=(j == 0)),
                    row=1, col=j + 1,
                )
        fig.update_layout(height=400, barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass
else:
    st.info("Configure parameters in the sidebar and click **Run Both Modes**.")
