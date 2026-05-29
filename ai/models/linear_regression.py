"""Scikit-learn LinearRegression / Ridge baseline."""
import numpy as np
from typing import Optional
from ai.models.base_model import BaseModel


class LinearRegressionModel(BaseModel):
    """Per-feature Ridge regression: each output feature trained independently."""

    def __init__(self, alpha: float = 1.0, n_steps: int = 50) -> None:
        super().__init__("LinearRegression")
        self._alpha = alpha
        self._n_steps = n_steps
        self._models = []

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """X_train: (N, seq_len, n_feat), y_train: (N, n_steps, n_feat)."""
        from sklearn.linear_model import Ridge
        N, seq_len, n_feat = X_train.shape
        X_flat = X_train.reshape(N, -1)
        _, out_steps, _ = y_train.shape
        y_flat = y_train.reshape(N, -1)

        self._models = []
        for j in range(y_flat.shape[1]):
            m = Ridge(alpha=self._alpha)
            m.fit(X_flat, y_flat[:, j])
            self._models.append(m)
        self._n_feat = n_feat
        self._out_steps = out_steps
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 2:
            X = X[np.newaxis]
        N, seq_len, n_feat = X.shape
        X_flat = X.reshape(N, -1)
        preds = np.column_stack([m.predict(X_flat) for m in self._models])
        return preds.reshape(N, self._out_steps, self._n_feat)
