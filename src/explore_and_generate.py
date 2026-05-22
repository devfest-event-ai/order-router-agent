import pandas as pd
import json
import random
import os

print("🚀 Starting dataset exploration and sample generation...")

# 1. LOAD DATASET
try:
    print("\n⏳ Loading dataset...")
    
    # Coba baca file
    df = pd.read_csv('data/all_months_clean.csv', sep=';')
    print(f"✅ Loaded {len(df)} records")
    
except FileNotFoundError:
    print("❌ Error: File 'data/all_months_clean.csv' not found!")
    print("💡 Please make sure you copied the CSV file to the data/ folder")
    exit()
except Exception as e:
    print(f"❌ Error reading file: {e}")
    print("💡 Trying alternative separators...")
    
    # Coba tanpa separator spesifik
    try:
        df = pd.read_csv('data/all_months_clean.csv')
        print(f"✅ Loaded {len(df)} records (auto-detected separator)")
    except Exception as e2:
        print(f"❌ Still failed: {e2}")
        exit()

# 2. CLEAN COLUMN NAMES
df.columns = df.columns.str.strip()

# Debug: Tampilkan semua kolom yang ada
print(f"\n📊 Available columns ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. '{col}'")

# 3. EXPLORE DATA
print("\n" + "="*60)
print("📈 DATASET OVERVIEW")
print("="*60)
print(f"Total records: {len(df):,}")
print(f"Total columns: {len(df.columns)}")

# 4. CARI KOLOM YANG RELEVAN
# Cari kolom yang mungkin berisi quantity
quantity_cols = [col for col in df.columns if 'jumlah' in col.lower() or 'qty' in col.lower() or 'quantity' in col.lower()]
payment_cols = [col for col in df.columns if 'pembayaran' in col.lower() or 'payment' in col.lower()]
city_cols = [col for col in df.columns if 'kota' in col.lower() or 'city' in col.lower()]
province_cols = [col for col in df.columns if 'provinsi' in col.lower() or 'province' in col.lower()]
status_cols = [col for col in df.columns if 'status' in col.lower()]

print("\n🔍 MAPPED COLUMNS:")
print(f"  Quantity columns: {quantity_cols}")
print(f"  Payment columns: {payment_cols}")
print(f"  City columns: {city_cols}")
print(f"  Province columns: {province_cols}")
print(f"  Status columns: {status_cols}")

# Gunakan kolom yang ditemukan
quantity_col = quantity_cols[0] if quantity_cols else None
payment_col = payment_cols[0] if payment_cols else None
city_col = city_cols[0] if city_cols else None
province_col = province_cols[0] if province_cols else None
status_col = status_cols[0] if status_cols else None

# 5. TAMPILKAN INFO
print("\n" + "="*60)
print("📊 KEY PATTERNS FOR VALIDATION")
print("="*60)

if payment_col:
    print(f"\nPayment Methods ({df[payment_col].nunique()}):")
    for pm in df[payment_col].unique()[:10]:
        print(f"  - {pm}")

if city_col:
    print(f"\nCities: {df[city_col].nunique()} unique cities")
    print(f"Sample: {df[city_col].sample(min(5, len(df))).tolist()}")

if province_col:
    print(f"\nProvinces: {df[province_col].nunique()} unique provinces")

if quantity_col:
    print(f"\nQuantity range: {df[quantity_col].min()} - {df[quantity_col].max()}")

if status_col:
    print(f"\nOrder Statuses: {df[status_col].unique()}")

# 6. GENERATE MESSY SAMPLES
print("\n" + "="*60)
print("🛠️ GENERATING MESSY TEST SAMPLES")
print("="*60)

# Template functions
def to_messy_whatsapp(row):
    product = row.get('product_category', 'Produk') if 'product_category' in row else 'Produk'
    qty = row.get(quantity_col, 1) if quantity_col else 1
    city = row.get(city_col, 'Jakarta') if city_col else 'Jakarta'
    province = row.get(province_col, '') if province_col else ''
    payment = row.get(payment_col, 'COD') if payment_col else 'COD'
    return f"Mau order {qty} {product}, kirim ke {city}, {province}. Bayar {payment}. Urgent!"

def to_messy_email(row):
    order_id = row.get('order_id', 'ORD-XXX')
    product = row.get('product_category', 'Produk') if 'product_category' in row else 'Produk'
    qty = row.get(quantity_col, 1) if quantity_col else 1
    city = row.get(city_col, 'Jakarta') if city_col else 'Jakarta'
    province = row.get(province_col, '') if province_col else ''
    payment = row.get(payment_col, 'COD') if payment_col else 'COD'
    return f"Subject: Order {order_id}\nHalo, saya mau pesan {qty} unit {product}. Kirim ke {city}, {province}. Pembayaran via {payment}. Terima kasih."

def to_messy_marketplace(row):
    order_id = row.get('order_id', 'ORD-XXX')
    product = row.get('product_category', 'Produk') if 'product_category' in row else 'Produk'
    qty = row.get(quantity_col, 1) if quantity_col else 1
    city = row.get(city_col, 'Jakarta') if city_col else 'Jakarta'
    payment = row.get(payment_col, 'COD') if payment_col else 'COD'
    total = row.get('Total Pembayaran', 0) if 'Total Pembayaran' in row else 0
    return f"Order: {order_id} | {product} x{qty} | Ship: {city} | Pay: {payment} | Total: {total}"

templates = [to_messy_whatsapp, to_messy_email, to_messy_marketplace]

# Generate samples
samples = []
sample_rows = df.sample(min(15, len(df)), random_state=42)

for idx, row in sample_rows.iterrows():
    messy_text = random.choice(templates)(row)
    
    sample_data = {
        "messy_input": messy_text,
        "ground_truth": {
            "order_id": row.get("order_id", "N/A"),
        }
    }
    
    # Add product_category if exists
    if 'product_category' in row:
        sample_data["ground_truth"]["product_category"] = row["product_category"]
    
    # Add quantity if found
    if quantity_col:
        sample_data["ground_truth"]["quantity"] = int(row[quantity_col])
    
    # Add location
    if city_col:
        sample_data["ground_truth"]["city"] = row[city_col]
    if province_col:
        sample_data["ground_truth"]["province"] = row[province_col]
    
    # Add payment
    if payment_col:
        sample_data["ground_truth"]["payment_method"] = row[payment_col]
    
    # Add total amount
    if 'Total Pembayaran' in row:
        sample_data["ground_truth"]["total_amount"] = float(row['Total Pembayaran'])
    
    # Add status
    if status_col:
        sample_data["ground_truth"]["status"] = row[status_col]
    
    samples.append(sample_data)

# 7. SAVE TO FILE
os.makedirs("examples", exist_ok=True)
output_file = "examples/messy_samples.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(samples, f, indent=2, ensure_ascii=False)

print(f"\n✅ Generated {len(samples)} messy samples")
print(f"💾 Saved to: {output_file}")

# Show sample
print("\n📝 SAMPLE OUTPUT:")
print("-" * 60)
print(f"Messy Input:\n{samples[0]['messy_input']}\n")
print(f"Ground Truth:\n{json.dumps(samples[0]['ground_truth'], indent=2)}")

print("\n" + "="*60)
print("✨ DONE! Ready for extraction testing")
print("="*60)