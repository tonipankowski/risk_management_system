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

def change_password(user_id, old_password, new_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT password_hash FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return False
    
    stored_hash = row[0]
    if not bcrypt.checkpw(old_password.encode(), stored_hash.encode()):
        conn.close()
        return False
    
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (new_hash, user_id)
    )
    conn.commit()
    conn.close()
    return True