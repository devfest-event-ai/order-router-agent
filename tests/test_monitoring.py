# tests/test_monitoring.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.api.webhook import app
from src.monitoring.metrics import metrics
from src.monitoring.alerts import AlertEngine

client = TestClient(app)

def run_monitoring_tests():
    print("=" * 70)
    print(" MONITORING AND ALERTING TEST SUITE")
    print("=" * 70)

    passed = 0
    total = 0

    # Reset metrics for clean test
    metrics.total_orders = 0
    metrics.successful_orders = 0
    metrics.failed_orders = 0
    metrics.total_processing_time = 0.0

    # TEST 1: Health Endpoint Returns Metrics
    total += 1
    print(f"\n Test {total}: Health Endpoint Returns System Metrics")
    
    response = client.get("/health")
    data = response.json()
    
    if response.status_code == 200 and "metrics" in data and "active_alerts" in data:
        print("   PASSED: Health endpoint returns metrics and alerts.")
        passed += 1
    else:
        print(f"   FAILED: Expected 200 with metrics structure. Got {response.status_code}")

    # TEST 2: Alert Threshold Triggers
    total += 1
    print(f"\n Test {total}: Alert Triggers on High Failure Rate")
    
    # Simulate 10 orders with 8 failures (80% failure rate)
    for i in range(10):
        metrics.record_order(success=(i >= 8), processing_time=0.1)
        
    alerts = AlertEngine.check_alerts()
    failure_alert = next((a for a in alerts if a["metric"] == "failure_rate"), None)
    
    if failure_alert and failure_alert["level"] == "CRITICAL":
        print("   PASSED: Failure rate alert triggered correctly.")
        passed += 1
    else:
        print("   FAILED: Expected critical alert for high failure rate.")

    # TEST 3: Latency Alert Triggers
    total += 1
    print(f"\n Test {total}: Alert Triggers on High Latency")
    
    # Reset and simulate slow processing
    metrics.total_orders = 5
    metrics.successful_orders = 5
    metrics.failed_orders = 0
    metrics.total_processing_time = 30.0  # 6 seconds average (6000ms)
    
    alerts = AlertEngine.check_alerts()
    latency_alert = next((a for a in alerts if a["metric"] == "processing_latency"), None)
    
    if latency_alert and latency_alert["level"] == "WARNING":
        print("   PASSED: Latency alert triggered correctly.")
        passed += 1
    else:
        print("   FAILED: Expected warning alert for high latency.")

    # SUMMARY
    print("\n" + "=" * 70)
    print(f" TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print(" All Monitoring tests passed!")
    else:
        print(" Some tests failed.")

if __name__ == "__main__":
    run_monitoring_tests()