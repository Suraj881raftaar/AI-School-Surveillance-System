"""
reports.py
AI School Surveillance System
"""

from __future__ import annotations

import csv
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import importlib
    openpyxl = importlib.import_module("openpyxl")
    Workbook = openpyxl.Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    Workbook = None
    OPENPYXL_AVAILABLE = False

from config import *


class ReportsFrame(ttk.Frame):

    def __init__(self, parent, app=None):

        super().__init__(parent)

        self.app = app

        self.configure(style="Reports.TFrame")

        self.configure_styles()

        self.create_widgets()

    # ==========================================
    # Styles
    # ==========================================

    def configure_styles(self):

        style = ttk.Style()

        style.configure(
            "Reports.TFrame",
            background=BG_COLOR
        )

        style.configure(
            "Reports.TLabelframe",
            background=BG_COLOR
        )

        style.configure(
            "Reports.TLabelframe.Label",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 11, "bold")
        )

    # ==========================================
    # Create Widgets
    # ==========================================

    def create_widgets(self):

        toolbar = tk.Frame(
            self,
            bg=BG_COLOR
        )

        toolbar.pack(
            fill="x",
            padx=15,
            pady=15
        )

        tk.Label(
            toolbar,
            text="Search",
            bg=BG_COLOR,
            font=("Arial",11,"bold")
        ).pack(side="left")

        self.search_var = tk.StringVar()

        tk.Entry(
            toolbar,
            textvariable=self.search_var,
            width=30
        ).pack(side="left",padx=8)

        tk.Button(
            toolbar,
            text="Search",
            command=self.search_reports
        ).pack(side="left",padx=5)

        tk.Button(
            toolbar,
            text="Refresh",
            command=self.load_reports
        ).pack(side="left",padx=5)

        tk.Button(
            toolbar,
            text="Export CSV",
            command=self.export_csv
        ).pack(side="right",padx=5)

        tk.Button(
            toolbar,
            text="Export Excel",
            command=self.export_excel
        ).pack(side="right",padx=5)

        self.content = tk.Frame(
            self,
            bg=BG_COLOR
        )

        self.content.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0,15)
        )
                # ==========================================
        # Attendance Report
        # ==========================================

        attendance_frame = ttk.LabelFrame(
            self.content,
            text="Attendance Report",
            style="Reports.TLabelframe"
        )

        attendance_frame.pack(
            fill="both",
            expand=True,
            pady=(0,10)
        )

        attendance_columns = (
            "ID",
            "Name",
            "Type",
            "Date",
            "Time",
            "Status"
        )

        self.attendance_table = ttk.Treeview(
            attendance_frame,
            columns=attendance_columns,
            show="headings",
            height=8
        )

        for col in attendance_columns:

            self.attendance_table.heading(col, text=col)

            self.attendance_table.column(
                col,
                width=120,
                anchor="center"
            )

        attendance_scroll = ttk.Scrollbar(
            attendance_frame,
            orient="vertical",
            command=self.attendance_table.yview
        )

        self.attendance_table.configure(
            yscrollcommand=attendance_scroll.set
        )

        self.attendance_table.pack(
            side="left",
            fill="both",
            expand=True
        )

        attendance_scroll.pack(
            side="right",
            fill="y")

        # ==========================================
        # Alert Report
        # ==========================================

        alert_frame = ttk.LabelFrame(
            self.content,
            text="Alert Report",
            style="Reports.TLabelframe"
        )

        alert_frame.pack(
            fill="both",
            expand=True
        )

        alert_columns = (
            "ID",
            "Alert Type",
            "Description",
            "Date",
            "Time"
        )

        self.alert_table = ttk.Treeview(
            alert_frame,
            columns=alert_columns,
            show="headings",
            height=6
        )

        for col in alert_columns:

            self.alert_table.heading(col, text=col)

            self.alert_table.column(
                col,
                width=150,
                anchor="center"
            )

        alert_scroll = ttk.Scrollbar(
            alert_frame,
            orient="vertical",
            command=self.alert_table.yview
        )

        self.alert_table.configure(
            yscrollcommand=alert_scroll.set
        )

        self.alert_table.pack(
            side="left",
            fill="both",
            expand=True
        )

        alert_scroll.pack(
            side="right",
            fill="y"
        )

        # Load data after BOTH tables exist
        self.load_reports()
            # ==========================================
    # Load Reports
    # ==========================================

    def load_reports(self):

        # Clear Attendance Table
        for item in self.attendance_table.get_children():
            self.attendance_table.delete(item)

        # Clear Alert Table
        for item in self.alert_table.get_children():
            self.alert_table.delete(item)

        try:

            conn = sqlite3.connect(DATABASE_PATH)

            cur = conn.cursor()

            # ---------------- Attendance ----------------

            cur.execute("""
                SELECT
                    id,
                    person_name,
                    person_type,
                    date,
                    time,
                    status
                FROM attendance
                ORDER BY id DESC
            """)

            attendance_rows = cur.fetchall()

            for row in attendance_rows:

                self.attendance_table.insert(
                    "",
                    "end",
                    values=row
                )

            # ---------------- Alerts ----------------

            cur.execute("""
                SELECT
                    id,
                    alert_type,
                    description,
                    date,
                    time
                FROM alerts
                ORDER BY id DESC
            """)

            alert_rows = cur.fetchall()

            for row in alert_rows:

                self.alert_table.insert(
                    "",
                    "end",
                    values=row
                )

            conn.close()

        except Exception as e:

            messagebox.showerror(
                "Database Error",
                str(e)
            )

    # ==========================================
    # Search Reports
    # ==========================================

    def search_reports(self):

        keyword = self.search_var.get().strip()

        # Empty search = reload everything
        if keyword == "":
            self.load_reports()
            return

        for item in self.attendance_table.get_children():
            self.attendance_table.delete(item)

        for item in self.alert_table.get_children():
            self.alert_table.delete(item)

        try:

            conn = sqlite3.connect(DATABASE_PATH)

            cur = conn.cursor()

            # Attendance search

            cur.execute("""
                SELECT
                    id,
                    person_name,
                    person_type,
                    date,
                    time,
                    status
                FROM attendance
                WHERE
                    person_name LIKE ?
                    OR person_type LIKE ?
                    OR status LIKE ?
                    OR date LIKE ?
                ORDER BY id DESC
            """, (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%"
            ))

            for row in cur.fetchall():

                self.attendance_table.insert(
                    "",
                    "end",
                    values=row
                )

            # Alerts search

            cur.execute("""
                SELECT
                    id,
                    alert_type,
                    description,
                    date,
                    time
                FROM alerts
                WHERE
                    alert_type LIKE ?
                    OR description LIKE ?
                    OR date LIKE ?
                ORDER BY id DESC
            """, (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%"
            ))

            for row in cur.fetchall():

                self.alert_table.insert(
                    "",
                    "end",
                    values=row
                )

            conn.close()

        except Exception as e:

            messagebox.showerror(
                "Search Error",
                str(e)
            )
                # ==========================================
    # Export Attendance to CSV
    # ==========================================

    def export_csv(self):

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            title="Save Attendance Report"
        )

        if not filename:
            return

        try:

            conn = sqlite3.connect(DATABASE_PATH)

            cur = conn.cursor()

            cur.execute("""
                SELECT
                    id,
                    person_name,
                    person_type,
                    date,
                    time,
                    status
                FROM attendance
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

            conn.close()

            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "ID",
                    "Person Name",
                    "Person Type",
                    "Date",
                    "Time",
                    "Status"
                ])

                writer.writerows(rows)

            messagebox.showinfo(
                "Success",
                "CSV exported successfully."
            )

        except Exception as e:

            messagebox.showerror(
                "Export Error",
                str(e)
            )
                # ==========================================
    # Export Attendance to Excel
    # ==========================================

    def export_excel(self):

        if not OPENPYXL_AVAILABLE:

            messagebox.showerror(
                "Missing Library",
                "Please install openpyxl\n\npip install openpyxl"
            )

            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            title="Save Attendance Report"
        )

        if not filename:
            return

        try:

            workbook = Workbook()

            sheet = workbook.active

            sheet.title = "Attendance Report"

            sheet.append([
                "ID",
                "Person Name",
                "Person Type",
                "Date",
                "Time",
                "Status"
            ])

            conn = sqlite3.connect(DATABASE_PATH)

            cur = conn.cursor()

            cur.execute("""
                SELECT
                    id,
                    person_name,
                    person_type,
                    date,
                    time,
                    status
                FROM attendance
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

            conn.close()

            for row in rows:

                sheet.append(row)

            workbook.save(filename)

            messagebox.showinfo(
                "Success",
                "Excel file exported successfully."
            )

        except Exception as e:

            messagebox.showerror(
                "Export Error",
                str(e)
            )