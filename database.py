import sqlite3


def init_db():

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_user_id INTEGER PRIMARY KEY,
        name TEXT,
        dob TEXT,
        notes TEXT,
        is_verified INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER,
        role_name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS class_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_role_id INTEGER,
        class_code TEXT,
        venue_lat REAL,
        venue_lng REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER,
        role_name TEXT,
        class_code TEXT,
        distance REAL,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()