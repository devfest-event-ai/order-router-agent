import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ ERROR: GROQ_API_KEY not found in .env file!")
    exit()

client = Groq(api_key=api_key)

# Sample messy order (Indonesian e-commerce style)
messy_order = """
Mau order 2 Celengan harga 500an, kirim ke Tangerang.
Nama Budi, WA 08123456789. Bayar COD.
"""

# System prompt
SYSTEM_PROMPT = """
Extract order data from Indonesian e-commerce text into JSON format.
Schema: {
  "product_name": "string",
  "quantity": integer,
  "price": integer or null,
  "city": "string",
  "customer_name": "string",
  "phone": "string",
  "payment_method": "string"
}
Return ONLY JSON. Use null for missing fields.
"""

try:
    print("⏳ Calling Groq API...")
    print(f"Using model: llama-3.3-70b-versatile")
    
    # API call - UPDATED MODEL
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # ✅ NEW ACTIVE MODEL
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": messy_order}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    # Parse result
    result = json.loads(response.choices[0].message.content)
    
    print("\n✅ SUCCESS! Extracted data:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to file
    os.makedirs("examples", exist_ok=True)
    with open("examples/output_001.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n💾 Saved to: examples/output_001.json")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Tip: Check https://console.groq.com/docs/models for active models")