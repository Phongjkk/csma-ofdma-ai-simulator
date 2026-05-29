"""Unit tests — OFDMA: TF cycle, RU allocation, simultaneous TX."""
import unittest

from simulator.config import SimConfig
from simulator.network.channel import Channel
from simulator.network.packet import Packet, reset_counter
from simulator.metrics.collector import MetricsCollector
from simulator.mac.ofdma import OFDMAScheduler, RUAllocator
from simulator.modes.mode_ofdma import run_ofdma_scenario


class TestRUAllocator(unittest.TestCase):
    def setUp(self):
        self.alloc = RUAllocator()
        self.cfg = SimConfig()

    def test_no_stations_returns_empty(self):
        result = self.alloc.allocate(0, 4)
        self.assertEqual(result, [])

    def test_fewer_stations_than_rus(self):
        result = self.alloc.allocate(2, 4)
        self.assertEqual(len(result), 2)

    def test_more_stations_than_rus(self):
        result = self.alloc.allocate(10, 4)
        self.assertEqual(len(result), 4)

    def test_ru_tx_time_scales_with_n(self):
        t1 = self.alloc.ru_tx_time(1, self.cfg)
        t4 = self.alloc.ru_tx_time(4, self.cfg)
        self.assertGreater(t4, t1)


class TestOFDMAScheduler(unittest.TestCase):
    def setUp(self):
        reset_counter()
        self.cfg = SimConfig(n_stations=4, n_ru=4, sim_time=10.0)
        self.channel = Channel()
        self.collector = MetricsCollector(10.0)
        self.scheduler = OFDMAScheduler(self.cfg, self.channel, self.collector)

    def _make_queues(self, n: int):
        queues = {}
        for i in range(n):
            pkt = Packet(station_id=i, size_bytes=self.cfg.payload_bytes, arrival_time=0.0)
            queues[i] = [pkt]
        return queues

    def test_cycle_returns_end_time_after_start(self):
        queues = self._make_queues(4)
        end_time, pkts = self.scheduler.run_cycle(0.0, queues)
        self.assertGreater(end_time, 0.0)

    def test_cycle_transmits_packets(self):
        queues = self._make_queues(4)
        _, pkts = self.scheduler.run_cycle(0.0, queues)
        self.assertGreater(len(pkts), 0)

    def test_no_collision_in_ofdma(self):
        queues = self._make_queues(4)
        _, pkts = self.scheduler.run_cycle(0.0, queues)
        # All transmitted packets should have distinct station IDs
        sids = [p.station_id for p in pkts]
        self.assertEqual(len(sids), len(set(sids)))

    def test_ack_time_set_on_packets(self):
        queues = self._make_queues(2)
        _, pkts = self.scheduler.run_cycle(0.0, queues)
        for pkt in pkts:
            self.assertGreater(pkt.ack_time, 0.0)


class TestCombinedMode(unittest.TestCase):
    def test_combined_has_positive_throughput(self):
        from simulator.modes.mode_combined import run_combined_scenario
        result = run_combined_scenario(n_stations=10, traffic_load=0.5, sim_time=5.0, seed=0)
        self.assertGreater(result["summary"]["throughput_mbps"], 0.0)

    def test_combined_ofdma_part_zero_collision(self):
        # OFDMA cycles (pure) dùng để kiểm chứng riêng vẫn không có collision
        result = run_ofdma_scenario(n_stations=10, traffic_load=0.5, sim_time=5.0, seed=0)
        self.assertEqual(result["summary"]["collision_rate"], 0.0)

    def test_combined_high_load_still_works(self):
        from simulator.modes.mode_combined import run_combined_scenario
        result = run_combined_scenario(n_stations=30, traffic_load=0.8, sim_time=5.0, seed=1)
        self.assertGreater(result["summary"]["throughput_mbps"], 0.0)
        self.assertGreaterEqual(result["summary"]["fairness_index"], 0.0)


if __name__ == "__main__":
    unittest.main()
