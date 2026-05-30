"""Page 6 — LSTM dự đoán quá tải + cảnh báo sớm."""
import streamlit as st
import numpy as np
import os

st.set_page_config(page_title="AI Prediction", page_icon="🤖", layout="wide")
st.title("🤖 Dự đoán quá tải bằng LSTM")

CHECKPOINT = "ai/saved_models/lstm_checkpoint.pt"
SCALER_PATH = "ai/saved_models/scalers.pkl"

if not os.path.exists(CHECKPOINT):
    st.warning("Chưa có model LSTM. Hãy vào trang **Model Evaluation** để huấn luyện trước.")
    st.stop()

with st.sidebar:
    st.header("Cài đặt Demo")
    n_stations = st.slider("Số Station", 5, 50, 20)
    traffic_load = st.slider("Traffic Load", 0.1, 3.0, 1.5, 0.1)
    mode = "combined"
    pattern = st.selectbox("Traffic Pattern", ["poisson", "ramp", "spike", "oscillate"])
    util_threshold = st.slider("Ngưỡng quá tải (util)", 0.5, 0.99, 0.80, 0.01)
    run_btn = st.button("▶ Chạy Demo LSTM", type="primary")

if run_btn:
    with st.spinner("Chạy mô phỏng..."):
        from simulator.config import SimConfig
        from simulator.core.simulator import Simulator
        from ai.data.preprocessor import samples_to_array, MinMaxScaler
        import pickle

        cfg = SimConfig(n_stations=n_stations, traffic_load=traffic_load,
                        traffic_pattern=pattern, sim_time=30.0, seed=42)
        sim = Simulator(cfg, mode=mode)
        sim.run()
        samples = sim.time_series

    with st.spinner("Chạy LSTM dự đoán..."):
        from ai.models.lstm_model import LSTMPredictor
        from ai.data.preprocessor import build_windows

        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)

        model = LSTMPredictor(n_features=6, hidden_size=64, num_layers=2, seq_out=50, device='cpu')
        model.load_weights(CHECKPOINT)

        data = samples_to_array(samples)
        scaled = scaler.transform(data)

        SEQ = 50
        # Dự đoán tại nhiều điểm thời gian
        forecasts = []
        for i in range(SEQ, len(scaled) - SEQ, 5):
            X = scaled[i - SEQ: i][np.newaxis]
            pred = model.predict(X)[0]
            pred_inv = scaler.inverse_transform(pred)
            forecasts.append({
                "window_end": samples[i].time,
                "forecast": pred_inv,
            })

        st.session_state["lstm_samples"] = samples
        st.session_state["lstm_forecasts"] = forecasts
        st.session_state["lstm_scaler"] = scaler
        st.success(f"Đã tạo {len(forecasts)} dự đoán LSTM!")

if "lstm_samples" in st.session_state:
    samples   = st.session_state["lstm_samples"]
    forecasts = st.session_state["lstm_forecasts"]

    times = [s.time for s in samples]
    utils = [s.channel_util for s in samples]
    cols  = [s.collision_rate for s in samples]

    try:
        import plotly.graph_objects as go

        # ── Chart 1: Channel Util actual + LSTM forecast ──────────────────
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=utils, name="Thực tế (channel_util)",
                                 line=dict(color='#2563EB', width=2)))

        if forecasts:
            last = forecasts[-1]
            fc_start = last["window_end"]
            fc_util  = last["forecast"][:, 5]   # channel_util = feature index 5
            fc_times = [fc_start + i * 0.1 for i in range(len(fc_util))]
            fig.add_trace(go.Scatter(x=fc_times, y=fc_util,
                                     name="Dự đoán LSTM (5s tới)",
                                     line=dict(color='#DC2626', dash='dash', width=2)))
            fig.add_hline(y=util_threshold, line_dash="dot", line_color="#D97706",
                          annotation_text=f"Ngưỡng quá tải = {util_threshold}")

        fig.update_layout(title="Channel Utilization: Thực tế vs Dự đoán LSTM",
                          xaxis_title="Thời gian (s)", yaxis_title="Channel Util",
                          height=380, legend=dict(x=0, y=1))
        st.plotly_chart(fig, use_container_width=True)

        # ── Chart 2: Collision Rate ───────────────────────────────────────
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=times, y=cols, name="Thực tế (collision_rate)",
                                  line=dict(color='#7C3AED', width=2)))
        if forecasts:
            fc_col = forecasts[-1]["forecast"][:, 3]  # collision_rate = feature index 3
            fig2.add_trace(go.Scatter(x=fc_times, y=fc_col,
                                      name="Dự đoán LSTM",
                                      line=dict(color='#D97706', dash='dash', width=2)))
        fig2.update_layout(title="Collision Rate: Thực tế vs Dự đoán LSTM",
                           xaxis_title="Thời gian (s)", yaxis_title="Collision Rate",
                           height=300)
        st.plotly_chart(fig2, use_container_width=True)

    except ImportError:
        st.info("Cài plotly để xem biểu đồ.")

    # ── Overload alert ─────────────────────────────────────────────────────
    if forecasts:
        last_util = forecasts[-1]["forecast"][:, 5]
        p_overload = float((last_util > util_threshold).mean())

        st.divider()
        st.subheader("Cảnh báo sớm (LSTM)")
        col1, col2, col3 = st.columns(3)
        col1.metric("P(quá tải) trong 5s tới", f"{p_overload:.1%}")
        col2.metric("Util thực tế hiện tại", f"{utils[-1]:.3f}")
        col3.metric("Collision hiện tại", f"{cols[-1]:.3f}")

        if p_overload > 0.6:
            st.error(f"🚨 CRITICAL: LSTM dự đoán xác suất quá tải = {p_overload:.1%} trong 5 giây tới!")
        elif p_overload > 0.3:
            st.warning(f"⚠️ WARNING: LSTM dự đoán xác suất quá tải = {p_overload:.1%}")
        else:
            st.success(f"✅ Mạng ổn định. LSTM dự đoán P(quá tải) = {p_overload:.1%}")

        # So sánh với Moving Average
        st.caption("*(So sánh: Moving Average chỉ nhìn vào giá trị gần nhất, không dự đoán xu hướng tương lai như LSTM)*")

else:
    st.info("Cấu hình tham số ở sidebar và nhấn **Chạy Demo LSTM**.")
    st.markdown("""
    **Cách hoạt động của LSTM:**
    1. Nhận 50 mẫu gần nhất (5 giây × 10 Hz) làm đầu vào
    2. Mạng LSTM 2 lớp (hidden=64) học mối quan hệ thời gian
    3. Dự đoán 50 bước tiếp theo (5 giây tương lai)
    4. Nếu `channel_util` dự đoán > ngưỡng → phát cảnh báo sớm
    """)
