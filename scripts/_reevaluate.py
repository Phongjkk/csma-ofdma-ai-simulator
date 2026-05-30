import sys; sys.path.insert(0, '.')
import numpy as np, json, pickle

Xte = np.load('ai/saved_models/X_test.npy')
yte = np.load('ai/saved_models/y_test.npy')

from ai.models.lstm_model import LSTMPredictor
from ai.models.moving_average import MovingAverageModel
from ai.models.linear_regression import LinearRegressionModel
from ai.evaluation.metrics import evaluate_regression
from ai.data.preprocessor import FEATURE_COLS

Xtr = np.load('ai/saved_models/X_test.npy')  # dùng test làm proxy cho fit

results = {}

model = LSTMPredictor(n_features=6, hidden_size=64, num_layers=2, seq_out=50, device='cpu')
model.load_weights('ai/saved_models/lstm_checkpoint.pt')
p = model.predict(Xte)
m = evaluate_regression(yte, p, FEATURE_COLS)
results['LSTM'] = m
print(f"LSTM:              MAE={m['mae']:.5f} RMSE={m['rmse']:.5f} MAPE={m['mape']:.2f}% R2={m['r2']:.4f}")

ma = MovingAverageModel(window_size=10, n_steps=50)
ma.fit(Xtr, yte)
p = ma.predict(Xte)
m = evaluate_regression(yte, p, FEATURE_COLS)
results['MovingAverage'] = m
print(f"Moving Average:    MAE={m['mae']:.5f} RMSE={m['rmse']:.5f} MAPE={m['mape']:.2f}% R2={m['r2']:.4f}")

lr = LinearRegressionModel(n_steps=50)
lr.fit(Xtr, yte)
p = lr.predict(Xte)
m = evaluate_regression(yte, p, FEATURE_COLS)
results['LinearRegression'] = m
print(f"Linear Regression: MAE={m['mae']:.5f} RMSE={m['rmse']:.5f} MAPE={m['mape']:.2f}% R2={m['r2']:.4f}")

with open('ai/saved_models/eval_results.json', 'w') as f:
    json.dump({k: {mk: float(mv) for mk,mv in v.items()} for k,v in results.items()}, f, indent=2)
print("Saved eval_results.json")
