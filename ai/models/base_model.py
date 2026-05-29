"""Abstract BaseModel: fit(), predict(), save(), load()."""
from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class BaseModel(ABC):
    """Common interface for all prediction models."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._is_fitted = False

    @abstractmethod
    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train the model."""

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predictions with same shape as y."""

    def save(self, path: str) -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> "BaseModel":
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
