"""STA: bounded queue, DCF contention-window (BEB) state machine."""
import random
from collections import deque
from typing import Deque, List, Optional

from simulator.config import SimConfig
from simulator.network.packet import Packet
from simulator.network.channel import Channel
from simulator.metrics.collector import MetricsCollector
from simulator.mac.csma_ca import DCFStation, DCFState


MAX_QUEUE_SIZE = 50


class Station:
    """IEEE 802.11 Station with a bounded packet queue and DCF logic."""

    def __init__(self, station_id: int, cfg: SimConfig, channel: Channel,
                 collector: MetricsCollector, rng: random.Random) -> None:
        self.station_id = station_id
        self._cfg = cfg
        self._channel = channel
        self._collector = collector
        self._rng = rng
        self._dcf = DCFStation(station_id, cfg, channel, collector, rng)
        self._queue: List[Packet] = []
        self._dropped_overflow: int = 0

    # ------------------------------------------------------------------
    # Packet arrival
    # ------------------------------------------------------------------

    def receive_packet(self, pkt: Packet) -> bool:
        """Try to enqueue a packet. Returns False if queue is full (dropped)."""
        if len(self._queue) >= MAX_QUEUE_SIZE:
            self._dropped_overflow += 1
            return False
        self._queue.append(pkt)
        self._dcf.enqueue(pkt)
        return True

    # ------------------------------------------------------------------
    # DCF helpers (delegate to DCFStation)
    # ------------------------------------------------------------------

    def has_packets(self) -> bool:
        return self._dcf.has_packets()

    @property
    def state(self) -> DCFState:
        return self._dcf.state

    @property
    def queue_length(self) -> int:
        return self._dcf.queue_length

    def start_difs_sensing(self, now: float) -> float:
        return self._dcf.start_difs_sensing(now)

    def start_backoff(self, now: float) -> float:
        return self._dcf.start_backoff(now)

    def start_transmission(self, now: float) -> float:
        return self._dcf.start_transmission(now)

    def on_tx_complete(self, now: float) -> float:
        return self._dcf.on_tx_complete(now)

    def on_ack_received(self, now: float) -> None:
        self._dcf.on_ack_received(now)

    def on_collision(self, now: float) -> bool:
        return self._dcf.on_collision(now)

    @property
    def current_packet(self) -> Optional[Packet]:
        return self._dcf.current_packet

    @property
    def dropped_overflow(self) -> int:
        return self._dropped_overflow

    # OFDMA uplink queue access
    @property
    def ofdma_queue(self) -> List[Packet]:
        return self._queue
