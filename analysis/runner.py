"""Run all 9 scenarios (3 modes × 3 load levels), N repeats each."""
import json
import os
from typing import Dict, List

from simulator.config import SimConfig
from simulator.modes.mode_su import run_su
from simulator.modes.mode_ofdma import run_ofdma
from simulator.modes.mode_combined import run_combined
from analysis.statistics import aggregate_runs

MODES = ["su", "ofdma", "combined"]
LOADS = [0.2, 0.5, 0.8]
STATION_COUNTS = [5, 10, 20, 30, 50, 75, 100]


def run_scenario(
    n_stations: int,
    traffic_load: float,
    mode: str,
    sim_time: float = 30.0,
    traffic_pattern: str = "poisson",
    seed: int = 42,
) -> dict:
    cfg = SimConfig(
        n_stations=n_stations,
        traffic_load=traffic_load,
        sim_time=sim_time,
        traffic_pattern=traffic_pattern,
        seed=seed,
    )
    if mode == "su":
        return run_su(cfg)
    elif mode == "ofdma":
        return run_ofdma(cfg)
    else:
        return run_combined(cfg)


def run_all_scenarios(
    n_repeats: int = 3,
    sim_time: float = 30.0,
    output_path: str = "results/raw/all_scenarios.json",
    n_stations_list: List[int] = None,
) -> List[dict]:
    """Run 3 modes × len(LOADS) loads × len(STATION_COUNTS) station counts × n_repeats."""
    stations = n_stations_list or STATION_COUNTS
    all_results: List[dict] = []
    total = len(MODES) * len(LOADS) * len(stations) * n_repeats
    done = 0

    for mode in MODES:
        for load in LOADS:
            for n in stations:
                run_results = []
                for rep in range(n_repeats):
                    seed = hash((mode, load, n, rep)) % (2 ** 31)
                    result = run_scenario(n, load, mode, sim_time, seed=seed)
                    run_results.append(result)
                    all_results.append(result)
                    done += 1
                    print(f"[{done}/{total}] mode={mode} load={load} n={n} rep={rep} "
                          f"thr={result['summary']['throughput_mbps']:.2f} Mbps")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved {len(all_results)} results to {output_path}")
    return all_results


def run_bianchi_validation(
    n_stations_list: List[int] = None,
    sim_time: float = 30.0,
    n_repeats: int = 3,
) -> Dict:
    """Compare simulator throughput vs Bianchi formula for CSMA/CA mode."""
    from simulator.mac.csma_ca import compute_bianchi_throughput
    stations = n_stations_list or STATION_COUNTS
    rows = []
    for n in stations:
        bianchi = compute_bianchi_throughput(SimConfig(n_stations=n), n)
        sim_runs = []
        for rep in range(n_repeats):
            r = run_scenario(n, traffic_load=1.0, mode="su", sim_time=sim_time, seed=rep)
            sim_runs.append(r["summary"]["throughput_mbps"])
        stats = aggregate_runs([{"thr": v} for v in sim_runs], "thr")
        error = abs(stats["mean"] - bianchi) / (bianchi + 1e-9) * 100
        rows.append({
            "n_stations": n,
            "bianchi_mbps": round(bianchi, 4),
            "sim_mbps": round(stats["mean"], 4),
            "error_pct": round(error, 2),
        })
        print(f"n={n:3d}: Bianchi={bianchi:.3f} Sim={stats['mean']:.3f} Error={error:.1f}%")
    return {"validation": rows, "pass": all(r["error_pct"] < 3.0 for r in rows)}
