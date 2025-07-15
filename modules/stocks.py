import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from config import Config


class StocksManager:
    def __init__(self, db_manager, user_id):
        self.db = db_manager
        self.user_id = user_id

    def render(self):
        tab1, tab2, tab3 = st.tabs(["📊 Portfolio", "➕ Add Stock", "📁 Import Data"])

        with tab1:
            self.render_portfolio()

        with tab2:
            self.render_add_stock()

        with tab3:
            self.render_import_data()

    def render_portfolio(self):
        st.subheader("📈 Your Stock Portfolio")

        stocks_df = self.db.get_dataframe(
            "SELECT * FROM stocks WHERE user_id = ? ORDER BY created_at DESC",
            (self.user_id,)
        )

        if stocks_df.empty:
            st.info("📈 No stock investments found. Start by adding your first stock!")
            return

        # Calculate total value
        stocks_df['total_value'] = stocks_df['quantity'] * stocks_df['purchase_price']
        total_investment = stocks_df['total_value'].sum()

        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Investment", f"₹{total_investment:,.0f}")
        with col2:
            st.metric("Total Stocks", len(stocks_df))
        with col3:
            avg_investment = total_investment / len(stocks_df)
            st.metric("Avg Investment", f"₹{avg_investment:,.0f}")

        # Sector-wise distribution
        if 'sector' in stocks_df.columns:
            sector_data = stocks_df.groupby('sector')['total_value'].sum().reset_index()
            fig = px.pie(sector_data, values='total_value', names='sector', title="Sector-wise Distribution")
            st.plotly_chart(fig, use_container_width=True)

        # Display table
        st.dataframe(stocks_df, use_container_width=True, hide_index=True)

    def render_add_stock(self):
        st.subheader("➕ Add New Stock Investment")

        with st.form("add_stock"):
            col1, col2 = st.columns(2)

            with col1:
                stock_name = st.text_input("Stock Name *", placeholder="e.g., Reliance Industries")
                symbol = st.text_input("Symbol", placeholder="e.g., RELIANCE")
                quantity = st.number_input("Quantity *", min_value=1, step=1)
                purchase_price = st.number_input("Purchase Price (₹) *", min_value=0.01, step=0.01)

            with col2:
                purchase_date = st.date_input("Purchase Date *", value=date.today())
                sector = st.selectbox("Sector", Config.STOCK_SECTORS)
                exchange = st.selectbox("Exchange", ["NSE", "BSE", "Other"])
                notes = st.text_area("Notes", placeholder="Any additional notes...")

            submitted = st.form_submit_button("📈 Add Stock", use_container_width=True)

            if submitted:
                if stock_name and quantity > 0 and purchase_price > 0:
                    try:
                        stock_data = {
                            'user_id': self.user_id,
                            'stock_name': stock_name,
                            'symbol': symbol or None,
                            'quantity': quantity,
                            'purchase_price': purchase_price,
                            'current_price': purchase_price,  # Initially same
                            'purchase_date': purchase_date.isoformat(),
                            'sector': sector,
                            'exchange': exchange,
                            'notes': notes or None,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }

                        record_id = self.db.insert_record('stocks', stock_data)
                        st.success(f"✅ Stock added successfully! Record ID: {record_id}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error adding stock: {str(e)}")
                else:
                    st.error("❌ Please fill all required fields")

    def render_import_data(self):
        st.subheader("📁 Import Stock Data")
        st.info("Upload a CSV or Excel file with your stock data")

        uploaded_file = st.file_uploader("Choose file", type=['csv', 'xlsx'])

        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.success(f"✅ File uploaded! Found {len(df)} rows.")
                st.dataframe(df.head(), use_container_width=True)

                # Column mapping
                st.subheader("🔗 Map Your Columns")
                available_cols = [''] + list(df.columns)

                col1, col2 = st.columns(2)
                with col1:
                    stock_name_col = st.selectbox("Stock Name *", available_cols)
                    quantity_col = st.selectbox("Quantity *", available_cols)
                    price_col = st.selectbox("Purchase Price *", available_cols)

                with col2:
                    date_col = st.selectbox("Purchase Date *", available_cols)
                    symbol_col = st.selectbox("Symbol", available_cols)
                    sector_col = st.selectbox("Sector", available_cols)

                if stock_name_col and quantity_col and price_col and date_col:
                    if st.button("📥 Import Data", use_container_width=True):
                        imported_count = 0

                        for _, row in df.iterrows():
                            try:
                                stock_data = {
                                    'user_id': self.user_id,
                                    'stock_name': str(row[stock_name_col]).strip(),
                                    'quantity': int(row[quantity_col]),
                                    'purchase_price': float(row[price_col]),
                                    'current_price': float(row[price_col]),
                                    'purchase_date': pd.to_datetime(row[date_col]).date().isoformat(),
                                    'created_at': datetime.now().isoformat(),
                                    'updated_at': datetime.now().isoformat()
                                }

                                if symbol_col and symbol_col != '':
                                    stock_data['symbol'] = str(row[symbol_col]).strip()

                                if sector_col and sector_col != '':
                                    stock_data['sector'] = str(row[sector_col]).strip()
                                else:
                                    stock_data['sector'] = 'Technology'

                                self.db.insert_record('stocks', stock_data)
                                imported_count += 1

                            except Exception as e:
                                st.error(f"Error in row {imported_count + 1}: {str(e)}")

                        if imported_count > 0:
                            st.success(f"✅ Successfully imported {imported_count} stock records!")
                            st.rerun()
                else:
                    st.warning("Please map required columns")

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

        # Sample format
        st.markdown("---")
        st.subheader("📄 Sample Format")
        sample_data = {
            'stock_name': ['Reliance Industries', 'TCS', 'HDFC Bank'],
            'symbol': ['RELIANCE', 'TCS', 'HDFCBANK'],
            'quantity': [10, 5, 15],
            'purchase_price': [2500, 3200, 1450],
            'purchase_date': ['2024-01-15', '2024-02-01', '2024-01-28'],
            'sector': ['Energy', 'Technology', 'Finance']
        }

        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True, hide_index=True)