# src/api/webhook.py

import sys
import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path so we can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.order_schema import UnifiedOrder
from src.pipeline import OrderProcessingPipeline
from src.api.middleware import verify_signature_middleware
from src.queue.processor import queue_manager
from src.monitoring.metrics import metrics
from src.monitoring.alerts import AlertEngine

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