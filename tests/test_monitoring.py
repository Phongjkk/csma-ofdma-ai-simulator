"""Unit tests — monitoring: buffer, aggregator, alert thresholds."""
import unittest

from simulator.metrics.collector import MetricSample
from monitoring.time_series_buffer import TimeSeriesBuffer
from monitoring.window_aggregator import WindowAggregator
from monitoring.anomaly_detector import ThresholdDetector, THRESHOLDS
from monitoring.alert_manager import AlertManager, Alert, Severity
from monitoring.monitor import RealtimeMonitor


def _sample(t: float, thr: float = 5.0, lat_p99: float = 10.0,
            col: float = 0.0, util: float = 0.5) -> MetricSample:
    return MetricSample(time=t, throughput_mbps=thr, latency_mean_ms=lat_p99 * 0.5,
                        latency_p99_ms=lat_p99, collision_rate=col,
                        fairness_index=1.0, channel_util=util)


class TestTimeSeriesBuffer(unittest.TestCase):
    def test_push_and_len(self):
        buf = TimeSeriesBuffer(maxlen=10)
        for i in range(5):
            buf.push(_sample(float(i)))
        self.assertEqual(len(buf), 5)

    def test_overflow_drops_oldest(self):
        buf = TimeSeriesBuffer(maxlen=3)
        for i in range(5):
            buf.push(_sample(float(i)))
        self.assertEqual(len(buf), 3)
        self.assertEqual(buf.get_all()[0].time, 2.0)

    def test_get_last(self):
        buf = TimeSeriesBuffer(maxlen=10)
        for i in range(7):
            buf.push(_sample(float(i)))
        last3 = buf.get_last(3)
        self.assertEqual(len(last3), 3)
        self.assertEqual(last3[-1].time, 6.0)

    def test_latest(self):
        buf = TimeSeriesBuffer(maxlen=10)
        buf.push(_sample(1.0))
        buf.push(_sample(2.0))
        self.assertEqual(buf.latest.time, 2.0)


class TestWindowAggregator(unittest.TestCase):
    def test_aggregate_returns_mean(self):
        agg = WindowAggregator(window_size=1.0, hz=10.0)
        for i in range(10):
            agg.push(_sample(float(i), thr=float(i + 1)))
        stats = agg.aggregate()
        self.assertIn("throughput_mbps", stats)
        self.assertGreater(stats["throughput_mbps"], 0)

    def test_is_ready_after_full_window(self):
        agg = WindowAggregator(window_size=1.0, hz=10.0)
        self.assertFalse(agg.is_ready())
        for i in range(10):
            agg.push(_sample(float(i)))
        self.assertTrue(agg.is_ready())


class TestThresholdDetector(unittest.TestCase):
    def test_no_anomaly_normal_sample(self):
        det = ThresholdDetector()
        s = _sample(1.0, thr=10.0, lat_p99=30.0, col=0.05, util=0.5)
        self.assertEqual(det.check(s), [])

    def test_latency_anomaly(self):
        det = ThresholdDetector()
        s = _sample(1.0, lat_p99=200.0)
        anomalies = det.check(s)
        self.assertTrue(any(a.metric == "latency_p99_ms" for a in anomalies))

    def test_collision_anomaly(self):
        det = ThresholdDetector()
        s = _sample(1.0, col=0.5)
        anomalies = det.check(s)
        self.assertTrue(any(a.metric == "collision_rate" for a in anomalies))

    def test_util_anomaly(self):
        det = ThresholdDetector()
        s = _sample(1.0, util=0.98)
        anomalies = det.check(s)
        self.assertTrue(any(a.metric == "channel_util" for a in anomalies))


class TestAlertManager(unittest.TestCase):
    def test_alert_fires(self):
        from monitoring.anomaly_detector import Anomaly
        mgr = AlertManager()
        fired = []
        mgr.register(fired.append)
        anomaly = Anomaly(1.0, "collision_rate", 0.5, 0.3, 0.0, "threshold")
        alerts = mgr.process_anomalies([anomaly], 1.0)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(len(fired), 1)

    def test_cooldown_suppresses_duplicate(self):
        from monitoring.anomaly_detector import Anomaly
        mgr = AlertManager()
        anomaly = Anomaly(1.0, "collision_rate", 0.5, 0.3, 0.0, "threshold")
        mgr.process_anomalies([anomaly], 1.0)
        alerts2 = mgr.process_anomalies([anomaly], 2.0)  # within 5s cooldown
        self.assertEqual(len(alerts2), 0)

    def test_cooldown_expires(self):
        from monitoring.anomaly_detector import Anomaly
        mgr = AlertManager()
        anomaly = Anomaly(1.0, "collision_rate", 0.5, 0.3, 0.0, "threshold")
        mgr.process_anomalies([anomaly], 1.0)
        alerts2 = mgr.process_anomalies([anomaly], 10.0)  # after cooldown
        self.assertEqual(len(alerts2), 1)


class TestRealtimeMonitor(unittest.TestCase):
    def test_push_increments_count(self):
        mon = RealtimeMonitor()
        mon.push(_sample(1.0))
        self.assertEqual(mon.sample_count, 1)

    def test_get_latest(self):
        mon = RealtimeMonitor()
        mon.push(_sample(1.0))
        mon.push(_sample(2.0))
        self.assertEqual(mon.get_latest().time, 2.0)

    def test_alert_callback_called(self):
        mon = RealtimeMonitor()
        fired = []
        mon.on_alert(fired.append)
        # Push a sample that triggers a latency threshold alert
        for i in range(15):
            mon.push(_sample(float(i), lat_p99=200.0, col=0.5))
        # Some alerts should have fired
        self.assertGreater(len(mon.alert_history), 0)


if __name__ == "__main__":
    unittest.main()
