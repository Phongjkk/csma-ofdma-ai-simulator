"""Isolation Forest anomaly detection (scikit-learn)."""
import numpy as np
from typing import List, Optional
from ai.models.base_model import BaseModel


class IsolationForestModel(BaseModel):
    """Wrapper around sklearn IsolationForest for tabular anomaly detection."""

    def __init__(self, contamination: float = 0.05, n_estimators: int = 100,
                 random_state: int = 42) -> None:
        super().__init__("IsolationForest")
        self._contamination = contamination
        self._n_estimators = n_estimators
        self._random_state = random_state
        self._model = None

    def fit(self, X_train: np.ndarray, y_train: Optional[np.ndarray] = None) -> None:
        from sklearn.ensemble import IsolationForest
        if X_train.ndim == 3:
            N, T, F = X_train.shape
            X_train = X_train.reshape(N, T * F)
        self._model = IsolationForest(
            contamination=self._contamination,
            n_estimators=self._n_estimators,
            random_state=self._random_state,
        )
        self._model.fit(X_train)
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Returns -1 for anomaly, +1 for normal."""
        if not self._is_fitted or self._model is None:
            return np.ones(len(X), dtype=int)
        if X.ndim == 3:
            N, T, F = X.shape
            X = X.reshape(N, T * F)
        return self._model.predict(X)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Anomaly score (lower = more anomalous)."""
        if not self._is_fitted or self._model is None:
            return np.zeros(len(X))
        if X.ndim == 3:
            N, T, F = X.shape
            X = X.reshape(N, T * F)
        return self._model.decision_function(X)

    def is_anomaly(self, x: np.ndarray) -> bool:
        pred = self.predict(x.reshape(1, -1))
        return bool(pred[0] == -1)
