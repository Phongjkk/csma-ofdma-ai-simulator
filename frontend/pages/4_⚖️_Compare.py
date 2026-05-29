"""Page 4 — So sánh hiệu năng theo mức tải và số station (CSMA/CA + OFDMA kết hợp)."""
import streamlit as st

st.set_page_config(page_title="So sánh hiệu năng", page_icon="⚖️", layout="wide")
st.title("⚖️ So sánh hiệu năng")
st.caption("Mô phỏng CSMA/CA + OFDMA kết hợp (IEEE 802.11ax) — đánh giá theo mức tải và số station")

with st.sidebar:
    st.header("Cài đặt so sánh")
    n_stations = st.slider("Số lượng Station", 5, 100, 20)
    sim_time = st.slider("Thời gian mô phỏng (s)", 5.0, 30.0, 15.0, 5.0)
    pattern = st.selectbox("Kiểu lưu lượng", ["poisson", "cbr", "ramp", "spike"])
    run_btn = st.button("▶ Chạy 3 mức tải", type="primary")

if run_btn:
    from simulator.config import SimConfig
    from simulator.modes.mode_combined import run_combined

    LOADS = {"Thấp (0.2)": 0.2, "Trung bình (0.5)": 0.5, "Cao (0.8)": 0.8}
    results = {}
    for label, load in LOADS.items():
        cfg = SimConfig(n_stations=n_stations, traffic_load=load,
                        sim_time=sim_time, traffic_pattern=pattern, seed=42)
        with st.spinner(f"Đang chạy mức tải {label}..."):
            results[label] = run_combined(cfg)["summary"]
    st.session_state["compare_results"] = results
    st.success("Hoàn tất 3 mức tải!")

if "compare_results" in st.session_state:
    results = st.session_state["compare_results"]
    load_labels = list(results.keys())
    metrics = ["throughput_mbps", "latency_p99_ms", "collision_rate", "fairness_index", "channel_util"]
    labels  = ["Throughput (Mbps)", "Latency P99 (ms)", "Collision Rate", "Fairness", "Channel Util"]

    st.subheader("Bảng so sánh")
    try:
        import pandas as pd
        rows = [{"Mức tải": lbl, **{l: round(results[lbl][m], 4)
                                     for m, l in zip(metrics, labels)}}
                for lbl in load_labels]
        st.dataframe(pd.DataFrame(rows).set_index("Mức tải"), use_container_width=True)
    except ImportError:
        st.json(results)

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        st.subheader("Biểu đồ cột")
        fig = make_subplots(rows=1, cols=len(metrics), subplot_titles=labels)
        colors = ["#00CC96", "#636EFA", "#EF553B"]
        for j, (m, lbl) in enumerate(zip(metrics, labels)):
            for i, load_lbl in enumerate(load_labels):
                fig.add_trace(
                    go.Bar(name=load_lbl, x=[load_lbl], y=[results[load_lbl][m]],
                           marker_color=colors[i], showlegend=(j == 0)),
                    row=1, col=j + 1,
                )
        fig.update_layout(height=400, barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass
else:
    st.info("Cấu hình tham số ở sidebar và nhấn **Chạy 3 mức tải**.")
