import time
from collections import defaultdict
from threading import Lock

class MetricsStore:
    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_latency = defaultdict(list)
        self.lock = Lock()

    def record(self, method: str, path: str, status: int, latency_ms: float):
        key = f"{method}:{path}:{status}"
        with self.lock:
            self.request_count[key] += 1
            self.request_latency[key].append(latency_ms)

    def get_metrics(self):
        with self.lock:
            result = {}
            for key in self.request_count:
                latencies = self.request_latency[key]
                result[key] = {
                    "count": self.request_count[key],
                    "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
                    "max_latency_ms": max(latencies),
                }
            return result

metrics_store = MetricsStore()