from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr, ConfigDict
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

class CustomerTier(str, Enum):
    NEW = "New"
    REGULAR = "Regular"
    VIP = "VIP"
    PREMIUM = "Premium"

class Customer(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = None
    tier: CustomerTier = Field(default=CustomerTier.REGULAR, description="Customer tier")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r'^\+?62?[0-9]{9,12}$', v.replace('-', '').replace(' ', '')):
            raise ValueError('Invalid Indonesian phone number')
        return v

class OrderItem(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., ge=1, le=256, description="Max 256 units based on dataset")
    unit_price: float = Field(..., ge=0, le=10_000_000)

class ShippingAddress(BaseModel):
    city: str = Field(..., min_length=2, description="City/Kabupaten")
    province: str = Field(..., min_length=2, description="Province")
    postal_code: Optional[str] = Field(None, pattern=r'^\d{5}$')
    
    @field_validator('province')
    @classmethod
    def validate_province(cls, v: str) -> str:
        valid_provinces = [
            'DKI JAKARTA', 'JAWA BARAT', 'JAWA TENGAH', 'JAWA TIMUR', 
            'BANTEN', 'SUMATERA UTARA', 'SUMATERA BARAT', 'SUMATERA SELATAN',
            'KALIMANTAN BARAT', 'KALIMANTAN TENGAH', 'SULAWESI SELATAN',
            'BALI', 'DI YOGYAKARTA', 'MALUKU UTARA', 'KEPULAUAN RIAU'
        ]
        if v.upper() not in valid_provinces:
            raise ValueError(f'Invalid province: {v}')
        return v.upper()

class PaymentDetails(BaseModel):
    method: PaymentMethodEnum
    status: str = Field(default="Pending", pattern="^(Pending|Paid|Failed|Refunded)$")
    transaction_id: Optional[str] = None

class ShippingDetails(BaseModel):
    option: ShippingOptionEnum
    weight_grams: int = Field(..., ge=0, le=50000)
    shipping_cost: float = Field(..., ge=0, le=500_000)
    estimated_delivery_days: Optional[int] = Field(None, ge=1, le=30)
    
class UnifiedOrder(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "order_id": "ORD_0007243",
            "customer": {"name": "Budi Santoso", "phone": "+628123456789"},
            "items": [{"product_name": "Celengan", "quantity": 2, "unit_price": 500}],
            "shipping_address": {"city": "KAB. TANGERANG", "province": "BANTEN"},
            "payment": {"method": "COD (Bayar di Tempat)", "status": "Pending"},
            "subtotal": 1000, "shipping_cost": 18000, "total_amount": 19000, "status": "Selesai"
        }
    })

    order_id: str = Field(..., pattern=r'^ORD_\d{7}$', description="Format: ORD_XXXXXXX")
    customer: Customer
    items: List[OrderItem] = Field(..., min_length=1, max_length=50)
    shipping_address: ShippingAddress
    shipping_details: Optional[ShippingDetails] = None
    payment: PaymentDetails
    subtotal: float = Field(..., ge=0, description="Sum of (quantity × unit_price)")
    shipping_cost: float = Field(default=0, ge=0, le=500_000)
    discount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0, description="subtotal + shipping - discount")
    status: OrderStatusEnum = Field(default=OrderStatusEnum.SELESAI)
    created_at: datetime = Field(default_factory=datetime.now)
    cancellation_reason: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_financials(self) -> 'UnifiedOrder':
        """Validate financial calculations after model is created."""
        # Calculate expected subtotal from items
        calculated_subtotal = sum(item.quantity * item.unit_price for item in self.items)
        
        # Check if provided subtotal matches
        if abs(self.subtotal - calculated_subtotal) > 0.01:
            raise ValueError(f"Subtotal mismatch. Expected {calculated_subtotal}, got {self.subtotal}")
        
        # Check total calculation
        expected_total = self.subtotal + self.shipping_cost - self.discount
        if abs(self.total_amount - expected_total) > 0.01:
            raise ValueError(f"Total mismatch. Expected {expected_total}, got {self.total_amount}")
        
        return self

def validate_order_against_rules(order: UnifiedOrder) -> dict:
    errors = []
    warnings = []
    
    if order.payment.method == PaymentMethodEnum.COD and order.total_amount > 5_000_000:
        errors.append("COD orders cannot exceed Rp 5,000,000")
    if order.total_amount > 2_000_000:
        warnings.append("High-value order - recommend manual review")
    if order.shipping_details:
        total_weight = sum(item.quantity * 500 for item in order.items)
        if order.shipping_details.weight_grams < total_weight * 0.8:
            warnings.append("Shipping weight seems underestimated")
    if "JAKARTA" in order.shipping_address.province and "KAB." in order.shipping_address.city:
        warnings.append("Jakarta should not have 'KAB.' prefix")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "confidence_score": 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1)
    }




