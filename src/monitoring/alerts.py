# src/monitoring/alerts.py

from typing import List, Dict
from src.monitoring.metrics import metrics

class AlertEngine:
    @staticmethod
    def check_alerts() -> List[Dict[str, str]]:
        alerts = []
        current_metrics = metrics.get_metrics()
        
        if current_metrics["failure_rate"] > metrics.alert_failure_rate_threshold:
            alerts.append({
                "level": "CRITICAL",
                "metric": "failure_rate",
                "current_value": current_metrics["failure_rate"],
                "threshold": metrics.alert_failure_rate_threshold,
                "message": "Order failure rate exceeds acceptable threshold"
            })
            
        if current_metrics["average_processing_time_ms"] > metrics.alert_latency_threshold_ms:
            alerts.append({
                "level": "WARNING",
                "metric": "processing_latency",
                "current_value": current_metrics["average_processing_time_ms"],
                "threshold": metrics.alert_latency_threshold_ms,
                "message": "Average processing latency exceeds threshold"
            })
            
        return alerts