# tests/test_e2e.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import (
    UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails, CustomerTier
)
from src.pipeline import OrderProcessingPipeline
from datetime import datetime

def run_e2e_tests():
    pipeline = OrderProcessingPipeline()
    passed = 0
    total = 0

    print("=" * 70)
    print(" END-TO-END PIPELINE TEST SUITE")
    print("=" * 70)

    # ─────────────────────────────────────────────────────────────────────
    # TEST 1: Happy Path (Valid Order)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Happy Path - Valid Order Processing")
    
    valid_order = UnifiedOrder(
        order_id="ORD_0000050",
        customer=Customer(name="Happy Customer", phone="+628123456789", tier=CustomerTier.VIP),
        #items=[OrderItem(product_name="Mouse", quantity=1, unit_price=100_000)],
        items=[OrderItem(product_name="Mouse Wireless", quantity=1, unit_price=100_000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
        subtotal=100_000,
        total_amount=100_000,
        created_at=datetime.now()
    )
    
    result = pipeline.process_order(valid_order)
    
    if result["success"] and result["decision"] == "APPROVED":
        print("   ✅ PASSED: Order approved successfully.")
        print(f"   ℹ️ Warehouse: {result['warehouse']}, Days: {result['estimated_days']}")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected APPROVED, got {result}")
        
    # ─────────────────────────────────────────────────────────────────────
    # TEST 2: Invalid Payment (Bitcoin)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Invalid Payment Method Rejection")
    
    try:
        invalid_payment_order = UnifiedOrder(
            order_id="ORD_0000051",
            customer=Customer(name="Test Customer", phone="+62822222222", tier=CustomerTier.NEW),
            items=[OrderItem(product_name="Keyboard Mechanical", quantity=1, unit_price=200_000)],
            shipping_address=ShippingAddress(city="Bandung", province="Jawa Barat"),
            payment=PaymentDetails(method="Bitcoin", status="Pending"),
            subtotal=200_000,
            total_amount=200_000,
            created_at=datetime.now()
        )
        
        # If we get here, schema didn't catch it (shouldn't happen)
        result = pipeline.process_order(invalid_payment_order)
        print(f"   ❌ FAILED: Schema allowed invalid payment method")
        
    except Exception as e:
        # Schema caught it - this is expected
        if "Bitcoin" in str(e) or "payment" in str(e).lower():
            print("   ✅ PASSED: Invalid payment caught by schema validation.")
            print(f"   ℹ️ Error: {str(e)[:50]}...")
            passed += 1
        else:
            print(f"   ❌ FAILED: Wrong error: {e}")
            
    # ────────────────────────────────────────────────────────────────────
    # TEST 3: Out of Stock
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n Test {total}: Out of Stock Rejection")
    
    out_of_stock_order = UnifiedOrder(
        order_id="ORD_0000052",
        customer=Customer(name="Buyer", phone="+62833333333", tier=CustomerTier.REGULAR),
        items=[OrderItem(product_name="Keyboard Mechanical", quantity=1, unit_price=500_000)],
        shipping_address=ShippingAddress(city="Surabaya", province="Jawa Timur"),
        payment=PaymentDetails(method="Online Payment", status="Paid"),
        subtotal=500_000,
        total_amount=500_000,
        created_at=datetime.now()
    )
    
    result = pipeline.process_order(out_of_stock_order)
    
    if not result["success"] and "Inventory check failed" in result["message"]:
        print("   ✅ PASSED: Out of stock caught and rejected.")
        print(f"   ℹ️ Error: {result['message'][:50]}...")
        passed += 1
    else:
        print(f"    FAILED: Expected inventory error")

        # ─────────────────────────────────────────────────────────────────────
    # TEST 4: Fraud Detection (Critical Risk)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Critical Fraud Detection Rejection")
    
    # Register 5 previous orders to trigger velocity check
    pipeline.fraud_detector.order_history["+62844444444"] = [
        "2026-05-20T10:00:00", "2026-05-20T10:05:00",
        "2026-05-20T10:10:00", "2026-05-20T10:15:00",
        "2026-05-20T10:20:00"
    ]
    
    fraud_order = UnifiedOrder(
        order_id="ORD_0000053",
        customer=Customer(name="Suspicious Buyer", phone="+62844444444", tier=CustomerTier.NEW),
        items=[OrderItem(product_name="Laptop Gaming", quantity=1, unit_price=15_000_000)],  # Changed
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="Online Payment", status="Pending"),
        subtotal=15_000_000,
        total_amount=15_000_000,
        created_at=datetime.now()
    )
    
    result = pipeline.process_order(fraud_order)
    
    if not result["success"] and "Fraud detection CRITICAL" in result["message"]:
        print("   ✅ PASSED: Critical fraud detected and rejected.")
        print(f"   ℹ️ Error: {result['message'][:50]}...")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected fraud rejection")
        print(f"   ℹ️ Got: {result}")
    
if __name__ == "__main__":
    run_e2e_tests()