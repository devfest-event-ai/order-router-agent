# src/api/webhook.py

import sys
import os
import time
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import UnifiedOrder
from src.pipeline import OrderProcessingPipeline
from src.api.middleware import verify_signature_middleware
from src.queue.processor import queue_manager
from src.monitoring.metrics import metrics
from src.monitoring.alerts import AlertEngine
from src.api.extraction import extractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrderRouter")

app = FastAPI(
    title="Order Router Agent API",
    description="Webhook interface & AI extraction for order processing",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach signature verification middleware
app.middleware("http")(verify_signature_middleware)

# =========================================================
# 1️⃣ AI EXTRACTION ENDPOINTS
# =========================================================

@app.post("/extract", status_code=200)
async def extract_order(messy_input: dict):
    """
    Extract structured order from messy text (email/WhatsApp).
    """
    text = messy_input.get("text", "").strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text field is required")
    
    result = extractor.extract(text)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.post("/webhook/extract-and-process", status_code=202)
async def extract_and_process(messy_input: dict, background_tasks: BackgroundTasks):
    """
    One-step: Extract messy text → validate → process order.
    """
    text = messy_input.get("text", "").strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text field is required")
    
    extraction_result = extractor.extract(text)
    
    if not extraction_result["success"]:
        return {
            "status": "extraction_failed",
            "error": extraction_result["error"],
            "confidence": 0.0
        }
    
    if extraction_result["confidence"] < 0.7:
        return {
            "status": "low_confidence",
            "message": "Extraction confidence too low, manual review recommended",
            "extracted_data": extraction_result["data"],
            "confidence": extraction_result["confidence"]
        }
    
    try:
        order_data = extraction_result["data"]
        
        order = UnifiedOrder(
            order_id=f"ORD_EXTRACTED_{int(time.time())}",
            customer=order_data.get("customer", {}),
            items=order_data.get("items", []),
            shipping_address=order_data.get("shipping_address", {}),
            payment=order_data.get("payment", {}),
            subtotal=0,
            total_amount=0
        )
        
        background_tasks.add_task(
            queue_manager.process_order_background,
            order
        )
        
        return {
            "status": "accepted",
            "message": "Order extracted and queued for processing",
            "confidence": extraction_result["confidence"],
            "order_id": order.order_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# =========================================================
# 2️⃣ EXISTING ENDPOINTS
# =========================================================

@app.get("/health")
async def health_check():
    current_metrics = metrics.get_metrics()
    active_alerts = AlertEngine.check_alerts()
    
    return {
        "status": "healthy",
        "metrics": current_metrics,
        "active_alerts": active_alerts
    }

@app.post("/webhook/order", status_code=202)
async def receive_order(order: UnifiedOrder, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    try:
        background_tasks.add_task(
            queue_manager.process_order_background,
            order
        )
        
        processing_time = time.time() - start_time
        metrics.record_order(success=True, processing_time=processing_time)
        
        return {
            "status": "accepted",
            "message": f"Order {order.order_id} received. Processing started in background.",
            "order_id": order.order_id
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        metrics.record_order(success=False, processing_time=processing_time)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)