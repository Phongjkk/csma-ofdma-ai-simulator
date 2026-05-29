"""Convert P(overload) > threshold into structured Alert objects."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import numpy as np

from ai.inference.stream_predictor import StreamPredictor


class AlertLevel(Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class PredictiveAlert:
    sim_time: float
    level: AlertLevel
    message: str
    overload_probability: float
    horizon_s: float
    metric: str


class AlertGenerator:
    """Convert StreamPredictor forecast into early-warning alerts."""

    def __init__(
        self,
        util_warning: float = 0.85,
        util_critical: float = 0.95,
        collision_warning: float = 0.25,
        collision_critical: float = 0.40,
        horizon_s: float = 5.0,
    ) -> None:
        self._util_warn = util_warning
        self._util_crit = util_critical
        self._col_warn = collision_warning
        self._col_crit = collision_critical
        self._horizon_s = horizon_s

    def generate(
        self,
        predictor: StreamPredictor,
        sim_time: float,
    ) -> List[PredictiveAlert]:
        alerts: List[PredictiveAlert] = []
        forecast = predictor.last_forecast
        if forecast is None:
            return alerts

        # Channel utilization alert
        p_overload = predictor.overload_probability(self._util_warn)
        if p_overload > 0.5:
            level = AlertLevel.CRITICAL if predictor.overload_probability(self._util_crit) > 0.3 else AlertLevel.WARNING
            alerts.append(PredictiveAlert(
                sim_time=sim_time,
                level=level,
                message=f"Predicted channel overload (P={p_overload:.1%}) in next {self._horizon_s}s",
                overload_probability=p_overload,
                horizon_s=self._horizon_s,
                metric="channel_util",
            ))

        # Collision rate alert
        col_pred = predictor.predicted_collision_rate()
        if col_pred is not None:
            mean_col = float(col_pred.mean())
            if mean_col > self._col_warn:
                level = AlertLevel.CRITICAL if mean_col > self._col_crit else AlertLevel.WARNING
                alerts.append(PredictiveAlert(
                    sim_time=sim_time,
                    level=level,
                    message=f"Predicted collision rate {mean_col:.1%} in next {self._horizon_s}s",
                    overload_probability=mean_col,
                    horizon_s=self._horizon_s,
                    metric="collision_rate",
                ))
        return alerts
