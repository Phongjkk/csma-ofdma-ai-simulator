"""Plotly: prediction-vs-actual, confusion matrix, ROC curve."""
from typing import List, Optional
import numpy as np


def plot_prediction_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    feature_names: Optional[List[str]] = None,
    title: str = "Prediction vs Actual",
    sample_idx: int = 0,
):
    """Plotly line chart comparing forecast vs ground truth for one sample."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        return None

    if y_true.ndim == 3:
        true_seq = y_true[sample_idx]
        pred_seq = y_pred[sample_idx]
    else:
        true_seq = y_true
        pred_seq = y_pred

    n_feat = true_seq.shape[-1]
    names = feature_names or [f"feature_{i}" for i in range(n_feat)]
    fig = make_subplots(rows=n_feat, cols=1, shared_xaxes=True,
                        subplot_titles=names)
    t = np.arange(len(true_seq))
    for i, name in enumerate(names):
        fig.add_trace(go.Scatter(x=t, y=true_seq[:, i], name=f"{name} actual",
                                 line=dict(color="blue")), row=i + 1, col=1)
        fig.add_trace(go.Scatter(x=t, y=pred_seq[:, i], name=f"{name} pred",
                                 line=dict(color="red", dash="dash")), row=i + 1, col=1)
    fig.update_layout(title=title, height=200 * n_feat)
    return fig


def plot_training_history(train_losses: List[float], val_losses: List[float]):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=train_losses, name="Train Loss"))
    fig.add_trace(go.Scatter(y=val_losses, name="Val Loss"))
    fig.update_layout(title="Training History", xaxis_title="Epoch", yaxis_title="MSE Loss")
    return fig


def plot_metric_over_time(
    time: np.ndarray,
    values: np.ndarray,
    label: str = "Metric",
    forecast_start: Optional[int] = None,
):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    fig = go.Figure()
    if forecast_start is not None:
        fig.add_trace(go.Scatter(x=time[:forecast_start], y=values[:forecast_start],
                                 name="Historical", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=time[forecast_start:], y=values[forecast_start:],
                                 name="Forecast", line=dict(color="red", dash="dash")))
    else:
        fig.add_trace(go.Scatter(x=time, y=values, name=label))
    fig.update_layout(title=label)
    return fig
