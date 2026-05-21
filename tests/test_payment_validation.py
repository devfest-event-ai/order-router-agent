# tests/test_payment_validation.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import (
    UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails
)
from src.validators.payment_rules import PaymentValidator
from pydantic import ValidationError
from datetime import datetime

def run_payment_tests():
    validator = PaymentValidator()
    passed = 0
    total = 0

    print("=" * 70)
    print("🧪 PAYMENT VALIDATION TEST SUITE")
    print("=" * 70)

    # TEST 1: Valid ShopeePay Order
    total += 1
    print(f"\n📋 Test {total}: Valid ShopeePay Order")
    try:
        valid_order = UnifiedOrder(
            order_id="ORD_0000001",
            customer=Customer(name="Budi", phone="+628123456789", tier="Regular"),
            items=[OrderItem(product_name="Celengan", quantity=1, unit_price=5000)],
            shipping_address=ShippingAddress(city="Tangerang", province="Banten"),
            payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
            subtotal=5000,
            total_amount=5000,
            created_at=datetime.now()
        )
        result = validator.validate(valid_order)
        if result["is_valid"] and result["risk_level"] == "LOW":
            print("   ✅ PASSED: Valid order accepted with LOW risk")
            passed += 1
        else:
            print(f"   ❌ FAILED: Expected valid, got {result}")
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")

    # TEST 2: Invalid Payment Method (Bitcoin)
    total += 1
    print(f"\n📋 Test {total}: Invalid Payment Method - Bitcoin")
    try:
        UnifiedOrder(
            order_id="ORD_0000002",
            customer=Customer(name="Test User", phone="+628123456789", tier="New"),
            items=[OrderItem(product_name="Phone", quantity=1, unit_price=1000)],
            shipping_address=ShippingAddress(city="Jakarta", province="DKI JAKARTA"),
            payment=PaymentDetails(method="Bitcoin", status="Pending"), 
            subtotal=1000,
            total_amount=1000,
            created_at=datetime.now()
        )
        print(f"   ❌ FAILED: Schema allowed invalid payment method")
    except ValidationError:
        print("   ✅ PASSED: Schema correctly rejected invalid payment method")
        passed += 1

    # TEST 3: COD Exceeds Limit
    total += 1
    print(f"\n📋 Test {total}: COD > Rp 5,000,000 (Business Rule)")
    try:
        cod_expensive_order = UnifiedOrder(
            order_id="ORD_0000003",
            customer=Customer(name="Rich Customer", phone="+628123456789", tier="VIP"),
            items=[OrderItem(product_name="Laptop", quantity=1, unit_price=10_000_000)],
            shipping_address=ShippingAddress(city="Jakarta", province="DKI JAKARTA"),
            payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
            subtotal=10_000_000,
            total_amount=10_000_000,
            created_at=datetime.now()
        )
        result = validator.validate(cod_expensive_order)
        if not result["is_valid"] and "COD_LIMIT_EXCEEDED" in result["errors"][0]:
            print("   ✅ PASSED: Business rule caught high COD value")
            passed += 1
        else:
            print(f"   ❌ FAILED: Expected COD_LIMIT_EXCEEDED error. Got: {result}")
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")

    # TEST 4: High Value COD Warning
    total += 1
    print(f"\n📋 Test {total}: COD Rp 2,500,000 (Warning Only)")
    try:
        cod_medium_order = UnifiedOrder(
            order_id="ORD_0000004",
            customer=Customer(name="Medium Customer", phone="+628123456789", tier="Regular"),
            items=[OrderItem(product_name="Phone", quantity=5, unit_price=500_000)],
            shipping_address=ShippingAddress(city="Bandung", province="Jawa Barat"),
            payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
            subtotal=2_500_000,
            total_amount=2_500_000,
            created_at=datetime.now()
        )
        result = validator.validate(cod_medium_order)
        if result["is_valid"] and "HIGH_VALUE_COD" in result["warnings"][0]:
            print("   ✅ PASSED: High value COD generated a warning (not error)")
            passed += 1
        else:
            print(f"   ❌ FAILED: Expected warning. Got: {result}")
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")

    # SUMMARY
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print("🚀 All tests passed! Payment Validator is production-ready.")
    else:
        print("⚠️ Some tests failed. Review logic.")

if __name__ == "__main__":
    run_payment_tests()





