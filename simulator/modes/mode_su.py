"""Mode 1 — CSMA/CA only (legacy single-user)."""
from simulator.config import SimConfig
from simulator.core.simulator import Simulator
from simulator.metrics.collector import SimMetrics


def run_su(cfg: SimConfig) -> dict:
    """Run a pure CSMA/CA simulation and return results dict."""
    sim = Simulator(cfg, mode="su")
    sim.run()
    return sim.get_results()


def run_su_scenario(
    n_stations: int,
    traffic_load: float = 0.5,
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
    return run_su(cfg)
