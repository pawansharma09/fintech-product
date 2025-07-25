# =============================================================================
# FILE: app.py (Main Streamlit Application)
# LOCATION: root/
# =============================================================================

import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
import pandas as pd
from datetime import datetime, timedelta
import random
import time

# Page configuration
st.set_page_config(
    page_title="🌾 AgroSage - AI Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# FILE: config.py (Configuration Settings)
# LOCATION: root/
# =============================================================================

class Config:
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Model Configuration
    MODEL_NAME = "mistralai/mistral-7b-instruct:free"
    
    # Supported Languages
    LANGUAGES = {
        "English": "en",
        "हिंदी (Hindi)": "hi",
        "मराठी (Marathi)": "mr",
        "தமிழ் (Tamil)": "ta",
        "বাংলা (Bengali)": "bn",
        "ગુજરાતી (Gujarati)": "gu"
    }
    
    # Indian States for Weather
    STATES = [
        "Andhra Pradesh", "Bihar", "Gujarat", "Haryana", "Karnataka",
        "Madhya Pradesh", "Maharashtra", "Punjab", "Rajasthan", "Tamil Nadu",
        "Uttar Pradesh", "West Bengal"
    ]

# =============================================================================
# FILE: utils/llm_handler.py (LLM API Handler)
# LOCATION: utils/
# =============================================================================

class LLMHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = Config.OPENROUTER_BASE_URL
    
    def get_response(self, prompt, language="English"):
        """Get response from OpenRouter API"""
        if not self.api_key:
            return "⚠️ Please configure OpenRouter API key in Streamlit secrets"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"""You are AgroSage, an expert agricultural assistant for Indian farmers. 
        Respond in {language} language. Provide practical, actionable advice specific to Indian farming conditions.
        Keep responses concise but informative. Include local context and traditional knowledge when relevant."""
        
        payload = {
            "model": Config.MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Connection error: {str(e)}"

# =============================================================================
# FILE: utils/knowledge_base.py (Simulated Knowledge Base)
# LOCATION: utils/
# =============================================================================

class KnowledgeBase:
    """Simulated RAG system with Indian agricultural knowledge"""
    
    @staticmethod
    def get_crop_info(crop_name, state=""):
        """Get crop-specific information"""
        crop_db = {
            "rice": {
                "best_season": "Kharif (June-November)",
                "water_requirement": "1200-1500mm",
                "soil_type": "Clay loam, well-drained",
                "fertilizer": "NPK 120:60:40 kg/ha",
                "pests": ["Brown planthopper", "Stem borer", "Leaf folder"]
            },
            "wheat": {
                "best_season": "Rabi (November-April)",
                "water_requirement": "450-650mm",
                "soil_type": "Well-drained loam",
                "fertilizer": "NPK 120:60:40 kg/ha",
                "pests": ["Aphids", "Termites", "Rust diseases"]
            },
            "cotton": {
                "best_season": "Kharif (April-October)",
                "water_requirement": "700-1300mm",
                "soil_type": "Black cotton soil",
                "fertilizer": "NPK 100:50:50 kg/ha",
                "pests": ["Bollworm", "Aphids", "Whitefly"]
            },
            "sugarcane": {
                "best_season": "Year-round",
                "water_requirement": "1800-2500mm",
                "soil_type": "Deep, well-drained soil",
                "fertilizer": "NPK 300:75:75 kg/ha",
                "pests": ["Early shoot borer", "Root borer", "Scale insects"]
            }
        }
        
        return crop_db.get(crop_name.lower(), {
            "message": "Crop information not found. Please consult local agricultural extension officer."
        })
    
    @staticmethod
    def get_government_schemes():
        """Get information about government schemes"""
        schemes = [
            {
                "name": "PM-KISAN",
                "description": "₹6000 per year direct income support",
                "eligibility": "Small and marginal farmers"
            },
            {
                "name": "Pradhan Mantri Fasal Bima Yojana",
                "description": "Crop insurance against natural calamities",
                "eligibility": "All farmers"
            },
            {
                "name": "Kisan Credit Card",
                "description": "Easy access to credit for farming needs",
                "eligibility": "All farmers with land documents"
            },
            {
                "name": "Soil Health Card",
                "description": "Free soil testing and nutrient recommendations",
                "eligibility": "All farmers"
            }
        ]
        return schemes
    
    @staticmethod
    def get_market_prices():
        """Simulated market prices (in real app, would connect to AgriPortal API)"""
        crops = ["Rice", "Wheat", "Cotton", "Sugarcane", "Onion", "Potato", "Tomato"]
        prices = []
        
        for crop in crops:
            base_price = random.randint(1500, 5000)
            prices.append({
                "crop": crop,
                "price": f"₹{base_price}/quintal",
                "market": "Mandal Average",
                "trend": random.choice(["📈 Rising", "📉 Falling", "➖ Stable"])
            })
        
        return prices

# =============================================================================
# FILE: utils/pest_classifier.py (Simulated Image Classification)
# LOCATION: utils/
# =============================================================================

class PestClassifier:
    """Simulated pest/disease classification"""
    
    @staticmethod
    def classify_image(image):
        """Simulate pest/disease classification"""
        # In real implementation, this would use a trained CNN model
        pests = [
            {
                "name": "Brown Planthopper",
                "confidence": 0.85,
                "crop": "Rice",
                "treatment": "Use Imidacloprid 17.8% SL @ 100ml/acre",
                "organic_treatment": "Neem oil spray, encourage natural predators"
            },
            {
                "name": "Aphids",
                "confidence": 0.78,
                "crop": "Multiple crops",
                "treatment": "Thiamethoxam 25% WG @ 100g/acre",
                "organic_treatment": "Soap water spray, ladybird beetles"
            },
            {
                "name": "Leaf Blight",
                "confidence": 0.72,
                "crop": "Wheat",
                "treatment": "Propiconazole 25% EC @ 250ml/acre",
                "organic_treatment": "Copper fungicide, proper spacing"
            }
        ]
        
        return random.choice(pests)

# =============================================================================
# FILE: utils/weather_service.py (Weather Information)
# LOCATION: utils/
# =============================================================================

class WeatherService:
    """Simulated weather service"""
    
    @staticmethod
    def get_weather_forecast(state):
        """Get weather forecast for farming decisions"""
        weather_conditions = ["Sunny", "Partly Cloudy", "Rainy", "Thunderstorm"]
        forecast = []
        
        for i in range(5):
            date = datetime.now() + timedelta(days=i)
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "condition": random.choice(weather_conditions),
                "temp_max": random.randint(25, 40),
                "temp_min": random.randint(15, 25),
                "humidity": random.randint(40, 90),
                "rainfall": random.randint(0, 50) if random.choice([True, False]) else 0
            })
        
        return forecast
    
    @staticmethod
    def get_farming_advice(forecast):
        """Get farming advice based on weather"""
        advice = []
        
        for day in forecast:
            if day["rainfall"] > 20:
                advice.append("Heavy rainfall expected. Avoid spraying pesticides.")
            elif day["temp_max"] > 35:
                advice.append("High temperature. Increase irrigation frequency.")
            elif day["humidity"] > 80:
                advice.append("High humidity. Monitor for fungal diseases.")
            else:
                advice.append("Good weather for field operations.")
        
        return advice

# =============================================================================
# FILE: components/sidebar.py (Sidebar Components)
# LOCATION: components/
# =============================================================================

def render_sidebar():
    """Render sidebar with user preferences"""
    st.sidebar.title("🌾 AgroSage Settings")
    
    # Language Selection
    selected_language = st.sidebar.selectbox(
        "🗣️ Select Language",
        list(Config.LANGUAGES.keys()),
        index=0
    )
    
    # State Selection
    selected_state = st.sidebar.selectbox(
        "📍 Select State",
        Config.STATES,
        index=5  # Default to Madhya Pradesh
    )
    
    # User Profile
    st.sidebar.markdown("---")
    st.sidebar.markdown("👨‍🌾 **Farmer Profile**")
    farm_size = st.sidebar.slider("Farm Size (acres)", 1, 100, 5)
    farming_type = st.sidebar.radio("Farming Type", ["Organic", "Conventional", "Mixed"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("📱 **Quick Actions**")
    if st.sidebar.button("🆘 Emergency Helpline"):
        st.sidebar.success("Kisan Call Center: 1800-180-1551")
    
    return selected_language, selected_state, farm_size, farming_type

# =============================================================================
# FILE: components/chat_interface.py (Chat Interface)
# LOCATION: components/
# =============================================================================

def render_chat_interface(llm_handler, language):
    """Render chat interface"""
    st.header("💬 Ask AgroSage")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Chat input
    user_input = st.chat_input("Ask your farming question...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get AI response
        with st.spinner("AgroSage is thinking..."):
            response = llm_handler.get_response(user_input, language)
        
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# =============================================================================
# FILE: components/image_diagnosis.py (Image Diagnosis Interface)
# LOCATION: components/
# =============================================================================

def render_image_diagnosis():
    """Render image diagnosis interface"""
    st.header("📸 Pest & Disease Diagnosis")
    
    uploaded_file = st.file_uploader(
        "Upload crop/leaf image for diagnosis",
        type=['png', 'jpg', 'jpeg'],
        help="Take a clear photo of affected plant parts"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(image, caption="Uploaded Image", use_container_width=True)
        
        with col2:
            with st.spinner("Analyzing image..."):
                # Simulate analysis delay
                time.sleep(2)
                
                # Get classification result
                result = PestClassifier.classify_image(image)
                
                st.success(f"**Detected:** {result['name']}")
                st.info(f"**Confidence:** {result['confidence']:.0%}")
                st.write(f"**Affected Crop:** {result['crop']}")
                
                st.markdown("### 💊 Treatment Recommendations")
                st.write(f"**Chemical:** {result['treatment']}")
                st.write(f"**Organic:** {result['organic_treatment']}")
                
                # Additional advice
                st.markdown("### 📋 Additional Advice")
                st.write("• Apply treatment during early morning or evening")
                st.write("• Maintain proper field sanitation")
                st.write("• Monitor regularly for re-infestation")

# =============================================================================
# FILE: components/weather_dashboard.py (Weather Dashboard)
# LOCATION: components/
# =============================================================================

def render_weather_dashboard(state):
    """Render weather dashboard"""
    st.header(f"🌤️ Weather Forecast - {state}")
    
    # Get weather data
    forecast = WeatherService.get_weather_forecast(state)
    advice = WeatherService.get_farming_advice(forecast)
    
    # Display forecast
    cols = st.columns(5)
    for i, day in enumerate(forecast):
        with cols[i]:
            st.metric(
                label=day["date"],
                value=f"{day['temp_max']}°C",
                delta=f"{day['temp_min']}°C min"
            )
            st.write(f"🌧️ {day['rainfall']}mm")
            st.write(f"💧 {day['humidity']}% RH")
    
    # Farming advice
    st.markdown("### 🌾 Weather-based Farming Advice")
    for i, tip in enumerate(advice):
        st.write(f"{i+1}. {tip}")

# =============================================================================
# FILE: components/market_info.py (Market Information)
# LOCATION: components/
# =============================================================================

def render_market_info():
    """Render market information"""
    st.header("💰 Market Prices")
    
    prices = KnowledgeBase.get_market_prices()
    
    # Create DataFrame for better display
    df = pd.DataFrame(prices)
    
    # Display as styled table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Price alerts
    st.markdown("### 🔔 Price Alerts")
    selected_crop = st.selectbox("Select crop for price alerts", [p["crop"] for p in prices])
    target_price = st.number_input("Target price (₹/quintal)", min_value=1000, value=3000)
    
    if st.button("Set Price Alert"):
        st.success(f"Price alert set for {selected_crop} at ₹{target_price}/quintal")

# =============================================================================
# FILE: components/government_schemes.py (Government Schemes)
# LOCATION: components/
# =============================================================================

def render_government_schemes():
    """Render government schemes information"""
    st.header("🏛️ Government Schemes")
    
    schemes = KnowledgeBase.get_government_schemes()
    
    for scheme in schemes:
        with st.expander(f"📋 {scheme['name']}"):
            st.write(f"**Description:** {scheme['description']}")
            st.write(f"**Eligibility:** {scheme['eligibility']}")
            st.button(f"Apply for {scheme['name']}", key=f"apply_{scheme['name']}")

# =============================================================================
# FILE: main.py (Main Application Logic)
# LOCATION: root/
# =============================================================================

def main():
    """Main application function"""
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(45deg, #f0f8f0, #e8f5e8);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2E8B57;
    }
    .stButton > button {
        background: linear-gradient(45deg, #2E8B57, #228B22);
        color: white;
        border: none;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🌾 AgroSage - AI Farming Assistant</h1>', unsafe_allow_html=True)
    st.markdown("**Empowering Indian Farmers with AI-driven Agricultural Intelligence**")
    
    # Sidebar
    language, state, farm_size, farming_type = render_sidebar()
    
    # Initialize LLM Handler
    llm_handler = LLMHandler(Config.OPENROUTER_API_KEY)
    
    # Main Navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Chat Assistant", 
        "📸 Pest Diagnosis", 
        "🌤️ Weather", 
        "💰 Market Prices", 
        "🏛️ Govt Schemes",
        "📚 Crop Guide"
    ])
    
    with tab1:
        render_chat_interface(llm_handler, language)
    
    with tab2:
        render_image_diagnosis()
    
    with tab3:
        render_weather_dashboard(state)
    
    with tab4:
        render_market_info()
    
    with tab5:
        render_government_schemes()
    
    with tab6:
        st.header("📚 Crop Information Guide")
        crop_name = st.selectbox("Select Crop", ["Rice", "Wheat", "Cotton", "Sugarcane"])
        
        if crop_name:
            crop_info = KnowledgeBase.get_crop_info(crop_name, state)
            
            if "message" not in crop_info:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🌱 Growing Information")
                    st.write(f"**Best Season:** {crop_info.get('best_season', 'N/A')}")
                    st.write(f"**Water Requirement:** {crop_info.get('water_requirement', 'N/A')}")
                    st.write(f"**Soil Type:** {crop_info.get('soil_type', 'N/A')}")
                
                with col2:
                    st.markdown("### 🧪 Fertilizer & Pests")
                    st.write(f"**Fertilizer:** {crop_info.get('fertilizer', 'N/A')}")
                    st.write("**Common Pests:**")
                    for pest in crop_info.get('pests', []):
                        st.write(f"• {pest}")
            else:
                st.warning(crop_info["message"])
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🌾 AgroSage - Built with ❤️ for Indian Farmers</p>
        <p>📞 Helpline: 1800-180-1551 | 🌐 Digital India Initiative</p>
    </div>
    """, unsafe_allow_html=True)
    
if __name__ == "__main__":
    main()
