"""LSTM overload predictor (PyTorch) — 2-layer, dropout, sigmoid output."""
import numpy as np
from typing import Optional, Tuple
from ai.models.base_model import BaseModel


class LSTMPredictor(BaseModel):
    """Seq2Seq LSTM: (batch, seq_in, n_feat) → (batch, seq_out, n_feat)."""

    def __init__(
        self,
        n_features: int = 6,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        seq_in: int = 50,
        seq_out: int = 50,
        lr: float = 1e-3,
        device: Optional[str] = None,
    ) -> None:
        super().__init__("LSTM")
        self.n_features = n_features
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.seq_in = seq_in
        self.seq_out = seq_out
        self.lr = lr
        self._device = device
        self._net = None
        self._optimizer = None

    def _build(self) -> None:
        import torch
        import torch.nn as nn
        device = self._get_device()

        class _Net(nn.Module):
            def __init__(self, n_feat, hidden, layers, drop, seq_out):
                super().__init__()
                self.lstm = nn.LSTM(n_feat, hidden, layers, batch_first=True,
                                    dropout=drop if layers > 1 else 0.0)
                self.fc = nn.Linear(hidden, n_feat)
                self.seq_out = seq_out

            def forward(self, x):
                out, _ = self.lstm(x)
                out = out[:, -self.seq_out:, :]
                return self.fc(out)

        self._net = _Net(self.n_features, self.hidden_size, self.num_layers,
                         self.dropout, self.seq_out).to(device)
        self._optimizer = torch.optim.Adam(self._net.parameters(), lr=self.lr)

    def _get_device(self):
        import torch
        if self._device:
            return torch.device(self._device)
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            epochs: int = 50, batch_size: int = 64) -> None:
        import torch
        import torch.nn as nn
        from torch.utils.data import TensorDataset, DataLoader

        if self._net is None:
            self._build()

        device = self._get_device()
        X_t = torch.tensor(X_train, dtype=torch.float32)
        y_t = torch.tensor(y_train, dtype=torch.float32)
        loader = DataLoader(TensorDataset(X_t, y_t), batch_size=batch_size, shuffle=True)
        criterion = nn.MSELoss()

        self._net.train()
        for epoch in range(epochs):
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                self._optimizer.zero_grad()
                pred = self._net(xb)
                loss = criterion(pred, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self._net.parameters(), 1.0)
                self._optimizer.step()
        self._is_fitted = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        import torch
        if self._net is None:
            self._build()
        device = self._get_device()
        if X.ndim == 2:
            X = X[np.newaxis]
        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        self._net.eval()
        with torch.no_grad():
            out = self._net(X_t)
        return out.cpu().numpy()

    def save(self, path: str) -> None:
        import torch
        if self._net is not None:
            torch.save({"state_dict": self._net.state_dict(),
                        "config": self._get_config()}, path)

    def load_weights(self, path: str) -> None:
        import torch
        ckpt = torch.load(path, map_location=self._get_device())
        if self._net is None:
            self._build()
        self._net.load_state_dict(ckpt["state_dict"])
        self._is_fitted = True

    def _get_config(self) -> dict:
        return {
            "n_features": self.n_features, "hidden_size": self.hidden_size,
            "num_layers": self.num_layers, "dropout": self.dropout,
            "seq_in": self.seq_in, "seq_out": self.seq_out,
        }
