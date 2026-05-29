"""ARIMA time-series model (statsmodels)."""
import numpy as np
from typing import List, Optional, Tuple
from ai.models.base_model import BaseModel


class ARIMAModel(BaseModel):
    """Per-feature ARIMA predictor using statsmodels auto_arima (pmdarima)."""

    def __init__(self, order: Tuple[int, int, int] = (2, 1, 2), n_steps: int = 50) -> None:
        super().__init__("ARIMA")
        self._order = order
        self._n_steps = n_steps
        self._fitted_models: List = []
        self._n_feat: int = 0

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Fit one ARIMA model per output feature using the last training sequence."""
        try:
            from statsmodels.tsa.arima.model import ARIMA as _ARIMA
        except ImportError:
            self._is_fitted = True
            return

        N, seq_len, n_feat = X_train.shape
        self._n_feat = n_feat
        self._fitted_models = []

        # Use the last training sequence (the most recent window)
        last_seq = X_train[-1]  # (seq_len, n_feat)
        for j in range(n_feat):
            series = last_seq[:, j]
            try:
                m = _ARIMA(series, order=self._order)
                fitted = m.fit()
                self._fitted_models.append(fitted)
            except Exception:
                self._fitted_models.append(None)
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        """X: (batch, seq_len, n_feat) → (batch, n_steps, n_feat)."""
        try:
            from statsmodels.tsa.arima.model import ARIMA as _ARIMA
        except ImportError:
            return np.zeros((X.shape[0], self._n_steps, self._n_feat))

        if X.ndim == 2:
            X = X[np.newaxis]
        N, seq_len, n_feat = X.shape
        results = np.zeros((N, self._n_steps, n_feat))

        for i in range(N):
            for j in range(n_feat):
                series = X[i, :, j]
                try:
                    m = _ARIMA(series, order=self._order)
                    fit = m.fit()
                    forecast = fit.forecast(steps=self._n_steps)
                    results[i, :, j] = forecast
                except Exception:
                    results[i, :, j] = series[-1]
        return results
