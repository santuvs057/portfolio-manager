import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from typing import Dict, List, Optional
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MutualFundsManager:
    """Manage mutual fund investments with enhanced features"""

    def __init__(self, db_manager, user_id: int):
        self.db = db_manager
        self.user_id = user_id

    def render(self):
        """Render the mutual funds interface"""
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Portfolio Overview",
            "➕ Add Investment",
            "📁 Import Data",
            "📈 Performance"
        ])

        with tab1:
            self.render_portfolio_overview()

        with tab2:
            self.render_add_investment()

        with tab3:
            self.render_import_data()

        with tab4:
            self.render_performance_analysis()

    def render_portfolio_overview(self):
        """Display mutual fund portfolio overview"""
        st.subheader("💰 Your Mutual Fund Portfolio")

        # Get mutual funds data
        mf_df = self.db.get_dataframe(
            "SELECT * FROM mutual_funds WHERE user_id = ? ORDER BY created_at DESC",
            (self.user_id,)
        )

        if mf_df.empty:
            st.info("📈 No mutual fund investments found. Start by adding your first investment!")
            return

        # Portfolio summary metrics
        total_invested = mf_df['amount_invested'].sum()
        total_current = mf_df['current_value'].fillna(mf_df['amount_invested']).sum()
        total_returns = total_current - total_invested
        returns_percentage = (total_returns / total_invested) * 100 if total_invested > 0 else 0

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "💰 Total Invested",
                f"₹{total_invested:,.0f}",
                help="Total amount invested in mutual funds"
            )

        with col2:
            st.metric(
                "📈 Current Value",
                f"₹{total_current:,.0f}",
                help="Current portfolio value"
            )

        with col3:
            st.metric(
                "💵 Total Returns",
                f"₹{total_returns:,.0f}",
                delta=f"{returns_percentage:+.2f}%",
                help="Absolute returns and percentage"
            )

        with col4:
            fund_count = len(mf_df)
            st.metric(
                "📊 Fund Count",
                fund_count,
                help="Number of mutual funds in portfolio"
            )

        # Category-wise allocation
        st.subheader("📊 Category Allocation")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart for category allocation
            category_data = mf_df.groupby('category')['amount_invested'].sum().reset_index()

            if not category_data.empty:
                fig_pie = px.pie(
                    category_data,
                    values='amount_invested',
                    names='category',
                    title="Investment by Category",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Top 5 funds by investment
            st.write("**🏆 Top 5 Holdings**")
            top_funds = mf_df.nlargest(5, 'amount_invested')[
                ['fund_name', 'amount_invested', 'category', 'purchase_date']
            ]

            for idx, fund in top_funds.iterrows():
                percentage = (fund['amount_invested'] / total_invested) * 100

                with st.container():
                    st.markdown(f"""
                    <div class="investment-card">
                        <h4>{fund['fund_name']}</h4>
                        <p><strong>₹{fund['amount_invested']:,.0f}</strong> ({percentage:.1f}%)</p>
                        <p><small>{fund['category']} • {fund['purchase_date']}</small></p>
                    </div>
                    """, unsafe_allow_html=True)

        # Detailed holdings table
        st.subheader("📋 Detailed Holdings")

        # Add filters
        col1, col2, col3 = st.columns(3)

        with col1:
            categories = ['All'] + list(mf_df['category'].unique())
            selected_category = st.selectbox("Filter by Category", categories)

        with col2:
            sort_options = ['Latest First', 'Oldest First', 'Highest Investment', 'Lowest Investment']
            sort_by = st.selectbox("Sort by", sort_options)

        with col3:
            search_term = st.text_input("🔍 Search funds", placeholder="Fund name...")

        # Apply filters
        filtered_df = mf_df.copy()

        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]

        if search_term:
            filtered_df = filtered_df[
                filtered_df['fund_name'].str.contains(search_term, case=False, na=False)
            ]

        # Apply sorting
        if sort_by == 'Latest First':
            filtered_df = filtered_df.sort_values('purchase_date', ascending=False)
        elif sort_by == 'Oldest First':
            filtered_df = filtered_df.sort_values('purchase_date', ascending=True)
        elif sort_by == 'Highest Investment':
            filtered_df = filtered_df.sort_values('amount_invested', ascending=False)
        elif sort_by == 'Lowest Investment':
            filtered_df = filtered_df.sort_values('amount_invested', ascending=True)

        # Display table
        if not filtered_df.empty:
            # Format display columns
            display_df = filtered_df[[
                'fund_name', 'category', 'amount_invested', 'units',
                'nav', 'purchase_date', 'fund_house'
            ]].copy()

            display_df.columns = [
                'Fund Name', 'Category', 'Invested (₹)', 'Units',
                'NAV (₹)', 'Purchase Date', 'Fund House'
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Invested (₹)": st.column_config.NumberColumn(
                        format="₹%.0f"
                    ),
                    "NAV (₹)": st.column_config.NumberColumn(
                        format="₹%.2f"
                    ),
                    "Units": st.column_config.NumberColumn(
                        format="%.3f"
                    )
                }
            )

            # Bulk actions
            st.subheader("⚡ Bulk Actions")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📊 Export to CSV"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"mutual_funds_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )

            with col2:
                if st.button("🔄 Update NAVs"):
                    st.info("NAV update feature coming soon!")

            with col3:
                if st.button("📈 Performance Report"):
                    st.info("Performance report feature coming soon!")

        else:
            st.info("No funds found matching your criteria.")

    def render_add_investment(self):
        """Form to add new mutual fund investment"""
        st.subheader("➕ Add New Mutual Fund Investment")

        with st.form("add_mutual_fund"):
            col1, col2 = st.columns(2)

            with col1:
                fund_name = st.text_input(
                    "Fund Name *",
                    placeholder="e.g., HDFC Top 100 Fund",
                    help="Enter the complete fund name"
                )

                fund_house = st.selectbox(
                    "Fund House",
                    ["", "HDFC", "SBI", "ICICI Prudential", "Axis", "Kotak", "DSP",
                     "Franklin Templeton", "Nippon India", "UTI", "Aditya Birla", "Other"]
                )

                amount_invested = st.number_input(
                    "Investment Amount (₹) *",
                    min_value=100.0,
                    step=500.0,
                    help="Amount invested in this fund"
                )

                units = st.number_input(
                    "Units",
                    min_value=0.001,
                    step=0.001,
                    format="%.3f",
                    help="Number of units purchased"
                )

                nav = st.number_input(
                    "NAV (₹)",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    help="Net Asset Value at purchase"
                )

            with col2:
                category = st.selectbox(
                    "Category *",
                    Config.MF_CATEGORIES,
                    help="Select fund category"
                )

                subcategory = st.text_input(
                    "Subcategory",
                    placeholder="e.g., Large Cap, Multi Cap",
                    help="Specific subcategory"
                )

                purchase_date = st.date_input(
                    "Purchase Date *",
                    value=date.today(),
                    help="Date of investment"
                )

                scheme_code = st.text_input(
                    "Scheme Code",
                    placeholder="e.g., 101206",
                    help="AMFI scheme code (optional)"
                )

                isin = st.text_input(
                    "ISIN",
                    placeholder="e.g., INF179K01158",
                    help="ISIN code (optional)"
                )

            # Additional details
            st.subheader("📊 Additional Details (Optional)")

            col1, col2, col3 = st.columns(3)

            with col1:
                expense_ratio = st.number_input(
                    "Expense Ratio (%)",
                    min_value=0.01,
                    max_value=5.0,
                    step=0.01,
                    format="%.2f"
                )

            with col2:
                fund_manager = st.text_input(
                    "Fund Manager",
                    placeholder="Manager name"
                )

            with col3:
                risk_level = st.selectbox(
                    "Risk Level",
                    ["", "Low", "Moderate", "High", "Very High"]
                )

            submitted = st.form_submit_button("💰 Add Investment", use_container_width=True)

            if submitted:
                if fund_name and amount_invested > 0 and category:
                    try:
                        investment_data = {
                            'user_id': self.user_id,
                            'fund_name': fund_name,
                            'fund_house': fund_house or None,
                            'scheme_code': scheme_code or None,
                            'isin': isin or None,
                            'amount_invested': amount_invested,
                            'units': units if units > 0 else None,
                            'nav': nav if nav > 0 else None,
                            'purchase_date': purchase_date.isoformat(),
                            'category': category,
                            'subcategory': subcategory or None,
                            'expense_ratio': expense_ratio if expense_ratio > 0 else None,
                            'fund_manager': fund_manager or None,
                            'risk_level': risk_level or None,
                            'current_value': amount_invested,  # Initially same as invested
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }

                        record_id = self.db.insert_record('mutual_funds', investment_data)

                        st.success(f"✅ Investment added successfully! Record ID: {record_id}")
                        st.balloons()

                        # Clear form by rerunning
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error adding investment: {str(e)}")
                        logger.error(f"Error adding mutual fund: {str(e)}")
                else:
                    st.error("❌ Please fill all required fields (marked with *)")

    def render_import_data(self):
        """Import mutual fund data from CSV/Excel"""
        st.subheader("📁 Import Mutual Fund Data")

        st.info("💡 Upload a CSV or Excel file with your mutual fund investment data.")

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload CSV or Excel file with mutual fund data"
        )

        if uploaded_file:
            try:
                # Read file
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.success(f"✅ File uploaded successfully! Found {len(df)} rows.")

                # Preview data
                st.subheader("📊 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)

                # Column mapping
                st.subheader("🔗 Map Your Columns")

                available_cols = [''] + list(df.columns)

                col1, col2, col3 = st.columns(3)

                with col1:
                    fund_name_col = st.selectbox("Fund Name *", available_cols, key="fund_name_col")
                    amount_col = st.selectbox("Investment Amount *", available_cols, key="amount_col")
                    category_col = st.selectbox("Category", available_cols, key="category_col")
                    units_col = st.selectbox("Units", available_cols, key="units_col")

                with col2:
                    purchase_date_col = st.selectbox("Purchase Date *", available_cols, key="date_col")
                    nav_col = st.selectbox("NAV", available_cols, key="nav_col")
                    fund_house_col = st.selectbox("Fund House", available_cols, key="fund_house_col")
                    scheme_code_col = st.selectbox("Scheme Code", available_cols, key="scheme_col")

                with col3:
                    subcategory_col = st.selectbox("Subcategory", available_cols, key="subcat_col")
                    expense_ratio_col = st.selectbox("Expense Ratio", available_cols, key="expense_col")
                    fund_manager_col = st.selectbox("Fund Manager", available_cols, key="manager_col")
                    risk_level_col = st.selectbox("Risk Level", available_cols, key="risk_col")

                # Validation and import
                if fund_name_col and amount_col and purchase_date_col:
                    if st.button("📥 Import Data", use_container_width=True):
                        imported_count = 0
                        errors = []

                        with st.progress(0) as progress_bar:
                            for idx, row in df.iterrows():
                                try:
                                    # Extract data
                                    investment_data = {
                                        'user_id': self.user_id,
                                        'fund_name': str(row[fund_name_col]).strip(),
                                        'amount_invested': float(row[amount_col]),
                                        'purchase_date': pd.to_datetime(row[purchase_date_col]).date().isoformat(),
                                        'current_value': float(row[amount_col]),  # Initially same as invested
                                        'created_at': datetime.now().isoformat(),
                                        'updated_at': datetime.now().isoformat()
                                    }

                                    # Optional fields
                                    if category_col and category_col != '':
                                        investment_data['category'] = str(row[category_col]).strip() if pd.notna(
                                            row[category_col]) else 'Equity'
                                    else:
                                        investment_data['category'] = 'Equity'

                                    if units_col and units_col != '' and pd.notna(row[units_col]):
                                        investment_data['units'] = float(row[units_col])

                                    if nav_col and nav_col != '' and pd.notna(row[nav_col]):
                                        investment_data['nav'] = float(row[nav_col])

                                    if fund_house_col and fund_house_col != '' and pd.notna(row[fund_house_col]):
                                        investment_data['fund_house'] = str(row[fund_house_col]).strip()

                                    if scheme_code_col and scheme_code_col != '' and pd.notna(row[scheme_code_col]):
                                        investment_data['scheme_code'] = str(row[scheme_code_col]).strip()

                                    if subcategory_col and subcategory_col != '' and pd.notna(row[subcategory_col]):
                                        investment_data['subcategory'] = str(row[subcategory_col]).strip()

                                    if expense_ratio_col and expense_ratio_col != '' and pd.notna(
                                            row[expense_ratio_col]):
                                        investment_data['expense_ratio'] = float(row[expense_ratio_col])

                                    if fund_manager_col and fund_manager_col != '' and pd.notna(row[fund_manager_col]):
                                        investment_data['fund_manager'] = str(row[fund_manager_col]).strip()

                                    if risk_level_col and risk_level_col != '' and pd.notna(row[risk_level_col]):
                                        investment_data['risk_level'] = str(row[risk_level_col]).strip()

                                    # Insert record
                                    self.db.insert_record('mutual_funds', investment_data)
                                    imported_count += 1

                                except Exception as e:
                                    errors.append(f"Row {idx + 1}: {str(e)}")

                                # Update progress
                                progress_bar.progress((idx + 1) / len(df))

                        # Show results
                        if imported_count > 0:
                            st.success(f"✅ Successfully imported {imported_count} mutual fund records!")
                            st.balloons()

                        if errors:
                            st.warning(f"⚠️ {len(errors)} records had errors:")
                            for error in errors[:5]:  # Show first 5 errors
                                st.error(error)
                            if len(errors) > 5:
                                st.info(f"... and {len(errors) - 5} more errors")

                        if imported_count > 0:
                            st.rerun()
                else:
                    st.warning("⚠️ Please map at least Fund Name, Amount, and Purchase Date columns")

            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

        # Sample format section
        st.markdown("---")
        st.subheader("📄 Sample File Format")

        sample_data = {
            'fund_name': ['HDFC Top 100 Fund', 'SBI Bluechip Fund', 'ICICI Pru Value Discovery'],
            'amount_invested': [10000, 15000, 8000],
            'purchase_date': ['2024-01-15', '2024-02-01', '2024-01-28'],
            'category': ['Equity', 'Equity', 'Equity'],
            'units': [156.25, 312.50, 89.34],
            'nav': [64.00, 48.00, 89.50],
            'fund_house': ['HDFC', 'SBI', 'ICICI Prudential']
        }

        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

        # Download sample template
        csv_sample = sample_df.to_csv(index=False)
        st.download_button(
            "📥 Download Sample Template",
            csv_sample,
            "mutual_funds_template.csv",
            "text/csv",
            help="Download this template and fill with your data"
        )

    def render_performance_analysis(self):
        """Analyze mutual fund performance"""
        st.subheader("📈 Performance Analysis")

        # Get mutual funds data
        mf_df = self.db.get_dataframe(
            "SELECT * FROM mutual_funds WHERE user_id = ? ORDER BY purchase_date",
            (self.user_id,)
        )

        if mf_df.empty:
            st.info("📊 No mutual fund data available for performance analysis.")
            return

        # Performance metrics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💹 Investment Timeline")

            # Monthly investment trend
            mf_df['purchase_date'] = pd.to_datetime(mf_df['purchase_date'])
            mf_df['month_year'] = mf_df['purchase_date'].dt.to_period('M')

            monthly_investments = mf_df.groupby('month_year')['amount_invested'].sum().reset_index()
            monthly_investments['month_year_str'] = monthly_investments['month_year'].astype(str)

            if len(monthly_investments) > 1:
                fig_timeline = px.line(
                    monthly_investments,
                    x='month_year_str',
                    y='amount_invested',
                    title='Monthly Investment Trend',
                    labels={'amount_invested': 'Investment Amount (₹)', 'month_year_str': 'Month'}
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("Need more than one month of data for timeline analysis")

        with col2:
            st.subheader("🎯 Category Performance")

            # Category-wise performance
            category_perf = mf_df.groupby('category').agg({
                'amount_invested': 'sum',
                'current_value': lambda x: x.fillna(0).sum() if x.fillna(0).sum() > 0 else
                mf_df.groupby('category')['amount_invested'].sum().loc[x.name]
            }).reset_index()

            category_perf['returns'] = category_perf['current_value'] - category_perf['amount_invested']
            category_perf['returns_pct'] = (category_perf['returns'] / category_perf['amount_invested']) * 100

            fig_category = px.bar(
                category_perf,
                x='category',
                y='returns_pct',
                title='Category-wise Returns (%)',
                color='returns_pct',
                color_continuous_scale='RdYlGn'
            )
            fig_category.update_layout(height=400)
            st.plotly_chart(fig_category, use_container_width=True)

        # Detailed performance table
        st.subheader("📊 Detailed Performance Metrics")

        # Calculate performance metrics for each fund
        performance_df = mf_df.copy()
        performance_df['current_value'] = performance_df['current_value'].fillna(performance_df['amount_invested'])
        performance_df['absolute_returns'] = performance_df['current_value'] - performance_df['amount_invested']
        performance_df['returns_pct'] = (performance_df['absolute_returns'] / performance_df['amount_invested']) * 100

        # Calculate days invested
        performance_df['days_invested'] = (datetime.now().date() - performance_df['purchase_date'].dt.date).dt.days

        # Annualized returns (approximate)
        performance_df['annualized_returns'] = performance_df.apply(
            lambda row: ((row['current_value'] / row['amount_invested']) ** (
                        365 / max(row['days_invested'], 1)) - 1) * 100 if row['days_invested'] > 0 else 0,
            axis=1
        )

        # Display performance table
        display_cols = [
            'fund_name', 'category', 'amount_invested', 'current_value',
            'absolute_returns', 'returns_pct', 'days_invested', 'annualized_returns'
        ]

        perf_display = performance_df[display_cols].copy()
        perf_display.columns = [
            'Fund Name', 'Category', 'Invested (₹)', 'Current Value (₹)',
            'Absolute Returns (₹)', 'Returns (%)', 'Days Invested', 'Annualized Returns (%)'
        ]

        # Sort by returns percentage
        perf_display = perf_display.sort_values('Returns (%)', ascending=False)

        st.dataframe(
            perf_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Invested (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                "Current Value (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                "Absolute Returns (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                "Returns (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Annualized Returns (%)": st.column_config.NumberColumn(format="%.2f%%"),
            }
        )

        # Performance insights
        st.subheader("💡 Performance Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            best_performer = perf_display.loc[perf_display['Returns (%)'].idxmax()]
            st.metric(
                "🏆 Best Performer",
                best_performer['Fund Name'][:20] + "...",
                f"+{best_performer['Returns (%)']:.2f}%"
            )

        with col2:
            worst_performer = perf_display.loc[perf_display['Returns (%)'].idxmin()]
            st.metric(
                "📉 Needs Attention",
                worst_performer['Fund Name'][:20] + "...",
                f"{worst_performer['Returns (%)']:.2f}%"
            )

        with col3:
            avg_returns = perf_display['Returns (%)'].mean()
            st.metric(
                "📊 Average Returns",
                f"{avg_returns:.2f}%",
                help="Average returns across all funds"
            )

        # Export performance report
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Export Performance Report"):
                performance_csv = perf_display.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV Report",
                    performance_csv,
                    f"mf_performance_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )

        with col2:
            if st.button("🔄 Update All NAVs"):
                st.info("🚧 Real-time NAV update feature coming soon!")
                st.caption("This will fetch latest NAVs from market data providers")