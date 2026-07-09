"""
settings_manager.py
AI School Surveillance System
"""

import os
import sqlite3
from typing import Callable, Any
from config import DATABASE_PATH, DATASET_FOLDER, MODEL_FOLDER, REPORT_FOLDER


class SettingsManager:
    """Singleton Configurations Manager utilizing the Observer Pattern."""

    _instance = None
    _listeners: list[Callable[[str, Any], None]] = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self) -> None:
        self.database_path = DATABASE_PATH
        self.defaults = {
            "dataset_path": DATASET_FOLDER,
            "model_path": MODEL_FOLDER,
            "export_path": REPORT_FOLDER,
            "attendance_cooldown": "60",
            "camera_index": "0",
            "recognition_threshold": "65.0",
            "theme": "default",
        }
        self.ensure_settings_table()

    def _connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_settings_table(self) -> None:
        conn = None
        try:
            conn = self._connect()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

    def get(self, key: str) -> str:
        default_val = self.defaults.get(key, "")
        conn = None
        try:
            conn = self._connect()
            row = conn.execute(
                "SELECT value FROM system_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default_val
        except sqlite3.Error:
            return default_val
        finally:
            if conn:
                conn.close()

    def set(self, key: str, value: str) -> bool:
        # Validation checks
        if key in ("camera_index", "attendance_cooldown"):
            try:
                int(value)
            except ValueError:
                return False
        elif key == "recognition_threshold":
            try:
                float(value)
            except ValueError:
                return False

        conn = None
        try:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO system_settings(key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()

            # Notify listeners of settings updates
            self.notify_listeners(key, value)
            return True
        except sqlite3.Error:
            return False
        finally:
            if conn:
                conn.close()

    def register_listener(self, callback: Callable[[str, Any], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str, Any], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self, key: str, value: Any) -> None:
        for listener in self._listeners:
            try:
                listener(key, value)
            except Exception:
                pass
