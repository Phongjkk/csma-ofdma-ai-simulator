"""MinMax / Standard scaling; build sliding-window tensors."""
import numpy as np
from typing import List, Optional, Tuple
from simulator.metrics.collector import MetricSample


FEATURE_COLS = [
    "throughput_mbps", "latency_mean_ms", "latency_p99_ms",
    "collision_rate", "fairness_index", "channel_util",
]


class MinMaxScaler:
    def __init__(self) -> None:
        self._min: Optional[np.ndarray] = None
        self._max: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "MinMaxScaler":
        self._min = X.min(axis=0)
        self._max = X.max(axis=0)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        rng = self._max - self._min
        rng[rng == 0] = 1.0
        return (X - self._min) / rng

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        rng = self._max - self._min
        rng[rng == 0] = 1.0
        return X * rng + self._min

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


class StandardScaler:
    def __init__(self) -> None:
        self._mean: Optional[np.ndarray] = None
        self._std: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "StandardScaler":
        self._mean = X.mean(axis=0)
        self._std = X.std(axis=0)
        self._std[self._std == 0] = 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self._mean) / self._std

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return X * self._std + self._mean

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


def samples_to_array(samples: List[MetricSample]) -> np.ndarray:
    """Convert list of MetricSample to (N, n_features) array."""
    return np.array([
        [s.throughput_mbps, s.latency_mean_ms, s.latency_p99_ms,
         s.collision_rate, s.fairness_index, s.channel_util]
        for s in samples
    ], dtype=np.float32)


def build_windows(
    data: np.ndarray,
    seq_in: int = 50,
    seq_out: int = 50,
) -> Tuple[np.ndarray, np.ndarray]:
    """Slide over time dimension → X (N, seq_in, F), y (N, seq_out, F)."""
    N, F = data.shape
    xs, ys = [], []
    for i in range(N - seq_in - seq_out + 1):
        xs.append(data[i: i + seq_in])
        ys.append(data[i + seq_in: i + seq_in + seq_out])
    if not xs:
        return np.empty((0, seq_in, F)), np.empty((0, seq_out, F))
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)
