import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekAIAdvisor:
    """AI-powered financial advisor using DeepSeek API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.base_url = Config.DEEPSEEK_BASE_URL
        self.model = Config.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if not self.api_key:
            logger.warning("DeepSeek API key not provided. AI features will be disabled.")

    def _make_api_call(self, messages: List[Dict], max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Make API call to DeepSeek"""
        if not self.api_key:
            return "AI advisor is not available. Please configure your DeepSeek API key."

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"API call failed: {response.status_code} - {response.text}")
                return f"AI service temporarily unavailable. Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Error making API call: {str(e)}")
            return f"Error connecting to AI service: {str(e)}"

    def analyze_portfolio(self, portfolio_data: Dict, user_preferences: Dict = None) -> str:
        """Analyze user's complete portfolio and provide insights"""

        # Prepare portfolio context
        context = self._prepare_portfolio_context(portfolio_data, user_preferences)

        messages = [
            {
                "role": "system",
                "content": """You are an expert financial advisor specializing in Indian markets. 
                Analyze the portfolio data and provide actionable insights including:
                1. Portfolio diversification analysis
                2. Risk assessment
                3. Asset allocation recommendations
                4. Specific investment suggestions
                5. Areas for improvement

                Be specific, practical, and focus on Indian financial instruments and market conditions.
                Provide numbers and percentages where relevant."""
            },
            {
                "role": "user",
                "content": f"Please analyze this portfolio and provide detailed recommendations:\n\n{context}"
            }
        ]

        return self._make_api_call(messages, max_tokens=2500, temperature=0.6)

    def investment_recommendation(self, user_query: str, portfolio_data: Dict, user_profile: Dict = None) -> str:
        """Provide investment recommendations based on user query"""

        context = self._prepare_portfolio_context(portfolio_data, user_profile)

        messages = [
            {
                "role": "system",
                "content": """You are a certified financial planner specializing in Indian markets. 
                Provide specific, actionable investment advice considering:
                - Current portfolio composition
                - User's risk profile and goals
                - Market conditions
                - Tax implications in India
                - Expense ratios and fund performance

                Always mention specific fund names, stock symbols, or investment options where appropriate.
                Include expected returns, time horizons, and risk levels."""
            },
            {
                "role": "user",
                "content": f"User Question: {user_query}\n\nCurrent Portfolio Context:\n{context}"
            }
        ]

        return self._make_api_call(messages, max_tokens=2000, temperature=0.7)

    def expense_analysis(self, expenses_data: pd.DataFrame, income_data: pd.DataFrame = None) -> str:
        """Analyze spending patterns and provide budgeting advice"""

        expense_summary = self._summarize_expenses(expenses_data)
        income_summary = self._summarize_income(income_data) if income_data is not None else "No income data provided"

        messages = [
            {
                "role": "system",
                "content": """You are a personal finance expert specializing in budgeting and expense management. 
                Analyze the spending patterns and provide:
                1. Spending pattern analysis
                2. Budget recommendations
                3. Areas to reduce expenses
                4. Savings opportunities
                5. Emergency fund suggestions

                Be specific with amounts and percentages. Consider Indian lifestyle and spending patterns."""
            },
            {
                "role": "user",
                "content": f"Expense Analysis:\n{expense_summary}\n\nIncome Summary:\n{income_summary}"
            }
        ]

        return self._make_api_call(messages, max_tokens=1500, temperature=0.6)

    def goal_planning(self, goals_data: pd.DataFrame, current_portfolio: Dict, user_profile: Dict = None) -> str:
        """Provide goal-based financial planning advice"""

        goals_summary = self._summarize_goals(goals_data)
        portfolio_summary = self._summarize_portfolio_for_goals(current_portfolio)

        messages = [
            {
                "role": "system",
                "content": """You are a goal-based financial planning expert. Analyze the user's goals and current portfolio to provide:
                1. Goal prioritization strategy
                2. Investment allocation for each goal
                3. Timeline feasibility analysis
                4. Monthly investment requirements
                5. Specific product recommendations for each goal

                Consider different risk profiles for different time horizons and goals."""
            },
            {
                "role": "user",
                "content": f"Financial Goals:\n{goals_summary}\n\nCurrent Portfolio:\n{portfolio_summary}\n\nUser Profile: {user_profile}"
            }
        ]

        return self._make_api_call(messages, max_tokens=2000, temperature=0.6)

    def market_insights(self, user_holdings: List[str] = None) -> str:
        """Provide current market insights and recommendations"""

        holdings_context = f"User currently holds: {', '.join(user_holdings)}" if user_holdings else "No specific holdings provided"

        messages = [
            {
                "role": "system",
                "content": """You are a market analyst with expertise in Indian equity and mutual fund markets. 
                Provide current market insights including:
                1. Overall market sentiment
                2. Sector-wise opportunities
                3. Interest rate environment impact
                4. Currency and inflation considerations
                5. Specific opportunities in mutual funds and stocks

                Focus on actionable insights for retail investors."""
            },
            {
                "role": "user",
                "content": f"Please provide current market insights and investment opportunities. {holdings_context}"
            }
        ]

        return self._make_api_call(messages, max_tokens=1800, temperature=0.7)

    def tax_optimization(self, portfolio_data: Dict, user_income: float = None) -> str:
        """Provide tax optimization strategies"""

        portfolio_context = self._prepare_tax_context(portfolio_data, user_income)

        messages = [
            {
                "role": "system",
                "content": """You are a tax planning expert specializing in Indian tax laws. 
                Provide tax optimization strategies including:
                1. Section 80C investment opportunities
                2. ELSS vs other tax-saving options
                3. Capital gains optimization
                4. Tax-efficient withdrawal strategies
                5. Long-term tax planning

                Be specific about tax implications and savings amounts."""
            },
            {
                "role": "user",
                "content": f"Portfolio and Tax Context:\n{portfolio_context}"
            }
        ]

        return self._make_api_call(messages, max_tokens=1500, temperature=0.6)

    def risk_assessment(self, portfolio_data: Dict, user_profile: Dict = None) -> str:
        """Assess portfolio risk and provide risk management advice"""

        risk_context = self._prepare_risk_context(portfolio_data, user_profile)

        messages = [
            {
                "role": "system",
                "content": """You are a risk management expert for investment portfolios. 
                Analyze the portfolio risk and provide:
                1. Overall risk assessment (Low/Medium/High)
                2. Concentration risk analysis
                3. Market risk exposure
                4. Risk mitigation strategies
                5. Hedging recommendations if needed

                Provide specific risk percentages and actionable risk management steps."""
            },
            {
                "role": "user",
                "content": f"Portfolio Risk Analysis:\n{risk_context}"
            }
        ]

        return self._make_api_call(messages, max_tokens=1500, temperature=0.6)

    def chat_with_advisor(self, user_message: str, conversation_history: List[Dict] = None,
                          portfolio_context: str = "") -> str:
        """General chat interface with the AI advisor"""

        messages = [
            {
                "role": "system",
                "content": f"""You are a friendly and knowledgeable financial advisor. 
                Help users with their financial questions, providing practical and actionable advice.

                User's Portfolio Context: {portfolio_context}

                Always be helpful, encouraging, and provide specific actionable advice when possible."""
            }
        ]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-5:])  # Keep last 5 exchanges

        messages.append({
            "role": "user",
            "content": user_message
        })

        return self._make_api_call(messages, max_tokens=1500, temperature=0.8)

    def _prepare_portfolio_context(self, portfolio_data: Dict, user_preferences: Dict = None) -> str:
        """Prepare portfolio context for AI analysis"""
        context = "PORTFOLIO ANALYSIS:\n"

        # Mutual Funds Analysis
        if 'mutual_funds' in portfolio_data and not portfolio_data['mutual_funds'].empty:
            mf_df = portfolio_data['mutual_funds']
            total_mf_investment = mf_df['amount_invested'].sum()

            context += f"\nMUTUAL FUNDS (Total Investment: ₹{total_mf_investment:,.2f}):\n"

            # Category-wise breakdown
            category_breakdown = mf_df.groupby('category')['amount_invested'].sum()
            for category, amount in category_breakdown.items():
                percentage = (amount / total_mf_investment) * 100
                context += f"- {category}: ₹{amount:,.2f} ({percentage:.1f}%)\n"

            # Top holdings
            top_funds = mf_df.nlargest(5, 'amount_invested')[['fund_name', 'amount_invested', 'category']]
            context += "\nTop 5 Mutual Fund Holdings:\n"
            for _, fund in top_funds.iterrows():
                context += f"- {fund['fund_name']}: ₹{fund['amount_invested']:,.2f} ({fund['category']})\n"

        # Stocks Analysis
        if 'stocks' in portfolio_data and not portfolio_data['stocks'].empty:
            stocks_df = portfolio_data['stocks']
            stocks_df['total_value'] = stocks_df['quantity'] * stocks_df['purchase_price']
            total_stocks_investment = stocks_df['total_value'].sum()

            context += f"\nSTOCKS (Total Investment: ₹{total_stocks_investment:,.2f}):\n"

            # Sector-wise breakdown
            sector_breakdown = stocks_df.groupby('sector')['total_value'].sum()
            for sector, amount in sector_breakdown.items():
                percentage = (amount / total_stocks_investment) * 100
                context += f"- {sector}: ₹{amount:,.2f} ({percentage:.1f}%)\n"

            # Top holdings
            top_stocks = stocks_df.nlargest(5, 'total_value')[['stock_name', 'quantity', 'purchase_price', 'sector']]
            context += "\nTop 5 Stock Holdings:\n"
            for _, stock in top_stocks.iterrows():
                value = stock['quantity'] * stock['purchase_price']
                context += f"- {stock['stock_name']}: {stock['quantity']} shares @ ₹{stock['purchase_price']} = ₹{value:,.2f} ({stock['sector']})\n"

        # Goals Analysis
        if 'goals' in portfolio_data and not portfolio_data['goals'].empty:
            goals_df = portfolio_data['goals']
            context += f"\nFINANCIAL GOALS:\n"
            for _, goal in goals_df.iterrows():
                progress = (goal['current_amount'] / goal['target_amount']) * 100
                context += f"- {goal['goal_name']}: ₹{goal['current_amount']:,.0f}/₹{goal['target_amount']:,.0f} ({progress:.1f}%) - Target: {goal['target_date']}\n"

        # User Preferences
        if user_preferences:
            context += f"\nUSER PROFILE:\n"
            context += f"- Risk Tolerance: {user_preferences.get('risk_tolerance', 'Not specified')}\n"
            context += f"- Investment Goal: {user_preferences.get('investment_goal', 'Not specified')}\n"
            context += f"- Monthly Income: ₹{user_preferences.get('monthly_income', 0):,.2f}\n"
            context += f"- Monthly Expenses: ₹{user_preferences.get('monthly_expenses', 0):,.2f}\n"

        return context

    def _summarize_expenses(self, expenses_df: pd.DataFrame) -> str:
        """Summarize expense data for AI analysis"""
        if expenses_df.empty:
            return "No expense data available"

        summary = "EXPENSE ANALYSIS:\n"

        # Filter only expenses (not income)
        expenses_only = expenses_df[expenses_df['type'] == 'expense']

        if not expenses_only.empty:
            total_expenses = expenses_only['amount'].sum()
            summary += f"Total Monthly Expenses: ₹{total_expenses:,.2f}\n\n"

            # Category-wise breakdown
            category_breakdown = expenses_only.groupby('category')['amount'].sum().sort_values(ascending=False)
            summary += "Category-wise Breakdown:\n"
            for category, amount in category_breakdown.items():
                percentage = (amount / total_expenses) * 100
                summary += f"- {category}: ₹{amount:,.2f} ({percentage:.1f}%)\n"

            # Recent high expenses
            recent_high = expenses_only.nlargest(5, 'amount')[['description', 'amount', 'category', 'date']]
            summary += "\nTop 5 Expenses:\n"
            for _, expense in recent_high.iterrows():
                summary += f"- {expense['description']}: ₹{expense['amount']:,.2f} ({expense['category']}) on {expense['date']}\n"

        return summary

    def _summarize_income(self, income_df: pd.DataFrame) -> str:
        """Summarize income data for AI analysis"""
        if income_df.empty:
            return "No income data available"

        income_only = income_df[income_df['type'] == 'income']
        if income_only.empty:
            return "No income data available"

        total_income = income_only['amount'].sum()
        summary = f"Total Monthly Income: ₹{total_income:,.2f}\n"

        # Income sources
        income_sources = income_only.groupby('category')['amount'].sum()
        summary += "Income Sources:\n"
        for source, amount in income_sources.items():
            percentage = (amount / total_income) * 100
            summary += f"- {source}: ₹{amount:,.2f} ({percentage:.1f}%)\n"

        return summary

    def _summarize_goals(self, goals_df: pd.DataFrame) -> str:
        """Summarize financial goals for AI analysis"""
        if goals_df.empty:
            return "No financial goals set"

        summary = "FINANCIAL GOALS SUMMARY:\n"

        total_target = goals_df['target_amount'].sum()
        total_current = goals_df['current_amount'].sum()
        overall_progress = (total_current / total_target) * 100

        summary += f"Overall Progress: ₹{total_current:,.0f}/₹{total_target:,.0f} ({overall_progress:.1f}%)\n\n"

        # Individual goals
        for _, goal in goals_df.iterrows():
            progress = (goal['current_amount'] / goal['target_amount']) * 100
            days_left = (pd.to_datetime(goal['target_date']).date() - datetime.now().date()).days

            summary += f"Goal: {goal['goal_name']}\n"
            summary += f"- Target: ₹{goal['target_amount']:,.0f} by {goal['target_date']}\n"
            summary += f"- Current: ₹{goal['current_amount']:,.0f} ({progress:.1f}%)\n"
            summary += f"- Time Remaining: {days_left} days\n"
            summary += f"- Category: {goal['category']}, Priority: {goal.get('priority', 'Medium')}\n\n"

        return summary

    def _summarize_portfolio_for_goals(self, portfolio_data: Dict) -> str:
        """Summarize portfolio specifically for goal planning"""
        summary = "CURRENT PORTFOLIO FOR GOAL PLANNING:\n"

        total_investments = 0

        # Mutual funds
        if 'mutual_funds' in portfolio_data and not portfolio_data['mutual_funds'].empty:
            mf_total = portfolio_data['mutual_funds']['amount_invested'].sum()
            total_investments += mf_total
            summary += f"Mutual Funds: ₹{mf_total:,.2f}\n"

        # Stocks
        if 'stocks' in portfolio_data and not portfolio_data['stocks'].empty:
            stocks_df = portfolio_data['stocks']
            stocks_total = (stocks_df['quantity'] * stocks_df['purchase_price']).sum()
            total_investments += stocks_total
            summary += f"Stocks: ₹{stocks_total:,.2f}\n"

        summary += f"Total Current Investments: ₹{total_investments:,.2f}\n"

        return summary

    def _prepare_tax_context(self, portfolio_data: Dict, user_income: float = None) -> str:
        """Prepare tax-related context for AI analysis"""
        context = "TAX OPTIMIZATION ANALYSIS:\n"

        if user_income:
            context += f"Annual Income: ₹{user_income:,.2f}\n"

            # Determine tax bracket
            if user_income <= 250000:
                tax_bracket = "0% (Below taxable limit)"
            elif user_income <= 500000:
                tax_bracket = "5%"
            elif user_income <= 750000:
                tax_bracket = "10%"
            elif user_income <= 1000000:
                tax_bracket = "15%"
            elif user_income <= 1250000:
                tax_bracket = "20%"
            elif user_income <= 1500000:
                tax_bracket = "25%"
            else:
                tax_bracket = "30%"

            context += f"Tax Bracket: {tax_bracket}\n\n"

        # ELSS investments
        if 'mutual_funds' in portfolio_data and not portfolio_data['mutual_funds'].empty:
            mf_df = portfolio_data['mutual_funds']
            elss_investments = mf_df[mf_df['category'] == 'ELSS']['amount_invested'].sum()
            context += f"Current ELSS Investments: ₹{elss_investments:,.2f}\n"
            remaining_80c = max(0, 150000 - elss_investments)
            context += f"Remaining 80C Limit: ₹{remaining_80c:,.2f}\n"

        return context

    def _prepare_risk_context(self, portfolio_data: Dict, user_profile: Dict = None) -> str:
        """Prepare risk analysis context"""
        context = "RISK ANALYSIS:\n"

        total_investment = 0
        equity_exposure = 0
        debt_exposure = 0

        # Mutual funds risk analysis
        if 'mutual_funds' in portfolio_data and not portfolio_data['mutual_funds'].empty:
            mf_df = portfolio_data['mutual_funds']
            mf_total = mf_df['amount_invested'].sum()
            total_investment += mf_total

            equity_funds = mf_df[mf_df['category'].isin(['Equity', 'ELSS'])]['amount_invested'].sum()
            debt_funds = mf_df[mf_df['category'] == 'Debt']['amount_invested'].sum()

            equity_exposure += equity_funds
            debt_exposure += debt_funds

        # Stocks risk analysis
        if 'stocks' in portfolio_data and not portfolio_data['stocks'].empty:
            stocks_df = portfolio_data['stocks']
            stocks_total = (stocks_df['quantity'] * stocks_df['purchase_price']).sum()
            total_investment += stocks_total
            equity_exposure += stocks_total  # All stocks are equity

        if total_investment > 0:
            equity_percentage = (equity_exposure / total_investment) * 100
            debt_percentage = (debt_exposure / total_investment) * 100

            context += f"Total Portfolio Value: ₹{total_investment:,.2f}\n"
            context += f"Equity Exposure: {equity_percentage:.1f}%\n"
            context += f"Debt Exposure: {debt_percentage:.1f}%\n"
            context += f"Other/Cash: {100 - equity_percentage - debt_percentage:.1f}%\n"

        if user_profile:
            context += f"\nUser Risk Profile: {user_profile.get('risk_tolerance', 'Not specified')}\n"
            context += f"Investment Horizon: {user_profile.get('investment_goal', 'Not specified')}\n"

        return context