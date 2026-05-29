"""EarlyStopping and ModelCheckpoint callbacks."""
import os
from typing import Optional


class EarlyStopping:
    """Stop training when validation loss stops improving."""

    def __init__(self, patience: int = 10, delta: float = 1e-5,
                 restore_best: bool = True) -> None:
        self._patience = patience
        self._delta = delta
        self._restore_best = restore_best
        self._best_loss: float = float("inf")
        self._counter: int = 0
        self._best_state = None
        self.stopped: bool = False

    def step(self, val_loss: float, model=None) -> bool:
        """Returns True if training should stop."""
        if val_loss < self._best_loss - self._delta:
            self._best_loss = val_loss
            self._counter = 0
            if self._restore_best and model is not None:
                import copy
                self._best_state = copy.deepcopy(model.state_dict())
        else:
            self._counter += 1
            if self._counter >= self._patience:
                self.stopped = True
                if self._restore_best and model is not None and self._best_state is not None:
                    model.load_state_dict(self._best_state)
                return True
        return False

    def reset(self) -> None:
        self._best_loss = float("inf")
        self._counter = 0
        self._best_state = None
        self.stopped = False


class ModelCheckpoint:
    """Save the best model checkpoint to disk."""

    def __init__(self, save_path: str, monitor: str = "val_loss",
                 mode: str = "min") -> None:
        self._save_path = save_path
        self._monitor = monitor
        self._mode = mode
        self._best: float = float("inf") if mode == "min" else float("-inf")
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

    def step(self, metric_value: float, model) -> bool:
        """Save if improved. Returns True if checkpoint was saved."""
        import torch
        improved = (
            metric_value < self._best if self._mode == "min"
            else metric_value > self._best
        )
        if improved:
            self._best = metric_value
            torch.save({"state_dict": model.state_dict(), "best_metric": self._best},
                       self._save_path)
            return True
        return False
