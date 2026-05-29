"""Mode 3 — Hybrid CSMA/CA + OFDMA (802.11ax style)."""
from simulator.config import SimConfig
from simulator.core.simulator import Simulator


def run_combined(cfg: SimConfig) -> dict:
    """Run hybrid CSMA/CA + OFDMA simulation and return results dict."""
    sim = Simulator(cfg, mode="combined")
    sim.run()
    return sim.get_results()


def run_combined_scenario(
    n_stations: int,
    traffic_load: float = 0.5,
    sim_time: float = 30.0,
    traffic_pattern: str = "poisson",
    seed: int = 42,
    n_ru: int = 4,
) -> dict:
    cfg = SimConfig(
        n_stations=n_stations,
        traffic_load=traffic_load,
        sim_time=sim_time,
        traffic_pattern=traffic_pattern,
        seed=seed,
        n_ru=n_ru,
    )
    return run_combined(cfg)
