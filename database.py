import sqlite3

DB_NAME = "attendance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_user_id INTEGER PRIMARY KEY,
        name TEXT,
        dob TEXT,
        notes TEXT
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
        role_id INTEGER,
        class_code TEXT,
        venue_name TEXT,
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
        latitude REAL,
        longitude REAL,
        date TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()