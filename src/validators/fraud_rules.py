# src/validators/fraud_rules.py

from typing import List, Dict, Any
from src.schemas.order_schema import UnifiedOrder, CustomerTier, PaymentMethodEnum

class FraudDetector:
    """
    Analyzes orders for fraud risk based on business rules.
    Returns a risk score between 0.0 (Safe) and 1.0 (Critical).
    """

    # Thresholds based on business logic
    HIGH_VALUE_THRESHOLD = 2_000_000  # Rp 2 Million
    VERY_HIGH_VALUE_THRESHOLD = 10_000_000  # Rp 10 Million
    COD_RISK_THRESHOLD = 1_000_000  # Rp 1 Million for new customers

    def __init__(self):
        # Simulated history store (In production, this connects to database)
        # Key: phone_number, Value: list of recent order timestamps
        self.order_history: Dict[str, List[str]] = {}

    def register_order(self, order: UnifiedOrder):
        """Records an order into history for velocity checks."""
        phone = order.customer.phone
        if phone not in self.order_history:
            self.order_history[phone] = []
        self.order_history[phone].append(order.created_at.isoformat())

    def calculate_risk(self, order: UnifiedOrder) -> Dict[str, Any]:
        """
        Calculates risk score for a specific order.
        """
        risk_score: float = 0.0
        reasons: List[str] = []

        # Rule 1: Velocity Check (Frequency of orders)
        phone = order.customer.phone
        recent_orders = self.order_history.get(phone, [])
        if len(recent_orders) >= 5:
            risk_score += 0.4
            reasons.append("HIGH_VELOCITY: Customer has 5+ recent orders.")

        # Rule 2: Payment Method Risk (COD is higher risk)
        if order.payment.method == PaymentMethodEnum.COD:
            # Base risk for COD
            risk_score += 0.1
            reasons.append("COD_PAYMENT: Cash on Delivery has higher risk.")
            
            # Extra risk if New Customer + High Value
            if order.customer.tier == CustomerTier.NEW:
                if order.total_amount > self.COD_RISK_THRESHOLD:
                    risk_score += 0.3
                    reasons.append(f"NEW_CUST_HIGH_COD: New customer COD > Rp {self.COD_RISK_THRESHOLD:,}")

        # Rule 3: Value Risk
        #if order.total_amount > self.VERY_HIGH_VALUE_THRESHOLD:
            #risk_score += 0.3
            #reasons.append(f"VERY_HIGH_VALUE: Order exceeds Rp {self.VERY_HIGH_VALUE_THRESHOLD:,}")
        #elif order.total_amount > self.HIGH_VALUE_THRESHOLD:
            #risk_score += 0.1
            #reasons.append(f"HIGH_VALUE: Order exceeds Rp {self.HIGH_VALUE_THRESHOLD:,}")
            
        # Rule 3: Value Risk
        if order.total_amount > self.VERY_HIGH_VALUE_THRESHOLD:
            risk_score += 0.5  # Increased from 0.3 to ensure HIGH risk
            reasons.append(f"VERY_HIGH_VALUE: Order exceeds Rp {self.VERY_HIGH_VALUE_THRESHOLD:,}")
        elif order.total_amount > self.HIGH_VALUE_THRESHOLD:
            risk_score += 0.2  # Increased from 0.1
            reasons.append(f"HIGH_VALUE: Order exceeds Rp {self.HIGH_VALUE_THRESHOLD:,}")

        # Rule 4: New Customer Penalty
        if order.customer.tier == CustomerTier.NEW:
            risk_score += 0.1
            reasons.append("NEW_CUSTOMER: No purchase history.")

        # Cap score at 1.0
        risk_score = min(risk_score, 1.0)

        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "reasons": reasons,
            "action_required": self._get_action(risk_score)
        }

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.7: return "CRITICAL"
        if score >= 0.4: return "HIGH"
        if score >= 0.15: return "MEDIUM"
        return "LOW"

    def _get_action(self, score: float) -> str:
        if score >= 0.7: return "REJECT"
        if score >= 0.4: return "MANUAL_REVIEW"
        return "AUTO_APPROVE"