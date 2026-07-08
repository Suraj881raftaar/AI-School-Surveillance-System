"""
attendance.py
AI School Surveillance System
"""

from __future__ import annotations

import csv
import os
import sqlite3
import sys
import subprocess
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from config import *


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
PERSON_TYPES = ("Student", "Teacher")
FILTER_TYPES = ("All", "Student", "Teacher")
STATUSES = ("Present", "Absent", "Late")


@dataclass(frozen=True)
class AttendanceRecord:
    record_id: int
    person_name: str
    person_type: str
    date: str
    time: str
    status: str


class AttendanceDB:
    """SQLite helper for attendance records."""

    def __init__(self) -> None:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.ensure_table()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_table(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_name TEXT,
                    person_type TEXT,
                    date TEXT,
                    time TEXT,
                    status TEXT
                )
                """
            )

            required_columns = {
                "person_name": "TEXT",
                "person_type": "TEXT",
                "date": "TEXT",
                "time": "TEXT",
                "status": "TEXT",
            }
            existing_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(attendance)")
            }

            for column_name, column_type in required_columns.items():
                if column_name not in existing_columns:
                    conn.execute(
                        f"ALTER TABLE attendance ADD COLUMN {column_name} {column_type}"
                    )

            conn.commit()

    def insert_record(
        self,
        person_name: str,
        person_type: str,
        date: str,
        time_value: str,
        status: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO attendance(person_name, person_type, date, time, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (person_name, person_type, date, time_value, status),
            )
            conn.commit()

    def delete_record(self, record_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
            conn.commit()

    def fetch_records(
        self,
        name: str = "",
        date: str = "",
        person_type: str = "All",
    ) -> list[AttendanceRecord]:
        conditions = []
        params: list[str] = []

        if name.strip():
            conditions.append("person_name LIKE ?")
            params.append(f"%{name.strip()}%")

        if date.strip():
            conditions.append("date = ?")
            params.append(date.strip())

        if person_type in PERSON_TYPES:
            conditions.append("person_type = ?")
            params.append(person_type)

        where_sql = ""
        if conditions:
            where_sql = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT id, person_name, person_type, date, time, status
            FROM attendance
            {where_sql}
            ORDER BY date DESC, time DESC, id DESC
        """

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            AttendanceRecord(
                record_id=int(row["id"]),
                person_name=row["person_name"] or "",
                person_type=row["person_type"] or "",
                date=row["date"] or "",
                time=row["time"] or "",
                status=row["status"] or "",
            )
            for row in rows
        ]


class AttendanceFrame(ttk.Frame):
    """Attendance management UI."""

    def __init__(self, parent, app=None) -> None:
        super().__init__(parent)

        self.app = app
        self.db = AttendanceDB()
        self.selected_id: int | None = None
        self.current_records: list[AttendanceRecord] = []

        now = datetime.now()
        self.person_name = tk.StringVar()
        self.person_type = tk.StringVar(value=PERSON_TYPES[0])
        self.date = tk.StringVar(value=now.strftime(DATE_FORMAT))
        self.time = tk.StringVar(value=now.strftime(TIME_FORMAT))
        self.status = tk.StringVar(value=STATUSES[0])
        self.search_name = tk.StringVar()
        self.filter_date = tk.StringVar()
        self.filter_type = tk.StringVar(value=FILTER_TYPES[0])
        self.total_text = tk.StringVar(value="Total Attendance: 0")
        self.status_text = tk.StringVar(value="Ready")

        self.configure(style="Attendance.TFrame")
        self.configure_styles()
        self.create_widgets()
        self.load_attendance()

    def configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Attendance.TFrame", background=BG_COLOR)
        style.configure("AttendancePanel.TFrame", background=WHITE)
        style.configure(
            "AttendanceTitle.TLabel",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 20, "bold"),
        )
        style.configure(
            "AttendanceSubtitle.TLabel",
            background=BG_COLOR,
            foreground="#667085",
            font=("Arial", 10),
        )
        style.configure(
            "AttendancePanelTitle.TLabel",
            background=WHITE,
            foreground=HEADER_COLOR,
            font=("Arial", 13, "bold"),
        )
        style.configure(
            "AttendanceLabel.TLabel",
            background=WHITE,
            foreground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
        )
        style.configure(
            "AttendanceMuted.TLabel",
            background=WHITE,
            foreground="#667085",
            font=("Arial", 9),
        )
        style.configure(
            "AttendanceMetric.TLabel",
            background=WHITE,
            foreground=HEADER_COLOR,
            font=("Arial", 14, "bold"),
        )
        style.configure(
            "Primary.TButton",
            background=BUTTON_COLOR,
            foreground=WHITE,
            font=BUTTON_FONT,
            padding=(10, 7),
        )
        style.map(
            "Primary.TButton",
            background=[("active", BUTTON_HOVER), ("pressed", BUTTON_HOVER)],
            foreground=[("active", WHITE)],
        )
        style.configure(
            "Success.TButton",
            background=SUCCESS_COLOR,
            foreground=WHITE,
            font=BUTTON_FONT,
            padding=(10, 7),
        )
        style.map(
            "Success.TButton",
            background=[("active", "#256D2B"), ("pressed", "#1E5A23")],
            foreground=[("active", WHITE)],
        )
        style.configure(
            "Danger.TButton",
            background=DANGER_COLOR,
            foreground=WHITE,
            font=BUTTON_FONT,
            padding=(10, 7),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#A61B1B"), ("pressed", "#8E1717")],
            foreground=[("active", WHITE)],
        )
        style.configure(
            "Attendance.Treeview",
            font=("Arial", 10),
            rowheight=28,
            background=WHITE,
            fieldbackground=WHITE,
            foreground=TEXT_COLOR,
        )
        style.configure(
            "Attendance.Treeview.Heading",
            font=("Arial", 10, "bold"),
            foreground=HEADER_COLOR,
        )

    def create_widgets(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Attendance.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="ATTENDANCE MANAGEMENT",
            style="AttendanceTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Manage manual attendance records and generate reports.",
            style="AttendanceSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.create_form_panel()
        self.create_table_panel()
        self.create_status_bar()

    def create_form_panel(self) -> None:
        panel = ttk.Frame(self, style="AttendancePanel.TFrame", padding=18)
        panel.grid(row=1, column=0, sticky="ns", padx=(0, 16))
        panel.grid_columnconfigure(1, weight=1)

        ttk.Label(
            panel,
            text="Manual Attendance Entry",
            style="AttendancePanelTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.add_entry(panel, "Person Name", self.person_name, 1)

        ttk.Label(panel, text="Person Type", style="AttendanceLabel.TLabel").grid(
            row=2,
            column=0,
            padx=(0, 10),
            pady=8,
            sticky="w",
        )
        ttk.Combobox(
            panel,
            textvariable=self.person_type,
            values=PERSON_TYPES,
            state="readonly",
            width=25,
        ).grid(row=2, column=1, pady=8, sticky="ew")

        self.add_entry(panel, "Date", self.date, 3)
        self.add_entry(panel, "Time", self.time, 4)

        ttk.Label(panel, text="Status", style="AttendanceLabel.TLabel").grid(
            row=5,
            column=0,
            padx=(0, 10),
            pady=8,
            sticky="w",
        )
        ttk.Combobox(
            panel,
            textvariable=self.status,
            values=STATUSES,
            state="readonly",
            width=25,
        ).grid(row=5, column=1, pady=8, sticky="ew")

        button_frame = ttk.Frame(panel, style="AttendancePanel.TFrame")
        button_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        button_frame.grid_columnconfigure((0, 1), weight=1, uniform="form_buttons")

        ttk.Button(
            button_frame,
            text="Add Attendance",
            command=self.mark_attendance,
            style="Success.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        ttk.Button(
            button_frame,
            text="Delete",
            command=self.delete_attendance,
            style="Danger.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.load_attendance,
            style="Primary.TButton",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=5)
        ttk.Button(
            button_frame,
            text="Print",
            command=self.print_report,
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=5)

        ttk.Label(
            panel,
            textvariable=self.total_text,
            style="AttendanceMetric.TLabel",
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(18, 6))

        ttk.Label(
            panel,
            text="Date format: YYYY-MM-DD",
            style="AttendanceMuted.TLabel",
        ).grid(row=8, column=0, columnspan=2, sticky="w")

    def add_entry(
        self,
        parent: ttk.Frame,
        label_text: str,
        variable: tk.StringVar,
        row: int,
    ) -> None:
        ttk.Label(parent, text=label_text, style="AttendanceLabel.TLabel").grid(
            row=row,
            column=0,
            padx=(0, 10),
            pady=8,
            sticky="w",
        )
        ttk.Entry(parent, textvariable=variable, width=28).grid(
            row=row,
            column=1,
            pady=8,
            sticky="ew",
        )

    def create_table_panel(self) -> None:
        panel = ttk.Frame(self, style="AttendancePanel.TFrame", padding=18)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ttk.Label(
            panel,
            text="Attendance Records",
            style="AttendancePanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        filter_frame = ttk.Frame(panel, style="AttendancePanel.TFrame")
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        filter_frame.grid_columnconfigure(0, weight=2)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=1)

        ttk.Entry(
            filter_frame,
            textvariable=self.search_name,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Entry(
            filter_frame,
            textvariable=self.filter_date,
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ttk.Combobox(
            filter_frame,
            textvariable=self.filter_type,
            values=FILTER_TYPES,
            state="readonly",
        ).grid(row=0, column=2, sticky="ew", padx=(0, 8))

        ttk.Button(
            filter_frame,
            text="Search",
            command=self.search_attendance,
            style="Primary.TButton",
        ).grid(row=0, column=3, padx=(0, 8))

        ttk.Button(
            filter_frame,
            text="Export CSV",
            command=self.export_csv,
            style="Primary.TButton",
        ).grid(row=0, column=4)

        table_frame = ttk.Frame(panel, style="AttendancePanel.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Name", "Type", "Date", "Time", "Status")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Attendance.Treeview",
        )

        for column in columns:
            self.table.heading(column, text=column)

        self.table.column("ID", width=60, minwidth=50, anchor="center", stretch=False)
        self.table.column("Name", width=190, minwidth=140)
        self.table.column("Type", width=95, minwidth=85, anchor="center")
        self.table.column("Date", width=110, minwidth=95, anchor="center")
        self.table.column("Time", width=95, minwidth=80, anchor="center")
        self.table.column("Status", width=100, minwidth=85, anchor="center")

        y_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview,
        )
        x_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.table.xview,
        )
        self.table.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.table.bind("<<TreeviewSelect>>", self.select_attendance)

    def create_status_bar(self) -> None:
        status_bar = ttk.Frame(self, style="AttendancePanel.TFrame", padding=(14, 8))
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        ttk.Label(
            status_bar,
            textvariable=self.status_text,
            style="AttendanceMuted.TLabel",
        ).pack(side="left")

    def load_attendance(self) -> None:
        self.search_name.set("")
        self.filter_date.set("")
        self.filter_type.set("All")
        self.filter_attendance()

    def mark_attendance(self) -> None:
        if not self.validate_form():
            return

        try:
            self.db.insert_record(
                self.clean_text(self.person_name.get()),
                self.person_type.get(),
                self.date.get().strip(),
                self.time.get().strip(),
                self.status.get(),
            )
            self.clear_form()
            self.filter_attendance()
            self.status_text.set("Attendance added successfully.")
            self.refresh_dashboard()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_attendance(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Delete Attendance", "Select an attendance record.")
            return

        if not messagebox.askyesno("Delete Attendance", "Delete selected attendance?"):
            return

        try:
            self.db.delete_record(self.selected_id)
            self.selected_id = None
            self.filter_attendance()
            self.status_text.set("Attendance deleted.")
            self.refresh_dashboard()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def search_attendance(self) -> None:
        self.filter_attendance()

    def filter_attendance(self) -> None:
        try:
            records = self.db.fetch_records(
                name=self.search_name.get(),
                date=self.filter_date.get(),
                person_type=self.filter_type.get(),
            )
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))
            records = []

        self.current_records = records
        self.populate_table(records)
        self.total_text.set(f"Total Attendance: {len(records)}")
        self.status_text.set(f"Loaded {len(records)} attendance record(s).")

    def populate_table(self, records: list[AttendanceRecord]) -> None:
        for item_id in self.table.get_children():
            self.table.delete(item_id)

        for record in records:
            self.table.insert(
                "",
                "end",
                iid=str(record.record_id),
                values=(
                    record.record_id,
                    record.person_name,
                    record.person_type,
                    record.date,
                    record.time,
                    record.status,
                ),
            )

    def select_attendance(self, event=None) -> None:
        selected = self.table.focus()
        if not selected:
            return

        values = self.table.item(selected, "values")
        if not values:
            return

        self.selected_id = int(values[0])
        self.person_name.set(values[1])
        self.person_type.set(values[2])
        self.date.set(values[3])
        self.time.set(values[4])
        self.status.set(values[5])

    def export_csv(self) -> None:
        if not self.current_records:
            messagebox.showwarning("Export CSV", "No attendance records to export.")
            return

        os.makedirs(REPORT_FOLDER, exist_ok=True)
        default_name = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            title="Export Attendance CSV",
            defaultextension=".csv",
            initialdir=REPORT_FOLDER,
            initialfile=default_name,
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["ID", "Name", "Type", "Date", "Time", "Status"])
                for record in self.current_records:
                    writer.writerow(
                        [
                            record.record_id,
                            record.person_name,
                            record.person_type,
                            record.date,
                            record.time,
                            record.status,
                        ]
                    )
            self.status_text.set(f"CSV exported: {file_path}")
            messagebox.showinfo("Export CSV", "Attendance exported successfully.")
        except OSError as error:
            messagebox.showerror("Export CSV", str(error))

    def print_report(self) -> None:
        if not self.current_records:
            messagebox.showwarning("Print Report", "No attendance records to print.")
            return

        os.makedirs(REPORT_FOLDER, exist_ok=True)
        report_path = os.path.join(
            REPORT_FOLDER,
            f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )

        try:
            with open(report_path, "w", encoding="utf-8") as report:
                report.write("AI School Surveillance System\n")
                report.write("Attendance Report\n")
                report.write("=" * 90 + "\n")
                report.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                report.write(f"Total Records: {len(self.current_records)}\n")
                report.write("=" * 90 + "\n")
                report.write(
                    f"{'ID':<6}{'Name':<28}{'Type':<12}"
                    f"{'Date':<14}{'Time':<12}{'Status':<12}\n"
                )
                report.write("-" * 90 + "\n")

                for record in self.current_records:
                    report.write(
                        f"{record.record_id:<6}"
                        f"{record.person_name[:27]:<28}"
                        f"{record.person_type:<12}"
                        f"{record.date:<14}"
                        f"{record.time:<12}"
                        f"{record.status:<12}\n"
                    )

            self.status_text.set(f"Report ready: {report_path}")

            try:
                if os.name == "nt":
                    os.startfile(report_path, "print")
                else:
                    if sys.platform == "darwin":
                        subprocess.Popen(["open", report_path])
                    else:
                        subprocess.Popen(["xdg-open", report_path])
                messagebox.showinfo("Print Report", "Report sent to printer.")
            except (AttributeError, OSError):
                messagebox.showinfo("Print Report", f"Report saved:\n{report_path}")
        except OSError as error:
            messagebox.showerror("Print Report", str(error))

    def validate_form(self) -> bool:
        if not self.clean_text(self.person_name.get()):
            messagebox.showerror("Validation Error", "Person name is required.")
            return False

        if self.person_type.get() not in PERSON_TYPES:
            messagebox.showerror("Validation Error", "Select Student or Teacher.")
            return False

        if self.status.get() not in STATUSES:
            messagebox.showerror("Validation Error", "Select a valid status.")
            return False

        if not self.is_valid_date(self.date.get().strip()):
            messagebox.showerror("Validation Error", "Date must be YYYY-MM-DD.")
            return False

        if not self.is_valid_time(self.time.get().strip()):
            messagebox.showerror("Validation Error", "Time must be HH:MM:SS.")
            return False

        return True

    @staticmethod
    def clean_text(value: str) -> str:
        return " ".join(value.strip().split())

    @staticmethod
    def is_valid_date(value: str) -> bool:
        try:
            datetime.strptime(value, DATE_FORMAT)
        except ValueError:
            return False
        return True

    @staticmethod
    def is_valid_time(value: str) -> bool:
        try:
            datetime.strptime(value, TIME_FORMAT)
        except ValueError:
            return False
        return True

    def clear_form(self) -> None:
        now = datetime.now()
        self.selected_id = None
        self.person_name.set("")
        self.person_type.set(PERSON_TYPES[0])
        self.date.set(now.strftime(DATE_FORMAT))
        self.time.set(now.strftime(TIME_FORMAT))
        self.status.set(STATUSES[0])

        selected_items = self.table.selection()
        if selected_items:
            self.table.selection_remove(*selected_items)

    def refresh_dashboard(self) -> None:
        if self.app is None:
            return

        active_route = getattr(self.app, "active_route", None)
        if active_route is not None and hasattr(active_route, "get"):
            try:
                if active_route.get() != "Dashboard":
                    return
            except tk.TclError:
                return

        try:
            if hasattr(self.app, "refresh_dashboard"):
                self.app.refresh_dashboard()
            elif hasattr(self.app, "refresh_dashboard_metrics"):
                self.app.refresh_dashboard_metrics()
        except tk.TclError:
            pass


AttendanceManagement = AttendanceFrame


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Attendance")
    root.geometry("1200x700")
    root.configure(bg=BG_COLOR)
    page = AttendanceFrame(root)
    page.pack(fill="both", expand=True, padx=20, pady=20)
    root.mainloop()
