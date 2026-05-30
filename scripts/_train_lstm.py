"""Sinh dataset từ simulator và huấn luyện LSTM thực sự."""
import sys, os, pickle
sys.path.insert(0, '.')
import numpy as np

print("=== 1. Sinh dữ liệu từ simulator ===")
from simulator.config import SimConfig
from simulator.core.simulator import Simulator
from ai.data.preprocessor import samples_to_array, MinMaxScaler, build_windows
from ai.data.splitter import split_by_scenario

all_data = []
configs = [
    (5,  0.2), (5,  0.8), (5,  2.0),
    (10, 0.2), (10, 0.5), (10, 1.0), (10, 2.0),
    (20, 0.2), (20, 0.5), (20, 1.0), (20, 2.0),
    (30, 0.5), (30, 1.5),
]
for idx, (n, load) in enumerate(configs):
    for seed in range(3):
        cfg = SimConfig(n_stations=n, traffic_load=load, sim_time=15.0, seed=seed)
        sim = Simulator(cfg, mode='combined')
        sim.run()
        arr = samples_to_array(sim.time_series)
        if len(arr) >= 110:
            all_data.append(arr)
    print(f"  n={n:2d} load={load} done ({(idx+1)*3} runs)")

print(f"  Total scenarios: {len(all_data)}")

all_concat = np.concatenate(all_data, axis=0)
scaler = MinMaxScaler()
scaler.fit(all_concat)

SEQ_IN = 50
SEQ_OUT = 50
windows = []
for arr in all_data:
    X, y = build_windows(scaler.transform(arr), SEQ_IN, SEQ_OUT)
    if len(X) > 0:
        windows.append((X, y))

splits = split_by_scenario(windows)
Xtr, ytr = splits['X_train'], splits['y_train']
Xva, yva = splits['X_val'],   splits['y_val']
Xte, yte  = splits['X_test'],  splits['y_test']
print(f"  Train={Xtr.shape} Val={Xva.shape} Test={Xte.shape}")

os.makedirs('ai/saved_models', exist_ok=True)
with open('ai/saved_models/scalers.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Lưu test set để đánh giá sau
np.save('ai/saved_models/X_test.npy', Xte)
np.save('ai/saved_models/y_test.npy', yte)

print("\n=== 2. Huấn luyện LSTM ===")
from ai.training.hyperparams import HyperParams
from ai.training.trainer import Trainer
from ai.models.lstm_model import LSTMPredictor

hp = HyperParams(
    n_features=6,
    hidden_size=64,
    num_layers=2,
    dropout=0.2,
    seq_in=SEQ_IN,
    seq_out=SEQ_OUT,
    epochs=30,
    batch_size=32,
    lr=1e-3,
    early_stop_patience=7,
    save_path='ai/saved_models/lstm_checkpoint.pt',
    device='cpu',
)

trainer = Trainer(hp)
model = trainer.train(Xtr, ytr, Xva, yva)

print("\n=== 3. Đánh giá so sánh ===")
from ai.models.moving_average import MovingAverageModel
from ai.models.linear_regression import LinearRegressionModel
from ai.evaluation.metrics import evaluate_regression
from ai.data.preprocessor import FEATURE_COLS

results = {}

# LSTM
preds_lstm = model.predict(Xte)
met = evaluate_regression(yte, preds_lstm, FEATURE_COLS)
results['LSTM'] = met
print(f"  LSTM:               MAE={met['mae']:.5f}  RMSE={met['rmse']:.5f}  MAPE={met['mape']:.2f}%  R2={met['r2']:.4f}")

# Moving Average (baseline)
ma = MovingAverageModel(window_size=10, n_steps=SEQ_OUT)
ma.fit(Xtr, ytr)
preds_ma = ma.predict(Xte)
met_ma = evaluate_regression(yte, preds_ma, FEATURE_COLS)
results['MovingAverage'] = met_ma
print(f"  Moving Average:     MAE={met_ma['mae']:.5f}  RMSE={met_ma['rmse']:.5f}  MAPE={met_ma['mape']:.2f}%  R2={met_ma['r2']:.4f}")

# Linear Regression (baseline)
lr = LinearRegressionModel(n_steps=SEQ_OUT)
lr.fit(Xtr, ytr)
preds_lr = lr.predict(Xte)
met_lr = evaluate_regression(yte, preds_lr, FEATURE_COLS)
results['LinearRegression'] = met_lr
print(f"  Linear Regression:  MAE={met_lr['mae']:.5f}  RMSE={met_lr['rmse']:.5f}  MAPE={met_lr['mape']:.2f}%  R2={met_lr['r2']:.4f}")

# Save results
import json
with open('ai/saved_models/eval_results.json', 'w') as f:
    json.dump({k: {m: float(v) for m, v in vals.items()} for k, vals in results.items()}, f, indent=2)

print("\nDone. LSTM checkpoint saved to ai/saved_models/lstm_checkpoint.pt")
print("LSTM improves over baselines:", results['LSTM']['mae'] < results['MovingAverage']['mae'])
