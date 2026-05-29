"""Main DES run-loop: dispatch events to MAC / traffic / monitoring handlers."""
import random
from typing import Dict, List, Optional

from simulator.config import SimConfig
from simulator.core.event import Event, EventType
from simulator.core.scheduler import EventScheduler
from simulator.network.packet import Packet
from simulator.network.channel import Channel
from simulator.network.station import Station
from simulator.network.access_point import AccessPoint
from simulator.metrics.collector import MetricsCollector, MetricSample, SimMetrics
from simulator.traffic.generator import generate_all_arrivals
from simulator.traffic.load_profiles import lambda_from_load
from simulator.mac.csma_ca import DCFState


class Simulator:
    """Discrete-Event Simulator for IEEE 802.11 CSMA/CA and OFDMA."""

    def __init__(self, cfg: SimConfig, mode: str = "combined") -> None:
        """
        mode: 'combined' = CSMA/CA + OFDMA (IEEE 802.11ax, mặc định)
              'su'       = chỉ CSMA/CA (dùng cho kiểm chứng Bianchi)
              'ofdma'    = chỉ OFDMA (dùng cho kiểm chứng lý thuyết)
        """
        self._cfg = cfg
        self._mode = mode
        self._rng = random.Random(cfg.seed)
        self._scheduler = EventScheduler()
        self._channel = Channel()
        self._collector = MetricsCollector(cfg.sim_time)
        self._ap = AccessPoint(cfg, self._channel, self._collector)
        self._stations: Dict[int, Station] = {}
        self._time_series: List[MetricSample] = []
        self._next_metrics_time: float = cfg.metrics_interval_s

        self._setup_stations()
        self._register_handlers()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_stations(self) -> None:
        for sid in range(self._cfg.n_stations):
            sta = Station(sid, self._cfg, self._channel, self._collector, self._rng)
            self._stations[sid] = sta
            self._ap.register_station(sid)

    def _register_handlers(self) -> None:
        sched = self._scheduler
        sched.register(EventType.PACKET_ARRIVAL, self._on_packet_arrival)
        sched.register(EventType.BACKOFF_END, self._on_backoff_end)
        sched.register(EventType.TX_END, self._on_tx_end)
        sched.register(EventType.ACK_RECEIVED, self._on_ack_received)
        sched.register(EventType.TRIGGER_FRAME, self._on_trigger_frame)
        sched.register(EventType.OFDMA_TX_END, self._on_ofdma_tx_end)
        sched.register(EventType.METRICS_TICK, self._on_metrics_tick)
        sched.register(EventType.SIM_END, self._on_sim_end)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> SimMetrics:
        lam = lambda_from_load(self._cfg.traffic_load)
        packets = generate_all_arrivals(
            n_stations=self._cfg.n_stations,
            lam=lam,
            sim_time=self._cfg.sim_time,
            payload_bytes=self._cfg.payload_bytes,
            mac_header_bytes=self._cfg.mac_header_bytes,
            pattern=self._cfg.traffic_pattern,
            rng=self._rng,
        )
        for pkt in packets:
            self._scheduler.schedule(pkt.arrival_time, EventType.PACKET_ARRIVAL,
                                     {"packet": pkt, "station_id": pkt.station_id})

        # Metrics ticks
        t = self._cfg.metrics_interval_s
        while t < self._cfg.sim_time:
            self._scheduler.schedule(t, EventType.METRICS_TICK, {"t": t})
            t += self._cfg.metrics_interval_s

        # OFDMA hoặc combined: schedule first trigger frame
        if self._mode in ("ofdma", "combined"):
            self._scheduler.schedule(0.0, EventType.TRIGGER_FRAME, {})

        self._scheduler.schedule(self._cfg.sim_time, EventType.SIM_END, {})
        self._scheduler.run()
        return self._collector.get_summary()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_packet_arrival(self, event: Event) -> None:
        pkt: Packet = event.data["packet"]
        sid: int = event.data["station_id"]
        sta = self._stations[sid]

        if self._mode == "ofdma":
            # Pure OFDMA: AP collects all packets, no contention
            self._ap.push_packet(sid, pkt)
        elif self._mode == "combined":
            # Combined: station uses CSMA/CA to contend, AP also schedules OFDMA cycles
            sta.receive_packet(pkt)
            if sta.state == DCFState.IDLE and sta.has_packets():
                difs_end = sta.start_difs_sensing(event.time)
                self._scheduler.schedule(difs_end, EventType.BACKOFF_END,
                                         {"station_id": sid, "phase": "difs"})
        else:
            # CSMA/CA only (su): station uses DCF
            sta.receive_packet(pkt)
            if sta.state == DCFState.IDLE and sta.has_packets():
                difs_end = sta.start_difs_sensing(event.time)
                self._scheduler.schedule(difs_end, EventType.BACKOFF_END,
                                         {"station_id": sid, "phase": "difs"})

    def _on_backoff_end(self, event: Event) -> None:
        sid: int = event.data["station_id"]
        phase: str = event.data.get("phase", "backoff")
        sta = self._stations[sid]
        now = event.time

        if not sta.has_packets():
            return

        if not self._channel.is_idle(now):
            # Channel busy: re-sense after channel clears
            resume = self._channel.busy_until() + self._cfg.difs_s
            self._scheduler.schedule(resume, EventType.BACKOFF_END,
                                     {"station_id": sid, "phase": "difs"})
            return

        if phase == "difs":
            bo_end = sta.start_backoff(now)
            self._scheduler.schedule(bo_end, EventType.BACKOFF_END,
                                     {"station_id": sid, "phase": "backoff"})
        else:
            # Backoff expired: start transmission
            tx_end = sta.start_transmission(now)
            self._scheduler.schedule(tx_end, EventType.TX_END, {"station_id": sid})

    def _on_tx_end(self, event: Event) -> None:
        sid: int = event.data["station_id"]
        sta = self._stations[sid]
        now = event.time

        # Check for collision
        colliders = self._channel.detect_collision(now - 1e-12)
        if sid in colliders and len(colliders) >= 2:
            for csid in colliders:
                if csid in self._stations:
                    survived = self._stations[csid].on_collision(now)
                    if survived and self._stations[csid].has_packets():
                        difs_end = self._stations[csid].start_difs_sensing(now)
                        self._scheduler.schedule(difs_end, EventType.BACKOFF_END,
                                                 {"station_id": csid, "phase": "difs"})
        else:
            # Successful transmission
            ack_time = sta.on_tx_complete(now)
            self._scheduler.schedule(ack_time, EventType.ACK_RECEIVED, {"station_id": sid})

    def _on_ack_received(self, event: Event) -> None:
        sid: int = event.data["station_id"]
        sta = self._stations[sid]
        now = event.time
        sta.on_ack_received(now)

        if sta.has_packets():
            difs_end = sta.start_difs_sensing(now)
            self._scheduler.schedule(difs_end, EventType.BACKOFF_END,
                                     {"station_id": sid, "phase": "difs"})

    def _on_trigger_frame(self, event: Event) -> None:
        now = event.time
        if now >= self._cfg.sim_time:
            return
        end_time, _ = self._ap.run_ofdma_cycle(now)
        if end_time < self._cfg.sim_time:
            self._scheduler.schedule(end_time, EventType.OFDMA_TX_END, {"cycle_end": end_time})

    def _on_ofdma_tx_end(self, event: Event) -> None:
        now = event.time
        if now >= self._cfg.sim_time:
            return
        # Schedule next trigger frame immediately after channel is free
        next_tf = max(now, self._channel.busy_until())
        if next_tf < self._cfg.sim_time:
            self._scheduler.schedule(next_tf, EventType.TRIGGER_FRAME, {})

    def _on_metrics_tick(self, event: Event) -> None:
        t = event.time
        window_start = max(0.0, t - self._cfg.metrics_interval_s)
        sample = self._collector.get_window_sample(window_start, t)
        self._time_series.append(sample)

    def _on_sim_end(self, event: Event) -> None:
        self._scheduler.stop()

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @property
    def time_series(self) -> List[MetricSample]:
        return self._time_series

    def get_results(self) -> dict:
        summary = self._collector.get_summary()
        return {
            "config": {
                "n_stations": self._cfg.n_stations,
                "sim_time": self._cfg.sim_time,
                "mode": self._mode,
                "traffic_load": self._cfg.traffic_load,
                "traffic_pattern": self._cfg.traffic_pattern,
                "seed": self._cfg.seed,
            },
            "summary": {
                "throughput_mbps": summary.throughput_mbps,
                "latency_mean_ms": summary.latency_mean_ms,
                "latency_p99_ms": summary.latency_p99_ms,
                "collision_rate": summary.collision_rate,
                "fairness_index": summary.fairness_index,
                "channel_util": summary.channel_util,
                "total_success": summary.total_success,
                "total_collisions": summary.total_collisions,
            },
            "time_series": [
                {
                    "time": s.time,
                    "throughput_mbps": s.throughput_mbps,
                    "latency_mean_ms": s.latency_mean_ms,
                    "latency_p99_ms": s.latency_p99_ms,
                    "collision_rate": s.collision_rate,
                    "fairness_index": s.fairness_index,
                    "channel_util": s.channel_util,
                }
                for s in self._time_series
            ],
        }
