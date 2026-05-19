import os, json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY))

SAMPLE = "Mau order 2 kaos hitam size L, kirim ke Jakarta, bayar BCA"

SYSTEM_PROMPT = (Extract order data as JSON ONLY, Schema:{customer:{name,phone}, items:[{product_name,quantity}], shipping:{city}, payment:{method}}, Return null for missing fields.")

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": SAMPLE}
    ],
    response_format={"type": "json_object"},
    temperature=0.1
)

result = json.loads(response.choices[0].message.content)
print(json.dumps(result, indent=2))
