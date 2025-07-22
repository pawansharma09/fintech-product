import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import hashlib
import sqlite3
from typing import Dict, List, Optional
import io
import base64

# Page config
st.set_page_config(
    page_title="FinanceAI - Smart Money Management",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .sidebar-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-left: 5px solid #007bff;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .ai-insight {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('financeai.db', check_same_thread=False)
        self.init_db()
    
    def init_db(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date TEXT,
                amount REAL,
                category TEXT,
                description TEXT,
                type TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                goal_name TEXT,
                target_amount REAL,
                current_amount REAL,
                target_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()

class OpenRouterAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def get_ai_insights(self, prompt: str, model: str = "microsoft/wizardlm-2-8x22b") -> str:
        """Get AI insights using free models from OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Free models available on OpenRouter
        free_models = [
            "microsoft/wizardlm-2-8x22b",
            "google/gemma-7b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "huggingface/starcoder:free"
        ]
        
        data = {
            "model": model if model in free_models else "microsoft/wizardlm-2-8x22b",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a professional financial advisor AI. Provide helpful, actionable financial advice based on the data provided."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error connecting to AI service: {str(e)}"

class FinanceAI:
    def __init__(self):
        self.db = DatabaseManager()
        if 'openrouter_api' not in st.session_state:
            st.session_state.openrouter_api = None
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        cursor = self.db.conn.cursor()
        password_hash = self.hash_password(password)
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", 
                      (username, password_hash))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def register_user(self, username: str, password: str, email: str) -> bool:
        try:
            cursor = self.db.conn.cursor()
            password_hash = self.hash_password(password)
            cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                          (username, password_hash, email))
            self.db.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def add_transaction(self, user_id: int, date: str, amount: float, 
                       category: str, description: str, trans_type: str):
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, date, amount, category, description, type) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, date, amount, category, description, trans_type))
        self.db.conn.commit()
    
    def get_transactions(self, user_id: int) -> pd.DataFrame:
        query = "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC"
        return pd.read_sql_query(query, self.db.conn, params=(user_id,))
    
    def generate_sample_data(self, user_id: int):
        """Generate sample financial data for demo purposes"""
        sample_transactions = [
            ("2024-07-01", -50.0, "Food", "Grocery shopping", "expense"),
            ("2024-07-02", -25.0, "Transportation", "Gas", "expense"),
            ("2024-07-03", 3000.0, "Salary", "Monthly salary", "income"),
            ("2024-07-05", -100.0, "Entertainment", "Movie night", "expense"),
            ("2024-07-07", -200.0, "Utilities", "Electricity bill", "expense"),
            ("2024-07-10", -75.0, "Food", "Restaurant", "expense"),
            ("2024-07-12", 500.0, "Freelance", "Side project", "income"),
            ("2024-07-15", -300.0, "Shopping", "Clothes", "expense"),
            ("2024-07-18", -60.0, "Health", "Pharmacy", "expense"),
            ("2024-07-20", -150.0, "Insurance", "Car insurance", "expense"),
        ]
        
        cursor = self.db.conn.cursor()
        for date, amount, category, description, trans_type in sample_transactions:
            cursor.execute("""
                INSERT OR IGNORE INTO transactions (user_id, date, amount, category, description, type) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, date, amount, category, description, trans_type))
        
        self.db.conn.commit()

def main():
    app = FinanceAI()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ Settings</div>', unsafe_allow_html=True)
        
        # OpenRouter API Key Input
        api_key = st.text_input("🔑 OpenRouter API Key", type="password", 
                               help="Enter your free OpenRouter API key for AI insights")
        if api_key:
            st.session_state.openrouter_api = OpenRouterAPI(api_key)
        
        if st.session_state.authenticated:
            st.success(f"👋 Welcome, {st.session_state.username}!")
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.rerun()
    
    # Authentication
    if not st.session_state.authenticated:
        st.markdown('<h1 class="main-header">💰 FinanceAI</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your AI-Powered Personal Finance Manager</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Login", use_container_width=True):
                        user_id = app.authenticate_user(username, password)
                        if user_id:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials!")
            
            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Choose Username")
                    new_email = st.text_input("Email")
                    new_password = st.text_input("Choose Password", type="password")
                    if st.form_submit_button("Register", use_container_width=True):
                        if app.register_user(new_username, new_password, new_email):
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Username already exists!")
        
        # Demo credentials info
        st.info("💡 **Demo Mode**: You can create a new account or use the demo features to explore the platform.")
        return
    
    # Main App
    st.markdown('<h1 class="main-header">💰 FinanceAI Dashboard</h1>', unsafe_allow_html=True)
    
    # Navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💳 Transactions", "🎯 Goals", "📈 Analytics", "🤖 AI Insights"])
    
    # Get user transactions
    df = app.get_transactions(st.session_state.user_id)
    
    # Generate sample data if empty
    if df.empty:
        if st.button("🎲 Generate Sample Data (Demo)"):
            app.generate_sample_data(st.session_state.user_id)
            st.rerun()
    
    with tab1:
        # Dashboard Overview
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = pd.to_numeric(df['amount'])
            
            # Key Metrics
            total_income = df[df['amount'] > 0]['amount'].sum()
            total_expenses = abs(df[df['amount'] < 0]['amount'].sum())
            net_worth = total_income - total_expenses
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>💰 Total Income</h3>
                    <h2>${total_income:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>💸 Total Expenses</h3>
                    <h2>${total_expenses:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📊 Net Worth</h3>
                    <h2>${net_worth:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                avg_daily = net_worth / max(1, (df['date'].max() - df['date'].min()).days)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📅 Daily Average</h3>
                    <h2>${avg_daily:.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Expense by category
                expense_by_category = df[df['amount'] < 0].groupby('category')['amount'].sum().abs()
                fig_pie = px.pie(values=expense_by_category.values, 
                               names=expense_by_category.index,
                               title="💳 Expenses by Category")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Income vs Expenses over time
                daily_summary = df.groupby([df['date'].dt.date, 'type'])['amount'].sum().unstack(fill_value=0)
                if 'expense' in daily_summary.columns:
                    daily_summary['expense'] = daily_summary['expense'].abs()
                
                fig_line = go.Figure()
                if 'income' in daily_summary.columns:
                    fig_line.add_trace(go.Scatter(x=daily_summary.index, y=daily_summary['income'], 
                                                mode='lines+markers', name='Income', line=dict(color='green')))
                if 'expense' in daily_summary.columns:
                    fig_line.add_trace(go.Scatter(x=daily_summary.index, y=daily_summary['expense'], 
                                                mode='lines+markers', name='Expenses', line=dict(color='red')))
                fig_line.update_layout(title="💹 Income vs Expenses Trend", xaxis_title="Date", yaxis_title="Amount ($)")
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("📈 Add some transactions to see your dashboard come to life!")
    
    with tab2:
        # Transaction Management
        st.subheader("💳 Add New Transaction")
        
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input("Date", datetime.now().date())
            trans_type = st.selectbox("Type", ["income", "expense"])
            amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
        
        with col2:
            categories = ["Food", "Transportation", "Entertainment", "Utilities", "Shopping", 
                         "Health", "Insurance", "Salary", "Freelance", "Investment", "Other"]
            category = st.selectbox("Category", categories)
            description = st.text_input("Description")
        
        if st.button("➕ Add Transaction", type="primary"):
            final_amount = amount if trans_type == "income" else -amount
            app.add_transaction(st.session_state.user_id, str(trans_date), 
                              final_amount, category, description, trans_type)
            st.success("✅ Transaction added successfully!")
            st.rerun()
        
        # Display transactions
        if not df.empty:
            st.subheader("📋 Recent Transactions")
            display_df = df.copy()
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(display_df[['date', 'category', 'description', 'amount', 'type']], 
                        use_container_width=True)
            
            # Download transactions
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Transactions CSV",
                data=csv,
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with tab3:
        # Financial Goals
        st.subheader("🎯 Set Financial Goals")
        
        col1, col2 = st.columns(2)
        with col1:
            goal_name = st.text_input("Goal Name")
            target_amount = st.number_input("Target Amount ($)", min_value=1.0)
        with col2:
            current_amount = st.number_input("Current Amount ($)", min_value=0.0)
            target_date = st.date_input("Target Date")
        
        if st.button("🎯 Add Goal"):
            cursor = app.db.conn.cursor()
            cursor.execute("""
                INSERT INTO goals (user_id, goal_name, target_amount, current_amount, target_date) 
                VALUES (?, ?, ?, ?, ?)
            """, (st.session_state.user_id, goal_name, target_amount, current_amount, str(target_date)))
            app.db.conn.commit()
            st.success("Goal added successfully!")
        
        # Display goals
        goals_df = pd.read_sql_query("SELECT * FROM goals WHERE user_id = ?", 
                                   app.db.conn, params=(st.session_state.user_id,))
        
        if not goals_df.empty:
            for _, goal in goals_df.iterrows():
                progress = (goal['current_amount'] / goal['target_amount']) * 100
                st.markdown(f"### 🎯 {goal['goal_name']}")
                st.progress(min(progress / 100, 1.0))
                st.markdown(f"**Progress:** ${goal['current_amount']:,.2f} / ${goal['target_amount']:,.2f} ({progress:.1f}%)")
                st.markdown(f"**Target Date:** {goal['target_date']}")
                st.markdown("---")
    
    with tab4:
        # Advanced Analytics
        if not df.empty:
            st.subheader("📈 Advanced Financial Analytics")
            
            # Spending trends
            df['month'] = df['date'].dt.to_period('M')
            monthly_spending = df[df['amount'] < 0].groupby('month')['amount'].sum().abs()
            
            fig_trend = px.line(x=monthly_spending.index.astype(str), y=monthly_spending.values,
                              title="📊 Monthly Spending Trend")
            fig_trend.update_layout(xaxis_title="Month", yaxis_title="Amount ($)")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Category analysis
            col1, col2 = st.columns(2)
            with col1:
                category_stats = df[df['amount'] < 0].groupby('category')['amount'].agg(['sum', 'count']).abs()
                category_stats.columns = ['Total Spent', 'Transaction Count']
                st.subheader("💰 Spending by Category")
                st.dataframe(category_stats.sort_values('Total Spent', ascending=False))
            
            with col2:
                # Weekly spending pattern
                df['day_of_week'] = df['date'].dt.day_name()
                weekly_pattern = df[df['amount'] < 0].groupby('day_of_week')['amount'].sum().abs()
                fig_weekly = px.bar(x=weekly_pattern.index, y=weekly_pattern.values,
                                  title="📅 Spending Pattern by Day of Week")
                st.plotly_chart(fig_weekly, use_container_width=True)
    
    with tab5:
        # AI Insights
        st.subheader("🤖 AI Financial Insights")
        
        if st.session_state.openrouter_api is None:
            st.warning("⚠️ Please enter your OpenRouter API key in the sidebar to access AI insights.")
        elif df.empty:
            st.info("📊 Add some transactions first to get personalized AI insights.")
        else:
            if st.button("🧠 Generate AI Insights", type="primary"):
                with st.spinner("🤖 AI is analyzing your financial data..."):
                    # Prepare data summary for AI
                    summary_data = {
                        "total_income": float(df[df['amount'] > 0]['amount'].sum()),
                        "total_expenses": float(abs(df[df['amount'] < 0]['amount'].sum())),
                        "top_spending_categories": df[df['amount'] < 0].groupby('category')['amount'].sum().abs().nlargest(5).to_dict(),
                        "transaction_count": len(df),
                        "average_transaction": float(df['amount'].mean())
                    }
                    
                    prompt = f"""
                    Analyze this financial data and provide actionable insights:
                    
                    Financial Summary:
                    - Total Income: ${summary_data['total_income']:,.2f}
                    - Total Expenses: ${summary_data['total_expenses']:,.2f}
                    - Net Income: ${summary_data['total_income'] - summary_data['total_expenses']:,.2f}
                    - Top Spending Categories: {summary_data['top_spending_categories']}
                    - Number of Transactions: {summary_data['transaction_count']}
                    
                    Please provide:
                    1. Key financial insights
                    2. Areas for improvement
                    3. Budgeting recommendations
                    4. Savings opportunities
                    
                    Keep it concise and actionable.
                    """
                    
                    insights = st.session_state.openrouter_api.get_ai_insights(prompt)
                    
                    st.markdown(f"""
                    <div class="ai-insight">
                        <h3>🧠 AI Financial Advisor</h3>
                        <p>{insights}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Quick AI tools
            st.subheader("⚡ Quick AI Tools")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💡 Budget Optimization Tips"):
                    if st.session_state.openrouter_api:
                        with st.spinner("Generating tips..."):
                            prompt = "Provide 5 practical budget optimization tips for personal finance management."
                            tips = st.session_state.openrouter_api.get_ai_insights(prompt)
                            st.success(tips)
            
            with col2:
                if st.button("🎯 Savings Goals Advice"):
                    if st.session_state.openrouter_api:
                        with st.spinner("Generating advice..."):
                            prompt = "Provide advice on setting and achieving financial savings goals."
                            advice = st.session_state.openrouter_api.get_ai_insights(prompt)
                            st.success(advice)

if __name__ == "__main__":
    main()
