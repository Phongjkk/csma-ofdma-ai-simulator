"""Page 7 — So sánh LSTM (AI) vs các baseline (Moving Average, Linear Regression)."""
import streamlit as st
import numpy as np
import os

st.set_page_config(page_title="Model Evaluation", page_icon="🧪", layout="wide")
st.title("🧪 Đánh giá mô hình AI")

st.markdown("""
Trang này so sánh **LSTM (mô hình AI thực sự)** với hai baseline thống kê:
- **Moving Average** — trung bình trượt, không phải AI
- **Linear Regression** — hồi quy tuyến tính, không phải AI

LSTM mới là mô hình học sâu (deep learning) thực sự, được huấn luyện trên dữ liệu từ bộ mô phỏng.
""")

CHECKPOINT = "ai/saved_models/lstm_checkpoint.pt"
SCALER_PATH = "ai/saved_models/scalers.pkl"
XTEST_PATH  = "ai/saved_models/X_test.npy"
YTEST_PATH  = "ai/saved_models/y_test.npy"
EVAL_PATH   = "ai/saved_models/eval_results.json"

# ── Load pre-computed results if available ──────────────────────────────────
if os.path.exists(EVAL_PATH):
    import json
    with open(EVAL_PATH) as f:
        cached = json.load(f)
    st.success("Kết quả đánh giá từ lần huấn luyện gần nhất:")

    try:
        import pandas as pd
        rows = []
        labels = {"LSTM": "**LSTM (AI)**", "MovingAverage": "Moving Average (baseline)",
                  "LinearRegression": "Linear Regression (baseline)"}
        for name, m in cached.items():
            rows.append({
                "Mô hình": labels.get(name, name),
                "MAE":  f"{m.get('mae', 0):.5f}",
                "RMSE": f"{m.get('rmse', 0):.5f}",
                "MAPE (%)": f"{m.get('mape', 0):.2f}",
                "R²":  f"{m.get('r2', 0):.4f}",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except ImportError:
        st.json(cached)

    # Bar chart so sánh MAE
    try:
        import plotly.graph_objects as go
        names  = list(cached.keys())
        maes   = [cached[n].get('mae',0) for n in names]
        r2s    = [cached[n].get('r2',0)  for n in names]
        colors = {'LSTM': '#2563EB', 'MovingAverage': '#6B7280', 'LinearRegression': '#6B7280'}

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure(go.Bar(
                x=names, y=maes,
                marker_color=[colors.get(n, '#6B7280') for n in names],
                text=[f"{v:.5f}" for v in maes], textposition='outside',
            ))
            fig.update_layout(title="MAE theo mô hình (thấp hơn = tốt hơn)",
                              yaxis_title="MAE", height=350,
                              annotations=[dict(x='LSTM', y=max(maes)*0.5,
                                               text="AI model", showarrow=False,
                                               font=dict(color='#2563EB', size=11))])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = go.Figure(go.Bar(
                x=names, y=r2s,
                marker_color=[colors.get(n, '#6B7280') for n in names],
                text=[f"{v:.4f}" for v in r2s], textposition='outside',
            ))
            fig2.update_layout(title="R² theo mô hình (cao hơn = tốt hơn)",
                               yaxis_title="R²", height=350)
            st.plotly_chart(fig2, use_container_width=True)

    except ImportError:
        st.info("Cài plotly để xem biểu đồ.")

    st.info("Để huấn luyện lại LSTM: `python scripts/_train_lstm.py`")

else:
    st.warning("Chưa có checkpoint LSTM. Nhấn nút dưới để huấn luyện.")
    if st.button("▶ Sinh dữ liệu + Huấn luyện LSTM", type="primary"):
        with st.spinner("Đang chạy (có thể mất vài phút)..."):
            import subprocess, sys
            result = subprocess.run(
                [sys.executable, "scripts/_train_lstm.py"],
                capture_output=True, text=True, cwd="."
            )
            if result.returncode == 0:
                st.success("Huấn luyện xong!")
                st.code(result.stdout[-2000:])
                st.rerun()
            else:
                st.error("Lỗi:")
                st.code(result.stderr[-1000:])

# ── Horizon accuracy ─────────────────────────────────────────────────────────
if os.path.exists(XTEST_PATH) and os.path.exists(CHECKPOINT):
    st.divider()
    st.subheader("Độ chính xác theo tầm dự đoán (LSTM)")
    if st.button("📊 Tính horizon accuracy"):
        with st.spinner("Đang dự đoán..."):
            import pickle
            from ai.models.lstm_model import LSTMPredictor
            from ai.evaluation.metrics import evaluate_regression
            from ai.data.preprocessor import FEATURE_COLS

            Xte = np.load(XTEST_PATH)
            yte = np.load(YTEST_PATH)

            model = LSTMPredictor(n_features=6, hidden_size=64, num_layers=2, seq_out=50, device='cpu')
            model.load_weights(CHECKPOINT)
            preds = model.predict(Xte)

            rows = []
            for label, steps in [("1 giây (10 bước)", 10), ("3 giây (30 bước)", 30), ("5 giây (50 bước)", 50)]:
                met = evaluate_regression(yte[:, :steps, :], preds[:, :steps, :], FEATURE_COLS)
                rows.append({"Tầm dự đoán": label,
                             "MAE": round(met['mae'], 5),
                             "MAPE (%)": round(met['mape'], 2),
                             "R²": round(met['r2'], 4)})

            try:
                import pandas as pd
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            except ImportError:
                st.json(rows)
