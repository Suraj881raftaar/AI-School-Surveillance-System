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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")

STUDENT_FOLDER = os.path.join(DATASET_FOLDER, "students")
TEACHER_FOLDER = os.path.join(DATASET_FOLDER, "teachers")

ICON_FOLDER = os.path.join(BASE_DIR, "icons")
HAARCASCADE_FOLDER = os.path.join(BASE_DIR, "haarcascades")
HAARCASCADE_PATH = os.path.join(HAARCASCADE_FOLDER, "haarcascade_frontalface_default.xml")
MODEL_FOLDER = os.path.join(BASE_DIR, "models")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
SCREENSHOT_FOLDER = os.path.join(BASE_DIR, "screenshots")

# -----------------------------
# Files
# -----------------------------
DATABASE_PATH = os.path.join(DATABASE_FOLDER, DATABASE_NAME)

LOGO_PATH = os.path.join(ICON_FOLDER, "logo.png")
ICON_PATH = os.path.join(ICON_FOLDER, "icon.ico")

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
# Create Required Folders
# -----------------------------
folders = [
    DATABASE_FOLDER,
    STUDENT_FOLDER,
    TEACHER_FOLDER,
    ICON_FOLDER,
    HAARCASCADE_FOLDER,
    MODEL_FOLDER,
    REPORT_FOLDER,
    LOG_FOLDER,
    SCREENSHOT_FOLDER,
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
