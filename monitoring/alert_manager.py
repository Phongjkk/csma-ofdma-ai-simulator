"""Fire threshold-based alerts; dispatch to registered callbacks."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional
import time as _time

from monitoring.anomaly_detector import Anomaly


class Severity(Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    id: int
    timestamp: float
    severity: Severity
    metric: str
    value: float
    threshold: float
    message: str


def _classify_severity(anomaly: Anomaly) -> Severity:
    if anomaly.metric == "latency_p99_ms" and anomaly.value > anomaly.threshold * 2:
        return Severity.CRITICAL
    if anomaly.metric == "collision_rate" and anomaly.value > 0.5:
        return Severity.CRITICAL
    if anomaly.metric == "channel_util" and anomaly.value > 0.99:
        return Severity.CRITICAL
    return Severity.WARNING


class AlertManager:
    """Deduplicates and dispatches alerts with per-metric cooldown."""

    COOLDOWN_S = 5.0

    def __init__(self) -> None:
        self._callbacks: List[Callable[[Alert], None]] = []
        self._last_fired: Dict[str, float] = {}
        self._history: List[Alert] = []
        self._counter: int = 0

    def register(self, callback: Callable[[Alert], None]) -> None:
        self._callbacks.append(callback)

    def process_anomalies(self, anomalies: List[Anomaly], sim_time: float) -> List[Alert]:
        new_alerts: List[Alert] = []
        for anomaly in anomalies:
            last = self._last_fired.get(anomaly.metric, -999.0)
            if sim_time - last < self.COOLDOWN_S:
                continue
            self._last_fired[anomaly.metric] = sim_time
            self._counter += 1
            severity = _classify_severity(anomaly)
            alert = Alert(
                id=self._counter,
                timestamp=sim_time,
                severity=severity,
                metric=anomaly.metric,
                value=anomaly.value,
                threshold=anomaly.threshold,
                message=(
                    f"[{severity.value}] {anomaly.metric}={anomaly.value:.3f} "
                    f"(threshold={anomaly.threshold:.3f}) at t={sim_time:.2f}s"
                ),
            )
            self._history.append(alert)
            new_alerts.append(alert)
            for cb in self._callbacks:
                cb(alert)
        return new_alerts

    @property
    def history(self) -> List[Alert]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
        self._last_fired.clear()
