import streamlit as st
import sys
import os

# Add modules directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import configuration and modules
from config import Config, validate_config, get_custom_css
from modules.database import DatabaseManager
from modules.auth import AuthManager, init_session_state, login_page, logout
from modules.ai_advisor import DeepSeekAIAdvisor

# Page configuration
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


class PortfolioApp:
    """Main application class"""

    def __init__(self):
        self.db_manager = DatabaseManager(Config.DATABASE_PATH)
        self.auth_manager = AuthManager(self.db_manager)
        self.ai_advisor = DeepSeekAIAdvisor()

        # Validate configuration
        config_issues = validate_config()
        if config_issues:
            st.sidebar.warning("⚠️ Configuration Issues:")
            for issue in config_issues:
                st.sidebar.warning(f"• {issue}")

    def run(self):
        """Run the main application"""
        init_session_state()

        # Check authentication
        if not st.session_state.authenticated:
            login_page(self.auth_manager)
            return

        # Main application interface
        self.render_sidebar()
        self.render_main_content()

    def render_sidebar(self):
        """Render the navigation sidebar"""
        user_data = st.session_state.user_data

        # User info section
        st.sidebar.markdown(f"""
        <div class="sidebar-header">
            <h3>👋 Welcome!</h3>
            <p><strong>{user_data.get('full_name') or user_data['username']}</strong></p>
            <p><small>📧 {user_data.get('email', 'No email')}</small></p>
        </div>
        """, unsafe_allow_html=True)

        # Navigation menu
        st.sidebar.markdown("### 📊 Navigation")

        pages = {
            "🏠 Dashboard": "dashboard",
            "💰 Mutual Funds": "mutual_funds",
            "📈 Stocks": "stocks",
            "💸 Expenses": "expenses",
            "🎯 Goals": "goals",
            "🤖 AI Advisor": "ai_advisor",
            "👤 Profile": "profile",
            "📊 Analytics": "analytics"
        }

        selected_page = st.sidebar.selectbox(
            "Choose a page:",
            list(pages.keys()),
            key="navigation"
        )

        st.session_state.current_page = pages[selected_page]

        # Quick stats
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📈 Quick Stats")

        user_stats = self.auth_manager.get_user_stats(user_data['id'])

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("MF Holdings", user_stats.get('mutual_funds_count', 0))
            st.metric("Expenses", user_stats.get('expenses_count', 0))

        with col2:
            st.metric("Stocks", user_stats.get('stocks_count', 0))
            st.metric("Goals", user_stats.get('goals_count', 0))

        total_investment = user_stats.get('total_investment', 0)
        st.sidebar.metric("Total Investment", f"₹{total_investment:,.0f}")

        # AI Status
        st.sidebar.markdown("---")
        if Config.DEEPSEEK_API_KEY:
            st.sidebar.success("🤖 AI Advisor: Active")
        else:
            st.sidebar.error("🤖 AI Advisor: Disabled")
            st.sidebar.caption("Add DEEPSEEK_API_KEY to enable")

        # Logout button
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()

    def render_main_content(self):
        """Render the main content based on selected page"""
        current_page = st.session_state.get('current_page', 'dashboard')

        if current_page == 'dashboard':
            self.render_dashboard()
        elif current_page == 'mutual_funds':
            self.render_mutual_funds()
        elif current_page == 'stocks':
            self.render_stocks()
        elif current_page == 'expenses':
            self.render_expenses()
        elif current_page == 'goals':
            self.render_goals()
        elif current_page == 'ai_advisor':
            self.render_ai_advisor()
        elif current_page == 'profile':
            self.render_profile()
        elif current_page == 'analytics':
            self.render_analytics()

    def render_dashboard(self):
        """Render the main dashboard"""
        user_data = st.session_state.user_data

        st.markdown(f"""
        <div class="main-header">
            <h1>🏠 Dashboard - Welcome {user_data.get('full_name') or user_data['username']}!</h1>
            <p>Your complete financial overview</p>
        </div>
        """, unsafe_allow_html=True)

        # Get portfolio data
        portfolio_data = self.db_manager.get_user_portfolio_summary(user_data['id'])

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        # Calculate totals
        mf_total = 0
        stocks_total = 0
        expenses_total = 0
        goals_total = 0

        if not portfolio_data['mutual_funds'].empty:
            mf_total = portfolio_data['mutual_funds']['total_invested'].sum()

        if not portfolio_data['stocks'].empty:
            stocks_total = portfolio_data['stocks']['total_invested'].sum()

        if not portfolio_data['expenses'].empty:
            expenses_df = self.db_manager.get_dataframe(
                "SELECT SUM(amount) as total FROM expenses WHERE user_id = ? AND type = 'expense' AND date >= date('now', '-30 days')",
                (user_data['id'],)
            )
            expenses_total = expenses_df['total'].iloc[0] if not expenses_df.empty and expenses_df['total'].iloc[
                0] else 0

        if not portfolio_data['goals'].empty:
            goals_total = portfolio_data['goals']['total_target'].sum()

        with col1:
            st.metric(
                "💰 Mutual Funds",
                f"₹{mf_total:,.0f}",
                delta=None,
                help="Total mutual fund investments"
            )

        with col2:
            st.metric(
                "📈 Stocks",
                f"₹{stocks_total:,.0f}",
                delta=None,
                help="Total stock investments"
            )

        with col3:
            st.metric(
                "💸 Monthly Expenses",
                f"₹{expenses_total:,.0f}",
                delta=None,
                help="Expenses in last 30 days"
            )

        with col4:
            st.metric(
                "🎯 Goal Targets",
                f"₹{goals_total:,.0f}",
                delta=None,
                help="Total financial goals target"
            )

        # Charts and insights
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Portfolio Distribution")
            if mf_total > 0 or stocks_total > 0:
                import plotly.express as px

                portfolio_dist = {
                    'Investment Type': ['Mutual Funds', 'Stocks'],
                    'Amount': [mf_total, stocks_total]
                }

                fig = px.pie(
                    values=portfolio_dist['Amount'],
                    names=portfolio_dist['Investment Type'],
                    title="Investment Distribution",
                    color_discrete_sequence=['#667eea', '#764ba2']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 No investment data yet. Start by adding your mutual funds or stocks!")

        with col2:
            st.subheader("🎯 Goals Progress")
            if not portfolio_data['goals'].empty:
                goals_df = self.db_manager.get_dataframe(
                    "SELECT goal_name, target_amount, current_amount FROM goals WHERE user_id = ? ORDER BY target_date",
                    (user_data['id'],)
                )

                for _, goal in goals_df.head(5).iterrows():
                    progress = (goal['current_amount'] / goal['target_amount']) * 100 if goal[
                                                                                             'target_amount'] > 0 else 0
                    st.markdown(f"**{goal['goal_name']}**")
                    st.progress(min(progress / 100, 1.0))
                    st.caption(f"₹{goal['current_amount']:,.0f} / ₹{goal['target_amount']:,.0f} ({progress:.1f}%)")
            else:
                st.info("💡 No financial goals set yet. Create your first goal!")

        # Recent activity
        st.markdown("---")
        st.subheader("📈 Recent Activity")

        # Recent transactions
        recent_mf = self.db_manager.get_dataframe(
            "SELECT fund_name, amount_invested, purchase_date FROM mutual_funds WHERE user_id = ? ORDER BY created_at DESC LIMIT 3",
            (user_data['id'],)
        )

        recent_stocks = self.db_manager.get_dataframe(
            "SELECT stock_name, quantity, purchase_price, purchase_date FROM stocks WHERE user_id = ? ORDER BY created_at DESC LIMIT 3",
            (user_data['id'],)
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Recent Mutual Fund Investments:**")
            if not recent_mf.empty:
                st.dataframe(recent_mf, use_container_width=True, hide_index=True)
            else:
                st.caption("No recent mutual fund investments")

        with col2:
            st.write("**Recent Stock Investments:**")
            if not recent_stocks.empty:
                st.dataframe(recent_stocks, use_container_width=True, hide_index=True)
            else:
                st.caption("No recent stock investments")

        # AI Insights section
        if Config.DEEPSEEK_API_KEY:
            st.markdown("---")
            st.subheader("🤖 AI Insights")

            if st.button("🔍 Get Portfolio Analysis", use_container_width=True):
                with st.spinner("🤖 AI is analyzing your portfolio..."):
                    portfolio_data_for_ai = {
                        'mutual_funds': self.db_manager.get_dataframe(
                            "SELECT * FROM mutual_funds WHERE user_id = ?", (user_data['id'],)
                        ),
                        'stocks': self.db_manager.get_dataframe(
                            "SELECT * FROM stocks WHERE user_id = ?", (user_data['id'],)
                        ),
                        'goals': self.db_manager.get_dataframe(
                            "SELECT * FROM goals WHERE user_id = ?", (user_data['id'],)
                        )
                    }

                    analysis = self.ai_advisor.analyze_portfolio(portfolio_data_for_ai, user_data)

                    st.markdown(f"""
                    <div class="ai-chat-container">
                        <h4>🤖 AI Portfolio Analysis</h4>
                        <p>{analysis}</p>
                    </div>
                    """, unsafe_allow_html=True)

    def render_mutual_funds(self):
        """Render mutual funds page"""
        st.markdown("""
        <div class="main-header">
            <h1>💰 Mutual Funds Portfolio</h1>
            <p>Manage your mutual fund investments</p>
        </div>
        """, unsafe_allow_html=True)

        # Import the mutual funds module
        from modules.mutual_funds import MutualFundsManager
        mf_manager = MutualFundsManager(self.db_manager, st.session_state.user_data['id'])
        mf_manager.render()

    def render_stocks(self):
        """Render stocks page"""
        st.markdown("""
        <div class="main-header">
            <h1>📈 Stock Portfolio</h1>
            <p>Track your stock investments</p>
        </div>
        """, unsafe_allow_html=True)

        from modules.stocks import StocksManager
        stocks_manager = StocksManager(self.db_manager, st.session_state.user_data['id'])
        stocks_manager.render()

    def render_expenses(self):
        """Render expenses page"""
        st.markdown("""
        <div class="main-header">
            <h1>💸 Expense Tracker</h1>
            <p>Monitor your spending and income</p>
        </div>
        """, unsafe_allow_html=True)

        from modules.expenses import ExpensesManager
        expenses_manager = ExpensesManager(self.db_manager, st.session_state.user_data['id'])
        expenses_manager.render()

    def render_goals(self):
        """Render goals page"""
        st.markdown("""
        <div class="main-header">
            <h1>🎯 Financial Goals</h1>
            <p>Set and track your financial objectives</p>
        </div>
        """, unsafe_allow_html=True)

        from modules.goals import GoalsManager
        goals_manager = GoalsManager(self.db_manager, st.session_state.user_data['id'], self.ai_advisor)
        goals_manager.render()

    def render_ai_advisor(self):
        """Render AI advisor page"""
        st.markdown("""
        <div class="main-header">
            <h1>🤖 AI Financial Advisor</h1>
            <p>Get personalized investment advice powered by DeepSeek AI</p>
        </div>
        """, unsafe_allow_html=True)

        if not Config.DEEPSEEK_API_KEY:
            st.error("🚫 AI Advisor is not configured. Please add your DeepSeek API key to the .env file.")
            st.code("DEEPSEEK_API_KEY=your_api_key_here")
            return

        from modules.ai_chat import AIChatInterface
        ai_chat = AIChatInterface(self.db_manager, self.ai_advisor, st.session_state.user_data['id'])
        ai_chat.render()

    def render_profile(self):
        """Render user profile page"""
        st.markdown("""
        <div class="main-header">
            <h1>👤 User Profile</h1>
            <p>Manage your account settings and preferences</p>
        </div>
        """, unsafe_allow_html=True)

        from modules.profile import ProfileManager
        profile_manager = ProfileManager(self.db_manager, self.auth_manager, st.session_state.user_data)
        profile_manager.render()

    def render_analytics(self):
        """Render analytics page"""
        st.markdown("""
        <div class="main-header">
            <h1>📊 Portfolio Analytics</h1>
            <p>Deep insights into your financial performance</p>
        </div>
        """, unsafe_allow_html=True)

        from modules.analytics import AnalyticsManager
        analytics_manager = AnalyticsManager(self.db_manager, st.session_state.user_data['id'], self.ai_advisor)
        analytics_manager.render()


def main():
    """Main application entry point"""
    try:
        app = PortfolioApp()
        app.run()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.info("Please check your configuration and try again.")


if __name__ == "__main__":
    main()