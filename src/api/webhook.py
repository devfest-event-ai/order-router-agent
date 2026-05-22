# src/api/webhook.py

import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import UnifiedOrder
from src.pipeline import OrderProcessingPipeline
from src.api.middleware import verify_signature_middleware

app = FastAPI(
    title="Order Router Agent API",
    description="Webhook interface for order processing",
    version="1.0.0"
)

# Add CORS middleware (optional, for local frontend testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach signature verification middleware
app.middleware("http")(verify_signature_middleware)

# Initialize the processing pipeline (single instance)
pipeline = OrderProcessingPipeline()

@app.post("/webhook/order", status_code=200)
async def receive_order(order: UnifiedOrder):
    """
    Endpoint to receive and process new orders.
    """
    try:
        # Process the order through the full pipeline
        result = pipeline.process_order(order)
        
        # Return standardized response
        if result["success"]:
            return {
                "status": "success",
                "order_id": result["order_id"],
                "decision": result["decision"],
                "warehouse": result.get("warehouse"),
                "estimated_days": result.get("estimated_days")
            }
        else:
            # Order rejected by pipeline (validation, inventory, fraud, etc.)
            return {
                "status": "rejected",
                "order_id": order.order_id,
                "reason": result.get("message", "Validation failed"),
                "action_required": result.get("action_required", "MANUAL_REVIEW")
            }
            
    except Exception as e:
        # Critical system error
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)