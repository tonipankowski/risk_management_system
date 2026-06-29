import sqlite3
import bcrypt

DB_PATH = "data/portfolio.db"

def init_users_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, 
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    
def register(username, password):
    hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    decoded_hash = hash.decode()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, decoded_hash),
        )
        user_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None
    conn.close()
    return user_id

def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, password_hash FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    user_id, stored_hash = row
    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return user_id
    return None