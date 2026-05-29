"""Page 3 — Detailed per-run metrics and charts."""
import streamlit as st

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
st.title("📊 Detailed Results")

if "last_result" not in st.session_state:
    st.warning("No simulation results found. Go to **Simulate** page first.")
    st.stop()

result = st.session_state["last_result"]
s = result["summary"]
ts_data = result.get("time_series", [])

st.subheader("Performance Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Throughput (Mbps)", f"{s['throughput_mbps']:.4f}")
    st.metric("Latency Mean (ms)", f"{s['latency_mean_ms']:.2f}")
with col2:
    st.metric("Latency P99 (ms)", f"{s['latency_p99_ms']:.2f}")
    st.metric("Collision Rate", f"{s['collision_rate']:.4f}")
with col3:
    st.metric("Fairness Index", f"{s['fairness_index']:.4f}")
    st.metric("Channel Utilization", f"{s['channel_util']:.4f}")

st.divider()
st.metric("Total Successful Transmissions", s["total_success"])
st.metric("Total Collisions", s["total_collisions"])

if ts_data:
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        st.subheader("Time Series Charts")
        times = [x["time"] for x in ts_data]
        metrics = ["throughput_mbps", "latency_p99_ms", "collision_rate", "channel_util", "fairness_index"]
        labels = ["Throughput (Mbps)", "Latency P99 (ms)", "Collision Rate", "Channel Util", "Fairness"]

        fig = make_subplots(rows=len(metrics), cols=1, shared_xaxes=True,
                            subplot_titles=labels, vertical_spacing=0.05)
        for i, (m, label) in enumerate(zip(metrics, labels)):
            vals = [x[m] for x in ts_data]
            fig.add_trace(go.Scatter(x=times, y=vals, mode="lines", name=label),
                          row=i + 1, col=1)
        fig.update_layout(height=150 * len(metrics), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.json(ts_data[:10])

st.subheader("Configuration")
st.json(result["config"])
