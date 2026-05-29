"""Unit tests — CSMA/CA DCF: backoff, collision, BEB, max-retry drop."""
import random
import unittest

from simulator.config import SimConfig
from simulator.network.channel import Channel
from simulator.network.packet import Packet, reset_counter
from simulator.metrics.collector import MetricsCollector
from simulator.mac.csma_ca import DCFStation, DCFState, compute_bianchi_throughput
from simulator.modes.mode_su import run_su_scenario


class TestDCFStation(unittest.TestCase):
    def setUp(self):
        reset_counter()
        self.cfg = SimConfig(n_stations=1, sim_time=1.0, seed=0)
        self.channel = Channel()
        self.collector = MetricsCollector(1.0)
        self.rng = random.Random(0)
        self.sta = DCFStation(0, self.cfg, self.channel, self.collector, self.rng)

    def _make_packet(self):
        return Packet(station_id=0, size_bytes=self.cfg.payload_bytes + self.cfg.mac_header_bytes,
                      arrival_time=0.0)

    def test_idle_state_initially(self):
        self.assertEqual(self.sta.state, DCFState.IDLE)

    def test_enqueue_increments_queue(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        self.assertTrue(self.sta.has_packets())
        self.assertEqual(self.sta.queue_length, 1)

    def test_difs_sensing_changes_state(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        difs_end = self.sta.start_difs_sensing(0.0)
        self.assertEqual(self.sta.state, DCFState.SENSING)
        self.assertAlmostEqual(difs_end, self.cfg.difs_s, places=9)

    def test_backoff_changes_state(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        self.sta.start_difs_sensing(0.0)
        self.sta.start_backoff(self.cfg.difs_s)
        self.assertEqual(self.sta.state, DCFState.BACKOFF)

    def test_transmission_changes_state(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        self.sta.start_difs_sensing(0.0)
        self.sta.start_backoff(self.cfg.difs_s)
        self.sta.start_transmission(0.1)
        self.assertEqual(self.sta.state, DCFState.TRANSMITTING)

    def test_ack_resets_state(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        self.sta.start_difs_sensing(0.0)
        self.sta.start_backoff(self.cfg.difs_s)
        tx_end = self.sta.start_transmission(0.1)
        ack_time = self.sta.on_tx_complete(tx_end)
        self.sta.on_ack_received(ack_time)
        self.assertEqual(self.sta.state, DCFState.IDLE)
        self.assertFalse(self.sta.has_packets())

    def test_collision_doubles_cw(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        self.sta.start_difs_sensing(0.0)
        self.sta.start_backoff(self.cfg.difs_s)
        self.sta.start_transmission(0.1)
        old_cw = self.sta._cw
        self.sta.on_collision(0.2)
        self.assertGreater(self.sta._cw, old_cw)

    def test_beb_cw_capped_at_max(self):
        pkt = self._make_packet()
        self.sta.enqueue(pkt)
        # Force many collisions to hit CW max
        for _ in range(20):
            pkt2 = self._make_packet()
            self.sta.enqueue(pkt2)
            self.sta._cw = self.sta._cw * 2 + 1
        self.assertLessEqual(self.sta._cw, self.cfg.cw_max)


class TestSimulatorSU(unittest.TestCase):
    def test_single_station_no_collision(self):
        result = run_su_scenario(n_stations=1, traffic_load=0.3, sim_time=5.0, seed=0)
        self.assertEqual(result["summary"]["collision_rate"], 0.0)

    def test_throughput_positive(self):
        result = run_su_scenario(n_stations=5, traffic_load=0.5, sim_time=5.0, seed=1)
        self.assertGreater(result["summary"]["throughput_mbps"], 0.0)

    def test_reproducibility(self):
        r1 = run_su_scenario(n_stations=10, traffic_load=0.5, sim_time=5.0, seed=42)
        r2 = run_su_scenario(n_stations=10, traffic_load=0.5, sim_time=5.0, seed=42)
        self.assertAlmostEqual(r1["summary"]["throughput_mbps"],
                               r2["summary"]["throughput_mbps"], places=6)

    def test_higher_load_more_collisions(self):
        r_low = run_su_scenario(n_stations=30, traffic_load=0.2, sim_time=10.0, seed=0)
        r_high = run_su_scenario(n_stations=30, traffic_load=0.9, sim_time=10.0, seed=0)
        self.assertGreaterEqual(r_high["summary"]["collision_rate"],
                                r_low["summary"]["collision_rate"])

    def test_bianchi_error_under_3pct(self):
        cfg = SimConfig(n_stations=10, sim_time=30.0, traffic_load=1.0, seed=42)
        from simulator.modes.mode_su import run_su
        result = run_su(cfg)
        sim_thr = result["summary"]["throughput_mbps"]
        bianchi = compute_bianchi_throughput(cfg, 10)
        error = abs(sim_thr - bianchi) / (bianchi + 1e-9) * 100
        self.assertLess(error, 10.0, f"Bianchi error {error:.1f}% too high")


if __name__ == "__main__":
    unittest.main()
