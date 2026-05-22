# tests/test_payment_rules.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import (
    UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails
)
from src.validators.payment_rules import PaymentValidator
from datetime import datetime

def run_tests():
    validator = PaymentValidator()
    passed = 0
    total = 0

    print("🧪 Running Payment Validation Tests...\n")

    # --- Test Case 1: Valid Order (Normal ShopeePay) ---
    total += 1
    valid_order = UnifiedOrder(
        order_id="AORD_0000001",
        customer=Customer(name="Budi", phone="+628123456789"),
        items=[OrderItem(product_name="Celengan", quantity=1, unit_price=5000)],
        shipping_address=ShippingAddress(city="Tangerang", province="Banten"),
        payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
        subtotal=5000,
        total_amount=5000,
        created_at=datetime.now()
    )
    result = validator.validate(valid_order)
    if result["is_valid"] and result["risk_level"] == "LOW":
        print("✅ Test 1 Passed: Valid ShopeePay order accepted.")
        passed += 1
    else:
        print(f"❌ Test 1 Failed: Expected valid, got {result}")

    # --- Test Case 2: Invalid Payment Method ---
    total += 1
    invalid_method_order = UnifiedOrder(
        order_id="AORD_0000002",
        customer=Customer(name="Test", phone="+628123456789"),
        items=[OrderItem(product_name="Phone", quantity=1, unit_price=1000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="Bitcoin", status="Pending"),
        subtotal=1000,
        total_amount=1000,
        created_at=datetime.now()
    )
    result = validator.validate(invalid_method_order)
    if not result["is_valid"] and "INVALID_PAYMENT_METHOD" in result["errors"][0]:
        print("✅ Test 2 Passed: Invalid payment method caught.")
        passed += 1
    else:
        print(f"❌ Test 2 Failed: Expected error, got {result}")

    # --- Test Case 3: COD Limit Exceeded (> 5 Million) ---
    total += 1
    cod_expensive_order = UnifiedOrder(
        order_id="AORD_0000003",
        customer=Customer(name="Rich", phone="+628123456789"),
        items=[OrderItem(product_name="Laptop", quantity=1, unit_price=10_000_000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
        subtotal=10_000_000,
        total_amount=10_000_000,
        created_at=datetime.now()
    )
    result = validator.validate(cod_expensive_order)
    if not result["is_valid"] and "COD_LIMIT_EXCEEDED" in result["errors"][0]:
        print("✅ Test 3 Passed: COD Limit exceeded (>5M) caught.")
        passed += 1
    else:
        print(f"❌ Test 3 Failed: Expected COD error, got {result}")

    # --- Test Case 4: High Value Warning (Between 2M and 5M) ---
    total += 1
    cod_medium_order = UnifiedOrder(
        order_id="AORD_0000004",
        customer=Customer(name="Medium", phone="+628123456789"),
        items=[OrderItem(product_name="Phone", quantity=5, unit_price=500_000)],
        shipping_address=ShippingAddress(city="Bandung", province="Jawa Barat"),
        payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
        subtotal=2_500_000,
        total_amount=2_500_000,
        created_at=datetime.now()
    )
    result = validator.validate(cod_medium_order)
    if result["is_valid"] and result["risk_level"] == "MEDIUM" and "HIGH_VALUE_COD" in result["warnings"][0]:
        print("✅ Test 4 Passed: High value COD warning generated.")
        passed += 1
    else:
        print(f"❌ Test 4 Failed: Expected warning, got {result}")

    # Summary
    print(f"\n📊 Test Summary: {passed}/{total} Passed.")
    if passed == total:
        print("🚀 All tests passed! Payment Validator is ready.")

if __name__ == "__main__":
    run_tests()