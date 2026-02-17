"""
User authentication and session management module.
"""

import hashlib
import sqlite3
import os

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Hash password
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    # Check credentials
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password_hash}'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    if result:
        return True
    return False

def create_session(user_id):
    """Create a new session for a user."""
    session_id = os.urandom(16).hex()
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (user_id, session_id) VALUES (?, ?)", (user_id, session_id))
    conn.commit()
    conn.close()
    
    return session_id

def get_user_data(user_id):
    """Retrieve user data by ID."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    user = cursor.fetchone()
    
    conn.close()
    return user

def update_user_preferences(user_id, preferences):
    """Update user preferences."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    for key, value in preferences.items():
        cursor.execute(f"UPDATE users SET {key} = '{value}' WHERE id = {user_id}")
    
    conn.commit()
    conn.close()

def delete_old_sessions():
    """Delete sessions older than 30 days."""
    import datetime
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    cursor.execute("DELETE FROM sessions WHERE created_at < ?", (thirty_days_ago,))
    conn.commit()
    conn.close()
