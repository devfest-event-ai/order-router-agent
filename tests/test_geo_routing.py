# tests/test_geo_routing.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import (
    UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails
)
from src.router.geo_routing import GeoRouter
from datetime import datetime

def run_geo_routing_tests():
    router = GeoRouter()
    passed = 0
    total = 0

    print("=" * 70)
    print("🗺️ GEOGRAPHIC ROUTING TEST SUITE")
    print("=" * 70)

    # TEST 1: Jakarta Order (Local Warehouse)
    total += 1
    print(f"\n📋 Test {total}: Order Jakarta (Local Warehouse)")
    
    order_jkt = UnifiedOrder(
        order_id="ORD_0000020",
        customer=Customer(name="Jakarta Buyer", phone="+628123456789"),
        items=[OrderItem(product_name="Celengan", quantity=2, unit_price=5000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
        subtotal=10000,
        total_amount=10000,
        created_at=datetime.now()
    )
    
    result = router.validate_routing(order_jkt)
    
    if result["is_valid"] and result["routing_info"]["warehouse_id"] == "WH_JKT":
        print("   ✅ PASSED: Routed to WH_JKT")
        print(f"   ℹ️ Est. delivery: {result['routing_info']['estimated_delivery_days']} days")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected WH_JKT, got {result}")

    # TEST 2: Bandung Order (Provincial Warehouse)
    total += 1
    print(f"\n📋 Test {total}: Order Bandung (Provincial Warehouse)")
    
    order_bdg = UnifiedOrder(
        order_id="ORD_0000021",
        customer=Customer(name="Bandung Buyer", phone="+628123456789"),
        items=[OrderItem(product_name="Kaos", quantity=3, unit_price=50000)],
        shipping_address=ShippingAddress(city="Bandung", province="Jawa Barat"),
        payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
        subtotal=150000,
        total_amount=150000,
        created_at=datetime.now()
    )
    
    result = router.validate_routing(order_bdg)
    
    if result["is_valid"] and result["routing_info"]["warehouse_id"] == "WH_BDG":
        print("   ✅ PASSED: Routed to WH_BDG")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected WH_BDG, got {result}")

    # TEST 3: COD Unavailable City
    total += 1
    print(f"\n📋 Test {total}: COD Unavailable City (Kab. Tangerang)")
    
    order_cod_unavail = UnifiedOrder(
        order_id="ORD_0000022",
        customer=Customer(name="Tangerang Buyer", phone="+628123456789"),
        items=[OrderItem(product_name="Mouse", quantity=1, unit_price=100000)],
        shipping_address=ShippingAddress(city="Kab. Tangerang", province="Banten"),
        payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
        subtotal=100000,
        total_amount=100000,
        created_at=datetime.now()
    )
    
    result = router.validate_routing(order_cod_unavail)
    
    if not result["is_valid"] and "COD_UNAVAILABLE" in result["errors"][0]:
        print("   ✅ PASSED: COD correctly marked unavailable")
        print(f"   ️ Error: {result['errors'][0][:60]}...")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected COD_UNAVAILABLE error")

    # TEST 4: Remote Area Warning
    total += 1
    print(f"\n📋 Test {total}: Remote Area (Papua) - Warning Expected")
    
    order_papua = UnifiedOrder(
        order_id="ORD_0000023",
        customer=Customer(name="Papua Buyer", phone="+628123456789"),
        items=[OrderItem(product_name="Laptop", quantity=1, unit_price=10000000)],
        shipping_address=ShippingAddress(city="Jayapura", province="Papua"),
        payment=PaymentDetails(method="Online Payment", status="Paid"),
        subtotal=10000000,
        total_amount=10000000,
        created_at=datetime.now()
    )
    
    result = router.validate_routing(order_papua)
    
    if result["is_valid"] and "REMOTE_AREA" in result["warnings"][0]:
        print("   ✅ PASSED: Remote area warning generated")
        print(f"   ℹ️ Warning: {result['warnings'][0][:60]}...")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected REMOTE_AREA warning")

    # TEST 5: Fallback to Default Warehouse
    total += 1
    print(f"\n📋 Test {total}: Unknown City (Fallback to WH_JKT)")
    
    order_unknown = UnifiedOrder(
        order_id="ORD_0000024",
        customer=Customer(name="Unknown City Buyer", phone="+628123456789"),
        items=[OrderItem(product_name="Keyboard", quantity=1, unit_price=200000)],
        shipping_address=ShippingAddress(city="Ambon", province="Maluku"),
        payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
        subtotal=200000,
        total_amount=200000,
        created_at=datetime.now()
    )
    
    result = router.validate_routing(order_unknown)
    
    if result["is_valid"] and result["routing_info"]["warehouse_id"] == "WH_JKT":
        print("   ✅ PASSED: Fallback to WH_JKT worked")
        passed += 1
    else:
        print(f"   ❌ FAILED: Expected fallback to WH_JKT")

    # SUMMARY
    print("\n" + "=" * 70)
    print(f" TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print("🚀 All routing tests passed! Geographic routing is working.")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    run_geo_routing_tests()