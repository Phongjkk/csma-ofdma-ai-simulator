"""MAC frame dataclass with latency / tx_duration computed properties."""
from dataclasses import dataclass, field


_counter = 0


def _next_id() -> int:
    global _counter
    _counter += 1
    return _counter


def reset_counter() -> None:
    global _counter
    _counter = 0


@dataclass
class Packet:
    station_id: int
    size_bytes: int
    arrival_time: float
    id: int = field(default_factory=_next_id)
    tx_start_time: float = 0.0
    tx_end_time: float = 0.0
    ack_time: float = 0.0
    retries: int = 0
    dropped: bool = False

    def tx_duration(self, data_rate_mbps: float) -> float:
        return (self.size_bytes * 8) / (data_rate_mbps * 1e6)

    @property
    def latency(self) -> float:
        if self.ack_time > 0:
            return (self.ack_time - self.arrival_time) * 1000.0
        return 0.0

    @property
    def queuing_delay(self) -> float:
        if self.tx_start_time > 0:
            return (self.tx_start_time - self.arrival_time) * 1000.0
        return 0.0
