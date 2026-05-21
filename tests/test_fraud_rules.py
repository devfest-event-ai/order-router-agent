# tests/test_fraud_rules.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import (
    UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails, CustomerTier
)
from src.validators.fraud_rules import FraudDetector
from datetime import datetime

def run_fraud_tests():
    detector = FraudDetector()
    passed = 0
    total = 0

    print("=" * 70)
    print("️ FRAUD DETECTION TEST SUITE")
    print("=" * 70)

    # ─────────────────────────────────────────────────────────────────────
    # TEST 1: Normal Order (VIP Customer, Low Value)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: VIP Customer, ShopeePay, Low Value -> LOW RISK")
    
    order_vip = UnifiedOrder(
        order_id="ORD_0000030",
        customer=Customer(name="VIP Buyer", phone="+62811111111", tier=CustomerTier.VIP),
        items=[OrderItem(product_name="Mouse", quantity=1, unit_price=100_000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
        subtotal=100_000,
        total_amount=100_000,
        created_at=datetime.now()
    )
    
    result = detector.calculate_risk(order_vip)
    
    if result["risk_level"] == "LOW" and result["action_required"] == "AUTO_APPROVE":
        print("   ✅ PASSED: Low risk score, auto-approve recommended.")
        print(f"   ℹ️ Score: {result['risk_score']:.1f}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected LOW, got {result}")

    # ─────────────────────────────────────────────────────────────────────
    # TEST 2: New Customer + High Value COD
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: New Customer, COD, High Value (Rp 2.5M) -> MEDIUM/HIGH RISK")
    
    order_risk = UnifiedOrder(
        order_id="ORD_0000031",
        customer=Customer(name="New Buyer", phone="+62822222222", tier=CustomerTier.NEW),
        items=[OrderItem(product_name="Phone", quantity=1, unit_price=2_500_000)],
        shipping_address=ShippingAddress(city="Surabaya", province="Jawa Timur"),
        payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
        subtotal=2_500_000,
        total_amount=2_500_000,
        created_at=datetime.now()
    )
    
    result = detector.calculate_risk(order_risk)
    
    # Expected: High risk due to New + COD + High Value
    if result["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]:
        print("   ✅ PASSED: Risk flagged correctly.")
        print(f"   ℹ️ Score: {result['risk_score']:.1f}, Level: {result['risk_level']}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected MEDIUM/HIGH, got {result}")

    # ────────────────────────────────────────────────────────────────────
    # TEST 3: Velocity Check (Simulate 5 previous orders)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Velocity Check (5 Previous Orders) -> HIGH RISK")
    
    # Register 5 fake previous orders for this phone number
    detector.order_history["+62833333333"] = [
        "2026-05-20T10:00:00",
        "2026-05-20T10:05:00",
        "2026-05-20T10:10:00",
        "2026-05-20T10:15:00",
        "2026-05-20T10:20:00"
    ]
    
    order_vel = UnifiedOrder(
        order_id="ORD_0000032",
        customer=Customer(name="Fast Buyer", phone="+62833333333", tier=CustomerTier.REGULAR),
        items=[OrderItem(product_name="Keyboard", quantity=1, unit_price=500_000)],
        shipping_address=ShippingAddress(city="Bandung", province="Jawa Barat"),
        payment=PaymentDetails(method="Online Payment", status="Paid"),
        subtotal=500_000,
        total_amount=500_000,
        created_at=datetime.now()
    )
    
    result = detector.calculate_risk(order_vel)
    
    if result["risk_level"] in ["HIGH", "CRITICAL"]:
        print("   ✅ PASSED: High velocity detected.")
        print(f"   ℹ️ Score: {result['risk_score']:.1f}, Level: {result['risk_level']}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected HIGH velocity risk, got {result}")

    # ─────────────────────────────────────────────────────────────────────
    # TEST 4: Very High Value Order (Above 10M)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Very High Value (Rp 15M) -> CRITICAL RISK")
    
    order_expensive = UnifiedOrder(
        order_id="ORD_0000033",
        customer=Customer(name="Wholesaler", phone="+62844444444", tier=CustomerTier.REGULAR),
        items=[OrderItem(product_name="Laptop Pro", quantity=1, unit_price=15_000_000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="Online Payment", status="Pending"),
        subtotal=15_000_000,
        total_amount=15_000_000,
        created_at=datetime.now()
    )
    
    result = detector.calculate_risk(order_expensive)
    
    if result["risk_level"] in ["HIGH", "CRITICAL"]:
        print("   ✅ PASSED: Very high value flagged.")
        print(f"   ℹ️ Score: {result['risk_score']:.1f}, Level: {result['risk_level']}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected HIGH risk for >10M order, got {result}")
    
    # SUMMARY
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print("🚀 All Fraud Detection tests passed!")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    run_fraud_tests()