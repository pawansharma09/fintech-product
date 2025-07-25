# =============================================================================
# File: app.py (Root directory)
# PolicyPal - GenAI Compliance Navigator for Global Startups
# =============================================================================

import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import base64
from io import BytesIO
import zipfile

# =============================================================================
# File: config/settings.py
# Configuration and Constants
# =============================================================================

# Jurisdiction-specific compliance frameworks
JURISDICTIONS = {
    "European Union": {
        "primary_law": "GDPR",
        "risk_factors": ["data_transfer", "consent_mechanism", "data_retention"],
        "required_sections": ["data_controller", "legal_basis", "data_subject_rights", "dpo_contact"]
    },
    "United States": {
        "primary_law": "CCPA/HIPAA",
        "risk_factors": ["healthcare_data", "financial_data", "state_laws"],
        "required_sections": ["privacy_notice", "opt_out_rights", "data_sale_disclosure"]
    },
    "India": {
        "primary_law": "DPDP Act 2023",
        "risk_factors": ["consent_management", "cross_border_transfer", "data_localization"],
        "required_sections": ["data_fiduciary", "consent_notice", "grievance_officer"]
    },
    "United Kingdom": {
        "primary_law": "UK GDPR",
        "risk_factors": ["post_brexit_adequacy", "ico_compliance", "data_transfer"],
        "required_sections": ["lawful_basis", "data_protection_officer", "breach_notification"]
    }
}

BUSINESS_TYPES = {
    "SaaS Platform": ["user_data", "payment_processing", "analytics"],
    "E-commerce": ["customer_data", "payment_processing", "marketing", "shipping"],
    "HealthTech": ["health_data", "hipaa_compliance", "patient_records"],
    "FinTech": ["financial_data", "pci_compliance", "transaction_records"],
    "EdTech": ["student_data", "coppa_compliance", "learning_analytics"],
    "IoT/Hardware": ["device_data", "location_tracking", "sensor_data"]
}

# =============================================================================
# File: utils/llm_client.py
# OpenRouter LLM Integration
# =============================================================================

class LLMClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, messages: List[Dict], model: str = "anthropic/claude-3-haiku") -> str:
        """Generate response using OpenRouter API"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            st.error(f"LLM API Error: {str(e)}")
            return "Error generating response. Please check your API key and try again."

# =============================================================================
# File: components/policy_generator.py
# Core Policy Generation Logic
# =============================================================================

class PolicyGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def generate_privacy_policy(self, jurisdiction: str, business_type: str, 
                              company_details: Dict, data_practices: Dict) -> str:
        """Generate comprehensive privacy policy"""
        
        jurisdiction_info = JURISDICTIONS.get(jurisdiction, {})
        business_info = BUSINESS_TYPES.get(business_type, [])
        
        prompt = f"""
        Generate a comprehensive privacy policy for a {business_type} startup operating in {jurisdiction}.
        
        Company Details:
        - Company Name: {company_details.get('name', 'Your Company')}
        - Website: {company_details.get('website', 'yourcompany.com')}
        - Contact Email: {company_details.get('email', 'privacy@yourcompany.com')}
        - Address: {company_details.get('address', 'Company Address')}
        
        Data Practices:
        - Data Collection: {data_practices.get('collection', [])}
        - Data Usage: {data_practices.get('usage', [])}
        - Third-party Sharing: {data_practices.get('sharing', 'No')}
        - Data Retention: {data_practices.get('retention', '12 months')}
        - Cookies Used: {data_practices.get('cookies', 'Essential only')}
        
        Legal Framework: {jurisdiction_info.get('primary_law', 'General Privacy Laws')}
        Required Sections: {jurisdiction_info.get('required_sections', [])}
        
        Generate a complete, legally-compliant privacy policy with:
        1. Clear, plain language explanations
        2. All required sections for {jurisdiction}
        3. Specific clauses for {business_type} businesses
        4. Contact information and grievance procedures
        5. Data subject rights and procedures
        
        Format the output in clean markdown with proper headers and sections.
        """
        
        messages = [
            {"role": "system", "content": "You are a legal compliance expert specializing in privacy laws. Generate accurate, comprehensive privacy policies that comply with local regulations."},
            {"role": "user", "content": prompt}
        ]
        
        return self.llm_client.generate_response(messages)
    
    def generate_cookie_banner(self, jurisdiction: str, cookie_types: List[str]) -> str:
        """Generate cookie banner content"""
        
        prompt = f"""
        Generate a cookie banner/notice for a website operating in {jurisdiction}.
        
        Cookie Types Used:
        {', '.join(cookie_types)}
        
        Requirements:
        - Compliant with {JURISDICTIONS.get(jurisdiction, {}).get('primary_law', 'privacy laws')}
        - Clear consent mechanism
        - Easy opt-out options
        - Mobile-friendly text
        
        Provide both the banner text and technical implementation guidance.
        """
        
        messages = [
            {"role": "system", "content": "You are a privacy compliance expert. Generate user-friendly cookie notices that meet legal requirements."},
            {"role": "user", "content": prompt}
        ]
        
        return self.llm_client.generate_response(messages)
    
    def assess_compliance_risk(self, jurisdiction: str, business_type: str, 
                             data_practices: Dict) -> Dict:
        """Assess compliance risk level"""
        
        risk_factors = JURISDICTIONS.get(jurisdiction, {}).get('risk_factors', [])
        business_risks = BUSINESS_TYPES.get(business_type, [])
        
        prompt = f"""
        Assess the privacy compliance risk for a {business_type} operating in {jurisdiction}.
        
        Data Practices:
        {json.dumps(data_practices, indent=2)}
        
        Key Risk Factors for {jurisdiction}:
        {', '.join(risk_factors)}
        
        Business-Specific Risks:
        {', '.join(business_risks)}
        
        Provide:
        1. Overall Risk Level (Low/Medium/High)
        2. Top 3 specific risk areas
        3. Immediate action items
        4. Compliance timeline recommendations
        
        Format as JSON with clear structure.
        """
        
        messages = [
            {"role": "system", "content": "You are a privacy risk assessment expert. Provide accurate risk evaluations and actionable recommendations."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.generate_response(messages)
        
        # Parse JSON response or return structured fallback
        try:
            return json.loads(response)
        except:
            return {
                "risk_level": "Medium",
                "risk_areas": ["Data retention policies", "Consent mechanisms", "Third-party integrations"],
                "action_items": ["Review data retention", "Implement consent management", "Audit third-party services"],
                "timeline": "3-6 months for full compliance"
            }

# =============================================================================
# File: components/document_exporter.py
# Document Export Functionality
# =============================================================================

class DocumentExporter:
    @staticmethod
    def create_download_package(documents: Dict[str, str], company_name: str) -> BytesIO:
        """Create a ZIP file with all generated documents"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc_name, content in documents.items():
                # Clean filename
                filename = f"{doc_name.lower().replace(' ', '_')}.md"
                zip_file.writestr(filename, content)
            
            # Add a README
            readme_content = f"""
# {company_name} - Privacy Compliance Package

Generated on: {datetime.now().strftime("%B %d, %Y")}

## Contents:
{chr(10).join([f"- {name}" for name in documents.keys()])}

## Next Steps:
1. Review all documents with legal counsel
2. Customize placeholder content
3. Implement technical requirements
4. Test consent mechanisms
5. Train your team on privacy procedures

## Disclaimer:
These documents are generated for informational purposes. 
Please consult with qualified legal counsel before implementation.
"""
            zip_file.writestr("README.md", readme_content)
        
        zip_buffer.seek(0)
        return zip_buffer

# =============================================================================
# File: main.py (Streamlit App)
# Main Application Interface
# =============================================================================

def initialize_session_state():
    """Initialize session state variables"""
    if 'documents' not in st.session_state:
        st.session_state.documents = {}
    if 'risk_assessment' not in st.session_state:
        st.session_state.risk_assessment = {}

def main():
    st.set_page_config(
        page_title="PolicyPal - AI Compliance Navigator",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    
    # Header
    st.title("🛡️ PolicyPal")
    st.subheader("AI-Powered Compliance Navigator for Global Startups")
    st.markdown("---")
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Configuration")
    
    # API Key Input
    api_key = st.sidebar.text_input(
        "OpenRouter API Key",
        type="password",
        help="Get your free API key from openrouter.ai"
    )
    
    if not api_key:
        st.warning("Please enter your OpenRouter API key in the sidebar to continue.")
        st.info("🔗 Get your free API key at [openrouter.ai](https://openrouter.ai)")
        return
    
    # Initialize clients
    llm_client = LLMClient(api_key)
    policy_generator = PolicyGenerator(llm_client)
    
    # Main Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🌍 Business Details")
        
        jurisdiction = st.selectbox(
            "Operating Jurisdiction",
            list(JURISDICTIONS.keys()),
            help="Primary jurisdiction where your business operates"
        )
        
        business_type = st.selectbox(
            "Business Type",
            list(BUSINESS_TYPES.keys()),
            help="Your primary business model"
        )
        
        # Company Details
        with st.expander("Company Information"):
            company_name = st.text_input("Company Name", value="Your Startup Inc.")
            website = st.text_input("Website", value="yourcompany.com")
            email = st.text_input("Privacy Contact Email", value="privacy@yourcompany.com")
            address = st.text_area("Business Address", value="123 Business St, City, Country")
    
    with col2:
        st.header("📊 Data Practices")
        
        # Data Collection
        data_collection = st.multiselect(
            "What data do you collect?",
            ["Email addresses", "Names", "Phone numbers", "Location data", 
             "Payment information", "Usage analytics", "Device information", 
             "Health data", "Financial data", "Biometric data"],
            default=["Email addresses", "Usage analytics"]
        )
        
        # Data Usage
        data_usage = st.multiselect(
            "How do you use this data?",
            ["Service provision", "Marketing", "Analytics", "Customer support",
             "Legal compliance", "Security", "Product improvement", "Research"],
            default=["Service provision", "Analytics"]
        )
        
        # Additional practices
        third_party_sharing = st.radio(
            "Do you share data with third parties?",
            ["No", "Yes - Service providers only", "Yes - Marketing partners", "Yes - Data brokers"]
        )
        
        data_retention = st.selectbox(
            "Data retention period",
            ["6 months", "12 months", "24 months", "As long as legally required", "Indefinitely"]
        )
        
        cookie_types = st.multiselect(
            "Cookie types used",
            ["Essential", "Analytics", "Marketing", "Personalization", "Social media"],
            default=["Essential", "Analytics"]
        )
    
    # Generate Documents
    st.markdown("---")
    st.header("📄 Generate Compliance Documents")
    
    col1, col2, col3 = st.columns(3)
    
    company_details = {
        'name': company_name,
        'website': website,
        'email': email,
        'address': address
    }
    
    data_practices = {
        'collection': data_collection,
        'usage': data_usage,
        'sharing': third_party_sharing,
        'retention': data_retention,
        'cookies': cookie_types
    }
    
    with col1:
        if st.button("📋 Generate Privacy Policy", type="primary"):
            with st.spinner("Generating privacy policy..."):
                policy = policy_generator.generate_privacy_policy(
                    jurisdiction, business_type, company_details, data_practices
                )
                st.session_state.documents['Privacy Policy'] = policy
    
    with col2:
        if st.button("🍪 Generate Cookie Banner", type="primary"):
            with st.spinner("Generating cookie banner..."):
                banner = policy_generator.generate_cookie_banner(jurisdiction, cookie_types)
                st.session_state.documents['Cookie Banner'] = banner
    
    with col3:
        if st.button("⚠️ Assess Compliance Risk", type="primary"):
            with st.spinner("Assessing compliance risk..."):
                risk = policy_generator.assess_compliance_risk(
                    jurisdiction, business_type, data_practices
                )
                st.session_state.risk_assessment = risk
    
    # Display Results
    if st.session_state.documents or st.session_state.risk_assessment:
        st.markdown("---")
        st.header("📊 Results")
        
        # Risk Assessment Display
        if st.session_state.risk_assessment:
            st.subheader("🎯 Compliance Risk Assessment")
            
            risk_data = st.session_state.risk_assessment
            
            # Risk level with color coding
            risk_level = risk_data.get('risk_level', 'Medium')
            risk_colors = {'Low': 'green', 'Medium': 'orange', 'High': 'red'}
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Risk Level", risk_level, delta=None)
                st.markdown(f"<span style='color: {risk_colors.get(risk_level, 'gray')}'>{risk_level} Risk</span>", 
                           unsafe_allow_html=True)
            
            with col2:
                st.write("**Top Risk Areas:**")
                for area in risk_data.get('risk_areas', [])[:3]:
                    st.write(f"• {area}")
            
            with col3:
                st.write("**Action Items:**")
                for item in risk_data.get('action_items', [])[:3]:
                    st.write(f"• {item}")
            
            if 'timeline' in risk_data:
                st.info(f"**Recommended Timeline:** {risk_data['timeline']}")
        
        # Documents Display
        for doc_name, content in st.session_state.documents.items():
            st.subheader(f"📄 {doc_name}")
            
            # Display content in expandable section
            with st.expander(f"View {doc_name}", expanded=False):
                st.markdown(content)
            
            # Download individual document
            st.download_button(
                label=f"📥 Download {doc_name}",
                data=content,
                file_name=f"{doc_name.lower().replace(' ', '_')}.md",
                mime="text/markdown"
            )
        
        # Download All Documents
        if st.session_state.documents:
            st.markdown("---")
            
            # Create download package
            documents_package = DocumentExporter.create_download_package(
                st.session_state.documents, 
                company_name
            )
            
            st.download_button(
                label="📦 Download Complete Compliance Package",
                data=documents_package.getvalue(),
                file_name=f"{company_name.lower().replace(' ', '_')}_compliance_package.zip",
                mime="application/zip",
                type="primary"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🛡️ PolicyPal - Built with ❤️ for startup compliance</p>
        <p><small>⚠️ Disclaimer: Generated documents are for informational purposes. 
        Please consult qualified legal counsel before implementation.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
