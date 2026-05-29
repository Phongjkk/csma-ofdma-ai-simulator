"""Shared wireless channel — carrier sense + collision detection."""
from typing import Dict, List, Optional, Set, Tuple


class Channel:
    """Models the shared wireless medium.

    Tracks which stations are currently transmitting.  Collision occurs when
    2+ stations start a transmission in the same slot.
    """

    def __init__(self) -> None:
        self._busy_until: float = 0.0
        self._transmitting: Dict[int, Tuple[float, float]] = {}  # sta_id -> (start, end)
        self._total_busy: float = 0.0
        self._last_busy_start: float = 0.0

    # ------------------------------------------------------------------
    # Carrier sense
    # ------------------------------------------------------------------

    def is_idle(self, now: float) -> bool:
        return now >= self._busy_until

    def busy_until(self) -> float:
        return self._busy_until

    # ------------------------------------------------------------------
    # Transmission management
    # ------------------------------------------------------------------

    def start_transmission(self, station_id: int, now: float, duration: float) -> None:
        end = now + duration
        self._transmitting[station_id] = (now, end)
        if now >= self._busy_until:
            self._last_busy_start = now
        self._busy_until = max(self._busy_until, end)

    def end_transmission(self, station_id: int) -> None:
        self._transmitting.pop(station_id, None)

    def occupy(self, duration: float, now: float) -> None:
        """Reserve channel for a fixed duration (e.g. ACK, OFDMA block)."""
        if now >= self._busy_until:
            self._last_busy_start = now
        end = now + duration
        self._busy_until = max(self._busy_until, end)

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------

    def detect_collision(self, now: float) -> List[int]:
        """Return list of station IDs whose transmissions overlap at *now*."""
        active = [sid for sid, (start, end) in self._transmitting.items() if start <= now < end]
        if len(active) >= 2:
            return active
        return []

    def active_transmitters(self, now: float) -> List[int]:
        return [sid for sid, (start, end) in self._transmitting.items() if start <= now < end]

    def clear_transmissions(self) -> None:
        self._transmitting.clear()

    # ------------------------------------------------------------------
    # Multi-RU OFDMA (no collision by design)
    # ------------------------------------------------------------------

    def start_ofdma_transmissions(self, station_ids: List[int], now: float, duration: float) -> None:
        for sid in station_ids:
            self.start_transmission(sid, now, duration)

    def end_ofdma_transmissions(self, station_ids: List[int]) -> None:
        for sid in station_ids:
            self.end_transmission(sid)
