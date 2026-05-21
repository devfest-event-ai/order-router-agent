# src/error_handling.py

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OrderRouter")

class ProcessingError(Exception):
    """Custom exception for order processing errors."""
    pass

def handle_processing_error(error: Exception, order_id: str = None) -> Dict[str, Any]:
    """
    Centralized error handling for order processing.
    Returns a standardized error response.
    """
    error_type = type(error).__name__
    
    logger.error(f"Error processing order {order_id or 'unknown'}: {str(error)}", exc_info=True)
    
    return {
        "success": False,
        "error_type": error_type,
        "message": str(error),
        "order_id": order_id,
        "action_required": "MANUAL_REVIEW" if "validation" in error_type.lower() else "SYSTEM_ALERT"
    }

def log_processing_stage(stage: str, order_id: str, status: str, details: str = ""):
    """Log each stage of order processing."""
    logger.info(f"Stage: {stage} | Order: {order_id} | Status: {status} | Details: {details}")