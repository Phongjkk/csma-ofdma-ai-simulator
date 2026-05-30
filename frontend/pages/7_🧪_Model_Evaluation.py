"""Page 7 — Model evaluation: LSTM vs baselines."""
import streamlit as st
import numpy as np
import os

st.set_page_config(page_title="Model Evaluation", page_icon="🧪", layout="wide")
st.title("🧪 Model Evaluation")
st.caption("So sánh hiệu năng dự đoán: LSTM · Moving Average · Linear Regression")

CHECKPOINT  = "ai/saved_models/lstm_checkpoint.pt"
SCALER_PATH = "ai/saved_models/scalers.pkl"
XTEST_PATH  = "ai/saved_models/X_test.npy"
YTEST_PATH  = "ai/saved_models/y_test.npy"
EVAL_PATH   = "ai/saved_models/eval_results.json"

if os.path.exists(EVAL_PATH):
    import json
    with open(EVAL_PATH) as f:
        cached = json.load(f)

    # ── Metric cards ───────────────────────────────────────────────────
    MODEL_META = {
        "LSTM":              {"label": "LSTM",              "color": "#2563EB", "icon": "🤖"},
        "MovingAverage":     {"label": "Moving Average",    "color": "#6B7280", "icon": "📈"},
        "LinearRegression":  {"label": "Linear Regression", "color": "#6B7280", "icon": "📉"},
    }

    cols = st.columns(len(cached))
    for col, (name, metrics) in zip(cols, cached.items()):
        meta = MODEL_META.get(name, {"label": name, "color": "#374151", "icon": "📊"})
        with col:
            st.markdown(f"""
<div style="border:1px solid #E5E7EB; border-radius:10px; padding:16px; text-align:center;">
  <div style="font-size:28px">{meta['icon']}</div>
  <div style="font-size:16px; font-weight:700; color:{meta['color']}; margin:6px 0">{meta['label']}</div>
  <hr style="margin:8px 0; border-color:#F3F4F6">
  <div style="display:flex; justify-content:space-between; margin:4px 0">
    <span style="color:#6B7280; font-size:12px">MAE</span>
    <span style="font-weight:600; font-size:14px">{metrics.get('mae',0):.5f}</span>
  </div>
  <div style="display:flex; justify-content:space-between; margin:4px 0">
    <span style="color:#6B7280; font-size:12px">RMSE</span>
    <span style="font-weight:600; font-size:14px">{metrics.get('rmse',0):.5f}</span>
  </div>
  <div style="display:flex; justify-content:space-between; margin:4px 0">
    <span style="color:#6B7280; font-size:12px">MAPE</span>
    <span style="font-weight:600; font-size:14px">{metrics.get('mape',0):.2f}%</span>
  </div>
  <div style="display:flex; justify-content:space-between; margin:4px 0">
    <span style="color:#6B7280; font-size:12px">R²</span>
    <span style="font-weight:600; font-size:14px">{metrics.get('r2',0):.4f}</span>
  </div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── Charts ─────────────────────────────────────────────────────────
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        names  = list(cached.keys())
        labels = [MODEL_META.get(n, {}).get("label", n) for n in names]
        colors = [MODEL_META.get(n, {}).get("color", "#374151") for n in names]
        maes   = [cached[n].get("mae", 0)  for n in names]
        rmses  = [cached[n].get("rmse", 0) for n in names]
        mapes  = [cached[n].get("mape", 0) for n in names]
        r2s    = [cached[n].get("r2", 0)   for n in names]

        fig = make_subplots(rows=1, cols=4,
                            subplot_titles=["MAE ↓", "RMSE ↓", "MAPE (%) ↓", "R² ↑"])

        bar_kw = dict(showlegend=False)
        for col_i, (vals, fmt) in enumerate([(maes, ".5f"), (rmses, ".5f"),
                                              (mapes, ".2f"), (r2s, ".4f")], start=1):
            for i, (lbl, v, c) in enumerate(zip(labels, vals, colors)):
                fig.add_trace(go.Bar(
                    name=lbl, x=[lbl], y=[v],
                    marker_color=c,
                    text=[f"{v:{fmt}}"], textposition="outside",
                    **bar_kw
                ), row=1, col=col_i)

        fig.update_layout(height=380, bargap=0.3,
                          plot_bgcolor="white",
                          paper_bgcolor="white",
                          font=dict(size=12))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6")
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        pass

    st.caption("Tập kiểm thử: 357 cửa sổ (seq_in=50, seq_out=50, 10 Hz). "
               "Dữ liệu tổng hợp từ bộ mô phỏng CSMA/CA + OFDMA.")

else:
    # ── Train button ────────────────────────────────────────────────────
    st.info("Chưa có kết quả đánh giá. Nhấn nút bên dưới để huấn luyện và đánh giá.")
    if st.button("▶ Huấn luyện & Đánh giá", type="primary"):
        with st.spinner("Đang huấn luyện LSTM (khoảng 2–5 phút)..."):
            import subprocess, sys
            r = subprocess.run([sys.executable, "scripts/_train_lstm.py"],
                               capture_output=True, text=True, cwd=".")
            if r.returncode == 0:
                st.success("Hoàn tất!")
                st.rerun()
            else:
                st.error("Lỗi huấn luyện")
                st.code(r.stderr[-800:])

# ── Horizon accuracy ────────────────────────────────────────────────────
if os.path.exists(XTEST_PATH) and os.path.exists(CHECKPOINT):
    st.divider()
    st.subheader("Độ chính xác theo tầm dự đoán")

    if st.button("📊 Phân tích horizon"):
        with st.spinner("Đang tính toán..."):
            import pickle
            from ai.models.lstm_model import LSTMPredictor
            from ai.evaluation.metrics import evaluate_regression
            from ai.data.preprocessor import FEATURE_COLS

            Xte = np.load(XTEST_PATH)
            yte = np.load(YTEST_PATH)
            model = LSTMPredictor(n_features=6, hidden_size=64,
                                  num_layers=2, seq_out=50, device="cpu")
            model.load_weights(CHECKPOINT)
            preds = model.predict(Xte)

            rows = []
            for label, steps in [("1 giây", 10), ("3 giây", 30), ("5 giây", 50)]:
                m = evaluate_regression(yte[:, :steps, :], preds[:, :steps, :], FEATURE_COLS)
                rows.append({"Tầm dự đoán": label,
                             "MAE": f"{m['mae']:.5f}",
                             "MAPE (%)": f"{m['mape']:.2f}",
                             "R²": f"{m['r2']:.4f}"})

            try:
                import pandas as pd
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            except ImportError:
                st.json(rows)

            try:
                import plotly.graph_objects as go
                horizons = [r["Tầm dự đoán"] for r in rows]
                maes_h   = [float(r["MAE"]) for r in rows]
                fig = go.Figure(go.Scatter(
                    x=horizons, y=maes_h, mode="lines+markers+text",
                    text=[f"{v:.5f}" for v in maes_h], textposition="top center",
                    line=dict(color="#2563EB", width=2.5), marker=dict(size=9),
                ))
                fig.update_layout(title="LSTM — MAE theo tầm dự đoán",
                                  yaxis_title="MAE", height=320,
                                  plot_bgcolor="white",
                                  yaxis=dict(gridcolor="#F3F4F6"))
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass
