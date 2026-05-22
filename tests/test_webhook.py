# tests/test_webhook.py

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.api.webhook import app

client = TestClient(app)

def run_webhook_tests():
    print("=" * 70)
    print(" WEBHOOK API TEST SUITE")
    print("=" * 70)

    passed = 0
    total = 0

    # TEST 1: Valid Order Submission
    total += 1
    print(f"\n📋 Test {total}: Valid Order Submission")
    
    valid_payload = {
        #"order_id": "ORD_0000001",
        "order_id": "ORD_0000001",
        "customer": {
            "name": "API Customer", 
            "phone": "+628123456789", 
            "tier": "VIP"
        },
        "items": [
            {
                "product_name": "Mouse Wireless", 
                "quantity": 1, 
                "unit_price": 100000
            }
        ],
        "shipping_address": {
            "city": "Jakarta", 
            "province": "DKI JAKARTA"
        },
        "payment": {
            "method": "Saldo ShopeePay", 
            "status": "Paid"
        },
        "subtotal": 100000,
        "total_amount": 100000,
        "created_at": datetime.now().isoformat()
    }
    
    response = client.post("/webhook/order", json=valid_payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            print("   ✅ PASSED: Order accepted and processed.")
            print(f"   ℹ️ Response: {result.get('decision')}")
            passed += 1
        else:
            print(f"   ❌ FAILED: Order rejected - {result.get('reason')}")
    else:
        print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
        print(f"   ℹ️ Detail: {response.json()}")

    # TEST 2: Invalid Payload (Missing Fields)
    total += 1
    print(f"\n📋 Test {total}: Invalid Payload Validation")
    
    invalid_payload = {"order_id": "ORD_0000002",}
    
    response = client.post("/webhook/order", json=invalid_payload)
    
    if response.status_code == 422:
        print("   ✅ PASSED: Schema validation rejected invalid payload.")
        print(f"   ℹ️ Error: 422 Unprocessable Entity")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected 422, got {response.status_code}")

    # TEST 3: Business Logic Rejection (Invalid Payment)
    total += 1
    print(f"\n📋 Test {total}: Business Logic Rejection (Invalid Payment)")
    
    rejected_payload = {
        "order_id": "ORD_0000003",
        "customer": {
            "name": "Bad Customer", 
            "phone": "+62822222222", 
            "tier": "NEW"
        },
        "items": [
            {
                "product_name": "Celengan", 
                "quantity": 1, 
                "unit_price": 5000
            }
        ],
        "shipping_address": {
            "city": "Jakarta", 
            "province": "DKI JAKARTA"
        },
        "payment": {
            "method": "Bitcoin", 
            "status": "Pending"
        },
        "subtotal": 5000,
        "total_amount": 5000,
        "created_at": datetime.now().isoformat()
    }
    
    response = client.post("/webhook/order", json=rejected_payload)
    
    if response.status_code == 422:
        # Schema caught it first (Bitcoin not in enum)
        print("   ✅ PASSED: Invalid payment method rejected by schema.")
        print(f"   ℹ️ Error: 422 Unprocessable Entity")
        passed += 1
    elif response.status_code == 200 and response.json().get("status") == "rejected":
        # Pipeline caught it
        print("   ✅ PASSED: Invalid payment method rejected by pipeline.")
        print(f"   ℹ️ Reason: {response.json().get('reason')}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected rejection, got {response.status_code}")

    # SUMMARY
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print("🚀 All Webhook tests passed!")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    run_webhook_tests()