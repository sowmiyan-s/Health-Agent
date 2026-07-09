import sqlite3
import os
import uuid
import hashlib
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../hia_database.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        content TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User functions
def create_user(email, password, name):
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    created_at = datetime.now().isoformat()
    
    try:
        cursor.execute(
            "INSERT INTO users (id, email, name, password, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, name, hashed, created_at)
        )
        conn.commit()
        user_data = {"id": user_id, "email": email, "name": name, "created_at": created_at}
        return True, user_data
    except sqlite3.IntegrityError:
        return False, "Email already registered"
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = hash_password(password)
    
    cursor.execute(
        "SELECT id, email, name, created_at FROM users WHERE email = ? AND password = ?",
        (email, hashed)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return True, dict(row)
    return False, "Invalid email or password"

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# Session functions
def create_chat_session_db(user_id, title):
    conn = get_db_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO chat_sessions (id, user_id, title, created_at) VALUES (?, ?, ?, ?)",
        (session_id, user_id, title, created_at)
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "user_id": user_id, "title": title, "created_at": created_at}

def get_user_sessions_db(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_session_db(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# Message functions
def save_chat_message_db(session_id, content, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    message_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO chat_messages (id, session_id, content, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (message_id, session_id, content, role, created_at)
    )
    conn.commit()
    conn.close()
    return {"id": message_id, "session_id": session_id, "content": content, "role": role, "created_at": created_at}

def get_session_messages_db(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Config functions
def get_config_db(key, default=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['value']
    except Exception:
        pass
    return default

def set_config_db(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()
