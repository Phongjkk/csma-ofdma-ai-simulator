"""Min-heap priority-queue event scheduler."""
import heapq
from typing import Callable, Dict, Optional

from simulator.core.event import Event, EventType


class EventScheduler:
    def __init__(self) -> None:
        self._heap: list = []
        self._seq: int = 0
        self._now: float = 0.0
        self._running: bool = False
        self._handlers: Dict[EventType, Callable[[Event], None]] = {}
        self._cancelled: set = set()

    @property
    def now(self) -> float:
        return self._now

    def register(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        self._handlers[event_type] = handler

    def schedule(self, time: float, event_type: EventType, data: dict = None) -> Event:
        event = Event(time=time, seq=self._seq, type=event_type, data=data or {})
        self._seq += 1
        heapq.heappush(self._heap, event)
        return event

    def cancel(self, event: Event) -> None:
        self._cancelled.add(event.seq)

    def run(self) -> None:
        self._running = True
        while self._heap and self._running:
            event = heapq.heappop(self._heap)
            if event.seq in self._cancelled:
                self._cancelled.discard(event.seq)
                continue
            self._now = event.time
            handler = self._handlers.get(event.type)
            if handler:
                handler(event)
        self._running = False

    def stop(self) -> None:
        self._running = False

    def has_events(self) -> bool:
        return len(self._heap) > 0
