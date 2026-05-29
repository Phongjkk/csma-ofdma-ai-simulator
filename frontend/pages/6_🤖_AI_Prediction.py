"""Page 6 — LSTM overload prediction + stream alerts."""
import streamlit as st
import numpy as np

st.set_page_config(page_title="AI Prediction", page_icon="🤖", layout="wide")
st.title("🤖 AI Overload Prediction")

with st.sidebar:
    st.header("Prediction Settings")
    n_stations = st.slider("Stations", 10, 100, 30)
    traffic_load = st.slider("Load", 0.3, 1.0, 0.8, 0.05)
    mode = st.selectbox("Mode", ["su", "ofdma"],
                        format_func=lambda x: {"su": "CSMA/CA", "ofdma": "OFDMA"}[x])
    util_threshold = st.slider("Overload Threshold (util)", 0.7, 0.99, 0.85, 0.01)
    run_btn = st.button("▶ Run Prediction Demo", type="primary")

if run_btn:
    with st.spinner("Running simulator..."):
        from simulator.config import SimConfig
        from simulator.core.simulator import Simulator
        cfg = SimConfig(n_stations=n_stations, traffic_load=traffic_load,
                        traffic_pattern="ramp", sim_time=30.0, seed=42)
        sim = Simulator(cfg, mode=mode)
        sim.run()
        samples = sim.time_series

    from ai.data.preprocessor import samples_to_array, MinMaxScaler
    from ai.models.moving_average import MovingAverageModel

    data = samples_to_array(samples)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)

    SEQ = 50
    model = MovingAverageModel(window_size=10, n_steps=SEQ)

    forecasts = []
    for i in range(SEQ, len(scaled) - SEQ, 10):
        X = scaled[i - SEQ: i][np.newaxis]
        pred = model.predict(X)[0]
        pred_inv = scaler.inverse_transform(pred)
        forecasts.append({"window_end": samples[i].time, "forecast": pred_inv})

    st.session_state["ai_samples"] = samples
    st.session_state["ai_forecasts"] = forecasts
    st.session_state["ai_scaler"] = scaler
    st.success(f"Generated {len(forecasts)} forecasts.")

if "ai_samples" in st.session_state:
    samples = st.session_state["ai_samples"]
    forecasts = st.session_state["ai_forecasts"]

    times = [s.time for s in samples]
    utils = [s.channel_util for s in samples]

    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=utils, name="Actual util", line=dict(color="blue")))

        if forecasts:
            last_fc = forecasts[-1]
            fc_start = last_fc["window_end"]
            fc_vals = last_fc["forecast"][:, 5]
            fc_times = [fc_start + i * 0.1 for i in range(len(fc_vals))]
            fig.add_trace(go.Scatter(x=fc_times, y=fc_vals, name="Forecast util",
                                     line=dict(color="red", dash="dash")))
            fig.add_hline(y=util_threshold, line_dash="dot", line_color="orange",
                          annotation_text=f"Threshold={util_threshold}")

        fig.update_layout(title="Channel Utilization: Actual vs Forecast",
                          xaxis_title="Time (s)", yaxis_title="Channel Util", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Alert summary
        if forecasts:
            last_vals = forecasts[-1]["forecast"][:, 5]
            p_overload = float((last_vals > util_threshold).mean())
            if p_overload > 0.5:
                st.error(f"CRITICAL: Predicted overload probability = {p_overload:.1%} in next 5s")
            elif p_overload > 0.2:
                st.warning(f"WARNING: Overload probability = {p_overload:.1%} in next 5s")
            else:
                st.success(f"Network healthy. Overload probability = {p_overload:.1%}")
    except ImportError:
        st.info("Install plotly for charts.")
else:
    st.info("Click **Run Prediction Demo** in the sidebar.")
