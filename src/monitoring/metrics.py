# src/monitoring/metrics.py

import time
import os
from typing import Dict, Any

class MetricsCollector:
    def __init__(self):
        self.total_orders = 0
        self.successful_orders = 0
        self.failed_orders = 0
        self.total_processing_time = 0.0
        self.start_time = time.time()
        
        self.alert_failure_rate_threshold = float(os.getenv("ALERT_FAILURE_RATE_THRESHOLD", "0.2"))
        self.alert_latency_threshold_ms = float(os.getenv("ALERT_LATENCY_THRESHOLD_MS", "5000"))

    def record_order(self, success: bool, processing_time: float):
        self.total_orders += 1
        if success:
            self.successful_orders += 1
        else:
            self.failed_orders += 1
        self.total_processing_time += processing_time

    def get_metrics(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        avg_latency = self.total_processing_time / self.total_orders if self.total_orders > 0 else 0
        failure_rate = self.failed_orders / self.total_orders if self.total_orders > 0 else 0
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_orders": self.total_orders,
            "successful_orders": self.successful_orders,
            "failed_orders": self.failed_orders,
            "average_processing_time_ms": round(avg_latency * 1000, 2),
            "failure_rate": round(failure_rate, 4)
        }

# Global instance
metrics = MetricsCollector()