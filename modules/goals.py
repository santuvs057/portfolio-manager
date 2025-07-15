import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from config import Config


class GoalsManager:
    def __init__(self, db_manager, user_id, ai_advisor):
        self.db = db_manager
        self.user_id = user_id
        self.ai_advisor = ai_advisor

    def render(self):
        tab1, tab2, tab3 = st.tabs(["➕ Add Goal", "🎯 View Goals", "🤖 AI Planning"])

        with tab1:
            self.render_add_goal()

        with tab2:
            self.render_view_goals()

        with tab3:
            self.render_ai_planning()

    def render_add_goal(self):
        st.subheader("🎯 Add New Financial Goal")

        with st.form("add_goal"):
            col1, col2 = st.columns(2)

            with col1:
                goal_name = st.text_input("Goal Name *", placeholder="e.g., Emergency Fund")
                target_amount = st.number_input("Target Amount (₹) *", min_value=1000.0, step=1000.0)
                current_amount = st.number_input("Current Amount (₹)", min_value=0.0, step=100.0)

            with col2:
                target_date = st.date_input("Target Date *", min_value=date.today())
                category = st.selectbox("Category *", Config.GOAL_CATEGORIES)
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])

            description = st.text_area("Description", placeholder="Describe your goal...")
            monthly_contribution = st.number_input("Monthly Contribution (₹)", min_value=0.0, step=500.0)

            submitted = st.form_submit_button("🎯 Add Goal", use_container_width=True)

            if submitted:
                if goal_name and target_amount > 0:
                    try:
                        goal_data = {
                            'user_id': self.user_id,
                            'goal_name': goal_name,
                            'description': description or None,
                            'target_amount': target_amount,
                            'current_amount': current_amount,
                            'target_date': target_date.isoformat(),
                            'category': category,
                            'priority': priority,
                            'monthly_contribution': monthly_contribution if monthly_contribution > 0 else None,
                            'status': 'active',
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }

                        record_id = self.db.insert_record('goals', goal_data)
                        st.success(f"✅ Goal added successfully! Record ID: {record_id}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error adding goal: {str(e)}")
                else:
                    st.error("❌ Please fill all required fields")

    def render_view_goals(self):
        st.subheader("🎯 Your Financial Goals")

        goals_df = self.db.get_dataframe(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY target_date",
            (self.user_id,)
        )

        if goals_df.empty:
            st.info("🎯 No financial goals set yet. Create your first goal!")
            return

        # Summary metrics
        total_target = goals_df['target_amount'].sum()
        total_current = goals_df['current_amount'].sum()
        overall_progress = (total_current / total_target) * 100 if total_target > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Goals", len(goals_df))
        with col2:
            st.metric("Target Amount", f"₹{total_target:,.0f}")
        with col3:
            st.metric("Overall Progress", f"{overall_progress:.1f}%")

        # Goals display
        for _, goal in goals_df.iterrows():
            with st.container():
                progress = (goal['current_amount'] / goal['target_amount']) * 100 if goal['target_amount'] > 0 else 0
                days_left = (pd.to_datetime(goal['target_date']).date() - datetime.now().date()).days

                # Goal header
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"""
                    <div class="goal-progress">
                        <h4>{goal['goal_name']} ({goal['category']})</h4>
                        <p>{goal['description'] or 'No description'}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.metric("Days Left", days_left)

                with col3:
                    st.metric("Priority", goal['priority'])

                # Progress bar
                st.progress(min(progress / 100, 1.0))

                # Progress details
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Current:** ₹{goal['current_amount']:,.0f}")
                with col2:
                    st.write(f"**Target:** ₹{goal['target_amount']:,.0f}")
                with col3:
                    remaining = goal['target_amount'] - goal['current_amount']
                    st.write(f"**Remaining:** ₹{remaining:,.0f}")

                # Monthly contribution analysis
                if goal['monthly_contribution'] and goal['monthly_contribution'] > 0:
                    months_needed = remaining / goal['monthly_contribution']
                    st.info(
                        f"💡 At ₹{goal['monthly_contribution']:,.0f}/month, you'll reach this goal in {months_needed:.1f} months")
                elif days_left > 0:
                    monthly_needed = remaining / (days_left / 30)
                    st.info(f"💡 You need to save ₹{monthly_needed:,.0f}/month to reach this goal on time")

                # Update goal
                with st.expander("✏️ Update Goal"):
                    new_current = st.number_input(
                        "Update Current Amount",
                        value=float(goal['current_amount']),
                        key=f"update_{goal['id']}"
                    )

                    if st.button(f"Update Goal {goal['id']}", key=f"btn_{goal['id']}"):
                        try:
                            self.db.update_record('goals', goal['id'], {'current_amount': new_current})
                            st.success("✅ Goal updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating goal: {str(e)}")

                st.divider()

        # Goals analytics
        st.subheader("📊 Goals Analytics")

        col1, col2 = st.columns(2)

        with col1:
            # Progress by category
            category_progress = goals_df.groupby('category').agg({
                'target_amount': 'sum',
                'current_amount': 'sum'
            }).reset_index()
            category_progress['progress'] = (category_progress['current_amount'] / category_progress[
                'target_amount']) * 100

            fig_category = px.bar(
                category_progress,
                x='category',
                y='progress',
                title="Progress by Category (%)",
                color='progress',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_category, use_container_width=True)

        with col2:
            # Priority distribution
            priority_data = goals_df['priority'].value_counts().reset_index()
            fig_priority = px.pie(
                priority_data,
                values='count',
                names='priority',
                title="Goals by Priority"
            )
            st.plotly_chart(fig_priority, use_container_width=True)

    def render_ai_planning(self):
        st.subheader("🤖 AI Goal Planning Assistant")

        if not Config.DEEPSEEK_API_KEY:
            st.error("🚫 AI features require DeepSeek API key. Please configure it in your .env file.")
            return

        # Get goals data
        goals_df = self.db.get_dataframe(
            "SELECT * FROM goals WHERE user_id = ?", (self.user_id,)
        )

        # Get portfolio data for context
        portfolio_data = {
            'mutual_funds': self.db.get_dataframe(
                "SELECT * FROM mutual_funds WHERE user_id = ?", (self.user_id,)
            ),
            'stocks': self.db.get_dataframe(
                "SELECT * FROM stocks WHERE user_id = ?", (self.user_id,)
            ),
            'goals': goals_df
        }

        if goals_df.empty:
            st.info("💡 Add some financial goals first to get AI-powered planning advice!")
            return

        # AI Analysis Options
        st.subheader("🎯 Choose Analysis Type")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Analyze All Goals", use_container_width=True):
                with st.spinner("🤖 AI is analyzing your goals..."):
                    user_data = st.session_state.user_data
                    analysis = self.ai_advisor.goal_planning(goals_df, portfolio_data, user_data)

                    st.markdown(f"""
                    <div class="ai-chat-container">
                        <h4>🤖 Goal Analysis & Recommendations</h4>
                        <p>{analysis}</p>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            if st.button("💡 Get Investment Strategy", use_container_width=True):
                with st.spinner("🤖 AI is creating investment strategy..."):
                    user_data = st.session_state.user_data
                    strategy = self.ai_advisor.investment_recommendation(
                        "Suggest investment strategy for my financial goals",
                        portfolio_data,
                        user_data
                    )

                    st.markdown(f"""
                    <div class="ai-chat-container">
                        <h4>🤖 Investment Strategy for Goals</h4>
                        <p>{strategy}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # Custom goal planning
        st.markdown("---")
        st.subheader("💬 Ask AI About Your Goals")

        goal_question = st.text_area(
            "Ask anything about your financial goals:",
            placeholder="e.g., How should I prioritize my goals? What's the best way to achieve my house purchase goal?"
        )

        if st.button("🤖 Get AI Advice", use_container_width=True) and goal_question:
            with st.spinner("🤖 AI is thinking..."):
                user_data = st.session_state.user_data

                # Prepare context for AI
                context = f"User's financial goals and portfolio data"
                response = self.ai_advisor.chat_with_advisor(
                    goal_question,
                    [],
                    self.ai_advisor._prepare_portfolio_context(portfolio_data, user_data)
                )

                st.markdown(f"""
                <div class="ai-chat-container">
                    <h4>🤖 AI Response</h4>
                    <p>{response}</p>
                </div>
                """, unsafe_allow_html=True)