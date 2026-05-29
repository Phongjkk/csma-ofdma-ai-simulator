"""AP: OFDMA Trigger Frame coordinator, round-robin RU scheduler."""
from typing import Dict, List, Optional, Tuple

from simulator.config import SimConfig
from simulator.network.packet import Packet
from simulator.network.channel import Channel
from simulator.metrics.collector import MetricsCollector
from simulator.mac.ofdma import OFDMAScheduler


class AccessPoint:
    """802.11ax Access Point managing OFDMA uplink scheduling."""

    def __init__(self, cfg: SimConfig, channel: Channel,
                 collector: MetricsCollector) -> None:
        self._cfg = cfg
        self._channel = channel
        self._collector = collector
        self._scheduler = OFDMAScheduler(cfg, channel, collector)
        self._station_queues: Dict[int, List[Packet]] = {}

    # ------------------------------------------------------------------
    # Station registration
    # ------------------------------------------------------------------

    def register_station(self, station_id: int) -> None:
        self._station_queues[station_id] = []

    def push_packet(self, station_id: int, pkt: Packet) -> None:
        """Called when a station has a packet ready for OFDMA uplink."""
        if station_id in self._station_queues:
            self._station_queues[station_id].append(pkt)

    # ------------------------------------------------------------------
    # OFDMA cycle
    # ------------------------------------------------------------------

    def run_ofdma_cycle(self, now: float) -> Tuple[float, List[Packet]]:
        """Trigger Frame → parallel TX → Block-ACK. Returns (end_time, pkts)."""
        return self._scheduler.run_cycle(now, self._station_queues)

    def has_pending(self) -> bool:
        return any(bool(q) for q in self._station_queues.values())

    def pending_count(self) -> int:
        return sum(len(q) for q in self._station_queues.values())

    def cycle_duration(self, n_selected: Optional[int] = None) -> float:
        if n_selected is None:
            n_selected = min(
                sum(1 for q in self._station_queues.values() if q),
                self._cfg.n_ru,
            )
        return self._scheduler.cycle_duration(n_selected)

    @property
    def station_queues(self) -> Dict[int, List[Packet]]:
        return self._station_queues
