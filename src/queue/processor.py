# src/queue/processor.py

import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.schemas.order_schema import UnifiedOrder
from src.pipeline import OrderProcessingPipeline
from src.database.audit_log import AuditLogger

logger = logging.getLogger("OrderRouter")

class TaskManager:
    """
    Manages background order processing tasks.
    """
    
    def __init__(self):
        self.pipeline = OrderProcessingPipeline()
        self.audit_logger = AuditLogger()

    @retry(
        stop=stop_after_attempt(3),  # Retry max 3 times
        wait=wait_exponential(multiplier=1, min=2, max=10),  # Wait 2s, 4s, 8s between retries
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),  # Only retry specific errors
        reraise=True
    )
    async def process_order_background(self, order: UnifiedOrder) -> dict:
        """
        Executes the order processing pipeline.
        Retries automatically on network/database errors.
        """
        try:
            logger.info(f"Background processing started for {order.order_id}")
            
            # Run the main pipeline logic
            result = self.pipeline.process_order(order)
            
            # Log the decision
            self.audit_logger.log_order(
                order.order_id, 
                {"is_valid": result["success"], "risk_level": result.get("fraud_risk", "LOW")},
                {"warehouse_id": result.get("warehouse", "N/A")}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Background processing failed for {order.order_id}: {str(e)}")
            raise e

# Global instance for the queue
queue_manager = TaskManager()