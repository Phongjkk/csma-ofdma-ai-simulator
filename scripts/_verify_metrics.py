import sys; sys.path.insert(0, '.')
from simulator.config import SimConfig
from simulator.modes.mode_combined import run_combined

print(f"{'Load':>6} | {'Thr(Mbps)':>9} | {'LatP50(ms)':>10} | {'LatP99(ms)':>10} | "
      f"{'Col%':>6} | {'Util%':>6} | {'Occup%':>7} | {'Drop':>5}")
print('-' * 85)
for label, load in [('Thap', 0.2), ('Trung', 0.5), ('Cao', 2.0)]:
    r = run_combined(SimConfig(n_stations=20, traffic_load=load, sim_time=8.0, seed=42))
    s = r['summary']
    print(f"{label:>6} | {s['throughput_mbps']:>9.3f} | {s['latency_p50_ms']:>10.2f} | "
          f"{s['latency_p99_ms']:>10.2f} | {s['collision_rate']*100:>5.1f}% | "
          f"{s['channel_util']*100:>5.1f}% | {s['channel_occupancy']*100:>6.1f}% | "
          f"{s['dropped_overflow']:>5}")
