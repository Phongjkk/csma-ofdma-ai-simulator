"""CSMA/CA + OFDMA kết hợp theo chuẩn IEEE 802.11ax (Wi-Fi 6/7).

OFDMA không thay thế mà bổ sung cho CSMA/CA:
- AP dùng CSMA/CA để cạnh tranh kênh, sau đó phát Trigger Frame
- Các STA truyền song song trên các Resource Unit khác nhau (không xung đột)
"""
from simulator.config import SimConfig
from simulator.core.simulator import Simulator


def run_combined(cfg: SimConfig) -> dict:
    """Chạy mô phỏng CSMA/CA + OFDMA kết hợp, trả về kết quả dict."""
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


# Alias ngắn gọn
run = run_combined
run_scenario = run_combined_scenario
