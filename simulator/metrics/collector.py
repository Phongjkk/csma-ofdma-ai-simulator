"""MetricsCollector + SimMetrics dataclass (throughput, p99 latency, Jain index)."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from simulator.network.packet import Packet


@dataclass
class MetricSample:
    time: float
    throughput_mbps: float = 0.0
    latency_mean_ms: float = 0.0
    latency_p99_ms: float = 0.0
    collision_rate: float = 0.0
    fairness_index: float = 1.0
    channel_util: float = 0.0
    n_success: int = 0
    n_collisions: int = 0


@dataclass
class SimMetrics:
    throughput_mbps: float = 0.0
    latency_mean_ms: float = 0.0
    latency_p99_ms: float = 0.0
    collision_rate: float = 0.0
    fairness_index: float = 1.0
    channel_util: float = 0.0      # data efficiency = success_bits / (sim_time * capacity)
    channel_occupancy: float = 0.0 # actual busy time = (success_tx + collision_tx) / sim_time
    total_success: int = 0
    total_collisions: int = 0
    total_transmissions: int = 0
    dropped_overflow: int = 0
    latency_p50_ms: float = 0.0


class MetricsCollector:
    def __init__(self, sim_time: float) -> None:
        self._sim_time = sim_time
        self._completed: List[Packet] = []
        self._collision_times: List[float] = []
        self._n_collisions: int = 0
        self._n_transmissions: int = 0
        self._busy_duration: float = 0.0
        self._per_station_bits: Dict[int, int] = {}

    def record_success(self, packet: Packet) -> None:
        self._completed.append(packet)
        self._n_transmissions += 1
        sta = packet.station_id
        self._per_station_bits[sta] = self._per_station_bits.get(sta, 0) + packet.size_bytes * 8

    def record_collision(self, station_ids: List[int]) -> None:
        self._n_collisions += 1
        self._n_transmissions += 1

    def record_channel_busy(self, duration: float) -> None:
        self._busy_duration += duration

    def get_window_sample(self, window_start: float, window_end: float) -> MetricSample:
        duration = window_end - window_start
        if duration <= 0:
            return MetricSample(time=window_end)

        packets = [p for p in self._completed if window_start <= p.ack_time < window_end]
        bits = sum(p.size_bytes * 8 for p in packets)
        throughput = bits / (duration * 1e6)

        latencies = [p.latency for p in packets if p.latency > 0]
        lat_mean = float(np.mean(latencies)) if latencies else 0.0
        lat_p99 = float(np.percentile(latencies, 99)) if latencies else 0.0

        n_success = len(packets)
        n_col = sum(1 for t in self._collision_times if window_start <= t < window_end)
        total_tx = n_success + n_col
        col_rate = n_col / total_tx if total_tx > 0 else 0.0

        channel_util = min(1.0, bits / (duration * self._get_capacity_bits(duration)))

        return MetricSample(
            time=window_end,
            throughput_mbps=throughput,
            latency_mean_ms=lat_mean,
            latency_p99_ms=lat_p99,
            collision_rate=col_rate,
            fairness_index=self._jain_index(),
            channel_util=channel_util,
            n_success=n_success,
            n_collisions=n_col,
        )

    def get_summary(self) -> SimMetrics:
        if not self._completed:
            return SimMetrics()

        total_bits = sum(p.size_bytes * 8 for p in self._completed)
        throughput = total_bits / (self._sim_time * 1e6)

        latencies = [p.latency for p in self._completed if p.latency > 0]
        lat_mean = float(np.mean(latencies)) if latencies else 0.0
        lat_p50 = float(np.percentile(latencies, 50)) if latencies else 0.0
        lat_p99 = float(np.percentile(latencies, 99)) if latencies else 0.0

        total_tx = self._n_transmissions
        col_rate = self._n_collisions / total_tx if total_tx > 0 else 0.0

        cap_bits = self._get_capacity_bits(self._sim_time)
        # channel_util = data efficiency (success bits / raw capacity)
        util = min(1.0, total_bits / cap_bits) if cap_bits > 0 else 0.0

        # channel_occupancy = fraction of time channel is physically busy
        # = (success_tx_time + collision_tx_time) / sim_time
        from simulator.config import SimConfig
        cfg = SimConfig()
        success_time = len(self._completed) * cfg.data_tx_time()
        collision_time = self._n_collisions * cfg.data_tx_time()
        occupancy = min(1.0, (success_time + collision_time) / self._sim_time)

        return SimMetrics(
            throughput_mbps=throughput,
            latency_mean_ms=lat_mean,
            latency_p50_ms=lat_p50,
            latency_p99_ms=lat_p99,
            collision_rate=col_rate,
            fairness_index=self._jain_index(),
            channel_util=util,
            channel_occupancy=occupancy,
            total_success=len(self._completed),
            total_collisions=self._n_collisions,
            total_transmissions=total_tx,
        )

    def _jain_index(self) -> float:
        bits = list(self._per_station_bits.values())
        if not bits:
            return 1.0
        arr = np.array(bits, dtype=float)
        return float((arr.sum() ** 2) / (len(arr) * (arr ** 2).sum())) if (arr ** 2).sum() > 0 else 1.0

    def _get_capacity_bits(self, duration: float) -> float:
        from simulator.config import SimConfig
        cfg = SimConfig()
        return duration * cfg.data_rate_mbps * 1e6
