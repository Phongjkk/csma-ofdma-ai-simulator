"""Training loop: Adam optimiser, MSELoss, LR scheduling, early stopping."""
from typing import Dict, List, Optional, Tuple
import numpy as np

from ai.training.hyperparams import HyperParams
from ai.training.callbacks import EarlyStopping, ModelCheckpoint
from ai.models.lstm_model import LSTMPredictor


class Trainer:
    def __init__(self, hp: HyperParams) -> None:
        self._hp = hp
        self._history: Dict[str, List[float]] = {"train_loss": [], "val_loss": []}

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        model: Optional[LSTMPredictor] = None,
    ) -> LSTMPredictor:
        import torch
        import torch.nn as nn
        from torch.utils.data import TensorDataset, DataLoader

        hp = self._hp
        if model is None:
            model = LSTMPredictor(
                n_features=hp.n_features,
                hidden_size=hp.hidden_size,
                num_layers=hp.num_layers,
                dropout=hp.dropout,
                seq_in=hp.seq_in,
                seq_out=hp.seq_out,
                lr=hp.lr,
                device=hp.device,
            )

        model._build()
        net = model._net
        device = model._get_device()

        optimizer = torch.optim.Adam(net.parameters(), lr=hp.lr, weight_decay=hp.weight_decay)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, patience=hp.lr_patience, factor=hp.lr_factor, min_lr=hp.lr_min
        )
        criterion = nn.MSELoss()
        early_stop = EarlyStopping(patience=hp.early_stop_patience, delta=hp.early_stop_delta)
        checkpoint = ModelCheckpoint(hp.save_path)

        X_t = torch.tensor(X_train, dtype=torch.float32)
        y_t = torch.tensor(y_train, dtype=torch.float32)
        X_v = torch.tensor(X_val, dtype=torch.float32).to(device)
        y_v = torch.tensor(y_val, dtype=torch.float32).to(device)
        loader = DataLoader(TensorDataset(X_t, y_t), batch_size=hp.batch_size, shuffle=True)

        for epoch in range(hp.epochs):
            net.train()
            train_losses = []
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                optimizer.zero_grad()
                pred = net(xb)
                loss = criterion(pred, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), hp.grad_clip)
                optimizer.step()
                train_losses.append(loss.item())

            net.eval()
            with torch.no_grad():
                val_pred = net(X_v)
                val_loss = criterion(val_pred, y_v).item()

            train_loss = float(np.mean(train_losses))
            self._history["train_loss"].append(train_loss)
            self._history["val_loss"].append(val_loss)

            scheduler.step(val_loss)
            checkpoint.step(val_loss, net)

            print(f"Epoch {epoch+1:3d}/{hp.epochs} | train={train_loss:.6f} | val={val_loss:.6f}")

            if early_stop.step(val_loss, net):
                print(f"Early stopping at epoch {epoch+1}")
                break

        model._is_fitted = True
        return model

    @property
    def history(self) -> Dict[str, List[float]]:
        return self._history
