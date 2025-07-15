import streamlit as st
import pandas as pd
from datetime import datetime
from config import Config


class AIChatInterface:
    def __init__(self, db_manager, ai_advisor, user_id):
        self.db = db_manager
        self.ai_advisor = ai_advisor
        self.user_id = user_id

    def render(self):
        if not Config.DEEPSEEK_API_KEY:
            st.error("🚫 AI Chat requires DeepSeek API key. Please configure it in your .env file.")
            st.code("DEEPSEEK_API_KEY=your_api_key_here")
            return

        # Initialize chat history in session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # AI advisor options
        st.subheader("🤖 AI Financial Advisor")
        st.info("💡 Ask me anything about investments, portfolio analysis, market insights, or financial planning!")

        # Quick action buttons
        st.subheader("⚡ Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Analyze My Portfolio", use_container_width=True):
                self.get_portfolio_analysis()

        with col2:
            if st.button("💡 Investment Advice", use_container_width=True):
                self.get_investment_advice()

        with col3:
            if st.button("📈 Market Insights", use_container_width=True):
                self.get_market_insights()

        # Chat interface
        st.markdown("---")
        st.subheader("💬 Chat with AI Advisor")

        # Display chat history
        self.display_chat_history()

        # Chat input
        user_question = st.text_input(
            "Ask your question:",
            placeholder="e.g., Should I invest in ELSS or PPF for tax saving?",
            key="chat_input"
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("💬 Send", use_container_width=True) and user_question:
                self.process_chat_message(user_question)

        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        # Suggested questions
        st.markdown("---")
        st.subheader("💡 Suggested Questions")

        suggestions = [
            "How should I diversify my portfolio?",
            "What's the best investment for retirement planning?",
            "Should I invest in mutual funds or stocks?",
            "How much emergency fund should I maintain?",
            "Which tax-saving investments are best for me?",
            "How can I reduce my investment risk?",
            "What's the ideal asset allocation for my age?",
            "Should I invest lump sum or through SIP?"
        ]

        col1, col2 = st.columns(2)

        for i, suggestion in enumerate(suggestions):
            col = col1 if i % 2 == 0 else col2

            with col:
                if st.button(f"💡 {suggestion}", key=f"suggestion_{i}"):
                    self.process_chat_message(suggestion)

    def display_chat_history(self):
        """Display the chat history"""
        if st.session_state.chat_history:
            for i, (role, message, timestamp) in enumerate(st.session_state.chat_history):
                if role == "user":
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;">
                        <strong>You:</strong> {message}
                        <br><small>{timestamp}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ai-chat-container">
                        <strong>🤖 AI Advisor:</strong><br>
                        {message}
                        <br><small>{timestamp}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("💬 Start a conversation with your AI advisor!")

    def process_chat_message(self, user_message):
        """Process user message and get AI response"""
        try:
            # Add user message to history
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append(("user", user_message, timestamp))

            # Get portfolio context
            portfolio_context = self.get_portfolio_context()

            # Get AI response
            with st.spinner("🤖 AI is thinking..."):
                ai_response = self.ai_advisor.chat_with_advisor(
                    user_message,
                    self.get_conversation_history(),
                    portfolio_context
                )

            # Add AI response to history
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append(("assistant", ai_response, timestamp))

            # Store in database
            self.store_interaction(user_message, ai_response)

            st.rerun()

        except Exception as e:
            st.error(f"Error getting AI response: {str(e)}")

    def get_portfolio_analysis(self):
        """Get comprehensive portfolio analysis"""
        try:
            portfolio_data = self.get_full_portfolio_data()
            user_data = st.session_state.user_data

            with st.spinner("🤖 AI is analyzing your portfolio..."):
                analysis = self.ai_advisor.analyze_portfolio(portfolio_data, user_data)

            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append(("user", "Analyze my portfolio", timestamp))
            st.session_state.chat_history.append(("assistant", analysis, timestamp))

            self.store_interaction("Analyze my portfolio", analysis)
            st.rerun()

        except Exception as e:
            st.error(f"Error getting portfolio analysis: {str(e)}")

    def get_investment_advice(self):
        """Get investment recommendations"""
        try:
            portfolio_data = self.get_full_portfolio_data()
            user_data = st.session_state.user_data

            with st.spinner("🤖 AI is preparing investment advice..."):
                advice = self.ai_advisor.investment_recommendation(
                    "Provide investment recommendations based on my current portfolio",
                    portfolio_data,
                    user_data
                )

            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append(("user", "Give me investment advice", timestamp))
            st.session_state.chat_history.append(("assistant", advice, timestamp))

            self.store_interaction("Give me investment advice", advice)
            st.rerun()

        except Exception as e:
            st.error(f"Error getting investment advice: {str(e)}")

    def get_market_insights(self):
        """Get current market insights"""
        try:
            # Get user holdings for context
            holdings = []

            # Get mutual fund holdings
            mf_df = self.db.get_dataframe(
                "SELECT fund_name FROM mutual_funds WHERE user_id = ?", (self.user_id,)
            )
            if not mf_df.empty:
                holdings.extend(mf_df['fund_name'].tolist())

            # Get stock holdings
            stocks_df = self.db.get_dataframe(
                "SELECT stock_name FROM stocks WHERE user_id = ?", (self.user_id,)
            )
            if not stocks_df.empty:
                holdings.extend(stocks_df['stock_name'].tolist())

            with st.spinner("🤖 AI is fetching market insights..."):
                insights = self.ai_advisor.market_insights(holdings[:10])  # Limit to 10 holdings

            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append(("user", "Give me market insights", timestamp))
            st.session_state.chat_history.append(("assistant", insights, timestamp))

            self.store_interaction("Give me market insights", insights)
            st.rerun()

        except Exception as e:
            st.error(f"Error getting market insights: {str(e)}")

    def get_portfolio_context(self):
        """Get portfolio context for AI"""
        try:
            portfolio_data = self.get_full_portfolio_data()
            user_data = st.session_state.user_data
            return self.ai_advisor._prepare_portfolio_context(portfolio_data, user_data)
        except:
            return "No portfolio data available"

    def get_full_portfolio_data(self):
        """Get complete portfolio data"""
        return {
            'mutual_funds': self.db.get_dataframe(
                "SELECT * FROM mutual_funds WHERE user_id = ?", (self.user_id,)
            ),
            'stocks': self.db.get_dataframe(
                "SELECT * FROM stocks WHERE user_id = ?", (self.user_id,)
            ),
            'expenses': self.db.get_dataframe(
                "SELECT * FROM expenses WHERE user_id = ?", (self.user_id,)
            ),
            'goals': self.db.get_dataframe(
                "SELECT * FROM goals WHERE user_id = ?", (self.user_id,)
            )
        }

    def get_conversation_history(self):
        """Get recent conversation history for context"""
        recent_history = []
        for role, message, _ in st.session_state.chat_history[-6:]:  # Last 6 messages
            recent_history.append({
                "role": "user" if role == "user" else "assistant",
                "content": message
            })
        return recent_history

    def store_interaction(self, question, response):
        """Store AI interaction in database"""
        try:
            interaction_data = {
                'user_id': self.user_id,
                'question': question,
                'response': response,
                'created_at': datetime.now().isoformat()
            }
            self.db.insert_record('ai_interactions', interaction_data)
        except Exception as e:
            # Don't fail the main functionality if storage fails
            pass