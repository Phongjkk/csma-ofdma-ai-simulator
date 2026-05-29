"""Stateful predictor: update() one sample at a time, returns P(overload)."""
from collections import deque
from typing import Deque, List, Optional
import numpy as np

from simulator.metrics.collector import MetricSample
from ai.data.preprocessor import MinMaxScaler, FEATURE_COLS
from ai.inference.predictor import Predictor


FEATURE_IDX = {f: i for i, f in enumerate(FEATURE_COLS)}
CHANNEL_UTIL_IDX = FEATURE_IDX["channel_util"]
COLLISION_IDX = FEATURE_IDX["collision_rate"]
LATENCY_IDX = FEATURE_IDX["latency_p99_ms"]


def _sample_to_vec(s: MetricSample) -> np.ndarray:
    return np.array([
        s.throughput_mbps, s.latency_mean_ms, s.latency_p99_ms,
        s.collision_rate, s.fairness_index, s.channel_util,
    ], dtype=np.float32)


class StreamPredictor:
    """Maintains a sliding window buffer and runs LSTM inference on each push."""

    def __init__(
        self,
        predictor: Predictor,
        scaler: Optional[MinMaxScaler],
        seq_in: int = 50,
    ) -> None:
        self._predictor = predictor
        self._scaler = scaler
        self._seq_in = seq_in
        self._buffer: Deque[np.ndarray] = deque(maxlen=seq_in)
        self._last_forecast: Optional[np.ndarray] = None

    def update(self, sample: MetricSample) -> Optional[np.ndarray]:
        """Push one sample; return (seq_out, n_feat) forecast when buffer is full."""
        vec = _sample_to_vec(sample)
        if self._scaler is not None:
            vec = self._scaler.transform(vec.reshape(1, -1)).flatten()
        self._buffer.append(vec)

        if len(self._buffer) < self._seq_in:
            return None

        X = np.array(self._buffer, dtype=np.float32)[np.newaxis]  # (1, seq_in, F)
        raw = self._predictor.predict(X)  # (1, seq_out, F)
        forecast = raw[0]

        if self._scaler is not None:
            N, F = forecast.shape
            forecast = self._scaler.inverse_transform(forecast)

        self._last_forecast = forecast
        return forecast

    def overload_probability(self, util_threshold: float = 0.90) -> float:
        """Fraction of forecast horizon where channel_util > threshold."""
        if self._last_forecast is None:
            return 0.0
        utils = self._last_forecast[:, CHANNEL_UTIL_IDX]
        return float((utils > util_threshold).mean())

    def predicted_collision_rate(self) -> Optional[np.ndarray]:
        if self._last_forecast is None:
            return None
        return self._last_forecast[:, COLLISION_IDX]

    @property
    def is_ready(self) -> bool:
        return len(self._buffer) >= self._seq_in

    @property
    def last_forecast(self) -> Optional[np.ndarray]:
        return self._last_forecast
