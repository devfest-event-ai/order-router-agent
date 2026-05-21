# tests/test_inventory.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import (
    UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails
)
from src.validators.inventory_rules import MockInventory, InventoryValidator
from datetime import datetime

def run_inventory_tests():
    """Menjalankan test untuk Inventory Validator."""
    
    # Setup Mock Inventory
    inventory_db = MockInventory()
    validator = InventoryValidator(inventory_db)
    
    passed = 0
    total = 0

    print("=" * 70)
    print("📦 INVENTORY VALIDATION TEST SUITE")
    print("=" * 70)

    # ─────────────────────────────────────────────────────────────────────
    # TEST 1: Stok Tersedia (Valid)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Order 'Celengan' (Stok: 150, Pesan: 5) -> Seharusnya VALID")
    
    order_1 = UnifiedOrder(
        order_id="ORD_0000010",
        customer=Customer(name="Buyer 1", phone="+628123456789"),
        items=[OrderItem(product_name="Celengan", quantity=5, unit_price=5000)],
        shipping_address=ShippingAddress(city="Tangerang", province="Banten"),
        payment=PaymentDetails(method="Saldo ShopeePay", status="Paid"),
        subtotal=25000,
        total_amount=25000,
        created_at=datetime.now()
    )
    
    result = validator.validate(order_1)
    
    if result["is_valid"]:
        print("   ✅ PASSED: Order diterima.")
        # Cek apakah stok berkurang
        remaining = inventory_db.get_stock("Celengan")
        print(f"   ℹ️ Stok 'Celengan' tersisa: {remaining} (Seharusnya 145)")
        if remaining == 145:
            passed += 1
            print("   ✅ Stok berhasil dikurangi!")
        else:
            print(f"   ❌ FAILED: Stok tidak berkurang dengan benar.")
    else:
        print(f"   ❌ FAILED: Seharusnya valid, tapi error: {result['errors']}")

    # ─────────────────────────────────────────────────────────────────────
    # TEST 2: Stok Tidak Cukup (Invalid)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Order 'Laptop Gaming' (Stok: 5, Pesan: 10) -> Seharusnya INVALID")
    
    order_2 = UnifiedOrder(
        order_id="ORD_0000011",
        customer=Customer(name="Buyer 2", phone="+628123456789"),
        items=[OrderItem(product_name="Laptop Gaming", quantity=10, unit_price=15_000_000)],
        shipping_address=ShippingAddress(city="Jakarta", province="DKI Jakarta"),
        payment=PaymentDetails(method="COD (Bayar di Tempat)", status="Pending"),
        subtotal=150_000_000,
        total_amount=150_000_000,
        created_at=datetime.now()
    )
    
    result = validator.validate(order_2)
    
    if not result["is_valid"] and "INSUFFICIENT_STOCK" in result["errors"][0]:
        print("   ✅ PASSED: Stok tidak cukup tertangkap.")
        print(f"   ℹ️ Error: {result['errors'][0][:60]}...")
        passed += 1
    else:
        print(f"   ❌ FAILED: Seharusnya INSUFFICIENT_STOCK.")

    # ─────────────────────────────────────────────────────────────────────
    # TEST 3: Produk Tidak Dikenali (Invalid)
    # ─────────────────────────────────────────────────────────────────────
    total += 1
    print(f"\n📋 Test {total}: Order 'Pesawat Tempur' (Produk asing) -> Seharusnya INVALID")
    
    #order_3 = UnifiedOrder(
        #order_id="ORD_0000012",
        #customer=Customer(name="Buyer 3", phone="+628123456789"),
        #items=[OrderItem(product_name="Pesawat Tempur", quantity=1, unit_price=500_000_000)],
        #items=[OrderItem(product_name="Pesawat Tempur", quantity=1, unit_price=50_000_000)],  # Rp 50 juta
        #shipping_address=ShippingAddress(city="Surabaya", province="Jawa Timur"),
        #payment=PaymentDetails(method="Online Payment", status="Paid"),
        #subtotal=500_000_000,
        #total_amount=500_000_000,
        #created_at=datetime.now()
    #)
    
    order_3 = UnifiedOrder(
        order_id="ORD_0000012",
        customer=Customer(name="Buyer 3", phone="+628123456789"),
        items=[OrderItem(product_name="Pesawat Tempur", quantity=1, unit_price=50_000_000)],
        shipping_address=ShippingAddress(city="Surabaya", province="Jawa Timur"),
        payment=PaymentDetails(method="Online Payment", status="Paid"),
        subtotal=50_000_000,  # ← BENAR: 1 × 50 juta
        total_amount=50_000_000,  # ← BENAR: subtotal + ongkir (0)
        created_at=datetime.now()
    )
    result = validator.validate(order_3)
    
    if not result["is_valid"] and "UNKNOWN_PRODUCT" in result["errors"][0]:
        print("   ✅ PASSED: Produk asing tertangkap.")
        passed += 1
    else:
        print(f"   ❌ FAILED: Seharusnya UNKNOWN_PRODUCT.")

    # ─────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY: {passed}/{total} Passed.")
    print("=" * 70)
    
    if passed == total:
        print("🚀 All Inventory tests passed! Stock validation is working.")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    run_inventory_tests()