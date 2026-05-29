"""Plotly / Matplotlib bar charts, CDF, time-series figures."""
from typing import List
import numpy as np


def plot_throughput_vs_stations(results: List[dict], modes: List[str]):
    """Line chart: throughput (Mbps) vs n_stations for each mode."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    fig = go.Figure()
    for mode in modes:
        mode_data = [r for r in results if r["config"]["mode"] == mode]
        mode_data.sort(key=lambda r: r["config"]["n_stations"])
        xs = [r["config"]["n_stations"] for r in mode_data]
        ys = [r["summary"]["throughput_mbps"] for r in mode_data]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=mode))
    fig.update_layout(
        title="Throughput vs Number of Stations",
        xaxis_title="Number of Stations",
        yaxis_title="Throughput (Mbps)",
    )
    return fig


def plot_collision_rate_vs_stations(results: List[dict], modes: List[str]):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    fig = go.Figure()
    for mode in modes:
        mode_data = sorted(
            [r for r in results if r["config"]["mode"] == mode],
            key=lambda r: r["config"]["n_stations"],
        )
        xs = [r["config"]["n_stations"] for r in mode_data]
        ys = [r["summary"]["collision_rate"] for r in mode_data]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=mode))
    fig.update_layout(
        title="Collision Rate vs Number of Stations",
        xaxis_title="Number of Stations",
        yaxis_title="Collision Rate",
    )
    return fig


def plot_latency_cdf(latencies: List[float], label: str = "Latency"):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    sorted_lat = np.sort(latencies)
    cdf = np.arange(1, len(sorted_lat) + 1) / len(sorted_lat)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sorted_lat, y=cdf, mode="lines", name=label))
    fig.update_layout(title="Latency CDF", xaxis_title="Latency (ms)", yaxis_title="CDF")
    return fig


def plot_time_series(time_series: List[dict], metric: str = "throughput_mbps"):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    ts = [s["time"] for s in time_series]
    vs = [s[metric] for s in time_series]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts, y=vs, mode="lines", name=metric))
    fig.update_layout(title=f"{metric} over time", xaxis_title="Time (s)", yaxis_title=metric)
    return fig


def plot_bianchi_comparison(n_list: List[int], sim_thr: List[float], bianchi_thr: List[float]):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=n_list, y=bianchi_thr, mode="lines+markers", name="Bianchi"))
    fig.add_trace(go.Scatter(x=n_list, y=sim_thr, mode="lines+markers", name="Simulation",
                              line=dict(dash="dash")))
    fig.update_layout(
        title="Bianchi vs Simulation Throughput Validation",
        xaxis_title="Number of Stations",
        yaxis_title="Throughput (Mbps)",
    )
    return fig


def plot_mode_comparison_bar(results: List[dict], load: float = 0.5):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    filtered = [r for r in results if abs(r["config"]["traffic_load"] - load) < 0.01]
    modes = list(set(r["config"]["mode"] for r in filtered))
    metrics = ["throughput_mbps", "latency_mean_ms", "collision_rate"]

    fig = go.Figure()
    for metric in metrics:
        vals = [
            next((r["summary"][metric] for r in filtered if r["config"]["mode"] == m), 0)
            for m in modes
        ]
        fig.add_trace(go.Bar(name=metric, x=modes, y=vals))
    fig.update_layout(barmode="group", title=f"Mode Comparison (load={load})")
    return fig
