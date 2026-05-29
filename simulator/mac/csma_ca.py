"""CSMA/CA DCF: DIFS wait, BEB backoff, collision/retry, ACK."""
import random
from enum import Enum, auto
from typing import Optional, List

from simulator.config import SimConfig
from simulator.network.packet import Packet
from simulator.network.channel import Channel
from simulator.metrics.collector import MetricsCollector


class DCFState(Enum):
    IDLE = auto()
    SENSING = auto()
    BACKOFF = auto()
    TRANSMITTING = auto()
    WAIT_ACK = auto()


class DCFStation:
    """One station running IEEE 802.11 DCF (CSMA/CA)."""

    def __init__(self, station_id: int, cfg: SimConfig, channel: Channel,
                 collector: MetricsCollector, rng: random.Random) -> None:
        self.station_id = station_id
        self._cfg = cfg
        self._channel = channel
        self._collector = collector
        self._rng = rng

        self._queue: List[Packet] = []
        self._state = DCFState.IDLE
        self._backoff_counter: int = 0
        self._cw: int = cfg.cw_min
        self._current_pkt: Optional[Packet] = None
        self._retries: int = 0

        # Timestamps for scheduler callbacks
        self.backoff_end_time: float = 0.0
        self.tx_end_time: float = 0.0

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def enqueue(self, pkt: Packet) -> None:
        self._queue.append(pkt)

    def has_packets(self) -> bool:
        return bool(self._queue)

    @property
    def queue_length(self) -> int:
        return len(self._queue)

    # ------------------------------------------------------------------
    # State machine helpers
    # ------------------------------------------------------------------

    def start_difs_sensing(self, now: float) -> float:
        """Begin DIFS sensing; return time when DIFS expires."""
        self._state = DCFState.SENSING
        return now + self._cfg.difs_s

    def start_backoff(self, now: float) -> float:
        """Draw random backoff, return time when backoff expires."""
        self._backoff_counter = self._rng.randint(0, self._cw)
        self._state = DCFState.BACKOFF
        self.backoff_end_time = now + self._backoff_counter * self._cfg.slot_time_s
        return self.backoff_end_time

    def start_transmission(self, now: float) -> float:
        """Begin transmitting head-of-queue packet; return TX end time."""
        if not self._queue:
            return now
        self._current_pkt = self._queue.pop(0)
        self._current_pkt.tx_start_time = now
        tx_dur = self._cfg.data_tx_time()
        self._current_pkt.tx_end_time = now + tx_dur
        self._state = DCFState.TRANSMITTING
        self._channel.start_transmission(self.station_id, now, tx_dur)
        self.tx_end_time = now + tx_dur
        return self.tx_end_time

    def on_ack_received(self, now: float) -> None:
        """Handle successful ACK reception."""
        if self._current_pkt:
            self._current_pkt.ack_time = now
            self._collector.record_success(self._current_pkt)
            self._current_pkt = None
        self._cw = self._cfg.cw_min
        self._retries = 0
        self._state = DCFState.IDLE
        self._channel.end_transmission(self.station_id)

    def on_collision(self, now: float) -> bool:
        """Handle collision; return False if packet dropped (max retries)."""
        self._channel.end_transmission(self.station_id)
        self._collector.record_collision([self.station_id])
        self._retries += 1
        if self._retries >= self._cfg.max_retries:
            if self._current_pkt:
                self._current_pkt.dropped = True
                self._current_pkt = None
            self._retries = 0
            self._cw = self._cfg.cw_min
            self._state = DCFState.IDLE
            return False
        # Binary exponential backoff
        self._cw = min(self._cw * 2 + 1, self._cfg.cw_max)
        if self._current_pkt:
            self._queue.insert(0, self._current_pkt)
            self._current_pkt = None
        self._state = DCFState.IDLE
        return True

    def on_tx_complete(self, now: float) -> float:
        """TX done, wait SIFS+ACK; return ACK expected arrival time."""
        self._state = DCFState.WAIT_ACK
        self._channel.end_transmission(self.station_id)
        ack_dur = self._cfg.sifs_s + self._cfg.ack_tx_time()
        # Reserve channel for ACK window
        self._channel.occupy(ack_dur, now)
        return now + ack_dur

    @property
    def state(self) -> DCFState:
        return self._state

    @property
    def current_packet(self) -> Optional[Packet]:
        return self._current_pkt


def compute_bianchi_throughput(cfg: SimConfig, n: int) -> float:
    """Analytical Bianchi throughput for saturated CSMA/CA (Mbps).

    Solves the nonlinear system {τ, p} using scipy.optimize.fsolve for
    numerical stability across all n values.
    """
    import math
    try:
        from scipy.optimize import fsolve
    except ImportError:
        return 0.0

    W = cfg.cw_min       # W = CW_min
    m = math.ceil(math.log2((cfg.cw_max + 1) / (W + 1)))  # max backoff stage

    def equations(x):
        tau, p = x
        if p <= 0 or p >= 1 or tau <= 0 or tau >= 1:
            return [1e6, 1e6]
        # τ formula (Bianchi eq. 11)
        num = 2 * (1 - 2 * p)
        denom = (1 - 2 * p) * (W + 1) + p * W * (1 - (2 * p) ** m)
        tau_eq = num / denom if denom != 0 else 1e6
        # p formula
        p_eq = 1 - (1 - tau) ** (n - 1)
        return [tau - tau_eq, p - p_eq]

    # Try multiple starting points to find the physical solution
    best = None
    for tau0 in [0.1, 0.2, 0.05, 0.3, 0.5]:
        for p0 in [0.1, 0.3, 0.5, 0.7]:
            try:
                sol = fsolve(equations, [tau0, p0], full_output=True)
                tau_s, p_s = sol[0]
                if 0 < tau_s < 1 and 0 < p_s < 1:
                    residual = sum(x**2 for x in sol[1]["fvec"])
                    if best is None or residual < best[2]:
                        best = (tau_s, p_s, residual)
            except Exception:
                continue

    if best is None or best[0] <= 0 or best[1] <= 0:
        return 0.0

    tau, p = best[0], best[1]
    Ptr = 1 - (1 - tau) ** n
    Ps = n * tau * (1 - tau) ** (n - 1) / Ptr if Ptr > 0 else 0

    Ts = cfg.data_tx_time() + cfg.sifs_s + cfg.ack_tx_time() + cfg.difs_s
    Tc = cfg.data_tx_time() + cfg.difs_s
    payload_bits = cfg.payload_bytes * 8

    denom = ((1 - Ptr) * cfg.slot_time_s
             + Ptr * Ps * Ts
             + Ptr * (1 - Ps) * Tc)
    if denom <= 0:
        return 0.0
    return (Ps * Ptr * payload_bits) / denom / 1e6
