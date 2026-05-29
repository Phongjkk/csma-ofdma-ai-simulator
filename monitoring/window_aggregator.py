"""Aggregate raw samples into 1-s / 5-s windowed statistics."""
from typing import Dict, List, Optional
import numpy as np

from simulator.metrics.collector import MetricSample


class WindowAggregator:
    """Accumulate MetricSamples and compute aggregate statistics over windows."""

    FIELDS = [
        "throughput_mbps", "latency_mean_ms", "latency_p99_ms",
        "collision_rate", "fairness_index", "channel_util",
    ]

    def __init__(self, window_size: float = 1.0, hz: float = 10.0) -> None:
        self._window_size = window_size
        self._hz = hz
        self._capacity = int(window_size * hz)
        self._samples: List[MetricSample] = []

    def push(self, sample: MetricSample) -> None:
        self._samples.append(sample)
        if len(self._samples) > self._capacity:
            self._samples.pop(0)

    def aggregate(self) -> Dict[str, float]:
        if not self._samples:
            return {f: 0.0 for f in self.FIELDS}
        result = {}
        for field in self.FIELDS:
            vals = [getattr(s, field) for s in self._samples]
            result[field] = float(np.mean(vals))
            result[f"{field}_std"] = float(np.std(vals))
            result[f"{field}_min"] = float(np.min(vals))
            result[f"{field}_max"] = float(np.max(vals))
        return result

    def latest_sample(self) -> Optional[MetricSample]:
        return self._samples[-1] if self._samples else None

    def sample_count(self) -> int:
        return len(self._samples)

    def is_ready(self) -> bool:
        return len(self._samples) >= self._capacity

    def clear(self) -> None:
        self._samples.clear()
