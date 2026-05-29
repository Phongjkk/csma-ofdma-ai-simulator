"""Mean + 95 % confidence intervals (scipy.stats)."""
from typing import Dict, List, Tuple
import numpy as np


def mean_ci(values: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
    """Returns (mean, ci_low, ci_high)."""
    from scipy import stats
    arr = np.array(values)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0
    m = float(arr.mean())
    if n == 1:
        return m, m, m
    se = stats.sem(arr)
    h = se * stats.t.ppf((1 + confidence) / 2, n - 1)
    return m, float(m - h), float(m + h)


def summary_stats(values: List[float]) -> Dict[str, float]:
    arr = np.array(values)
    if len(arr) == 0:
        return {}
    m, lo, hi = mean_ci(values)
    return {
        "mean": m,
        "ci_low": lo,
        "ci_high": hi,
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
    }


def aggregate_runs(runs: List[dict], key: str) -> Dict[str, float]:
    vals = [r[key] for r in runs if key in r]
    return summary_stats(vals)
