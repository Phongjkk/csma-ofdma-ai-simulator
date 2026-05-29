"""Load checkpoint; batch-predict overload probability."""
import numpy as np
from typing import Optional

from ai.models.lstm_model import LSTMPredictor
from ai.data.preprocessor import MinMaxScaler


class Predictor:
    """Load a trained LSTM and run batch predictions."""

    def __init__(self, model: LSTMPredictor, scaler: Optional[MinMaxScaler] = None) -> None:
        self._model = model
        self._scaler = scaler

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: str,
        scaler_path: Optional[str] = None,
        **lstm_kwargs,
    ) -> "Predictor":
        model = LSTMPredictor(**lstm_kwargs)
        model.load_weights(checkpoint_path)
        scaler = None
        if scaler_path:
            import pickle
            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)
        return cls(model, scaler)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """X: (batch, seq_in, n_feat) or (seq_in, n_feat) → (batch, seq_out, n_feat)."""
        if X.ndim == 2:
            X = X[np.newaxis]
        return self._model.predict(X)

    def predict_inverse(self, X: np.ndarray) -> np.ndarray:
        """Predict and inverse-transform if scaler is available."""
        raw = self.predict(X)
        if self._scaler is not None:
            N, T, F = raw.shape
            flat = raw.reshape(N * T, F)
            flat = self._scaler.inverse_transform(flat)
            return flat.reshape(N, T, F)
        return raw

    def channel_util_forecast(self, X: np.ndarray) -> np.ndarray:
        """Return predicted channel_util (index 5) across forecast horizon."""
        pred = self.predict(X)
        return pred[:, :, 5]  # channel_util is feature index 5

    @property
    def model(self) -> LSTMPredictor:
        return self._model
