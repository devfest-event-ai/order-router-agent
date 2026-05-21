# src/validators/payment_rules.py

from typing import List, Dict, Any
from src.schemas.order_schema import UnifiedOrder

class PaymentValidator:
    """Validates payment details based on business rules."""

    ALLOWED_PAYMENT_METHODS = {
        "COD (Bayar di Tempat)",
        "Saldo ShopeePay",
        "SPayLater",
        "Online Payment",
        "SeaBank Bayar Instan",
        "Kartu Kredit/Debit",
        "Alfamart/Alfamidi/Dan+Dan"
    }

    COD_MAX_LIMIT = 5_000_000
    HIGH_VALUE_THRESHOLD = 2_000_000

    def validate(self, order: UnifiedOrder) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        risk_score: float = 0.0

        # 1. Payment Method Whitelist
        if order.payment.method not in self.ALLOWED_PAYMENT_METHODS:
            errors.append(f"INVALID_PAYMENT_METHOD: '{order.payment.method}' tidak didukung.")
            risk_score += 0.5

        # 2. COD Rules
        if order.payment.method == "COD (Bayar di Tempat)":
            if order.total_amount > self.COD_MAX_LIMIT:
                errors.append(f"COD_LIMIT_EXCEEDED: Max Rp {self.COD_MAX_LIMIT:,}")
                risk_score += 0.4
            elif order.total_amount > self.HIGH_VALUE_THRESHOLD:
                warnings.append("HIGH_VALUE_COD: Manual review recommended")
                risk_score += 0.2

            # New customer check
            if hasattr(order.customer, 'tier') and order.customer.tier == "New":
                if order.total_amount > 1_000_000:
                    warnings.append("NEW_CUSTOMER_HIGH_VALUE_COD")
                    risk_score += 0.3

        # 3. Payment Status
        if order.payment.status == "Failed":
            errors.append("PAYMENT_FAILED")
            risk_score += 0.6
        elif order.payment.status == "Pending":
            if order.payment.method not in ["COD (Bayar di Tempat)", "Bank Transfer"]:
                warnings.append("PENDING_NON_COD_PAYMENT")
                risk_score += 0.2

        # 4. Order Value
        if order.total_amount < 0:
            errors.append("NEGATIVE_TOTAL")
            risk_score += 0.7
        elif order.total_amount > 50_000_000:
            warnings.append("VERY_HIGH_VALUE")
            risk_score += 0.3

        # 5. Discount Validation
        if order.discount < 0:
            errors.append("NEGATIVE_DISCOUNT")
            risk_score += 0.5
        elif order.discount > order.subtotal:
            errors.append(f"DISCOUNT_EXCEEDS_SUBTOTAL")
            risk_score += 0.6

        # 6. Shipping Cost
        if order.shipping_cost < 0:
            errors.append("NEGATIVE_SHIPPING_COST")
            risk_score += 0.5
        elif order.shipping_cost > 500_000:
            warnings.append("HIGH_SHIPPING_COST")
            risk_score += 0.2

        # 7. Total Calculation
        expected_total = order.subtotal + order.shipping_cost - order.discount
        if abs(order.total_amount - expected_total) > 1:
            errors.append(f"TOTAL_MISMATCH: Expected {expected_total}, got {order.total_amount}")
            risk_score += 0.4

        risk_score = min(risk_score, 1.0)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "requires_manual_review": len(warnings) > 0 or risk_score > 0.4
        }

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.8: return "CRITICAL"
        if score >= 0.5: return "HIGH"
        if score >= 0.2: return "MEDIUM"
        return "LOW"




