import requests
import json

print("=" * 60)
print("Testing AI Extraction Endpoint")
print("=" * 60)

url = "http://localhost:8000/extract"

# Test case 1: WhatsApp order
test_data = {
    "text": "Mau order 3 kaos hitam size L, kirim ke Jakarta, bayar BCA. Nama: Budi, WA: 08123456789"
}

print(f"\n📤 Sending to: {url}")
print(f"📝 Input text: {test_data['text'][:50]}...")

try:
    response = requests.post(url, json=test_data, timeout=30)
    
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n📋 Extracted Data:")
        print(json.dumps(result, indent=2))
        
        # Show key info
        print("\n🎯 Key Information:")
        if result.get('data', {}).get('customer'):
            print(f"  • Customer: {result['data']['customer'].get('name')}")
            print(f"  • Phone: {result['data']['customer'].get('phone')}")
        if result.get('data', {}).get('items'):
            print(f"  • Items: {len(result['data']['items'])} product(s)")
        print(f"  • Confidence: {result.get('confidence', 0):.0%}")
    else:
        print(f"\n❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to server!")
    print("   Make sure server is running: uvicorn src.api.webhook:app --reload")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")