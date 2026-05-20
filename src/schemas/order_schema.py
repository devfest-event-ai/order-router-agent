from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime
import re

# Enums berdasarkan dataset
class PaymentMethodEnum(str, Enum):
    COD = "COD (Bayar di Tempat)"
    SHOPEEPAY = "Saldo ShopeePay"
    SPAYLATER = "SPayLater"
    ONLINE_PAYMENT = "Online Payment"
    SEABANK = "SeaBank Bayar Instan"
    KARTU_KREDIT = "Kartu Kredit/Debit"
    ALFAMART = "Alfamart/Alfamidi/Dan+Dan"
    GIFTCARD = "Gift Card"

class OrderStatusEnum(str, Enum):
    SELESAI = "Selesai"
    BATAL = "Batal"
    DIPROSES = "Sedang Dikirim"
    DIKIRIM = "Telah Dikirim"

class ShippingOptionEnum(str, Enum):
    SPX_STANDARD = "SPX Standard"
    SPX_HEMAT = "SPX Hemat"
    JNE_REGULER = "JNE Reguler"
    JNT_ECONOMY = "J&T Economy"
    GOSSEND_SAMEDAY = "GoSend Same Day"

# Pydantic Models
class Customer(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        # Indonesian phone format
        if not re.match(r'^\+?62?[0-9]{9,12}$', v.replace('-', '').replace(' ', '')):
            raise ValueError('Invalid Indonesian phone number')
        return v

class OrderItem(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., ge=1, le=256, description="Max 256 units based on dataset")
    unit_price: float = Field(..., ge=0, le=10_000_000)  # Max 10 juta per unit
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        if v > 256:
            raise ValueError('Quantity exceeds maximum (256)')
        return v

class ShippingAddress(BaseModel):
    city: str = Field(..., min_length=2, description="City/Kabupaten")
    province: str = Field(..., min_length=2, description="Province")
    postal_code: Optional[str] = Field(None, pattern=r'^\d{5}$')
    
    @validator('province')
    def validate_province(cls, v):
        # Validate against 34 Indonesian provinces
        valid_provinces = [
            'DKI JAKARTA', 'JAWA BARAT', 'JAWA TENGAH', 'JAWA TIMUR', 
            'BANTEN', 'SUMATERA UTARA', 'SUMATERA BARAT', 'SUMATERA SELATAN',
            'KALIMANTAN BARAT', 'KALIMANTAN TENGAH', 'SULAWESI SELATAN',
            'BALI', 'DI YOGYAKARTA', 'MALUKU UTARA', 'KEPULAUAN RIAU',
            # ... add all 34 provinces
        ]
        if v.upper() not in valid_provinces:
            raise ValueError(f'Invalid province: {v}')
        return v.upper()

class PaymentDetails(BaseModel):
    method: PaymentMethodEnum
    status: str = Field(default="Pending", pattern="^(Pending|Paid|Failed|Refunded)$")
    transaction_id: Optional[str] = None
    
    @validator('method')
    def validate_payment_method(cls, v):
        # Based on dataset analysis
        allowed_methods = [
            "COD (Bayar di Tempat)",
            "Saldo ShopeePay",
            "SPayLater", 
            "Online Payment",
            "SeaBank Bayar Instan",
            "Kartu Kredit/Debit",
            "Alfamart/Alfamidi/Dan+Dan"
        ]
        if v not in allowed_methods:
            raise ValueError(f'Payment method not allowed: {v}')
        return v

class ShippingDetails(BaseModel):
    option: ShippingOptionEnum
    weight_grams: int = Field(..., ge=0, le=50000)  # Max 50kg
    shipping_cost: float = Field(..., ge=0, le=500_000)
    estimated_delivery_days: Optional[int] = Field(None, ge=1, le=30)

class UnifiedOrder(BaseModel):
    """
    Main order schema based on Indonesia e-commerce dataset patterns
    """
    order_id: str = Field(..., pattern=r'^ORD_\d{7}$', description="Format: ORD_XXXXXXX")
    
    customer: Customer
    items: List[OrderItem] = Field(..., min_items=1, max_items=50)
    
    shipping_address: ShippingAddress
    shipping_details: Optional[ShippingDetails] = None
    
    payment: PaymentDetails
    
    # Financial fields
    subtotal: float = Field(..., ge=0, description="Sum of (quantity × unit_price)")
    shipping_cost: float = Field(default=0, ge=0, le=500_000)
    discount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0, description="subtotal + shipping - discount")
    
    # Metadata
    status: OrderStatusEnum = Field(default=OrderStatusEnum.SELESAI)
    created_at: datetime = Field(default_factory=datetime.now)
    cancellation_reason: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
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
                "total_amount": 19000,
                "status": "Selesai"
            }
        }
    
    @validator('total_amount')
    def validate_total(cls, v, values):
        """Validate total calculation"""
        subtotal = values.get('subtotal', 0)
        shipping = values.get('shipping_cost', 0)
        discount = values.get('discount', 0)
        
        expected_total = subtotal + shipping - discount
        if abs(v - expected_total) > 0.01:  # Allow small floating point diff
            raise ValueError(f'Total amount mismatch. Expected {expected_total}, got {v}')
        return v
    
    @validator('subtotal')
    def calculate_subtotal(cls, v, values):
        """Auto-calculate subtotal from items"""
        if 'items' in values:
            calculated = sum(item.quantity * item.unit_price for item in values['items'])
            if abs(v - calculated) > 0.01:
                raise ValueError(f'Subtotal mismatch. Expected {calculated}, got {v}')
        return v

# Validation helper functions
def validate_order_against_rules(order: UnifiedOrder) -> dict:
    """
    Additional business rules validation beyond schema
    Based on Indonesia e-commerce patterns
    """
    errors = []
    warnings = []
    
    # Rule 1: COD max amount (based on dataset: max ~5 juta)
    if order.payment.method == PaymentMethodEnum.COD and order.total_amount > 5_000_000:
        errors.append("COD orders cannot exceed Rp 5,000,000")
    
    # Rule 2: High-value orders need extra validation
    if order.total_amount > 2_000_000:
        warnings.append("High-value order - recommend manual review")
    
    # Rule 3: Weight validation for shipping
    if order.shipping_details:
        total_weight = sum(item.quantity * 500 for item in order.items)  # Assume 500g avg
        if order.shipping_details.weight_grams < total_weight * 0.8:
            warnings.append("Shipping weight seems underestimated")
    
    # Rule 4: Province-city consistency (basic check)
    if "JAKARTA" in order.shipping_address.province and "KAB." in order.shipping_address.city:
        warnings.append("Jakarta should not have 'KAB.' prefix")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "confidence_score": 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1)
    }