# src/pipeline.py

from typing import Dict, Any
from src.schemas.order_schema import UnifiedOrder
from src.validators.payment_rules import PaymentValidator
from src.validators.inventory_rules import MockInventory, InventoryValidator
from src.validators.fraud_rules import FraudDetector
from src.router.geo_routing import GeoRouter
from src.database.audit_log import AuditLogger
from src.error_handling import ProcessingError, handle_processing_error, log_processing_stage

class OrderProcessingPipeline:
    """
    Orchestrates the complete order processing flow.
    Runs all validations, routing, and logging in sequence.
    """
    
    def __init__(self):
        self.payment_validator = PaymentValidator()
        self.inventory = MockInventory()
        self.inventory_validator = InventoryValidator(self.inventory)
        self.fraud_detector = FraudDetector()
        self.geo_router = GeoRouter()
        self.audit_logger = AuditLogger()
    
    def process_order(self, order: UnifiedOrder) -> Dict[str, Any]:
        """
        Process an order through the complete pipeline.
        Returns final decision with all validation results.
        """
        order_id = order.order_id
        log_processing_stage("START", order_id, "IN_PROGRESS", "Order received")
        
        try:
            # Step 1: Payment Validation
            log_processing_stage("PAYMENT_VALIDATION", order_id, "RUNNING", "")
            payment_result = self.payment_validator.validate(order)
            if not payment_result["is_valid"]:
                raise ProcessingError(f"Payment validation failed: {payment_result['errors']}")
            log_processing_stage("PAYMENT_VALIDATION", order_id, "PASSED", f"Risk: {payment_result['risk_level']}")
            
            # Step 2: Inventory Validation
            log_processing_stage("INVENTORY_CHECK", order_id, "RUNNING", "")
            inventory_result = self.inventory_validator.validate(order)
            if not inventory_result["is_valid"]:
                raise ProcessingError(f"Inventory check failed: {inventory_result['errors']}")
            log_processing_stage("INVENTORY_CHECK", order_id, "PASSED", "Stock available")
            
            # Step 3: Fraud Detection
            log_processing_stage("FRAUD_CHECK", order_id, "RUNNING", "")
            fraud_result = self.fraud_detector.calculate_risk(order)
            self.fraud_detector.register_order(order)  # Record for velocity checks
            if fraud_result["risk_level"] in ["CRITICAL"]:
                raise ProcessingError(f"Fraud detection CRITICAL: {fraud_result['reasons']}")
            log_processing_stage("FRAUD_CHECK", order_id, "PASSED", f"Risk: {fraud_result['risk_level']}")
            
            # Step 4: Geographic Routing
            log_processing_stage("ROUTING", order_id, "RUNNING", "")
            routing_result = self.geo_router.validate_routing(order)
            if not routing_result["is_valid"]:
                raise ProcessingError(f"Routing failed: {routing_result['errors']}")
            log_processing_stage("ROUTING", order_id, "PASSED", f"Warehouse: {routing_result['routing_info']['warehouse_id']}")
            
            # Step 5: Audit Logging
            log_processing_stage("AUDIT_LOG", order_id, "RUNNING", "")
            combined_validation = {
                "is_valid": True,
                "risk_level": fraud_result["risk_level"],
                "risk_score": fraud_result["risk_score"],
                "errors": []
            }
            self.audit_logger.log_order(order_id, combined_validation, routing_result["routing_info"])
            log_processing_stage("AUDIT_LOG", order_id, "PASSED", "Logged successfully")
            
            # Final Decision
            final_decision = "APPROVED"
            if fraud_result["risk_level"] in ["HIGH"]:
                final_decision = "APPROVED_WITH_REVIEW"
            
            log_processing_stage("COMPLETE", order_id, "SUCCESS", final_decision)
            
            return {
                "success": True,
                "order_id": order_id,
                "decision": final_decision,
                "payment_risk": payment_result["risk_level"],
                "fraud_risk": fraud_result["risk_level"],
                "warehouse": routing_result["routing_info"]["warehouse_id"],
                "estimated_days": routing_result["routing_info"]["estimated_delivery_days"]
            }
            
        except ProcessingError as e:
            log_processing_stage("FAILED", order_id, "ERROR", str(e))
            return handle_processing_error(e, order_id)
        except Exception as e:
            log_processing_stage("FAILED", order_id, "SYSTEM_ERROR", str(e))
            return handle_processing_error(e, order_id)