"""Compare multiple model results in a single summary table."""
from typing import Dict, List, Optional
import numpy as np

from ai.evaluation.metrics import evaluate_regression, FEATURE_COLS


try:
    FEATURE_COLS
except NameError:
    FEATURE_COLS = ["throughput_mbps", "latency_mean_ms", "latency_p99_ms",
                    "collision_rate", "fairness_index", "channel_util"]

from ai.data.preprocessor import FEATURE_COLS


class ModelComparator:
    """Run multiple models on the same test set and produce comparison metrics."""

    def __init__(self, feature_names: Optional[List[str]] = None) -> None:
        self._feature_names = feature_names or FEATURE_COLS
        self._results: Dict[str, Dict[str, float]] = {}

    def add(self, model_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
        metrics = evaluate_regression(y_true, y_pred, self._feature_names)
        self._results[model_name] = metrics

    def summary_table(self) -> "pd.DataFrame":
        try:
            import pandas as pd
        except ImportError:
            return None
        rows = []
        for name, metrics in self._results.items():
            row = {"model": name, "MAE": metrics["mae"], "RMSE": metrics["rmse"],
                   "MAPE": metrics["mape"], "R2": metrics["r2"]}
            rows.append(row)
        return pd.DataFrame(rows).set_index("model").round(4)

    def best_model(self, metric: str = "mae") -> str:
        return min(self._results, key=lambda m: self._results[m].get(metric, float("inf")))

    @property
    def results(self) -> Dict[str, Dict[str, float]]:
        return self._results

    def print_summary(self) -> None:
        df = self.summary_table()
        if df is not None:
            print(df.to_string())
        else:
            for name, m in self._results.items():
                print(f"{name}: MAE={m['mae']:.4f}, RMSE={m['rmse']:.4f}, MAPE={m['mape']:.2f}%")
