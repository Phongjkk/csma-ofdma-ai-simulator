"""Z-score anomaly detector on sliding metric windows."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from simulator.metrics.collector import MetricSample


# Threshold-based limits (doc §5)
THRESHOLDS = {
    "latency_p99_ms": 100.0,     # ms — alert if above
    "collision_rate": 0.30,      # fraction — alert if above
    "channel_util": 0.95,        # fraction — alert if above
    "throughput_mbps": 1.0,      # Mbps — alert if below
}


@dataclass
class Anomaly:
    time: float
    metric: str
    value: float
    threshold: float
    z_score: float
    method: str  # 'threshold' or 'isolation_forest' or 'zscore'


class ThresholdDetector:
    def check(self, sample: MetricSample) -> List[Anomaly]:
        anomalies: List[Anomaly] = []
        t = sample.time
        if sample.latency_p99_ms > THRESHOLDS["latency_p99_ms"]:
            anomalies.append(Anomaly(t, "latency_p99_ms", sample.latency_p99_ms,
                                     THRESHOLDS["latency_p99_ms"], 0.0, "threshold"))
        if sample.collision_rate > THRESHOLDS["collision_rate"]:
            anomalies.append(Anomaly(t, "collision_rate", sample.collision_rate,
                                     THRESHOLDS["collision_rate"], 0.0, "threshold"))
        if sample.channel_util > THRESHOLDS["channel_util"]:
            anomalies.append(Anomaly(t, "channel_util", sample.channel_util,
                                     THRESHOLDS["channel_util"], 0.0, "threshold"))
        if sample.throughput_mbps < THRESHOLDS["throughput_mbps"] and sample.time > 1.0:
            anomalies.append(Anomaly(t, "throughput_mbps", sample.throughput_mbps,
                                     THRESHOLDS["throughput_mbps"], 0.0, "threshold"))
        return anomalies


class ZScoreDetector:
    """Detect anomalies using rolling z-score on a sliding window."""

    def __init__(self, window: int = 30, z_thresh: float = 3.0) -> None:
        self._window = window
        self._z_thresh = z_thresh
        self._history: Dict[str, List[float]] = {
            "throughput_mbps": [],
            "latency_mean_ms": [],
            "collision_rate": [],
            "channel_util": [],
        }

    def push_and_check(self, sample: MetricSample) -> List[Anomaly]:
        anomalies: List[Anomaly] = []
        fields = {
            "throughput_mbps": sample.throughput_mbps,
            "latency_mean_ms": sample.latency_mean_ms,
            "collision_rate": sample.collision_rate,
            "channel_util": sample.channel_util,
        }
        for field, val in fields.items():
            hist = self._history[field]
            hist.append(val)
            if len(hist) > self._window:
                hist.pop(0)
            if len(hist) >= 5:
                arr = np.array(hist[:-1])
                mean, std = arr.mean(), arr.std()
                if std > 1e-9:
                    z = abs(val - mean) / std
                    if z > self._z_thresh:
                        anomalies.append(Anomaly(sample.time, field, val, mean, z, "zscore"))
        return anomalies


class IsolationForestDetector:
    """Sklearn Isolation Forest for multivariate anomaly detection."""

    def __init__(self, contamination: float = 0.05, n_estimators: int = 100) -> None:
        self._contamination = contamination
        self._n_estimators = n_estimators
        self._model = None
        self._is_fitted = False

    def fit(self, samples: List[MetricSample]) -> None:
        if len(samples) < 20:
            return
        try:
            from sklearn.ensemble import IsolationForest
            X = self._to_matrix(samples)
            self._model = IsolationForest(
                contamination=self._contamination,
                n_estimators=self._n_estimators,
                random_state=42,
            )
            self._model.fit(X)
            self._is_fitted = True
        except ImportError:
            pass

    def predict(self, sample: MetricSample) -> bool:
        """Returns True if anomaly."""
        if not self._is_fitted or self._model is None:
            return False
        X = self._to_matrix([sample])
        pred = self._model.predict(X)
        return bool(pred[0] == -1)

    def _to_matrix(self, samples: List[MetricSample]):
        import numpy as np
        return np.array([
            [s.throughput_mbps, s.latency_mean_ms, s.latency_p99_ms,
             s.collision_rate, s.fairness_index, s.channel_util]
            for s in samples
        ])


class AnomalyDetector:
    """Combined anomaly detector: threshold + z-score + optional IF."""

    def __init__(self) -> None:
        self._threshold = ThresholdDetector()
        self._zscore = ZScoreDetector()
        self._iforest = IsolationForestDetector()

    def check(self, sample: MetricSample) -> List[Anomaly]:
        anomalies: List[Anomaly] = []
        anomalies.extend(self._threshold.check(sample))
        anomalies.extend(self._zscore.push_and_check(sample))
        return anomalies

    def fit_isolation_forest(self, samples: List[MetricSample]) -> None:
        self._iforest.fit(samples)
