import streamlit as st
from datetime import datetime
from config import Config


class ProfileManager:
    def __init__(self, db_manager, auth_manager, user_data):
        self.db = db_manager
        self.auth_manager = auth_manager
        self.user_data = user_data

    def render(self):
        tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "⚙️ Preferences", "🔒 Security", "📊 Account Stats"])

        with tab1:
            self.render_profile()

        with tab2:
            self.render_preferences()

        with tab3:
            self.render_security()

        with tab4:
            self.render_account_stats()

    def render_profile(self):
        st.subheader("👤 Profile Information")

        with st.form("update_profile"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input("Username", value=self.user_data['username'], disabled=True)
                full_name = st.text_input("Full Name", value=self.user_data.get('full_name', ''))
                email = st.text_input("Email", value=self.user_data.get('email', ''))

            with col2:
                phone = st.text_input("Phone", value=self.user_data.get('phone', ''))
                member_since = st.text_input("Member Since",
                                             value=self.user_data.get('created_at', '').split('T')[
                                                 0] if self.user_data.get('created_at') else '',
                                             disabled=True)

            submitted = st.form_submit_button("💾 Update Profile", use_container_width=True)

            if submitted:
                try:
                    profile_data = {
                        'full_name': full_name,
                        'email': email,
                        'phone': phone
                    }

                    success, message = self.auth_manager.update_user_profile(
                        self.user_data['id'], profile_data
                    )

                    if success:
                        st.success(message)
                        # Update session state
                        st.session_state.user_data.update(profile_data)
                    else:
                        st.error(message)

                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")

    def render_preferences(self):
        st.subheader("⚙️ Investment Preferences")

        with st.form("update_preferences"):
            col1, col2 = st.columns(2)

            with col1:
                risk_tolerance = st.selectbox(
                    "Risk Tolerance",
                    ["Conservative", "Moderate", "Aggressive"],
                    index=["Conservative", "Moderate", "Aggressive"].index(
                        self.user_data.get('risk_tolerance', 'Moderate').title()
                    )
                )

                investment_goal = st.text_input(
                    "Primary Investment Goal",
                    value=self.user_data.get('investment_goal', ''),
                    placeholder="e.g., Retirement, Wealth Creation"
                )

            with col2:
                monthly_income = st.number_input(
                    "Monthly Income (₹)",
                    value=float(self.user_data.get('monthly_income', 0)),
                    min_value=0.0,
                    step=1000.0
                )

                monthly_expenses = st.number_input(
                    "Monthly Expenses (₹)",
                    value=float(self.user_data.get('monthly_expenses', 0)),
                    min_value=0.0,
                    step=1000.0
                )

            # Financial goals
            st.subheader("🎯 Financial Planning")

            col1, col2 = st.columns(2)

            with col1:
                investment_horizon = st.selectbox(
                    "Investment Horizon",
                    ["Short-term (1-3 years)", "Medium-term (3-7 years)", "Long-term (7+ years)"]
                )

            with col2:
                preferred_instruments = st.multiselect(
                    "Preferred Investment Instruments",
                    ["Mutual Funds", "Stocks", "Bonds", "Fixed Deposits", "Gold", "Real Estate"],
                    default=["Mutual Funds", "Stocks"]
                )

            submitted = st.form_submit_button("💾 Update Preferences", use_container_width=True)

            if submitted:
                try:
                    preferences_data = {
                        'risk_tolerance': risk_tolerance.lower(),
                        'investment_goal': investment_goal,
                        'monthly_income': monthly_income,
                        'monthly_expenses': monthly_expenses
                    }

                    success, message = self.auth_manager.update_user_profile(
                        self.user_data['id'], preferences_data
                    )

                    if success:
                        st.success(message)
                        # Update session state
                        st.session_state.user_data.update(preferences_data)
                    else:
                        st.error(message)

                except Exception as e:
                    st.error(f"Error updating preferences: {str(e)}")

        # Financial health score
        st.markdown("---")
        st.subheader("💰 Financial Health Score")

        if monthly_income > 0 and monthly_expenses > 0:
            savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Savings Rate", f"{savings_rate:.1f}%")

            with col2:
                surplus = monthly_income - monthly_expenses
                st.metric("Monthly Surplus", f"₹{surplus:,.0f}")

            with col3:
                # Simple health score calculation
                if savings_rate >= 20:
                    score = "Excellent 🟢"
                elif savings_rate >= 10:
                    score = "Good 🟡"
                else:
                    score = "Needs Improvement 🔴"
                st.metric("Health Score", score)

            # Recommendations
            if savings_rate < 10:
                st.warning("💡 Try to save at least 10-20% of your income for a healthy financial future.")
            elif savings_rate >= 20:
                st.success("🎉 Excellent savings rate! You're on track for financial success.")
        else:
            st.info("💡 Add your income and expenses to see your financial health score.")

    def render_security(self):
        st.subheader("🔒 Security Settings")

        # Change password
        st.subheader("🔑 Change Password")

        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            submitted = st.form_submit_button("🔒 Change Password", use_container_width=True)

            if submitted:
                if current_password and new_password and confirm_password:
                    if new_password == confirm_password:
                        try:
                            success, message = self.auth_manager.change_password(
                                self.user_data['id'], current_password, new_password
                            )

                            if success:
                                st.success(message)
                            else:
                                st.error(message)

                        except Exception as e:
                            st.error(f"Error changing password: {str(e)}")
                    else:
                        st.error("New passwords do not match")
                else:
                    st.error("Please fill all password fields")

        # Account deletion
        st.markdown("---")
        st.subheader("⚠️ Danger Zone")

        with st.expander("🗑️ Delete Account"):
            st.error("**Warning: This action cannot be undone!**")
            st.write("Deleting your account will permanently remove:")
            st.write("• All your investment data")
            st.write("• All expense records")
            st.write("• All financial goals")
            st.write("• All AI interaction history")

            delete_password = st.text_input("Enter your password to confirm deletion", type="password")

            if st.button("🗑️ DELETE ACCOUNT", type="primary"):
                if delete_password:
                    try:
                        success, message = self.auth_manager.delete_user_account(
                            self.user_data['id'], delete_password
                        )

                        if success:
                            st.success(message)
                            st.info("Redirecting to login page...")
                            # Clear session and redirect
                            st.session_state.authenticated = False
                            st.session_state.user_data = None
                            st.rerun()
                        else:
                            st.error(message)

                    except Exception as e:
                        st.error(f"Error deleting account: {str(e)}")
                else:
                    st.error("Please enter your password to confirm deletion")

    def render_account_stats(self):
        st.subheader("📊 Account Statistics")

        # Get user statistics
        user_stats = self.auth_manager.get_user_stats(self.user_data['id'])

        # Investment stats
        st.subheader("💰 Investment Portfolio")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Mutual Funds", user_stats.get('mutual_funds_count', 0))

        with col2:
            st.metric("Stocks", user_stats.get('stocks_count', 0))

        with col3:
            st.metric("Expense Records", user_stats.get('expenses_count', 0))

        with col4:
            st.metric("Financial Goals", user_stats.get('goals_count', 0))

        # Investment values
        st.subheader("💵 Investment Values")

        col1, col2, col3 = st.columns(3)

        with col1:
            mf_investment = user_stats.get('total_mf_investment', 0)
            st.metric("MF Investment", f"₹{mf_investment:,.0f}")

        with col2:
            stocks_investment = user_stats.get('total_stocks_investment', 0)
            st.metric("Stocks Investment", f"₹{stocks_investment:,.0f}")

        with col3:
            total_investment = user_stats.get('total_investment', 0)
            st.metric("Total Portfolio", f"₹{total_investment:,.0f}")

        # Activity stats
        st.subheader("📈 Activity Overview")

        # Recent activity
        recent_mf = self.db.get_dataframe(
            "SELECT COUNT(*) as count FROM mutual_funds WHERE user_id = ? AND created_at >= date('now', '-30 days')",
            (self.user_data['id'],)
        )

        recent_stocks = self.db.get_dataframe(
            "SELECT COUNT(*) as count FROM stocks WHERE user_id = ? AND created_at >= date('now', '-30 days')",
            (self.user_data['id'],)
        )

        recent_expenses = self.db.get_dataframe(
            "SELECT COUNT(*) as count FROM expenses WHERE user_id = ? AND created_at >= date('now', '-30 days')",
            (self.user_data['id'],)
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            mf_count = recent_mf['count'].iloc[0] if not recent_mf.empty else 0
            st.metric("MF Added (30 days)", mf_count)

        with col2:
            stocks_count = recent_stocks['count'].iloc[0] if not recent_stocks.empty else 0
            st.metric("Stocks Added (30 days)", stocks_count)

        with col3:
            expenses_count = recent_expenses['count'].iloc[0] if not recent_expenses.empty else 0
            st.metric("Expenses Added (30 days)", expenses_count)

        # Data export
        st.markdown("---")
        st.subheader("📥 Data Export")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Export Portfolio Data", use_container_width=True):
                # Export all user data
                all_data = {
                    'mutual_funds': self.db.get_dataframe(
                        "SELECT * FROM mutual_funds WHERE user_id = ?", (self.user_data['id'],)
                    ),
                    'stocks': self.db.get_dataframe(
                        "SELECT * FROM stocks WHERE user_id = ?", (self.user_data['id'],)
                    ),
                    'expenses': self.db.get_dataframe(
                        "SELECT * FROM expenses WHERE user_id = ?", (self.user_data['id'],)
                    ),
                    'goals': self.db.get_dataframe(
                        "SELECT * FROM goals WHERE user_id = ?", (self.user_data['id'],)
                    )
                }

                # Create Excel file with multiple sheets
                import io
                buffer = io.BytesIO()

                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    for sheet_name, df in all_data.items():
                        if not df.empty:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)

                st.download_button(
                    "📥 Download Excel File",
                    buffer.getvalue(),
                    f"portfolio_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with col2:
            if st.button("🤖 Export AI Chat History", use_container_width=True):
                ai_history = self.db.get_dataframe(
                    "SELECT question, response, created_at FROM ai_interactions WHERE user_id = ? ORDER BY created_at DESC",
                    (self.user_data['id'],)
                )

                if not ai_history.empty:
                    csv = ai_history.to_csv(index=False)
                    st.download_button(
                        "📥 Download Chat History",
                        csv,
                        f"ai_chat_history_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No AI chat history found")