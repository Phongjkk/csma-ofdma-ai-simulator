"""Script nhanh: chỉ lấy số liệu cốt lõi cho chương 7 (sim_time ngắn, n nhỏ)."""
import sys, time, json
sys.path.insert(0, '.')
import numpy as np

from simulator.config import SimConfig
from simulator.modes.mode_su import run_su
from simulator.modes.mode_combined import run_combined
from simulator.core.simulator import Simulator
from simulator.mac.csma_ca import compute_bianchi_throughput

# ===== 1. BIANCHI VALIDATION =====
print('=== 1. BIANCHI VALIDATION ===')
# Chỉ dùng n <= 30 để nhanh; n=50+ cần sim_time dài hơn
N_LIST = [5, 10, 20, 30]
bianchi_rows = []
for n in N_LIST:
    bianchi = compute_bianchi_throughput(SimConfig(n_stations=n), n)
    # lambda = 5 * service_rate_per_station đủ bão hòa
    sat_lam = max(200.0, 5.0 * 2857.0 / n)
    sat_load = sat_lam / 100.0
    sims = []
    for seed in range(2):
        cfg = SimConfig(n_stations=n, traffic_load=sat_load, sim_time=3.0, seed=seed)
        r = run_su(cfg)
        sims.append(r['summary']['throughput_mbps'])
    sim_avg = round(sum(sims)/len(sims), 3)
    err = abs(sim_avg - bianchi)/(bianchi+1e-9)*100 if bianchi > 0 else 0
    bianchi_rows.append({'n': n, 'bianchi': round(bianchi,3), 'sim': sim_avg, 'err': round(err,2)})
    print(f'  n={n:3d} | bianchi={bianchi:.3f} | sim={sim_avg:.3f} | err={err:.1f}%')

# For n=50,75,100 dùng formula-only (ghi chú là ước tính)
for n in [50, 75, 100]:
    bianchi = compute_bianchi_throughput(SimConfig(n_stations=n), n)
    bianchi_rows.append({'n': n, 'bianchi': round(bianchi,3), 'sim': '—', 'err': '—'})
    print(f'  n={n:3d} | bianchi={bianchi:.3f} | sim=skipped (too slow)')

print()

# ===== 2. PERFORMANCE TABLE =====
print('=== 2. PERFORMANCE TABLE (n=15, combined) ===')
N_PERF = 15
LOADS = [('Thấp', 0.2), ('Trung bình', 0.5), ('Cao', 2.0)]
perf_rows = []
for load_name, load_val in LOADS:
    runs = []
    for seed in range(2):
        cfg = SimConfig(n_stations=N_PERF, traffic_load=load_val, sim_time=10.0, seed=seed)
        r = run_combined(cfg)['summary']
        runs.append(r)
    def avg(k): return round(sum(r[k] for r in runs)/len(runs), 4)
    row = {'load': load_name, 'thr': avg('throughput_mbps'),
           'lat_p99': avg('latency_p99_ms'), 'col': avg('collision_rate'),
           'fair': avg('fairness_index'), 'util': avg('channel_util')}
    perf_rows.append(row)
    print(f'  {load_name}: thr={row["thr"]} lat_p99={row["lat_p99"]}ms '
          f'col={row["col"]} fair={row["fair"]} util={row["util"]}')

print()

# ===== 3. AI EVALUATION =====
print('=== 3. AI MODEL EVALUATION ===')
from ai.data.preprocessor import samples_to_array, MinMaxScaler, build_windows
from ai.data.splitter import split_by_scenario
from ai.models.moving_average import MovingAverageModel
from ai.models.linear_regression import LinearRegressionModel
from ai.evaluation.metrics import evaluate_regression

all_data = []
for n in [10, 20]:
    for load in [0.3, 1.5]:
        for seed in range(3):
            cfg = SimConfig(n_stations=n, traffic_load=load, sim_time=15.0, seed=seed)
            sim = Simulator(cfg, mode='combined'); sim.run()
            arr = samples_to_array(sim.time_series)
            if len(arr) >= 110:
                all_data.append(arr)

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
print(f'  Data: train={X_tr.shape}, test={X_te.shape}')

ai_rows = {}
for cls, name in [(MovingAverageModel,'Moving Average'),(LinearRegressionModel,'Linear Regression')]:
    m = cls(window_size=10, n_steps=SEQ) if cls==MovingAverageModel else cls(n_steps=SEQ)
    m.fit(X_tr, y_tr)
    t0 = time.time()
    preds = m.predict(X_te)
    inf_ms = round((time.time()-t0)/max(len(X_te),1)*1000, 1)
    met = evaluate_regression(y_te, preds)
    ai_rows[name] = {'mae':round(met['mae'],5),'rmse':round(met['rmse'],5),
                     'mape':round(met['mape'],2),'r2':round(met['r2'],4),'inf_ms':inf_ms}
    print(f'  {name}: MAE={met["mae"]:.5f} RMSE={met["rmse"]:.5f} '
          f'MAPE={met["mape"]:.2f}% R2={met["r2"]:.4f} inf={inf_ms}ms')

print()
print('=== HORIZON ACCURACY ===')
m_ma = MovingAverageModel(window_size=10, n_steps=SEQ); m_ma.fit(X_tr, y_tr)
preds_all = m_ma.predict(X_te)
horizon_rows = {}
for label, steps in [('1 giây',10),('3 giây',30),('5 giây',50)]:
    met = evaluate_regression(y_te[:,:steps,:], preds_all[:,:steps,:])
    horizon_rows[label] = {'mae':round(met['mae'],5),'mape':round(met['mape'],2)}
    print(f'  {label}: MAE={met["mae"]:.5f} MAPE={met["mape"]:.2f}%')

print()

# ===== 4. ALERT SYSTEM =====
print('=== 4. ALERT SYSTEM ===')
from monitoring.monitor import RealtimeMonitor
from monitoring.alert_manager import Severity

TP=FP=FN=TN=0
for n in [10,20]:
    for load in [0.3, 0.8, 2.5, 4.0]:
        cfg = SimConfig(n_stations=n, traffic_load=load, sim_time=10.0, seed=5)
        sim = Simulator(cfg, mode='combined'); sim.run()
        mon = RealtimeMonitor(); mon.push_batch(sim.time_series)
        overloaded = load >= 2.0
        alerted = any(a.severity==Severity.CRITICAL for a in mon.alert_history)
        if   overloaded and     alerted: TP+=1
        elif overloaded and not alerted: FN+=1
        elif not overloaded and alerted: FP+=1
        else:                            TN+=1

prec = TP/(TP+FP) if (TP+FP)>0 else 0.0
rec  = TP/(TP+FN) if (TP+FN)>0 else 0.0
f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
fpr  = FP/(FP+TN) if (FP+TN)>0 else 0.0
alert_row = {'precision':round(prec,3),'recall':round(rec,3),'f1':round(f1,3),'fpr':round(fpr,3)}
print(f'  TP={TP} FP={FP} FN={FN} TN={TN}')
print(f'  Precision={prec:.3f} Recall={rec:.3f} F1={f1:.3f} FPR={fpr:.3f}')

# ===== OUTPUT =====
print('\nFINAL_JSON_START')
print(json.dumps({'bianchi':bianchi_rows,'perf':perf_rows,'ai':ai_rows,
                  'horizon':horizon_rows,'alert':alert_row}, indent=2))
print('FINAL_JSON_END')
