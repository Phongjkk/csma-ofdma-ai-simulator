"""Mode 2 — OFDMA only (AP-scheduled)."""
from simulator.config import SimConfig
from simulator.core.simulator import Simulator


def run_ofdma(cfg: SimConfig) -> dict:
    """Run a pure OFDMA simulation and return results dict."""
    sim = Simulator(cfg, mode="ofdma")
    sim.run()
    return sim.get_results()


def run_ofdma_scenario(
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
    return run_ofdma(cfg)
