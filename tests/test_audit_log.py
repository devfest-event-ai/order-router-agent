# tests/test_audit_log.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.audit_log import AuditLogger
import json

def run_audit_tests():
    print("=" * 70)
    print(" AUDIT LOGGING TEST SUITE")
    print("=" * 70)

    # Use a temporary database file for testing
    logger = AuditLogger(db_path="test_audit_log.db")
    passed = 0
    total = 0

    # ─────────────────────────────────────────────────────────────────────
    # TEST 1: Log a Valid Order
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n Test {total}: Log Valid Order (ShopeePay)")
    
    # Mock validation result (Passed, Low Risk)
    validation_mock = {
        "is_valid": True,
        "risk_level": "LOW",
        "risk_score": 0.1,
        "errors": []
    }
    
    # Mock routing result
    routing_mock = {
        "warehouse_id": "WH_JKT",
        "estimated_delivery_days": 2
    }
    
    # Log it
    log_message = logger.log_order(
        order_id="ORD_0000040",
        validation_result=validation_mock,
        routing_result=routing_mock
    )
    
    # Check if saved
    logs = logger.get_logs(limit=1)
    
    if len(logs) > 0 and logs[0]["order_id"] == "ORD_0000040":
        print("   ✅ PASSED: Audit log saved successfully.")
        print(f"   ℹ️ Log ID: {logs[0]['id']}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Log not found.")

    # ─────────────────────────────────────────────────────────────────────
    # TEST 2: Log an Invalid Order (High Risk)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Log Invalid Order (High Risk)")
    
    validation_mock = {
        "is_valid": False,
        "risk_level": "HIGH",
        "risk_score": 0.7,
        "errors": ["COD_LIMIT_EXCEEDED"]
    }
    
    routing_mock = {
        "warehouse_id": "N/A",
        "estimated_delivery_days": 0
    }
    
    logger.log_order(
        order_id="ORD_0000041",
        validation_result=validation_mock,
        routing_result=routing_mock
    )
    
    # Get ALL logs and find the specific one
    all_logs = logger.get_logs(limit=10)
    target_log = None
    for log in all_logs:
        if log["order_id"] == "ORD_0000041":
            target_log = log
            break
    
    if target_log:
        # Check if it captured the error (handle both 0 and False)
        validation_passed = target_log["validation_passed"]
        is_invalid = (validation_passed == 0 or validation_passed == False)
        
        if is_invalid and "COD_LIMIT_EXCEEDED" in target_log["decision_reason"]:
            print("   ✅ PASSED: Invalid order logged with correct reason.")
            print(f"   ℹ️ Reason: {target_log['decision_reason']}")
            passed += 1
        else:
            print(f"   ❌ FAILED: Log data incorrect.")
            print(f"   ℹ️ validation_passed: {validation_passed}, reason: {target_log['decision_reason']}")
    else:
        print(f"   ❌ FAILED: Log for ORD_0000041 not found.")
    
    # ─────────────────────────────────────────────────────────────────────
    # TEST 3: PII Masking
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: PII Masking Utility")
    
    raw_data = {"phone": "+628123456789", "email": "test@test.com", "name": "Budi"}
    masked_data = AuditLogger.mask_pii(raw_data)
    
    if masked_data["phone"] == "***MASKED***" and masked_data["email"] == "***MASKED***":
        print("   ✅ PASSED: PII data masked correctly.")
        passed += 1
    else:
        print(f"   ❌ FAILED: PII not masked.")

    # Cleanup test database
    if os.path.exists("test_audit_log.db"):
        os.remove("test_audit_log.db")

    # SUMMARY
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print(" All Audit Logging tests passed!")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    run_audit_tests()