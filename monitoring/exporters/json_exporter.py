"""Write MetricSample stream to newline-delimited JSON file."""
import json
import os
from typing import List

from simulator.metrics.collector import MetricSample


class JsonExporter:
    """Append MetricSamples to a newline-delimited JSON (NDJSON) file."""

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    def export(self, sample: MetricSample) -> None:
        with open(self._filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(self._to_dict(sample)) + "\n")

    def export_batch(self, samples: List[MetricSample]) -> None:
        with open(self._filepath, "a", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(self._to_dict(s)) + "\n")

    def export_all(self, samples: List[MetricSample], overwrite: bool = True) -> None:
        mode = "w" if overwrite else "a"
        with open(self._filepath, mode, encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(self._to_dict(s)) + "\n")

    @staticmethod
    def _to_dict(s: MetricSample) -> dict:
        return {
            "time": s.time,
            "throughput_mbps": s.throughput_mbps,
            "latency_mean_ms": s.latency_mean_ms,
            "latency_p99_ms": s.latency_p99_ms,
            "collision_rate": s.collision_rate,
            "fairness_index": s.fairness_index,
            "channel_util": s.channel_util,
            "n_success": s.n_success,
            "n_collisions": s.n_collisions,
        }
