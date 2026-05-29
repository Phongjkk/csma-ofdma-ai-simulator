"""Script: lấy số liệu thực tế cho chương 7."""
import sys, time, json
sys.path.insert(0, '.')
import numpy as np

# ===== 1. BIANCHI VALIDATION =====
print('=== BIANCHI VALIDATION ===')
from simulator.config import SimConfig
from simulator.modes.mode_su import run_su
from simulator.mac.csma_ca import compute_bianchi_throughput

# Service rate per station = 2857/n packets/s; dùng 3x để đảm bảo bão hòa
N_LIST = [5, 10, 20, 30, 50, 75, 100]
bianchi_rows = []
for n in N_LIST:
    cfg_ref = SimConfig(n_stations=n)
    bianchi = compute_bianchi_throughput(cfg_ref, n)
    # Lambda tối thiểu để bão hòa = 3 * (2857 / n) pkt/s per station
    sat_lam = max(100.0, 3.0 * 2857.0 / n)
    # Chuyển về traffic_load: lam = load * 100 -> load = lam / 100
    sat_load = sat_lam / 100.0
    sims = []
    for seed in range(3):
        cfg = SimConfig(n_stations=n, traffic_load=sat_load, sim_time=5.0, seed=seed)
        r = run_su(cfg)
        sims.append(r['summary']['throughput_mbps'])
    sim_avg = round(sum(sims) / len(sims), 3)
    err = abs(sim_avg - bianchi) / (bianchi + 1e-9) * 100 if bianchi > 0 else 0
    bianchi_rows.append({'n': n, 'bianchi': round(bianchi, 3),
                         'sim': sim_avg, 'err': round(err, 2)})
    print(f'  n={n:3d} | lam={sat_lam:.0f} | bianchi={bianchi:.3f} | sim={sim_avg:.3f} | err={err:.1f}%')

print()

# ===== 2. PERFORMANCE TABLE (combined) =====
print('=== PERFORMANCE TABLE (CSMA/CA + OFDMA) ===')
from simulator.modes.mode_combined import run_combined

LOAD_MAP = [('Thap', 0.2), ('Trung_binh', 0.5), ('Cao', 2.0)]
N_PERF = 20
perf_rows = []
for load_name, load_val in LOAD_MAP:
    runs = []
    for seed in range(3):
        cfg = SimConfig(n_stations=N_PERF, traffic_load=load_val, sim_time=10.0, seed=seed)
        runs.append(run_combined(cfg)['summary'])
    def avg(key): return round(sum(r[key] for r in runs) / 3, 4)
    row = {'load': load_name,
           'thr': avg('throughput_mbps'), 'lat': avg('latency_p99_ms'),
           'col': avg('collision_rate'), 'fair': avg('fairness_index'),
           'util': avg('channel_util')}
    perf_rows.append(row)
    print(f'  {load_name}: thr={row["thr"]} lat_p99={row["lat"]}ms '
          f'col={row["col"]} fair={row["fair"]} util={row["util"]}')

print()

# ===== 3. AI EVALUATION =====
print('=== AI MODEL EVALUATION ===')
from simulator.core.simulator import Simulator
from ai.data.preprocessor import samples_to_array, MinMaxScaler, build_windows
from ai.data.splitter import split_by_scenario
from ai.models.moving_average import MovingAverageModel
from ai.models.linear_regression import LinearRegressionModel
from ai.evaluation.metrics import evaluate_regression

all_data = []
for n in [10, 20, 30]:
    for load in [0.3, 1.0, 2.0]:
        for seed in range(2):
            cfg = SimConfig(n_stations=n, traffic_load=load, sim_time=20.0, seed=seed)
            sim = Simulator(cfg, mode='combined')
            sim.run()
            arr = samples_to_array(sim.time_series)
            if len(arr) >= 120:
                all_data.append(arr)

if not all_data:
    print('No data generated!')
    sys.exit(1)

all_concat = np.concatenate(all_data, axis=0)
scaler = MinMaxScaler(); scaler.fit(all_concat)

SEQ = 50
windows = []
for arr in all_data:
    X, y = build_windows(scaler.transform(arr), SEQ, SEQ)
    if len(X) > 0:
        windows.append((X, y))

splits = split_by_scenario(windows)
X_tr, y_tr = splits['X_train'], splits['y_train']
X_te, y_te  = splits['X_test'],  splits['y_test']
print(f'  Train={X_tr.shape}  Test={X_te.shape}')

ai_rows = {}
for cls, name in [(MovingAverageModel, 'Moving Average'),
                  (LinearRegressionModel, 'Linear Regression')]:
    m = cls(window_size=10, n_steps=SEQ) if cls == MovingAverageModel else cls(n_steps=SEQ)
    m.fit(X_tr, y_tr)
    t0 = time.time()
    preds = m.predict(X_te)
    inf_ms = round((time.time() - t0) / max(len(X_te), 1) * 1000, 1)
    met = evaluate_regression(y_te, preds)
    ai_rows[name] = {'mae': round(met['mae'], 5), 'rmse': round(met['rmse'], 5),
                     'mape': round(met['mape'], 2), 'r2': round(met['r2'], 4),
                     'inf_ms': inf_ms}
    print(f'  {name}: MAE={met["mae"]:.5f} RMSE={met["rmse"]:.5f} '
          f'MAPE={met["mape"]:.2f}% R2={met["r2"]:.4f} inf={inf_ms}ms')

# Horizon accuracy
print()
print('=== HORIZON ACCURACY ===')
m_ma = MovingAverageModel(window_size=10, n_steps=SEQ)
m_ma.fit(X_tr, y_tr)
preds_all = m_ma.predict(X_te)
horizon_rows = {}
for label, steps in [('1 giay', 10), ('3 giay', 30), ('5 giay', 50)]:
    if steps > SEQ: continue
    met = evaluate_regression(y_te[:, :steps, :], preds_all[:, :steps, :])
    horizon_rows[label] = {'mae': round(met['mae'], 5), 'mape': round(met['mape'], 2)}
    print(f'  {label}: MAE={met["mae"]:.5f} MAPE={met["mape"]:.2f}%')

# ===== 4. ALERT EVALUATION =====
print()
print('=== ALERT SYSTEM EVALUATION ===')
from monitoring.monitor import RealtimeMonitor
from monitoring.alert_manager import Severity

TP = FP = FN = TN = 0
tests = [(n, load) for n in [15, 30] for load in [0.3, 1.0, 3.0]]
for n, load in tests:
    cfg = SimConfig(n_stations=n, traffic_load=load, sim_time=10.0, seed=7)
    sim = Simulator(cfg, mode='combined'); sim.run()
    mon = RealtimeMonitor()
    mon.push_batch(sim.time_series)
    overloaded = load >= 2.5
    alerted = any(a.severity == Severity.CRITICAL for a in mon.alert_history)
    if overloaded and alerted:     TP += 1
    elif overloaded and not alerted: FN += 1
    elif not overloaded and alerted: FP += 1
    else:                            TN += 1

prec = TP/(TP+FP) if (TP+FP)>0 else 0.0
rec  = TP/(TP+FN) if (TP+FN)>0 else 0.0
f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
fpr  = FP/(FP+TN) if (FP+TN)>0 else 0.0
alert_row = {'precision': round(prec,3), 'recall': round(rec,3),
             'f1': round(f1,3), 'fpr': round(fpr,3)}
print(f'  TP={TP} FP={FP} FN={FN} TN={TN}')
print(f'  Precision={prec:.3f} Recall={rec:.3f} F1={f1:.3f} FPR={fpr:.3f}')

# ===== OUTPUT =====
print('\n\nFINAL_JSON_START')
print(json.dumps({
    'bianchi': bianchi_rows,
    'perf': perf_rows,
    'ai': ai_rows,
    'horizon': horizon_rows,
    'alert': alert_row,
}, indent=2))
print('FINAL_JSON_END')
