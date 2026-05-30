"""MAE, RMSE, MAPE, accuracy, precision, recall, F1."""
import numpy as np
from typing import Dict, Optional


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, min_abs: float = 0.05) -> float:
    """MAPE chỉ tính trên các mẫu có |y_true| > min_abs để tránh chia cho ~0."""
    mask = np.abs(y_true) > min_abs
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return float(1 - ss_res / (ss_tot + 1e-10))


def evaluate_regression(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    feature_names: Optional[list] = None,
) -> Dict[str, float]:
    """Compute per-feature + aggregate regression metrics."""
    if y_true.ndim == 3:
        N, T, F = y_true.shape
        y_true_flat = y_true.reshape(-1, F)
        y_pred_flat = y_pred.reshape(-1, F)
    else:
        y_true_flat = y_true
        y_pred_flat = y_pred
        F = y_true.shape[-1]

    results: Dict[str, float] = {
        "mae": mae(y_true_flat, y_pred_flat),
        "rmse": rmse(y_true_flat, y_pred_flat),
        "mape": mape(y_true_flat, y_pred_flat),
        "r2": r2(y_true_flat, y_pred_flat),
    }
    if feature_names:
        for i, name in enumerate(feature_names):
            results[f"mae_{name}"] = mae(y_true_flat[:, i], y_pred_flat[:, i])
            results[f"rmse_{name}"] = rmse(y_true_flat[:, i], y_pred_flat[:, i])
    return results


def precision_recall_f1(
    y_true_binary: np.ndarray,
    y_pred_binary: np.ndarray,
) -> Dict[str, float]:
    tp = int(np.sum((y_true_binary == 1) & (y_pred_binary == 1)))
    fp = int(np.sum((y_true_binary == 0) & (y_pred_binary == 1)))
    fn = int(np.sum((y_true_binary == 1) & (y_pred_binary == 0)))
    tn = int(np.sum((y_true_binary == 0) & (y_pred_binary == 0)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "fpr": fpr,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}
