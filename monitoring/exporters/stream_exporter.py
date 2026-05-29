"""Push MetricSamples to an in-memory queue for Streamlit live pages."""
import queue
from typing import Optional

from simulator.metrics.collector import MetricSample


class StreamExporter:
    """Thread-safe in-memory queue for real-time dashboard consumption."""

    def __init__(self, maxsize: int = 500) -> None:
        self._q: queue.Queue = queue.Queue(maxsize=maxsize)

    def push(self, sample: MetricSample) -> None:
        try:
            self._q.put_nowait(sample)
        except queue.Full:
            # Drop oldest to make room
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            self._q.put_nowait(sample)

    def pop(self, timeout: float = 0.1) -> Optional[MetricSample]:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def pop_all(self) -> list:
        items = []
        while not self._q.empty():
            try:
                items.append(self._q.get_nowait())
            except queue.Empty:
                break
        return items

    def qsize(self) -> int:
        return self._q.qsize()

    def empty(self) -> bool:
        return self._q.empty()
