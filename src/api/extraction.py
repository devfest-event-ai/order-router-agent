# src/api/extraction.py

import os
import json
import logging
from groq import Groq
from typing import Dict, Any

logger = logging.getLogger("OrderRouter")

class OrderExtractor:
    """
    Extracts structured order data from messy text using Groq API.
    """
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        self.SYSTEM_PROMPT = """
You are an expert order data extraction specialist. Extract structured order information from messy customer messages (email, WhatsApp, chat).

RULES:
- Extract ONLY what is explicitly mentioned
- Return null for fields you cannot confidently extract
- Do NOT hallucinate or invent data
- Be conservative - better to return null than wrong data

OUTPUT JSON SCHEMA:
{
  "customer": {
    "name": "string or null",
    "phone": "string or null",
    "tier": "VIP|Regular|New"
  },
  "items": [
    {
      "product_name": "string",
      "sku": "string or null",
      "quantity": "integer",
      "unit_price": "number or null"
    }
  ],
  "shipping_address": {
    "city": "string or null",
    "province": "string or null",
    "address": "string or null"
  },
  "payment": {
    "method": "bank_transfer|cod|e_wallet|credit_card or null",
    "details": "string or null"
  },
  "metadata": {
    "channel": "email|whatsapp|chat|unknown",
    "urgency": "normal|urgent",
    "notes": "string or null"
  }
}

INFERENCE RULES:
- Customer tier: "VIP" if mentions repeat/loyal, "New" if first time, else "Regular"
- Urgency: "urgent" if contains: urgent, ASAP, cepat, segera, by Friday/tomorrow
- Payment method mapping:
  * "transfer", "BCA", "Mandiri", "BNI", "BRI" → "bank_transfer"
  * "COD", "bayar di tempat", "cash" → "cod"
  * "GoPay", "OVO", "DANA", "ShopeePay", "LinkAja" → "e_wallet"
  * "kartu kredit", "credit card" → "credit_card"

Return ONLY valid JSON, no explanations.
"""

    def extract(self, messy_text: str) -> Dict[str, Any]:
        """
        Extract structured order from messy text.
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # ← UPDATED!
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": messy_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048
            )
            
            extracted_data = json.loads(response.choices[0].message.content)
            confidence = self._calculate_confidence(extracted_data)
            
            return {
                "success": True,
                "data": extracted_data,
                "confidence": confidence,
                "raw_input": messy_text
            }
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0,
                "raw_input": messy_text
            }
    
    def _calculate_confidence(self, data: Dict) -> float:
    """
    Calculate extraction confidence based on completeness.
    """
    score = 0.0
    max_score = 7.0  # Total maximum possible points
    
    # Customer (max 2 points)
    if data.get("customer", {}).get("name"): 
        score += 1.5
    if data.get("customer", {}).get("phone"): 
        score += 0.5
    
    # Items (max 3 points)
    items = data.get("items", [])
    if items and len(items) > 0:
        score += 1.5
        if items[0].get("product_name"): 
            score += 1
        if items[0].get("quantity"): 
            score += 0.5
    
    # Shipping (max 1 point)
    if data.get("shipping_address", {}).get("city"): 
        score += 1
    
    # Payment (max 1 point)
    if data.get("payment", {}).get("method"): 
        score += 1
    
    # Return confidence capped at 1.0 (100%)
    return min(round(score / max_score, 2), 1.0)

# Global instance
extractor = OrderExtractor()