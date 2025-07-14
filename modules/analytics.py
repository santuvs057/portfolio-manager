import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import Config


class AnalyticsManager:
    def __init__(self, db_manager, user_id, ai_advisor):
        self.db = db_manager
        self.user_id = user_id
        self.ai_advisor = ai_advisor

    def render(self):
        st.info("📊 Analytics module - Basic version loaded. Full analytics coming soon!")

        # Basic analytics for now
        st.subheader("📈 Portfolio Overview")

        # Get basic data
        mf_data = self.db.get_dataframe(
            "SELECT * FROM mutual_funds WHERE user_id = ?", (self.user_id,)
        )

        stocks_data = self.db.get_dataframe(
            "SELECT * FROM stocks WHERE user_id = ?", (self.user_id,)
        )

        if not mf_data.empty or not stocks_data.empty:
            # Basic portfolio metrics
            total_mf = mf_data['amount_invested'].sum() if not mf_data.empty else 0
            total_stocks = (
                        stocks_data['quantity'] * stocks_data['purchase_price']).sum() if not stocks_data.empty else 0
            total_portfolio = total_mf + total_stocks

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Portfolio", f"₹{total_portfolio:,.0f}")
            with col2:
                st.metric("Mutual Funds", f"₹{total_mf:,.0f}")
            with col3:
                st.metric("Stocks", f"₹{total_stocks:,.0f}")

            # Simple pie chart
            if total_portfolio > 0:
                fig = px.pie(
                    values=[total_mf, total_stocks],
                    names=['Mutual Funds', 'Stocks'],
                    title="Portfolio Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No investment data available for analytics")

        st.info("🚧 Advanced analytics features will be added in future updates!")