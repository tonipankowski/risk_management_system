import sqlite3
import pandas as pd

DB_PATH = "data/portfolio.db"

def init_db():
    """Create the positions table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            user_id  TEXT,
            ticker   TEXT,
            quantity REAL,
            asset_type TEXT,
            PRIMARY KEY (user_id, ticker)
        )
    """)
    conn.commit()
    conn.close()
    
def save_positions(positions, asset_types, user_id="default"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # clear this user's old positions first
    cursor.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
    # insert each ticker/quantity
    for ticker, quantity in positions.items():
        cursor.execute(
            "INSERT INTO positions (user_id, ticker, quantity, asset_type) VALUES (?, ?, ?, ?)",
            (user_id, ticker, float(quantity), asset_types[ticker]),
        )
    conn.commit()
    conn.close()

def load_positions(user_id="default"):
    """Load a user's positions as a Series indexed by ticker."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticker, quantity, asset_type FROM positions WHERE user_id = ?", (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    positions = pd.Series({ticker: qty for ticker, qty, atype in rows})
    asset_types = {ticker: atype for ticker, qty, atype in rows}
    # turn [(ticker, qty), ...] into a Series indexed by ticker
    return positions, asset_types   
