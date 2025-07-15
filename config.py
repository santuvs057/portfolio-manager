import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # Database settings
    DATABASE_PATH = "portfolio.db"

    # DeepSeek API settings
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

    # Streamlit settings
    PAGE_TITLE = "SanthoshSwapna Portfolio Manager"
    PAGE_ICON = "💰"
    LAYOUT = "wide"

    # AI Assistant settings
    AI_MODEL = "deepseek-chat"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7

    # Financial categories
    EXPENSE_CATEGORIES = [
        "Food & Dining", "Transportation", "Shopping", "Entertainment",
        "Bills & Utilities", "Healthcare", "Education", "Travel",
        "Investment", "Insurance", "Other"
    ]

    MF_CATEGORIES = [
        "Equity", "Debt", "Hybrid", "Index", "ELSS", "International",
        "Sectoral", "Thematic"
    ]

    STOCK_SECTORS = [
        "Technology", "Healthcare", "Finance", "Energy", "Consumer Goods",
        "Industrial", "Real Estate", "Utilities", "Telecommunications",
        "Materials", "Consumer Services"
    ]

    GOAL_CATEGORIES = [
        "Emergency Fund", "Retirement", "House Purchase", "Car Purchase",
        "Education", "Travel", "Investment", "Business", "Marriage", "Other"
    ]

    # UI Colors and styling
    COLORS = {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8"
    }


# Validate configuration
def validate_config():
    """Validate configuration settings"""
    issues = []

    if not Config.DEEPSEEK_API_KEY:
        issues.append("DEEPSEEK_API_KEY not found in environment variables")

    return issues


# Get custom CSS
def get_custom_css():
    """Return custom CSS for the application"""
    return f"""
    <style>
        .main-header {{
            background: linear-gradient(90deg, {Config.COLORS['primary']} 0%, {Config.COLORS['secondary']} 100%);
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .metric-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {Config.COLORS['primary']};
            margin-bottom: 1rem;
        }}

        .success-msg {{
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid {Config.COLORS['success']};
        }}

        .error-msg {{
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid {Config.COLORS['danger']};
        }}

        .info-msg {{
            background: #d1ecf1;
            color: #0c5460;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid {Config.COLORS['info']};
        }}

        .sidebar-header {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
        }}

        .ai-chat-container {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 12px;
            margin: 1rem 0;
            color: white;
        }}

        .goal-progress {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid {Config.COLORS['info']};
        }}

        .investment-card {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
        }}

        .investment-card:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}

        .stSelectbox > div > div {{
            background: white;
        }}

        .stDateInput > div > div {{
            background: white;
        }}

        .stNumberInput > div > div {{
            background: white;
        }}

        .stTextInput > div > div {{
            background: white;
        }}
    </style>
    """