"""Derived features: rolling mean/std, delta, utilisation ratio."""
import numpy as np
from typing import List


def add_rolling_features(data: np.ndarray, windows: List[int] = [10, 30]) -> np.ndarray:
    """Append rolling mean and std for each window size.

    data: (T, F) → returns (T, F + 2*len(windows)*F)
    """
    T, F = data.shape
    extras = [data]
    for w in windows:
        roll_mean = np.zeros_like(data)
        roll_std = np.zeros_like(data)
        for t in range(T):
            start = max(0, t - w + 1)
            window = data[start: t + 1]
            roll_mean[t] = window.mean(axis=0)
            roll_std[t] = window.std(axis=0)
        extras.extend([roll_mean, roll_std])
    return np.concatenate(extras, axis=1)


def add_delta_features(data: np.ndarray) -> np.ndarray:
    """Append first-order difference (trend) features."""
    delta = np.zeros_like(data)
    delta[1:] = data[1:] - data[:-1]
    return np.concatenate([data, delta], axis=1)


def add_lag_features(data: np.ndarray, lags: List[int] = [1, 5, 10]) -> np.ndarray:
    """Append lagged copies of the data."""
    T, F = data.shape
    extras = [data]
    for lag in lags:
        lagged = np.zeros_like(data)
        lagged[lag:] = data[:-lag]
        extras.append(lagged)
    return np.concatenate(extras, axis=1)


def engineer_features(
    data: np.ndarray,
    add_rolling: bool = True,
    add_delta: bool = True,
    add_lags: bool = False,
) -> np.ndarray:
    """Full feature engineering pipeline."""
    result = data.copy()
    if add_rolling:
        result = add_rolling_features(result, windows=[10, 30])
    if add_delta:
        result = add_delta_features(result)
    if add_lags:
        result = add_lag_features(result, lags=[1, 5, 10])
    return result
