"""OFDMA: Trigger Frame cycle, parallel RU transmissions, Block-ACK."""
from collections import deque
from typing import Dict, List, Optional, Tuple

from simulator.config import SimConfig, RU_SIZES
from simulator.network.packet import Packet
from simulator.network.channel import Channel
from simulator.metrics.collector import MetricsCollector


class RUAllocator:
    """Map active station count to Resource Unit configuration."""

    def allocate(self, n_active: int, n_ru: int) -> List[int]:
        """Return list of station indices assigned to RUs (round-robin over n_ru slots)."""
        if n_active == 0:
            return []
        assigned = []
        for i in range(min(n_active, n_ru)):
            assigned.append(i)
        return assigned

    def ru_tx_time(self, n_ru: int, cfg: SimConfig) -> float:
        """Each RU gets 1/n_ru of bandwidth → n_ru× the slot time for same payload."""
        if n_ru <= 0:
            return cfg.data_tx_time()
        return cfg.data_tx_time() * n_ru


class OFDMAScheduler:
    """Round-Robin OFDMA scheduler for the Access Point.

    The AP sends a Trigger Frame to solicit parallel uplink transmissions
    from up to n_ru stations simultaneously.  Parallel transmissions on
    different Resource Units do not collide.
    """

    def __init__(self, cfg: SimConfig, channel: Channel,
                 collector: MetricsCollector) -> None:
        self._cfg = cfg
        self._channel = channel
        self._collector = collector
        self._allocator = RUAllocator()
        self._rr_pointer: int = 0

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def select_stations(self, pending: List[int]) -> List[int]:
        """Round-robin: select up to n_ru stations from the pending list."""
        if not pending:
            return []
        n = len(pending)
        n_select = min(n, self._cfg.n_ru)
        start = self._rr_pointer % n
        selected = []
        for i in range(n_select):
            selected.append(pending[(start + i) % n])
        self._rr_pointer = (start + n_select) % n
        return selected

    def run_cycle(
        self,
        now: float,
        station_queues: Dict[int, List[Packet]],
    ) -> Tuple[float, List[Packet]]:
        """Execute one OFDMA cycle.

        Returns (end_time, list_of_successfully_transmitted_packets).
        """
        pending = [sid for sid, q in station_queues.items() if q]
        if not pending:
            return now, []

        selected = self.select_stations(pending)
        if not selected:
            return now, []

        # Trigger Frame overhead
        tf_end = now + self._cfg.tf_overhead_s
        self._channel.occupy(self._cfg.tf_overhead_s, now)

        # Parallel TX (same duration, different RUs → no collision)
        tx_dur = self._allocator.ru_tx_time(len(selected), self._cfg)
        tx_start = tf_end
        tx_end = tx_start + tx_dur

        transmitted: List[Packet] = []
        for sid in selected:
            if station_queues[sid]:
                pkt = station_queues[sid].pop(0)
                pkt.tx_start_time = tx_start
                pkt.tx_end_time = tx_end
                transmitted.append(pkt)

        # Block-ACK after SIFS
        block_ack_dur = self._cfg.sifs_s + self._cfg.ack_tx_time()
        total_end = tx_end + block_ack_dur
        self._channel.occupy(tx_dur + block_ack_dur, tx_start)

        for pkt in transmitted:
            pkt.ack_time = total_end
            self._collector.record_success(pkt)

        return total_end, transmitted

    def trigger_frame_duration(self) -> float:
        return self._cfg.tf_overhead_s

    def cycle_duration(self, n_selected: int) -> float:
        tx_dur = self._allocator.ru_tx_time(n_selected, self._cfg)
        return self._cfg.tf_overhead_s + tx_dur + self._cfg.sifs_s + self._cfg.ack_tx_time()
