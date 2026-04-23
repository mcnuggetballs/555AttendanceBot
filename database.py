import sqlite3

DB_NAME = "attendance.db"


def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10)


def init_db():

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_user_id INTEGER PRIMARY KEY,
        name TEXT,
        dob TEXT,
        notes TEXT,
        verified INTEGER DEFAULT 0
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
        student_name TEXT,
        latitude REAL,
        longitude REAL,
        admin_hours INTEGER,
        date TEXT,
        timestamp TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS late_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER,
        role_name TEXT,
        class_code TEXT,
        student_name TEXT,
        eta TEXT,
        date TEXT,
        timestamp TEXT
    )
    """)

    c.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_attendance
    ON attendance_logs(telegram_user_id, class_code, date)
    """)

    # Ensure admin_hours column exists for older databases
    c.execute("PRAGMA table_info(attendance_logs)")
    columns = [col[1] for col in c.fetchall()]

    # Ensure admin_hours (Hours/Pax) exists
    if "admin_hours" not in columns:
        c.execute("ALTER TABLE attendance_logs ADD COLUMN admin_hours INTEGER")

    conn.commit()
    conn.close()