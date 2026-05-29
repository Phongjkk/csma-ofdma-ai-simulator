"""CLI: python scripts/run_live_demo.py — launches simulator + realtime monitor."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Live simulation + monitoring demo")
    parser.add_argument("--n", type=int, default=20, help="Number of stations")
    parser.add_argument("--load", type=float, default=0.7, help="Traffic load [0,1]")
    parser.add_argument("--mode", type=str, default="combined",
                        choices=["su", "ofdma", "combined"])
    parser.add_argument("--sim-time", type=float, default=30.0)
    parser.add_argument("--pattern", type=str, default="poisson")
    args = parser.parse_args()

    from simulator.config import SimConfig
    from simulator.core.simulator import Simulator
    from monitoring.monitor import RealtimeMonitor
    from monitoring.alert_manager import Alert

    print(f"Starting live demo: mode={args.mode}, n={args.n}, load={args.load}")

    def on_alert(alert: Alert):
        print(f"  >>> ALERT: {alert.message}")

    monitor = RealtimeMonitor(buffer_maxlen=300, window_size=1.0, hz=10.0)
    monitor.on_alert(on_alert)

    cfg = SimConfig(
        n_stations=args.n,
        traffic_load=args.load,
        sim_time=args.sim_time,
        traffic_pattern=args.pattern,
        seed=42,
    )
    sim = Simulator(cfg, mode=args.mode)
    sim.run()

    print(f"\nFeeding {len(sim.time_series)} metric samples to monitor...")
    for sample in sim.time_series:
        monitor.push(sample)

    latest = monitor.get_latest()
    if latest:
        print(f"\nFinal metrics:")
        print(f"  Throughput  : {latest.throughput_mbps:.3f} Mbps")
        print(f"  Latency P99 : {latest.latency_p99_ms:.3f} ms")
        print(f"  Collision   : {latest.collision_rate:.3f}")
        print(f"  Channel Util: {latest.channel_util:.3f}")
        print(f"  Fairness    : {latest.fairness_index:.3f}")

    if monitor.alert_history:
        print(f"\n{len(monitor.alert_history)} alert(s) fired during simulation.")
    else:
        print("\nNo alerts fired.")


if __name__ == "__main__":
    main()
