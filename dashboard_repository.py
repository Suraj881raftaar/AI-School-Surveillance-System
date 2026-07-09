import os
import sqlite3
from datetime import datetime

from config import DATABASE_PATH


class DashboardRepository:

    VALID_TABLES = {
        "students",
        "teachers",
        "attendance",
        "alerts",
    }

    def __init__(self):

        self.database_path = DATABASE_PATH
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