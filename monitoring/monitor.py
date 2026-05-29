"""RealtimeMonitor: receives simulator ticks, feeds buffer + alerts."""
from typing import Callable, List, Optional

from simulator.metrics.collector import MetricSample
from monitoring.time_series_buffer import TimeSeriesBuffer
from monitoring.window_aggregator import WindowAggregator
from monitoring.anomaly_detector import AnomalyDetector, Anomaly
from monitoring.alert_manager import AlertManager, Alert


class RealtimeMonitor:
    """Orchestrates the full monitoring pipeline.

    Pipeline:
        Simulator MetricSample → WindowAggregator → TimeSeriesBuffer
        → AnomalyDetector → AlertManager → callbacks
    """

    def __init__(
        self,
        buffer_maxlen: int = 100,
        window_size: float = 1.0,
        hz: float = 10.0,
    ) -> None:
        self._buffer = TimeSeriesBuffer(maxlen=buffer_maxlen)
        self._aggregator = WindowAggregator(window_size=window_size, hz=hz)
        self._detector = AnomalyDetector()
        self._alert_manager = AlertManager()
        self._sample_count: int = 0

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def on_alert(self, callback: Callable[[Alert], None]) -> None:
        self._alert_manager.register(callback)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def push(self, sample: MetricSample) -> List[Alert]:
        """Ingest one MetricSample, run anomaly detection, return any new alerts."""
        self._buffer.push(sample)
        self._aggregator.push(sample)
        self._sample_count += 1

        anomalies = self._detector.check(sample)
        alerts = self._alert_manager.process_anomalies(anomalies, sample.time)
        return alerts

    def push_batch(self, samples: List[MetricSample]) -> List[Alert]:
        all_alerts: List[Alert] = []
        for s in samples:
            all_alerts.extend(self.push(s))
        return all_alerts

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    @property
    def buffer(self) -> TimeSeriesBuffer:
        return self._buffer

    @property
    def alert_history(self) -> List[Alert]:
        return self._alert_manager.history

    def get_latest(self) -> Optional[MetricSample]:
        return self._buffer.latest

    def get_window(self, seconds: float = 5.0) -> List[MetricSample]:
        return self._buffer.get_window(seconds)

    def get_aggregate(self) -> dict:
        return self._aggregator.aggregate()

    def fit_anomaly_model(self) -> None:
        samples = self._buffer.get_all()
        self._detector.fit_isolation_forest(samples)

    @property
    def sample_count(self) -> int:
        return self._sample_count
