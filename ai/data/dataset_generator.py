"""Run N simulator scenarios and collect metric time-series for training."""
import os
import json
import random
from typing import Dict, List, Optional, Tuple

import numpy as np

from simulator.config import SimConfig
from simulator.core.simulator import Simulator
from simulator.metrics.collector import MetricSample
from ai.data.preprocessor import samples_to_array, build_windows, MinMaxScaler
from ai.data.splitter import split_by_scenario


SCENARIO_GRID = {
    "n_stations": [5, 10, 20, 30, 50, 75, 100],
    "traffic_load": [0.2, 0.5, 0.8, 1.0],
    "traffic_pattern": ["poisson", "cbr", "ramp", "spike", "oscillate"],
    "mode": ["su", "ofdma"],
}


def generate_scenario(
    n_stations: int,
    traffic_load: float,
    traffic_pattern: str,
    mode: str,
    sim_time: float = 30.0,
    seed: int = 42,
) -> List[MetricSample]:
    cfg = SimConfig(
        n_stations=n_stations,
        traffic_load=traffic_load,
        traffic_pattern=traffic_pattern,
        sim_time=sim_time,
        seed=seed,
    )
    sim = Simulator(cfg, mode=mode)
    sim.run()
    return sim.time_series


def generate_dataset(
    n_repeats: int = 3,
    sim_time: float = 30.0,
    seq_in: int = 50,
    seq_out: int = 50,
    output_dir: str = "results/datasets",
    max_scenarios: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
    """Generate full dataset: run all scenario combinations, return X, y, scaler."""
    os.makedirs(output_dir, exist_ok=True)
    scenario_windows: List[Tuple[np.ndarray, np.ndarray]] = []
    all_raw: List[np.ndarray] = []

    scenarios = [
        (n, load, pat, mode)
        for n in SCENARIO_GRID["n_stations"]
        for load in SCENARIO_GRID["traffic_load"]
        for pat in SCENARIO_GRID["traffic_pattern"]
        for mode in SCENARIO_GRID["mode"]
    ]
    if max_scenarios:
        scenarios = scenarios[:max_scenarios]

    for idx, (n, load, pat, mode) in enumerate(scenarios):
        for rep in range(n_repeats):
            seed = idx * 100 + rep
            try:
                samples = generate_scenario(n, load, pat, mode, sim_time, seed)
                if len(samples) < seq_in + seq_out:
                    continue
                arr = samples_to_array(samples)
                all_raw.append(arr)
            except Exception as e:
                print(f"Scenario {n}/{load}/{pat}/{mode} rep={rep} failed: {e}")

    if not all_raw:
        raise RuntimeError("No scenarios generated successfully.")

    # Fit scaler on all data concatenated
    all_concat = np.concatenate(all_raw, axis=0)
    scaler = MinMaxScaler()
    scaler.fit(all_concat)

    for arr in all_raw:
        scaled = scaler.transform(arr)
        X, y = build_windows(scaled, seq_in, seq_out)
        if len(X) > 0:
            scenario_windows.append((X, y))

    splits = split_by_scenario(scenario_windows)
    X_train, y_train = splits["X_train"], splits["y_train"]

    # Save
    np.save(os.path.join(output_dir, "X_train.npy"), splits["X_train"])
    np.save(os.path.join(output_dir, "y_train.npy"), splits["y_train"])
    np.save(os.path.join(output_dir, "X_val.npy"), splits["X_val"])
    np.save(os.path.join(output_dir, "y_val.npy"), splits["y_val"])
    np.save(os.path.join(output_dir, "X_test.npy"), splits["X_test"])
    np.save(os.path.join(output_dir, "y_test.npy"), splits["y_test"])

    import pickle
    with open(os.path.join(output_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)

    print(f"Dataset: train={len(splits['X_train'])}, val={len(splits['X_val'])}, test={len(splits['X_test'])}")
    return splits["X_train"], splits["y_train"], scaler
