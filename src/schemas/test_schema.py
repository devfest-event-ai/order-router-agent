import sys
import os

# Tambahkan src folder ke Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Baru import setelah path ditambahkan
from schemas.order_schema import UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails, PaymentMethodEnum

from schemas.order_schema import UnifiedOrder, Customer, OrderItem, ShippingAddress, PaymentDetails, PaymentMethodEnum
from datetime import datetime
import json

def test_valid_order():
    """Test with valid order data from dataset"""
    
    order_data = {
        "order_id": "ORD_0007243",
        "customer": {
            "name": "Budi Santoso",
            "phone": "+628123456789"
        },
        "items": [
            {
                "product_name": "Celengan",
                "quantity": 2,
                "unit_price": 500
            }
        ],
        "shipping_address": {
            "city": "KAB. TANGERANG",
            "province": "BANTEN"
        },
        "payment": {
            "method": "COD (Bayar di Tempat)",
            "status": "Pending"
        },
        "subtotal": 1000,
        "shipping_cost": 18000,
        "discount": 0,
        "total_amount": 19000,
        "status": "Selesai"
    }
    
    try:
        order = UnifiedOrder(**order_data)
        print("✅ Valid order created successfully!")
        print(json.dumps(order.dict(), indent=2, default=str))
        return order
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return None

def test_invalid_orders():
    """Test various invalid scenarios"""
    
    print("\n--- Testing Invalid Orders ---\n")
    
    # Test 1: Invalid phone
    print("Test 1: Invalid phone number")
    try:
        order = UnifiedOrder(
            order_id="ORD_0007244",
            customer=Customer(name="Test", phone="123"),  # Invalid
            items=[OrderItem(product_name="Test", quantity=1, unit_price=100)],
            shipping_address=ShippingAddress(city="Jakarta", province="DKI JAKARTA"),
            payment=PaymentDetails(method=PaymentMethodEnum.COD),
            subtotal=100,
            total_amount=100
        )
    except Exception as e:
        print(f"✅ Caught expected error: {e}")
    
    # Test 2: Quantity exceeds max
    print("\nTest 2: Quantity > 256")
    try:
        order = UnifiedOrder(
            order_id="ORD_0007245",
            customer=Customer(name="Test", phone="+628123456789"),
            items=[OrderItem(product_name="Test", quantity=300, unit_price=100)],  # Invalid
            shipping_address=ShippingAddress(city="Jakarta", province="DKI JAKARTA"),
            payment=PaymentDetails(method=PaymentMethodEnum.COD),
            subtotal=30000,
            total_amount=30000
        )
    except Exception as e:
        print(f"✅ Caught expected error: {e}")
    
    # Test 3: COD over limit
    print("\nTest 3: COD > 5 juta")
    order_data = {
        "order_id": "ORD_0007246",
        "customer": {"name": "Test", "phone": "+628123456789"},
        "items": [{"product_name": "Laptop", "quantity": 5, "unit_price": 2_000_000}],
        "shipping_address": {"city": "Jakarta", "province": "DKI JAKARTA"},
        "payment": {"method": "COD (Bayar di Tempat)", "status": "Pending"},
        "subtotal": 10_000_000,
        "total_amount": 10_000_000
    }
    
    from schemas.order_schema import validate_order_against_rules
    try:
        order = UnifiedOrder(**order_data)
        validation = validate_order_against_rules(order)
        if not validation['valid']:
            print(f"✅ Caught expected validation error: {validation['errors']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Pydantic Schema for Order Router")
    print("=" * 60)
    
    # Test valid order
    order = test_valid_order()
    
    # Test invalid orders
    test_invalid_orders()
    
    print("\n" + "=" * 60)
    print("Schema testing complete!")
    print("=" * 60)