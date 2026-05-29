"""Chronological train / val / test split with no data leakage."""
from typing import Dict, List, Tuple
import numpy as np


def chronological_split(
    X: np.ndarray,
    y: np.ndarray,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Dict[str, np.ndarray]:
    """Split windows in chronological order — no shuffle, no leakage."""
    N = len(X)
    n_train = int(N * train_ratio)
    n_val = int(N * val_ratio)

    return {
        "X_train": X[:n_train],
        "y_train": y[:n_train],
        "X_val": X[n_train: n_train + n_val],
        "y_val": y[n_train: n_train + n_val],
        "X_test": X[n_train + n_val:],
        "y_test": y[n_train + n_val:],
    }


def split_by_scenario(
    scenario_arrays: List[Tuple[np.ndarray, np.ndarray]],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Dict[str, np.ndarray]:
    """Split at the scenario level to avoid within-scenario leakage."""
    n = len(scenario_arrays)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    def concat(arrays):
        Xs = [a[0] for a in arrays]
        ys = [a[1] for a in arrays]
        return np.concatenate(Xs, axis=0), np.concatenate(ys, axis=0)

    X_train, y_train = concat(scenario_arrays[:n_train])
    X_val, y_val = concat(scenario_arrays[n_train: n_train + n_val])
    X_test, y_test = concat(scenario_arrays[n_train + n_val:])

    return {
        "X_train": X_train, "y_train": y_train,
        "X_val": X_val,   "y_val": y_val,
        "X_test": X_test,  "y_test": y_test,
    }
