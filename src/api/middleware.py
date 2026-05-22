# src/api/middleware.py

import hmac
import hashlib
import os
from fastapi import Request
from fastapi.responses import JSONResponse

async def verify_signature_middleware(request: Request, call_next):
    """
    Middleware to verify HMAC signature for webhook security.
    """
    # Get secret from environment variable
    secret_key = os.getenv("WEBHOOK_SECRET", "default-secret-for-dev")
    
    # Get signature from headers
    incoming_signature = request.headers.get("X-Signature")
    
    # If signature is provided, verify it
    if incoming_signature:
        body = await request.body()
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare securely
        if not hmac.compare_digest(incoming_signature, expected_signature):
            return JSONResponse(status_code=401, content={"detail": "Invalid signature"})
    
    # Proceed to the next middleware or route
    response = await call_next(request)
    return response