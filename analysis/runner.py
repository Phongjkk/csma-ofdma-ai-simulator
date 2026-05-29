"""Chạy các kịch bản mô phỏng CSMA/CA + OFDMA kết hợp (IEEE 802.11ax).

Đánh giá hiệu năng theo 3 mức tải × nhiều mức station count.
"""
import json
import os
from typing import Dict, List

from simulator.config import SimConfig
from simulator.modes.mode_combined import run_combined
from analysis.statistics import aggregate_runs

LOADS = [0.2, 0.5, 0.8]           # thấp, trung bình, cao
STATION_COUNTS = [5, 10, 20, 30, 50, 75, 100]


def run_scenario(
    n_stations: int,
    traffic_load: float,
    sim_time: float = 30.0,
    traffic_pattern: str = "poisson",
    seed: int = 42,
) -> dict:
    """Chạy một kịch bản CSMA/CA + OFDMA kết hợp."""
    cfg = SimConfig(
        n_stations=n_stations,
        traffic_load=traffic_load,
        sim_time=sim_time,
        traffic_pattern=traffic_pattern,
        seed=seed,
    )
    return run_combined(cfg)


def run_all_scenarios(
    n_repeats: int = 3,
    sim_time: float = 30.0,
    output_path: str = "results/raw/all_scenarios.json",
    n_stations_list: List[int] = None,
) -> List[dict]:
    """Chạy len(LOADS) mức tải × len(STATION_COUNTS) mức station × n_repeats lần."""
    stations = n_stations_list or STATION_COUNTS
    all_results: List[dict] = []
    total = len(LOADS) * len(stations) * n_repeats
    done = 0

    for load in LOADS:
        for n in stations:
            for rep in range(n_repeats):
                seed = hash((load, n, rep)) % (2 ** 31)
                result = run_scenario(n, load, sim_time, seed=seed)
                all_results.append(result)
                done += 1
                print(f"[{done}/{total}] load={load} n={n} rep={rep} "
                      f"thr={result['summary']['throughput_mbps']:.2f} Mbps  "
                      f"col={result['summary']['collision_rate']:.3f}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved {len(all_results)} results to {output_path}")
    return all_results


def run_bianchi_validation(
    n_stations_list: List[int] = None,
    sim_time: float = 10.0,
    n_repeats: int = 3,
) -> Dict:
    """Kiểm chứng simulator với mô hình Bianchi (dùng mode 'su' thuần CSMA/CA, tải bão hòa)."""
    from simulator.config import SimConfig
    from simulator.modes.mode_su import run_su
    from simulator.mac.csma_ca import compute_bianchi_throughput
    from simulator.traffic.load_profiles import lambda_from_load

    stations = n_stations_list or STATION_COUNTS
    rows = []
    for n in stations:
        cfg_ref = SimConfig(n_stations=n)
        bianchi = compute_bianchi_throughput(cfg_ref, n)
        sim_runs = []
        for rep in range(n_repeats):
            # Dùng lambda rất cao để đảm bảo bão hòa (> service_rate = ~2857 pkt/s)
            cfg = SimConfig(
                n_stations=n, traffic_load=50.0,  # -> lambda = 5000 pkt/s
                sim_time=sim_time, seed=rep,
            )
            r = run_su(cfg)
            sim_runs.append(r["summary"]["throughput_mbps"])
        stats = aggregate_runs([{"thr": v} for v in sim_runs], "thr")
        error = abs(stats["mean"] - bianchi) / (bianchi + 1e-9) * 100
        rows.append({
            "n_stations": n,
            "bianchi_mbps": round(bianchi, 4),
            "sim_mbps": round(stats["mean"], 4),
            "error_pct": round(error, 2),
        })
        print(f"n={n:3d}: Bianchi={bianchi:.3f}  Sim={stats['mean']:.3f}  Error={error:.1f}%")
    return {"validation": rows, "pass": all(r["error_pct"] < 15.0 for r in rows)}
