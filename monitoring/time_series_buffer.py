"""Sliding-window circular buffer for MetricSample objects."""
from collections import deque
from typing import Deque, List, Optional

from simulator.metrics.collector import MetricSample


class TimeSeriesBuffer:
    """Fixed-size circular buffer storing MetricSample objects.

    Default: 10 seconds × 10 Hz = 100 samples (FIFO, oldest dropped).
    """

    def __init__(self, maxlen: int = 100) -> None:
        self._buf: Deque[MetricSample] = deque(maxlen=maxlen)
        self._maxlen = maxlen

    def push(self, sample: MetricSample) -> None:
        self._buf.append(sample)

    def get_all(self) -> List[MetricSample]:
        return list(self._buf)

    def get_last(self, n: int) -> List[MetricSample]:
        samples = list(self._buf)
        return samples[-n:] if len(samples) >= n else samples

    def get_window(self, seconds: float, hz: float = 10.0) -> List[MetricSample]:
        n = int(seconds * hz)
        return self.get_last(n)

    def is_full(self) -> bool:
        return len(self._buf) == self._maxlen

    def __len__(self) -> int:
        return len(self._buf)

    def clear(self) -> None:
        self._buf.clear()

    @property
    def latest(self) -> Optional[MetricSample]:
        return self._buf[-1] if self._buf else None
