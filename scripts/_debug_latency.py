"""Chẩn đoán latency bất thường ở tải cao."""
import sys; sys.path.insert(0, '.')
import numpy as np
from simulator.config import SimConfig
from simulator.modes.mode_combined import run_combined
from simulator.core.simulator import Simulator

cfg = SimConfig(n_stations=20, traffic_load=2.0, sim_time=8.0, seed=42)
sim = Simulator(cfg, mode='combined')
sim.run()

collector = sim._collector
pkts = collector._completed

if not pkts:
    print("No packets!"); exit()

latencies = [p.latency for p in pkts if p.latency > 0]
arrival_times = [p.arrival_time for p in pkts if p.latency > 0]
wait_times = [p.tx_start_time - p.arrival_time for p in pkts if p.tx_start_time > 0]
tx_times = [p.tx_end_time - p.tx_start_time for p in pkts if p.tx_end_time > 0]
retries = [p.retries for p in pkts]

latencies_np = np.array(latencies)

print(f'Successful packets : {len(pkts)}')
print(f'Dropped (overflow) : {sum(s.dropped_overflow for s in sim._stations.values())}')
print(f'Collisions         : {collector._n_collisions}')
print()
print('=== LATENCY (ms) ===')
print(f'  min    = {latencies_np.min():.2f}')
print(f'  p25    = {np.percentile(latencies_np, 25):.2f}')
print(f'  median = {np.median(latencies_np):.2f}')
print(f'  p75    = {np.percentile(latencies_np, 75):.2f}')
print(f'  p90    = {np.percentile(latencies_np, 90):.2f}')
print(f'  p95    = {np.percentile(latencies_np, 95):.2f}')
print(f'  p99    = {np.percentile(latencies_np, 99):.2f}')
print(f'  max    = {latencies_np.max():.2f}')
print(f'  mean   = {latencies_np.mean():.2f}')
print()

wait_np = np.array(wait_times)
tx_np = np.array(tx_times)
print('=== QUEUE WAIT TIME (ms) ===')
print(f'  mean={wait_np.mean()*1000:.2f}  p99={np.percentile(wait_np*1000, 99):.2f}  max={wait_np.max()*1000:.2f}')
print()

print('=== TX DURATION (ms) ===')
print(f'  mean={tx_np.mean()*1000:.4f}  expected={cfg.data_tx_time()*1000:.4f}')
print()

print('=== RETRIES ===')
retry_np = np.array(retries)
print(f'  mean={retry_np.mean():.2f}  max={retry_np.max()}')
for r in range(8):
    count = (retry_np == r).sum()
    if count > 0:
        print(f'  retries={r}: {count} pkts ({100*count/len(pkts):.1f}%)')
print()

# Arrival time distribution of high-latency packets
high_lat_idx = latencies_np > 1000
if high_lat_idx.any():
    arr_high = np.array(arrival_times)[high_lat_idx]
    print(f'High-latency (>1000ms) packets: {high_lat_idx.sum()}')
    print(f'  Arrival time range: {arr_high.min():.3f}s – {arr_high.max():.3f}s')
    print(f'  → These arrived early but waited long in queue (queue buildup)')
else:
    print('No packets with latency > 1000ms')
