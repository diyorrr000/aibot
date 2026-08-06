import sqlite3
import os

DB_FILE = "database/userbot.db"

def init_db():
    if not os.path.exists("database"):
        os.makedirs("database", exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        user_id INTEGER PRIMARY KEY,
        phone TEXT,
        session_string TEXT,
        read_msg INTEGER DEFAULT 0,
        typing_msg INTEGER DEFAULT 0,
        online_msg INTEGER DEFAULT 0
    )
    ''')
    
    # Admins table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        nickname TEXT,
        is_owner INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

def get_sessions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, phone, session_string, read_msg as read, typing_msg as typing, online_msg as online FROM sessions")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_session(user_id, phone, session_string):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO sessions (user_id, phone, session_string)
    VALUES (?, ?, ?)
    ''', (user_id, phone, session_string))
    conn.commit()
    conn.close()

def update_session_setting(user_id, key, value):
    # key should be one of: read_msg, typing_msg, online_msg
    # Note: I renamed columns to avoid SQL keyword conflicts or for clarity
    valid_keys = ["read_msg", "typing_msg", "online_msg"]
    if key not in valid_keys:
        # Fallback if old code uses 'read', 'typing', 'online'
        mapping = {"read": "read_msg", "typing": "typing_msg", "online": "online_msg"}
        key = mapping.get(key, key)
        if key not in valid_keys: return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE sessions SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def delete_session(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Admin management
def add_admin(user_id, nickname, is_owner=0):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO admins (user_id, nickname, is_owner) VALUES (?, ?, ?)", (user_id, nickname, is_owner))
    conn.commit()
    conn.close()

def remove_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE user_id = ? AND is_owner = 0", (user_id,))
    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def get_admins():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_owner_id():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE is_owner = 1 LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None
