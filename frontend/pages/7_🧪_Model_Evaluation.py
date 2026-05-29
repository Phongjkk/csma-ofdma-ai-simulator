"""Page 7 — Model evaluation: metrics table, ROC, confusion matrix."""
import streamlit as st
import numpy as np

st.set_page_config(page_title="Model Evaluation", page_icon="🧪", layout="wide")
st.title("🧪 Model Evaluation")

with st.sidebar:
    st.header("Evaluation Settings")
    n_samples = st.slider("Test Windows", 50, 500, 100)
    seq_in = st.number_input("Input Sequence Length", 10, 100, 50)
    seq_out = st.number_input("Output Sequence Length", 5, 100, 50)
    run_eval = st.button("▶ Evaluate Models", type="primary")

if run_eval:
    with st.spinner("Generating test data via simulator..."):
        from simulator.config import SimConfig
        from simulator.core.simulator import Simulator
        from ai.data.preprocessor import samples_to_array, MinMaxScaler, build_windows

        cfg = SimConfig(n_stations=20, traffic_load=0.7, sim_time=60.0, seed=99)
        sim = Simulator(cfg, mode="su")
        sim.run()
        data = samples_to_array(sim.time_series)
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(data)
        X, y = build_windows(scaled, int(seq_in), int(seq_out))
        if len(X) == 0:
            st.error("Not enough data. Increase sim_time.")
            st.stop()
        idx = min(n_samples, len(X))
        X_test, y_test = X[-idx:], y[-idx:]

    from ai.models.moving_average import MovingAverageModel
    from ai.models.linear_regression import LinearRegressionModel
    from ai.evaluation.comparator import ModelComparator

    comparator = ModelComparator()

    with st.spinner("Evaluating Moving Average..."):
        ma = MovingAverageModel(n_steps=int(seq_out))
        ma.fit(X_test, y_test)
        comparator.add("MovingAverage", y_test, ma.predict(X_test))

    with st.spinner("Evaluating Linear Regression..."):
        lr = LinearRegressionModel(n_steps=int(seq_out))
        lr.fit(X_test, y_test)
        comparator.add("LinearRegression", y_test, lr.predict(X_test))

    st.session_state["eval_comparator"] = comparator
    st.session_state["eval_y_test"] = y_test
    st.session_state["eval_models"] = {"MovingAverage": ma, "LinearRegression": lr}
    st.success("Evaluation complete!")

if "eval_comparator" in st.session_state:
    comparator = st.session_state["eval_comparator"]
    results = comparator.results

    st.subheader("Model Comparison Table")
    try:
        import pandas as pd
        rows = [{"Model": name, "MAE": f"{m['mae']:.5f}", "RMSE": f"{m['rmse']:.5f}",
                 "MAPE": f"{m['mape']:.2f}%", "R²": f"{m['r2']:.4f}"}
                for name, m in results.items()]
        st.dataframe(pd.DataFrame(rows).set_index("Model"), use_container_width=True)
    except ImportError:
        for name, m in results.items():
            st.write(f"**{name}**: MAE={m['mae']:.5f}, RMSE={m['rmse']:.5f}")

    st.subheader("MAE by Feature")
    from ai.data.preprocessor import FEATURE_COLS
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        for model_name, m in results.items():
            mae_vals = [m.get(f"mae_{f}", 0) for f in FEATURE_COLS]
            fig.add_trace(go.Bar(name=model_name, x=FEATURE_COLS, y=mae_vals))
        fig.update_layout(barmode="group", title="MAE per Feature", height=350)
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass

    best = comparator.best_model("mae")
    st.info(f"Best model by MAE: **{best}**")
else:
    st.info("Click **Evaluate Models** in the sidebar.")
