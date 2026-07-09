import os
import sqlite3
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from config import DATABASE_PATH, DATASET_FOLDER, MODEL_FOLDER, LOG_FOLDER, BASE_DIR


class DashboardRepository:

    VALID_TABLES = {
        "students",
        "teachers",
        "attendance",
        "alerts",
    }

    def __init__(self):
        self.database_path = DATABASE_PATH
        self.ensure_indexes()
            # ==========================================
    # Database Connection
    # ==========================================

    def _connect(self) -> sqlite3.Connection:

        os.makedirs(
            os.path.dirname(self.database_path),
            exist_ok=True
        )

        conn = sqlite3.connect(
            self.database_path
        )

        conn.row_factory = sqlite3.Row

        return conn
        # ==========================================
    # Count Total Rows
    # ==========================================

    def count_rows(self, table_name: str) -> int:
        if table_name not in self.VALID_TABLES:
            raise ValueError(f"Unsupported table: {table_name}")

        conn = None
        try:
            conn = self._connect()
            cursor = conn.execute(f"SELECT COUNT(*) AS total FROM {table_name}")
            row = cursor.fetchone()
            return int(row["total"]) if row else 0
        except sqlite3.Error:
            return 0
        finally:
            if conn:
                conn.close()

    def count_today(self, table_name: str) -> int:
        if table_name not in {"attendance", "alerts"}:
            raise ValueError(f"Unsupported table: {table_name}")

        today = datetime.now()
        accepted_dates = (
            today.strftime("%Y-%m-%d"),
            today.strftime("%d-%m-%Y"),
            today.strftime("%d/%m/%Y"),
            today.strftime("%d %B %Y"),
            today.strftime("%d %b %Y"),
        )

        placeholders = ", ".join("?" for _ in accepted_dates)
        conn = None
        try:
            conn = self._connect()
            cursor = conn.execute(
                f"SELECT COUNT(*) AS total FROM {table_name} WHERE date IN ({placeholders})",
                accepted_dates
            )
            row = cursor.fetchone()
            return int(row["total"]) if row else 0
        except sqlite3.Error:
            return 0
        finally:
            if conn:
                conn.close()

    def latest_attendance(self, limit: int = 7) -> list[sqlite3.Row]:
        return self._latest_rows(
            "attendance",
            ("person_name", "person_type", "date", "time", "status"),
            limit
        )

    def latest_alerts(self, limit: int = 7) -> list[sqlite3.Row]:
        return self._latest_rows(
            "alerts",
            ("alert_type", "description", "date", "time"),
            limit
        )

    def _latest_rows(
        self,
        table_name: str,
        columns: tuple[str, ...],
        limit: int,
    ) -> list[sqlite3.Row]:
        if table_name not in self.VALID_TABLES:
            raise ValueError(f"Unsupported table: {table_name}")

        column_sql = ", ".join(columns)
        conn = None
        try:
            conn = self._connect()
            cursor = conn.execute(
                f"SELECT {column_sql} FROM {table_name} ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return list(cursor.fetchall())
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def metrics(self) -> dict[str, int]:
        return {
            "students": self.count_rows("students"),
            "teachers": self.count_rows("teachers"),
            "attendance": self.count_today("attendance"),
            "alerts": self.count_today("alerts"),
        }

    def ensure_indexes(self) -> None:
        """Create database indexes to optimize query speeds."""
        conn = None
        try:
            conn = self._connect()
            conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_person ON attendance(person_id, person_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_date ON alerts(date)")
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

    def get_setting(self, key: str, default: str) -> str:
        """Fetch persistent configurations from the database."""
        conn = None
        try:
            conn = self._connect()
            conn.execute("CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY, value TEXT)")
            row = conn.execute("SELECT value FROM system_settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default
        except sqlite3.Error:
            return default
        finally:
            if conn:
                conn.close()

    def set_setting(self, key: str, value: str) -> None:
        """Save persistent configurations to the database."""
        conn = None
        try:
            conn = self._connect()
            conn.execute("CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("INSERT OR REPLACE INTO system_settings(key, value) VALUES (?, ?)", (key, value))
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

    def get_advanced_analytics(self) -> dict:
        """Compiles real-time metrics, accuracy rates, and attendance trends."""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        stats = {
            "attendance_today": 0,
            "students_present": 0,
            "teachers_present": 0,
            "unknown_today": 0,
            "attendance_pct": 0.0,
            "avg_confidence": 0.0,
            "accuracy": 100.0,
            "last_recognition_name": "N/A",
            "last_recognition_time": "N/A",
            "weekly_trend": [],
            "most_recognized": [],
            "registrations_today": 0
        }

        conn = None
        try:
            conn = self._connect()
            
            # Today's counts
            row = conn.execute("SELECT COUNT(*) AS total FROM attendance WHERE date = ?", (date_str,)).fetchone()
            if row: stats["attendance_today"] = row["total"]

            row = conn.execute("SELECT COUNT(*) AS total FROM attendance WHERE date = ? AND person_type = 'Student'", (date_str,)).fetchone()
            if row: stats["students_present"] = row["total"]

            row = conn.execute("SELECT COUNT(*) AS total FROM attendance WHERE date = ? AND person_type = 'Teacher'", (date_str,)).fetchone()
            if row: stats["teachers_present"] = row["total"]

            row = conn.execute("SELECT COUNT(*) AS total FROM alerts WHERE date = ?", (date_str,)).fetchone()
            if row: stats["unknown_today"] = row["total"]

            # Attendance % (Students)
            students_row = conn.execute("SELECT COUNT(*) AS total FROM students").fetchone()
            total_students = students_row["total"] if students_row else 0
            if total_students > 0:
                stats["attendance_pct"] = (stats["students_present"] / total_students) * 100.0

            # Avg confidence based on LBPH distance values
            conf_row = conn.execute("SELECT AVG(confidence) AS avg_c FROM attendance WHERE date = ? AND confidence IS NOT NULL", (date_str,)).fetchone()
            if conf_row and conf_row["avg_c"] is not None:
                stats["avg_confidence"] = max(0.0, 100.0 - conf_row["avg_c"])

            # Accuracy (Recognized vs total detections)
            total_det = stats["attendance_today"] + stats["unknown_today"]
            if total_det > 0:
                stats["accuracy"] = (stats["attendance_today"] / total_det) * 100.0

            # Last recognition
            last_row = conn.execute("SELECT person_name, time FROM attendance WHERE date = ? ORDER BY id DESC LIMIT 1", (date_str,)).fetchone()
            if last_row:
                stats["last_recognition_name"] = last_row["person_name"]
                stats["last_recognition_time"] = last_row["time"]

            # Weekly attendance trend (past 7 days)
            cursor = conn.execute(
                "SELECT date, COUNT(*) AS count FROM attendance GROUP BY date ORDER BY date DESC LIMIT 7"
            )
            stats["weekly_trend"] = list(reversed([(r["date"], r["count"]) for r in cursor.fetchall()]))

            # Most recognized
            cursor = conn.execute(
                "SELECT person_name, COUNT(*) AS count FROM attendance GROUP BY person_name ORDER BY count DESC LIMIT 5"
            )
            stats["most_recognized"] = [(r["person_name"], r["count"]) for r in cursor.fetchall()]

            # Registrations today
            cursor = conn.execute(
                "SELECT (SELECT COUNT(*) FROM students WHERE image_path LIKE ?) + (SELECT COUNT(*) FROM teachers WHERE image_path LIKE ?) AS total",
                (f"%_{date_str.replace('-', '')}_%", f"%_{date_str.replace('-', '')}_%")
            )
            reg_row = cursor.fetchone()
            if reg_row:
                stats["registrations_today"] = reg_row["total"]

        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

        return stats

    def create_backup(self, backup_dir: str, db: bool, dataset: bool, models: bool, logs: bool) -> str:
        """Pack selected system components into a timestamped zip archive."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_name)

        os.makedirs(backup_dir, exist_ok=True)

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if db and os.path.exists(DATABASE_PATH):
                zipf.write(DATABASE_PATH, os.path.basename(DATABASE_PATH))

            if dataset and os.path.exists(DATASET_FOLDER):
                for root, _, files in os.walk(DATASET_FOLDER):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(DATASET_FOLDER))
                        zipf.write(file_path, arcname)

            if models and os.path.exists(MODEL_FOLDER):
                for root, _, files in os.walk(MODEL_FOLDER):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(MODEL_FOLDER))
                        zipf.write(file_path, arcname)

            if logs and os.path.exists(LOG_FOLDER):
                for root, _, files in os.walk(LOG_FOLDER):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(LOG_FOLDER))
                        zipf.write(file_path, arcname)

        return backup_path

    def restore_backup(self, zip_path: str) -> None:
        """Extract and restore files from selected backup zip."""
        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            
            # Validation
            has_db = "school.db" in namelist
            has_dataset = any(name.startswith("dataset/") for name in namelist)
            
            if not has_db and not has_dataset:
                raise ValueError("Invalid backup zip: Missing core surveillance files.")

            for name in namelist:
                if name == "school.db":
                    zipf.extract(name, os.path.dirname(DATABASE_PATH))
                elif name.startswith("dataset/") or name.startswith("models/") or name.startswith("logs/"):
                    zipf.extract(name, BASE_DIR)