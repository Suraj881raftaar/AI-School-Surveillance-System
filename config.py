# ==========================================
# AI School Surveillance System
# config.py
# ==========================================

import os

# -----------------------------
# Window Settings
# -----------------------------
APP_NAME = "AI School Surveillance System"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# -----------------------------
# Colors
# -----------------------------
BG_COLOR = "#F5F7FA"
HEADER_COLOR = "#0B3D91"
BUTTON_COLOR = "#1976D2"
BUTTON_HOVER = "#1565C0"

SUCCESS_COLOR = "#2E7D32"
WARNING_COLOR = "#EF6C00"
DANGER_COLOR = "#C62828"

TEXT_COLOR = "#212121"
WHITE = "#FFFFFF"

CARD_COLOR = "#FFFFFF"

# -----------------------------
# Fonts
# -----------------------------
TITLE_FONT = ("Arial", 24, "bold")
HEADER_FONT = ("Arial", 18, "bold")
LABEL_FONT = ("Arial", 12)
BUTTON_FONT = ("Arial", 11, "bold")
CARD_TITLE_FONT = ("Arial", 14, "bold")
CARD_VALUE_FONT = ("Arial", 24, "bold")

# -----------------------------
# Login Credentials
# -----------------------------
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "1234"

# -----------------------------
# Database
# -----------------------------
DATABASE_NAME = "school.db"

# -----------------------------
# Project Folders
# -----------------------------
import sys

IS_FROZEN = getattr(sys, 'frozen', False)

if IS_FROZEN:
    RESOURCE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = RESOURCE_DIR

DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")

STUDENT_FOLDER = os.path.join(DATASET_FOLDER, "students")
TEACHER_FOLDER = os.path.join(DATASET_FOLDER, "teachers")

ICON_FOLDER = os.path.join(RESOURCE_DIR, "icons")
HAARCASCADE_FOLDER = os.path.join(RESOURCE_DIR, "haarcascades")
HAARCASCADE_PATH = os.path.join(HAARCASCADE_FOLDER, "haarcascade_frontalface_default.xml")
MODEL_FOLDER = os.path.join(BASE_DIR, "models")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
SCREENSHOT_FOLDER = os.path.join(BASE_DIR, "screenshots")

# -----------------------------
# Files
# -----------------------------
DATABASE_PATH = os.path.join(DATABASE_FOLDER, DATABASE_NAME)

LOGO_PATH = os.path.join(ICON_FOLDER, "ai_school_surveillance.png")
ICON_PATH = os.path.join(ICON_FOLDER, "ai_school_surveillance.ico")

ATTENDANCE_FILE = os.path.join(
    REPORT_FOLDER,
    "attendance.csv"
)

# -----------------------------
# Camera
# -----------------------------
CAMERA_INDEX = 0

# -----------------------------
# Face Detection
# -----------------------------
FACE_WIDTH = 200
FACE_HEIGHT = 200

# -----------------------------
# Create Required Folders & Database Initialization
# -----------------------------
folders = [
    DATABASE_FOLDER,
    STUDENT_FOLDER,
    TEACHER_FOLDER,
    MODEL_FOLDER,
    REPORT_FOLDER,
    LOG_FOLDER,
    SCREENSHOT_FOLDER,
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

def init_database() -> None:
    import shutil
    import sqlite3

    # 1. Copy bundled read-only database to writable path if it doesn't exist
    bundled_db = os.path.join(RESOURCE_DIR, "database", DATABASE_NAME)
    if not os.path.exists(DATABASE_PATH) and os.path.exists(bundled_db):
        try:
            shutil.copy2(bundled_db, DATABASE_PATH)
        except Exception:
            pass

    # 2. Open / create writable database and verify table schemas
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()

        # users table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        # students table
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

        # teachers table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT,
            subject TEXT,
            mobile TEXT,
            image_path TEXT
        )
        """)

        # attendance table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            person_name TEXT,
            person_type TEXT,
            date TEXT,
            time TEXT,
            confidence REAL,
            camera_id INTEGER,
            recognition_method TEXT,
            status TEXT
        )
        """)

        # alerts table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            message TEXT,
            image TEXT,
            alert_type TEXT,
            description TEXT
        )
        """)

        # system_settings table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS system_settings(
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        # Ensure default administrator exists
        cur.execute("SELECT * FROM users WHERE username='admin'")
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users(username, password) VALUES(?, ?)",
                ("admin", "1234")
            )
        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            conn.close()

# Run database schema verifications
init_database()
