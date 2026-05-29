"""IEEE 802.11ax parameters (SIFS, DIFS, CW, RU sizes, load profiles...)."""
from dataclasses import dataclass, field
from typing import List


# RU sizes in subcarriers per Resource Unit (IEEE 802.11ax Table 27-1)
RU_SIZES = {1: [242], 2: [106, 106], 4: [52, 52, 52, 52], 9: [26] * 9}

# Trigger Frame overhead (µs): preamble + TF PPDU
TRIGGER_FRAME_OVERHEAD_US = 100.0


@dataclass
class SimConfig:
    n_stations: int = 10
    sim_time: float = 30.0
    payload_bytes: int = 1500
    data_rate_mbps: float = 54.0
    channel_bw_mhz: float = 20.0
    # IEEE 802.11ax timing (µs)
    slot_time_us: float = 9.0
    sifs_us: float = 16.0
    difs_us: float = 34.0
    # Contention window
    cw_min: int = 15
    cw_max: int = 1023
    max_retries: int = 7
    # Frame sizes (bytes)
    ack_bytes: int = 14
    mac_header_bytes: int = 34
    # OFDMA
    n_ru: int = 4
    tf_overhead_us: float = TRIGGER_FRAME_OVERHEAD_US
    # Traffic
    traffic_load: float = 0.5
    traffic_pattern: str = "poisson"
    # Reproducibility
    seed: int = 42
    # Metrics window
    metrics_interval_s: float = 0.1

    @property
    def slot_time_s(self) -> float:
        return self.slot_time_us * 1e-6

    @property
    def sifs_s(self) -> float:
        return self.sifs_us * 1e-6

    @property
    def difs_s(self) -> float:
        return self.difs_us * 1e-6

    @property
    def tf_overhead_s(self) -> float:
        return self.tf_overhead_us * 1e-6

    def frame_tx_time(self, size_bytes: int) -> float:
        return (size_bytes * 8) / (self.data_rate_mbps * 1e6)

    def ack_tx_time(self) -> float:
        return self.frame_tx_time(self.ack_bytes)

    def data_tx_time(self) -> float:
        return self.frame_tx_time(self.payload_bytes + self.mac_header_bytes)
