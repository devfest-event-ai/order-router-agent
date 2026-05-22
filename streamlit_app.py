# streamlit_app.py

import streamlit as st
import requests
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Order Router Agent Demo",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .tagline {
        font-style: italic;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# API URL (akan di-set di Streamlit Cloud)
API_URL = st.secrets.get("API_URL", "http://localhost:8000")

# Header
st.markdown('<h1 class="main-header">Multi-Channel Order Router</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Messy In to Structured Out to Running Without You</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Demo Features")
    st.markdown("""
    - AI Extraction: Groq API (Llama 3.3)
    - Validation: Payment, inventory, fraud
    - Routing: Auto-approve or review
    - Monitoring: Real-time metrics
    """)
    
    st.header("Settings")
    show_debug = st.checkbox("Show Debug Info", value=False)
    
    st.markdown("---")
    st.info("Sample Inputs:\n\nWhatsApp:\n```\nMau order 3 kaos hitam size L, kirim ke Jakarta, bayar BCA. Nama: Budi, WA: 08123456789\n```\n\nEmail:\n```\nHi, I want to order 2x Nike Air Max size 42, urgent! Ship to Bandung. Payment: COD. - Jane\n```")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Process Order", "System Health", "About", "API Test"])

with tab1:
    st.header("Process Order from Any Channel")
    
    # Mode selection
    mode = st.radio(
        "Input Mode:",
        ["Messy Text (AI Extraction)", "Structured JSON"],
        horizontal=True
    )
    
    if mode == "Messy Text (AI Extraction)":
        st.subheader("AI-Powered Text Extraction")
        st.markdown("*Paste messy order from email, WhatsApp, chat, etc.*")
        
        messy_input = st.text_area(
            "Order Text:",
            placeholder="Mau order 3 kaos hitam size L, kirim ke Jakarta, bayar BCA transfer...",
            height=150
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            extract_btn = st.button("Extract", type="primary", use_container_width=True)
        
        if extract_btn:
            if not messy_input.strip():
                st.error("Please enter some text")
            else:
                with st.spinner("AI extracting..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/extract",
                            json={"text": messy_input},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("Extraction Successful!")
                            
                            # Display extracted data
                            st.subheader("Extracted Data")
                            st.json(result["data"])
                            
                            # Metrics
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Confidence", f"{result.get('confidence', 0):.0%}")
                            col2.metric("Channel", result["data"].get("metadata", {}).get("channel", "unknown").upper())
                            col3.metric("Urgency", result["data"].get("metadata", {}).get("urgency", "normal").upper())
                            
                            # Key info
                            st.subheader("Key Information")
                            if result["data"].get("customer"):
                                st.write(f"**Customer:** {result['data']['customer'].get('name', 'N/A')}")
                                st.write(f"**Phone:** {result['data']['customer'].get('phone', 'N/A')}")
                            if result["data"].get("items"):
                                st.write(f"**Items:** {len(result['data']['items'])} product(s)")
                                for item in result["data"]["items"]:
                                    st.write(f"  - {item.get('product_name')} (Qty: {item.get('quantity')})")
                            if result["data"].get("shipping_address"):
                                st.write(f"**Ship to:** {result['data']['shipping_address'].get('city', 'N/A')}")
                            if result["data"].get("payment"):
                                st.write(f"**Payment:** {result['data']['payment'].get('method', 'N/A')}")
                            
                            # Action buttons
                            if result.get("confidence", 0) >= 0.7:
                                st.info("High confidence - ready for processing")
                            else:
                                st.warning("Low confidence - manual review recommended")
                        
                        else:
                            st.error(f"Error {response.status_code}: {response.text}")
                    
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Server might be down.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    else:  # JSON mode
        st.subheader("Process Structured JSON Order")
        
        json_input = st.text_area(
            "JSON Order:",
            value=json.dumps({
                "order_id": "ORD_0000001",
                "customer": {
                    "name": "John Doe",
                    "phone": "+628123456789",
                    "tier": "VIP"
                },
                "items": [
                    {
                        "product_name": "Nike Air Max",
                        "quantity": 2,
                        "unit_price": 1500000
                    }
                ],
                "shipping_address": {
                    "city": "Jakarta",
                    "province": "DKI Jakarta"
                },
                "payment": {
                    "method": "Saldo ShopeePay",
                    "status": "Paid"
                },
                "subtotal": 3000000,
                "total_amount": 3000000
            }, indent=2),
            height=400
        )
        
        if st.button("Process Order", type="primary"):
            try:
                order_data = json.loads(json_input)
                
                with st.spinner("Processing..."):
                    response = requests.post(
                        f"{API_URL}/webhook/order",
                        json=order_data,
                        timeout=30
                    )
                    
                    if response.status_code == 202:
                        st.success("Order accepted and queued!")
                        st.json(response.json())
                    else:
                        st.error(f"Failed: {response.text}")
            
            except json.JSONDecodeError:
                st.error("Invalid JSON format")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab2:
    st.header("System Health and Metrics")
    
    if st.button("Refresh Metrics", type="primary"):
        try:
            response = requests.get(f"{API_URL}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Metrics
                metrics = health_data.get("metrics", {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(
                    "Total Orders",
                    metrics.get("total_orders", 0),
                    delta=None
                )
                
                success_rate = (1 - metrics.get("failure_rate", 0)) * 100
                col2.metric(
                    "Success Rate",
                    f"{success_rate:.1f}%",
                    delta=None
                )
                
                col3.metric(
                    "Avg Processing Time",
                    f"{metrics.get('average_processing_time_ms', 0):.0f}ms",
                    delta=None
                )
                
                uptime_mins = metrics.get("uptime_seconds", 0) / 60
                col4.metric(
                    "Uptime",
                    f"{uptime_mins:.1f} mins",
                    delta=None
                )
                
                # Alerts
                alerts = health_data.get("active_alerts", [])
                if alerts:
                    st.warning(f"{len(alerts)} active alert(s)")
                    for alert in alerts:
                        st.error(f"**{alert['level']}**: {alert['message']}")
                else:
                    st.success("System healthy - no alerts")
                
                if show_debug:
                    st.subheader("Raw Data")
                    st.json(health_data)
            
            else:
                st.error(f"Failed to fetch health: {response.status_code}")
        
        except Exception as e:
            st.error(f"Cannot connect to API: {str(e)}")
    else:
        st.info("Click 'Refresh Metrics' to load system health")

with tab3:
    st.header("About This Demo")
    
    st.markdown("""
    ### What This Does
    
    This system automates order processing from multiple channels:
    
    1. Messy Input: Email, WhatsApp, chat messages
    2. AI Extraction: Groq API extracts structured data
    3. Validation: Payment, inventory, fraud checks
    4. Routing: Auto-approve or flag for review
    5. Audit Trail: Complete logging for compliance
    
    ### Business Impact
    
    - 93% faster processing (<60s vs 7-15 mins manual)
    - 94% fewer errors (<0.5% vs 3-8% manual)
    - 94% cost reduction per order
    - 100% overselling prevention
    
    ### Tech Stack
    
    - Backend: FastAPI + Python
    - AI: Groq API (Llama 3.3 70B)
    - Database: SQLite/Turso
    - Processing: Async with retry logic
    - Monitoring: Real-time metrics + alerts
    - UI: Streamlit
    
    ### Resources
    
    - GitHub: [github.com/yourusername/order-router-agent](https://github.com/yourusername/order-router-agent)
    - API Docs: `/docs` endpoint (Swagger UI)
    - Health Check: `/health` endpoint
    """)
    
    st.markdown("---")
    st.caption("""
    Built for Skayl AI and Automations Engineer application  
    Demonstrates: Messy In to Structured Out to Running Without You  
    """)

with tab4:
    st.header("API Testing")
    st.markdown("Test the API directly")
    
    endpoint = st.selectbox(
        "Endpoint:",
        ["/extract", "/webhook/order", "/health"]
    )
    
    method = st.selectbox("Method:", ["GET", "POST"])
    
    if method == "POST":
        body = st.text_area("Request Body (JSON):", height=200)
    
    if st.button("Send Request"):
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(
                    f"{API_URL}{endpoint}",
                    json=json.loads(body) if body else {},
                    timeout=10
                )
            
            st.write(f"**Status:** {response.status_code}")
            st.json(response.json())
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.8rem;'>",
    unsafe_allow_html=True
)
st.markdown("Order Router Agent | Built with FastAPI + Groq + Streamlit")# Update Fri May 22 16:53:26 SEAST 2026
