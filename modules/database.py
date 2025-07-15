import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database management for the portfolio app"""

    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize all database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    theme TEXT DEFAULT 'light',
                    currency TEXT DEFAULT 'INR',
                    risk_tolerance TEXT DEFAULT 'moderate',
                    investment_goal TEXT,
                    monthly_income REAL,
                    monthly_expenses REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Mutual funds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mutual_funds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    fund_name TEXT NOT NULL,
                    fund_house TEXT,
                    scheme_code TEXT,
                    isin TEXT,
                    amount_invested REAL NOT NULL,
                    units REAL,
                    nav REAL,
                    purchase_date DATE,
                    current_value REAL,
                    category TEXT,
                    subcategory TEXT,
                    expense_ratio REAL,
                    fund_manager TEXT,
                    risk_level TEXT,
                    returns_1y REAL,
                    returns_3y REAL,
                    returns_5y REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Stocks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stock_name TEXT NOT NULL,
                    symbol TEXT,
                    exchange TEXT,
                    quantity INTEGER,
                    purchase_price REAL,
                    current_price REAL,
                    purchase_date DATE,
                    sector TEXT,
                    industry TEXT,
                    market_cap TEXT,
                    pe_ratio REAL,
                    dividend_yield REAL,
                    beta REAL,
                    stop_loss REAL,
                    target_price REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    description TEXT,
                    amount REAL NOT NULL,
                    date DATE,
                    type TEXT DEFAULT 'expense',
                    payment_method TEXT,
                    tags TEXT,
                    is_recurring BOOLEAN DEFAULT FALSE,
                    recurring_frequency TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Financial goals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    goal_name TEXT NOT NULL,
                    description TEXT,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    target_date DATE,
                    category TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'active',
                    monthly_contribution REAL,
                    auto_invest BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Transactions table (for tracking all financial transactions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_type TEXT NOT NULL,
                    asset_type TEXT,
                    asset_id INTEGER,
                    amount REAL NOT NULL,
                    quantity REAL,
                    price REAL,
                    transaction_date DATE,
                    fees REAL DEFAULT 0,
                    taxes REAL DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # AI interactions table (for storing AI conversations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    context TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Portfolio snapshots (for tracking portfolio performance over time)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    snapshot_date DATE,
                    total_investment REAL,
                    current_value REAL,
                    total_returns REAL,
                    returns_percentage REAL,
                    asset_allocation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a database query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()
            result = cursor.fetchall()
            conn.close()
            return result

        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def get_dataframe(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Get pandas DataFrame from query"""
        try:
            conn = sqlite3.connect(self.db_path)

            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)

            conn.close()
            return df

        except Exception as e:
            logger.error(f"Error getting dataframe: {str(e)}")
            return pd.DataFrame()

    def insert_record(self, table: str, data: Dict) -> int:
        """Insert a record and return the ID"""
        try:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = list(data.values())

            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, values)
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return record_id

        except Exception as e:
            logger.error(f"Error inserting record into {table}: {str(e)}")
            raise

    def update_record(self, table: str, record_id: int, data: Dict) -> bool:
        """Update a record by ID"""
        try:
            set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
            values = list(data.values()) + [record_id]

            query = f"UPDATE {table} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error updating record in {table}: {str(e)}")
            return False

    def delete_record(self, table: str, record_id: int) -> bool:
        """Delete a record by ID"""
        try:
            query = f"DELETE FROM {table} WHERE id = ?"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, (record_id,))
            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error deleting record from {table}: {str(e)}")
            return False

    def get_user_portfolio_summary(self, user_id: int) -> Dict:
        """Get comprehensive portfolio summary for a user"""
        try:
            # Mutual funds summary
            mf_query = """
                SELECT 
                    COUNT(*) as total_funds,
                    SUM(amount_invested) as total_invested,
                    SUM(current_value) as total_current_value,
                    category
                FROM mutual_funds 
                WHERE user_id = ? 
                GROUP BY category
            """
            mf_summary = self.get_dataframe(mf_query, (user_id,))

            # Stocks summary
            stocks_query = """
                SELECT 
                    COUNT(*) as total_stocks,
                    SUM(quantity * purchase_price) as total_invested,
                    SUM(quantity * current_price) as total_current_value,
                    sector
                FROM stocks 
                WHERE user_id = ? 
                GROUP BY sector
            """
            stocks_summary = self.get_dataframe(stocks_query, (user_id,))

            # Expenses summary
            expenses_query = """
                SELECT 
                    category,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income
                FROM expenses 
                WHERE user_id = ? AND date >= date('now', '-30 days')
                GROUP BY category
            """
            expenses_summary = self.get_dataframe(expenses_query, (user_id,))

            # Goals summary
            goals_query = """
                SELECT 
                    COUNT(*) as total_goals,
                    SUM(target_amount) as total_target,
                    SUM(current_amount) as total_current,
                    status
                FROM goals 
                WHERE user_id = ? 
                GROUP BY status
            """
            goals_summary = self.get_dataframe(goals_query, (user_id,))

            return {
                'mutual_funds': mf_summary,
                'stocks': stocks_summary,
                'expenses': expenses_summary,
                'goals': goals_summary
            }

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return {}

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            return False

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            stats = {}
            tables = ['users', 'mutual_funds', 'stocks', 'expenses', 'goals', 'transactions']

            for table in tables:
                query = f"SELECT COUNT(*) FROM {table}"
                result = self.execute_query(query)
                stats[table] = result[0][0] if result else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}