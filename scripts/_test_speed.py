import sys, time; sys.path.insert(0,'.')
from simulator.config import SimConfig
from simulator.modes.mode_combined import run_combined

for n, load in [(10, 0.5), (20, 1.0), (20, 2.0)]:
    t0 = time.time()
    r = run_combined(SimConfig(n_stations=n, traffic_load=load, sim_time=8.0, seed=42))
    s = r['summary']
    elapsed = time.time() - t0
    print(f'n={n} load={load} | thr={s["throughput_mbps"]:.3f} lat={s["latency_p99_ms"]:.1f}ms '
          f'col={s["collision_rate"]:.4f} fair={s["fairness_index"]:.4f} '
          f'util={s["channel_util"]:.4f} | t={elapsed:.1f}s')
