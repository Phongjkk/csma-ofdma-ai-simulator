"""Naive moving-average baseline predictor."""
import numpy as np
from ai.models.base_model import BaseModel


class MovingAverageModel(BaseModel):
    """Predict next n_steps by repeating the mean of the last window_size steps."""

    def __init__(self, window_size: int = 10, n_steps: int = 50) -> None:
        super().__init__("MovingAverage")
        self._window_size = window_size
        self._n_steps = n_steps

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        # No training needed
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        """X: (batch, seq_len, n_features) → returns (batch, n_steps, n_features)."""
        if X.ndim == 2:
            X = X[np.newaxis]
        batch, seq_len, n_features = X.shape
        window = min(self._window_size, seq_len)
        means = X[:, -window:, :].mean(axis=1, keepdims=True)  # (batch, 1, n_features)
        predictions = np.repeat(means, self._n_steps, axis=1)   # (batch, n_steps, n_features)
        self._is_fitted = True
        return predictions
