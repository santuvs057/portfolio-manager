import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from config import Config


class ExpensesManager:
    def __init__(self, db_manager, user_id):
        self.db = db_manager
        self.user_id = user_id

    def render(self):
        tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📊 View Expenses", "📈 Analytics"])

        with tab1:
            self.render_add_expense()

        with tab2:
            self.render_view_expenses()

        with tab3:
            self.render_analytics()

    def render_add_expense(self):
        st.subheader("➕ Add New Expense/Income")

        with st.form("add_expense"):
            col1, col2 = st.columns(2)

            with col1:
                expense_type = st.selectbox("Type *", ["Expense", "Income"])
                category = st.selectbox("Category *", Config.EXPENSE_CATEGORIES)
                amount = st.number_input("Amount (₹) *", min_value=0.01, step=0.01)

            with col2:
                expense_date = st.date_input("Date *", value=date.today())
                payment_method = st.selectbox("Payment Method",
                                              ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking", "Other"])

            description = st.text_input("Description", placeholder="What was this expense for?")
            tags = st.text_input("Tags", placeholder="food, transport, etc. (comma separated)")

            submitted = st.form_submit_button(f"💰 Add {expense_type}", use_container_width=True)

            if submitted:
                if category and amount > 0:
                    try:
                        expense_data = {
                            'user_id': self.user_id,
                            'category': category,
                            'description': description or None,
                            'amount': amount,
                            'date': expense_date.isoformat(),
                            'type': expense_type.lower(),
                            'payment_method': payment_method,
                            'tags': tags or None,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }

                        record_id = self.db.insert_record('expenses', expense_data)
                        st.success(f"✅ {expense_type} added successfully! Record ID: {record_id}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error adding {expense_type.lower()}: {str(e)}")
                else:
                    st.error("❌ Please fill all required fields")

    def render_view_expenses(self):
        st.subheader("📊 Your Expenses & Income")

        expenses_df = self.db.get_dataframe(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC",
            (self.user_id,)
        )

        if expenses_df.empty:
            st.info("💸 No expenses recorded yet. Start by adding your first expense!")
            return

        # Summary metrics
        total_expenses = expenses_df[expenses_df['type'] == 'expense']['amount'].sum()
        total_income = expenses_df[expenses_df['type'] == 'income']['amount'].sum()
        net_amount = total_income - total_expenses

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Expenses", f"₹{total_expenses:,.0f}")
        with col2:
            st.metric("Total Income", f"₹{total_income:,.0f}")
        with col3:
            st.metric("Net Amount", f"₹{net_amount:,.0f}",
                      delta=f"{'Surplus' if net_amount >= 0 else 'Deficit'}")

        # Filters
        st.subheader("🔍 Filter Expenses")
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_type = st.selectbox("Type", ["All", "Expense", "Income"])
        with col2:
            categories = ["All"] + list(expenses_df['category'].unique())
            filter_category = st.selectbox("Category", categories)
        with col3:
            filter_days = st.selectbox("Time Period",
                                       ["All Time", "Last 7 days", "Last 30 days", "Last 90 days"])

        # Apply filters
        filtered_df = expenses_df.copy()

        if filter_type != "All":
            filtered_df = filtered_df[filtered_df['type'] == filter_type.lower()]

        if filter_category != "All":
            filtered_df = filtered_df[filtered_df['category'] == filter_category]

        if filter_days != "All Time":
            days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
            days = days_map[filter_days]
            cutoff_date = datetime.now().date() - pd.Timedelta(days=days)
            filtered_df['date'] = pd.to_datetime(filtered_df['date']).dt.date
            filtered_df = filtered_df[filtered_df['date'] >= cutoff_date]

        # Display filtered data
        if not filtered_df.empty:
            st.dataframe(
                filtered_df[['date', 'type', 'category', 'description', 'amount', 'payment_method']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "amount": st.column_config.NumberColumn(format="₹%.2f"),
                    "date": st.column_config.DateColumn(format="DD/MM/YYYY")
                }
            )

            # Export option
            if st.button("📥 Export to CSV"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        else:
            st.info("No records found matching your filters")

    def render_analytics(self):
        st.subheader("📈 Expense Analytics")

        expenses_df = self.db.get_dataframe(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date",
            (self.user_id,)
        )

        if expenses_df.empty:
            st.info("No expense data available for analytics")
            return

        # Convert date column
        expenses_df['date'] = pd.to_datetime(expenses_df['date'])

        col1, col2 = st.columns(2)

        with col1:
            # Category-wise breakdown
            st.subheader("💰 Category Breakdown")
            category_data = expenses_df.groupby(['category', 'type'])['amount'].sum().reset_index()

            fig_category = px.bar(
                category_data,
                x='category',
                y='amount',
                color='type',
                title="Expenses by Category",
                barmode='group'
            )
            fig_category.update_layout(height=400)
            st.plotly_chart(fig_category, use_container_width=True)

        with col2:
            # Monthly trend
            st.subheader("📅 Monthly Trend")
            expenses_df['month'] = expenses_df['date'].dt.to_period('M')
            monthly_data = expenses_df.groupby(['month', 'type'])['amount'].sum().reset_index()
            monthly_data['month_str'] = monthly_data['month'].astype(str)

            fig_monthly = px.line(
                monthly_data,
                x='month_str',
                y='amount',
                color='type',
                title="Monthly Expense Trend"
            )
            fig_monthly.update_layout(height=400)
            st.plotly_chart(fig_monthly, use_container_width=True)

        # Top expenses
        st.subheader("🔝 Top Expenses")
        top_expenses = expenses_df[expenses_df['type'] == 'expense'].nlargest(10, 'amount')

        if not top_expenses.empty:
            st.dataframe(
                top_expenses[['date', 'category', 'description', 'amount']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "amount": st.column_config.NumberColumn(format="₹%.2f"),
                    "date": st.column_config.DateColumn(format="DD/MM/YYYY")
                }
            )