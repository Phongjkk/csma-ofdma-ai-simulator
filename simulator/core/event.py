"""Event dataclass + EventType enum (PACKET_ARRIVAL, TX_END, TRIGGER_FRAME, ...)."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict


class EventType(Enum):
    PACKET_ARRIVAL = auto()
    BACKOFF_END = auto()
    TX_START = auto()
    TX_END = auto()
    ACK_RECEIVED = auto()
    COLLISION = auto()
    TRIGGER_FRAME = auto()
    OFDMA_TX_END = auto()
    METRICS_TICK = auto()
    SIM_END = auto()


@dataclass(order=True)
class Event:
    time: float
    seq: int = field(compare=True)
    type: EventType = field(compare=False)
    data: Dict[str, Any] = field(default_factory=dict, compare=False)
