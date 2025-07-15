import streamlit as st
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthManager:
    """Enhanced authentication system with user management"""

    def __init__(self, db_manager):
        self.db = db_manager

    def hash_password(self, password: str) -> str:
        """Hash password using SHA256 with salt"""
        salt = "santhoshswapna_portfolio_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def register_user(self, username: str, password: str, email: str = "",
                      full_name: str = "", phone: str = "") -> Tuple[bool, str]:
        """Register a new user with enhanced profile"""
        try:
            # Validate input
            if len(username) < 3:
                return False, "Username must be at least 3 characters long"

            if len(password) < 6:
                return False, "Password must be at least 6 characters long"

            # Check if username already exists
            existing_user = self.db.execute_query(
                "SELECT id FROM users WHERE username = ?", (username,)
            )

            if existing_user:
                return False, "Username already exists"

            # Hash password and create user
            password_hash = self.hash_password(password)

            user_data = {
                'username': username,
                'password_hash': password_hash,
                'email': email,
                'full_name': full_name,
                'phone': phone,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            user_id = self.db.insert_record('users', user_data)

            # Create default user preferences
            preferences_data = {
                'user_id': user_id,
                'theme': 'light',
                'currency': 'INR',
                'risk_tolerance': 'moderate',
                'monthly_income': 0,
                'monthly_expenses': 0
            }

            self.db.insert_record('user_preferences', preferences_data)

            logger.info(f"New user registered: {username}")
            return True, "User registered successfully!"

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return False, f"Registration failed: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        try:
            password_hash = self.hash_password(password)

            result = self.db.execute_query("""
                SELECT u.id, u.username, u.email, u.full_name, u.phone, u.created_at,
                       p.risk_tolerance, p.investment_goal, p.monthly_income, p.monthly_expenses
                FROM users u 
                LEFT JOIN user_preferences p ON u.id = p.user_id
                WHERE u.username = ? AND u.password_hash = ?
            """, (username, password_hash))

            if result:
                user_data = result[0]
                return {
                    'id': user_data[0],
                    'username': user_data[1],
                    'email': user_data[2] or '',
                    'full_name': user_data[3] or '',
                    'phone': user_data[4] or '',
                    'created_at': user_data[5],
                    'risk_tolerance': user_data[6] or 'moderate',
                    'investment_goal': user_data[7] or '',
                    'monthly_income': user_data[8] or 0,
                    'monthly_expenses': user_data[9] or 0
                }

            return None

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def update_user_profile(self, user_id: int, profile_data: Dict) -> Tuple[bool, str]:
        """Update user profile information"""
        try:
            # Update users table
            user_fields = ['email', 'full_name', 'phone']
            user_updates = {k: v for k, v in profile_data.items() if k in user_fields}

            if user_updates:
                self.db.update_record('users', user_id, user_updates)

            # Update preferences table
            pref_fields = ['risk_tolerance', 'investment_goal', 'monthly_income', 'monthly_expenses']
            pref_updates = {k: v for k, v in profile_data.items() if k in pref_fields}

            if pref_updates:
                # Check if preferences exist
                existing_prefs = self.db.execute_query(
                    "SELECT id FROM user_preferences WHERE user_id = ?", (user_id,)
                )

                if existing_prefs:
                    # Update existing preferences
                    pref_id = existing_prefs[0][0]
                    self.db.update_record('user_preferences', pref_id, pref_updates)
                else:
                    # Create new preferences
                    pref_updates['user_id'] = user_id
                    self.db.insert_record('user_preferences', pref_updates)

            return True, "Profile updated successfully!"

        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return False, f"Failed to update profile: {str(e)}"

    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Verify current password
            current_hash = self.hash_password(current_password)
            user = self.db.execute_query(
                "SELECT id FROM users WHERE id = ? AND password_hash = ?",
                (user_id, current_hash)
            )

            if not user:
                return False, "Current password is incorrect"

            # Validate new password
            if len(new_password) < 6:
                return False, "New password must be at least 6 characters long"

            # Update password
            new_hash = self.hash_password(new_password)
            success = self.db.update_record('users', user_id, {'password_hash': new_hash})

            if success:
                return True, "Password changed successfully!"
            else:
                return False, "Failed to change password"

        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            return False, f"Failed to change password: {str(e)}"

    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics and activity"""
        try:
            stats = {}

            # Investment stats
            mf_count = self.db.execute_query(
                "SELECT COUNT(*) FROM mutual_funds WHERE user_id = ?", (user_id,)
            )[0][0]

            stocks_count = self.db.execute_query(
                "SELECT COUNT(*) FROM stocks WHERE user_id = ?", (user_id,)
            )[0][0]

            expenses_count = self.db.execute_query(
                "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
            )[0][0]

            goals_count = self.db.execute_query(
                "SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,)
            )[0][0]

            # Total investment value
            mf_total = self.db.execute_query(
                "SELECT COALESCE(SUM(amount_invested), 0) FROM mutual_funds WHERE user_id = ?",
                (user_id,)
            )[0][0]

            stocks_total = self.db.execute_query(
                "SELECT COALESCE(SUM(quantity * purchase_price), 0) FROM stocks WHERE user_id = ?",
                (user_id,)
            )[0][0]

            stats = {
                'mutual_funds_count': mf_count,
                'stocks_count': stocks_count,
                'expenses_count': expenses_count,
                'goals_count': goals_count,
                'total_mf_investment': mf_total,
                'total_stocks_investment': stocks_total,
                'total_investment': mf_total + stocks_total
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}

    def delete_user_account(self, user_id: int, password: str) -> Tuple[bool, str]:
        """Delete user account and all associated data"""
        try:
            # Verify password
            password_hash = self.hash_password(password)
            user = self.db.execute_query(
                "SELECT id FROM users WHERE id = ? AND password_hash = ?",
                (user_id, password_hash)
            )

            if not user:
                return False, "Password is incorrect"

            # Delete all user data
            tables = ['ai_interactions', 'portfolio_snapshots', 'transactions',
                      'goals', 'expenses', 'stocks', 'mutual_funds',
                      'user_preferences', 'users']

            for table in tables:
                self.db.execute_query(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))

            return True, "Account deleted successfully"

        except Exception as e:
            logger.error(f"Account deletion error: {str(e)}")
            return False, f"Failed to delete account: {str(e)}"


def init_session_state():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0


def login_page(auth_manager: AuthManager):
    """Enhanced login/register page"""
    st.markdown('<div class="main-header"><h1>🏦 SanthoshSwapna Portfolio Manager</h1></div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Register", "❓ About"])

    with tab1:
        st.subheader("Welcome Back!")

        # Show login attempts warning
        if st.session_state.login_attempts >= 3:
            st.error("⚠️ Multiple failed login attempts. Please try again later.")
            return

        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🚀 Login", use_container_width=True):
                if username and password:
                    user_data = auth_manager.authenticate_user(username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user_data = user_data
                        st.session_state.login_attempts = 0
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        st.error("❌ Invalid username or password")
                else:
                    st.error("Please enter both username and password")

        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.login_username = ""
                st.session_state.login_password = ""
                st.rerun()

    with tab2:
        st.subheader("Create Your Account")

        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Username *", key="reg_username",
                                         placeholder="Choose a username (min 3 chars)")
            new_password = st.text_input("Password *", type="password", key="reg_password",
                                         placeholder="Choose a password (min 6 chars)")
            confirm_password = st.text_input("Confirm Password *", type="password", key="reg_confirm",
                                             placeholder="Confirm your password")

        with col2:
            full_name = st.text_input("Full Name", key="reg_fullname", placeholder="Your full name")
            email = st.text_input("Email", key="reg_email", placeholder="your@email.com")
            phone = st.text_input("Phone", key="reg_phone", placeholder="Your phone number")

        st.markdown("*Required fields")

        if st.button("📝 Create Account", use_container_width=True):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = auth_manager.register_user(
                        new_username, new_password, email, full_name, phone
                    )
                    if success:
                        st.success(f"✅ {message}")
                        st.info("You can now login with your credentials!")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match")
            else:
                st.error("❌ Please fill all required fields")

    with tab3:
        st.subheader("About SanthoshSwapna Portfolio Manager")

        st.markdown("""
        ### 🚀 Features
        - **Portfolio Management**: Track mutual funds and stocks
        - **Expense Tracking**: Monitor your spending patterns  
        - **Goal Planning**: Set and achieve financial goals
        - **AI Advisor**: Get personalized investment advice
        - **Data Import**: Upload CSV/Excel files
        - **Analytics**: Visual insights and reports

        ### 🔒 Security
        - Encrypted password storage
        - Secure user authentication
        - Private data isolation

        ### 💡 AI-Powered Insights
        - Powered by DeepSeek AI
        - Personalized recommendations
        - Market analysis and insights
        - Risk assessment and optimization
        """)

        st.info("💰 Start managing your wealth intelligently today!")


def logout():
    """Logout function"""
    st.session_state.authenticated = False
    st.session_state.user_data = None
    st.session_state.login_attempts = 0
    st.rerun()