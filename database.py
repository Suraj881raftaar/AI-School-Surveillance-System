# ==========================================
# AI School Surveillance System
# database.py
# ==========================================

import sqlite3
from config import DATABASE_PATH

# Connect Database
conn = sqlite3.connect(DATABASE_PATH)
cur = conn.cursor()

# ============================
# USERS TABLE
# ============================
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ============================
# STUDENTS TABLE
# ============================
cur.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    class_name TEXT,
    roll_no TEXT UNIQUE,
    gender TEXT,
    mobile TEXT,
    image_path TEXT
)
""")

# ============================
# TEACHERS TABLE
# ============================
cur.execute("""
CREATE TABLE IF NOT EXISTS teachers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT,
    subject TEXT,
    mobile TEXT,
    image_path TEXT
)
""")

# ============================
# ATTENDANCE TABLE
# ============================
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_name TEXT,
    person_type TEXT,
    date TEXT,
    time TEXT,
    status TEXT
)
""")

# ============================
# ALERTS TABLE
# ============================
cur.execute("""
CREATE TABLE IF NOT EXISTS alerts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,
    description TEXT,
    date TEXT,
    time TEXT
)
""")

# ============================
# DEFAULT LOGIN
# ============================
cur.execute("SELECT * FROM users WHERE username='admin'")

if cur.fetchone() is None:
    cur.execute(
        "INSERT INTO users(username,password) VALUES(?,?)",
        ("admin", "1234")
    )

conn.commit()
conn.close()

print("====================================")
print("Database Created Successfully")
print("Default Username : admin")
print("Default Password : 1234")
print("====================================")