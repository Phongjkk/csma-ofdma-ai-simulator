import sys; sys.path.insert(0,'.')
from simulator.config import SimConfig
from simulator.modes.mode_combined import run_combined
from simulator.core.simulator import Simulator
from simulator.modes.mode_su import run_su
from simulator.mac.csma_ca import compute_bianchi_throughput
from ai.data.preprocessor import samples_to_array, MinMaxScaler, build_windows
from ai.data.splitter import split_by_scenario
from ai.models.moving_average import MovingAverageModel
from ai.models.linear_regression import LinearRegressionModel
from ai.evaluation.metrics import evaluate_regression
from monitoring.monitor import RealtimeMonitor
from monitoring.alert_manager import Severity
import numpy as np, time, json

# ---- Performance Table ----
print('=== PERFORMANCE TABLE ===')
perf = []
for label, load in [('Thap', 0.2), ('Trung_binh', 0.5), ('Cao', 2.0)]:
    runs = [run_combined(SimConfig(n_stations=20, traffic_load=load, sim_time=8.0, seed=s))['summary'] for s in range(3)]
    def avg(k): return round(sum(r[k] for r in runs)/3, 3)
    row = dict(load=label, thr=avg('throughput_mbps'), lat=avg('latency_p99_ms'),
               col=avg('collision_rate'), fair=avg('fairness_index'), util=avg('channel_util'))
    perf.append(row)
    print(row)

# ---- Bianchi for n=75,100 (formula only) ----
print('\n=== BIANCHI n=75,100 (formula) ===')
for n in [75, 100]:
    b = compute_bianchi_throughput(SimConfig(n_stations=n), n)
    print(f'n={n}: bianchi={b:.3f}')

# ---- AI Baseline ----
print('\n=== AI BASELINE ===')
all_data = []
for n in [10, 20]:
    for load in [0.3, 1.5]:
        for seed in range(2):
            cfg = SimConfig(n_stations=n, traffic_load=load, sim_time=12.0, seed=seed)
            sim = Simulator(cfg, mode='combined'); sim.run()
            arr = samples_to_array(sim.time_series)
            if len(arr) >= 110: all_data.append(arr)

scaler = MinMaxScaler(); scaler.fit(np.concatenate(all_data))
SEQ = 50
windows = []
for arr in all_data:
    X, y = build_windows(scaler.transform(arr), SEQ, SEQ)
    if len(X) > 0: windows.append((X, y))

splits = split_by_scenario(windows)
Xtr, ytr = splits['X_train'], splits['y_train']
Xte, yte  = splits['X_test'],  splits['y_test']
print(f'train={Xtr.shape} test={Xte.shape}')

ai_results = {}
for cls, name in [(MovingAverageModel,'Moving Average'),(LinearRegressionModel,'Linear Regression')]:
    m = cls(window_size=10, n_steps=SEQ) if cls==MovingAverageModel else cls(n_steps=SEQ)
    m.fit(Xtr, ytr)
    t0 = time.time()
    preds = m.predict(Xte)
    inf_ms = round((time.time()-t0)/max(len(Xte),1)*1000,1)
    met = evaluate_regression(yte, preds)
    ai_results[name] = dict(mae=round(met['mae'],5), rmse=round(met['rmse'],5),
                            mape=round(met['mape'],2), r2=round(met['r2'],4), inf_ms=inf_ms)
    print(name, ai_results[name])

# Horizon
print('\n=== HORIZON ===')
m_ma = MovingAverageModel(window_size=10, n_steps=SEQ); m_ma.fit(Xtr, ytr)
pall = m_ma.predict(Xte)
horizon = {}
for label, steps in [('1s',10),('3s',30),('5s',50)]:
    met = evaluate_regression(yte[:,:steps,:], pall[:,:steps,:])
    horizon[label] = dict(mae=round(met['mae'],5), mape=round(met['mape'],2))
    print(label, horizon[label])

# ---- Alert System ----
print('\n=== ALERT SYSTEM ===')
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
alert = dict(precision=round(prec,3),recall=round(rec,3),f1=round(f1,3),fpr=round(fpr,3))
print(f'TP={TP} FP={FP} FN={FN} TN={TN}')
print(alert)

print('\nFINAL_JSON')
print(json.dumps(dict(perf=perf, ai=ai_results, horizon=horizon, alert=alert)))
