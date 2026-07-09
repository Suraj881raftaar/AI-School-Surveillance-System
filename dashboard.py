"""
dashboard.py
AI School Surveillance System
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config import *
from dashboard_repository import DashboardRepository


class DashboardFrame(ttk.Frame):

    def __init__(self, parent, app=None):

        super().__init__(parent)

        self.app = app

        self.repo = DashboardRepository()
        self.refresh_after_id = None

        self.configure(style="Dashboard.TFrame")

        self.configure_styles()

        self.create_widgets()

        self.refresh_dashboard()
            # ==========================================
    # Styles
    # ==========================================

    def configure_styles(self):

        style = ttk.Style()

        style.configure(
            "Dashboard.TFrame",
            background=BG_COLOR
        )

        style.configure(
            "DashboardTitle.TLabel",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 24, "bold")
        )

        style.configure(
            "DashboardCard.TFrame",
            background="white",
            relief="ridge"
        )

        style.configure(
            "DashboardCardTitle.TLabel",
            background="white",
            foreground="#555555",
            font=("Arial", 12, "bold")
        )

        style.configure(
            "DashboardCardValue.TLabel",
            background="white",
            foreground=BUTTON_COLOR,
            font=("Arial", 28, "bold")
        )

        style.configure(
            "DashboardClock.TLabel",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 12, "bold")
        )
            # ==========================================
    # Create Dashboard
    # ==========================================

    def create_widgets(self):

        self.grid_rowconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)

        # -------------------------
        # Header
        # -------------------------

        header = ttk.Frame(
            self,
            style="Dashboard.TFrame"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

        header.grid_columnconfigure(0, weight=1)

        self.title_label = ttk.Label(

            header,

            text="AI SCHOOL SURVEILLANCE SYSTEM",

            style="DashboardTitle.TLabel"

        )

        self.title_label.grid(
            row=0,
            column=0,
            sticky="w"
        )

        # -------------------------
        # Cards
        # -------------------------

        self.cards_frame = ttk.Frame(
            self,
            style="Dashboard.TFrame"
        )

        self.cards_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0,20)
        )

        self.cards_frame.grid_columnconfigure((0,1,2,3), weight=1)

        # -------------------------
        # Bottom Area
        # -------------------------

        self.bottom_frame = ttk.Frame(
            self,
            style="Dashboard.TFrame"
        )

        self.bottom_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0,20)
        )

        self.bottom_frame.grid_columnconfigure((0,1), weight=1)

        self.bottom_frame.grid_rowconfigure(0, weight=1)
        # ==========================================
    # Dashboard Card
    # ==========================================

    def create_card(self, parent, title, value, column):

        card = tk.Frame(
            parent,
            bg="white",
            bd=2,
            relief="ridge",
            padx=15,
            pady=15
        )

        card.grid(
            row=0,
            column=column,
            padx=10,
            sticky="nsew"
        )

        tk.Label(
         card,
    text=title,
    bg="white",
    fg="#555555",
    font=("Segoe UI", 12, "bold")
    ).pack(pady=(5, 8))

        value_label = tk.Label(
    card,
    text=str(value),
    bg="white",
    fg="#1976D2",
    font=("Segoe UI", 30, "bold")
)

        value_label.pack(pady=(0, 5))

        return value_label
        # ==========================================
    # Refresh Dashboard
    # ==========================================

    def refresh_dashboard(self):
        if not self.winfo_exists():
            return

        if self.refresh_after_id is not None:
            try:
                self.after_cancel(self.refresh_after_id)
            except tk.TclError:
                pass
            self.refresh_after_id = None

        metrics = self.repo.metrics()

        # Clear previous cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        self.student_value = self.create_card(
            self.cards_frame,
            "Students",
            metrics["students"],
            0
        )

        self.teacher_value = self.create_card(
            self.cards_frame,
            "Teachers",
            metrics["teachers"],
            1
        )

        self.attendance_value = self.create_card(
            self.cards_frame,
            "Attendance",
            metrics["attendance"],
            2
        )

        self.alert_value = self.create_card(
            self.cards_frame,
            "Alerts",
            metrics["alerts"],
            3
        )
        self.build_recent_tables()

        self.refresh_after_id = self.after(
            5000,
            self.refresh_dashboard
        )
            # ==========================================
    # Live Clock
    # ==========================================

    def update_clock(self):

        from datetime import datetime

        now = datetime.now()

        self.clock_label.config(

            text=now.strftime(
                "%d-%m-%Y   %I:%M:%S %p"
            )

        )
            # ==========================================
    # Recent Tables
    # ==========================================

    def build_recent_tables(self):

        # Clear old widgets
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()

        # ---------------- Attendance ----------------

        attendance_frame = ttk.LabelFrame(
            self.bottom_frame,
            text="Recent Attendance"
        )

        attendance_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0,10)
        )

        attendance = ttk.Treeview(

            attendance_frame,

            columns=("Name","Type","Date","Time","Status"),

            show="headings",

            height=8

        )

        for col in ("Name","Type","Date","Time","Status"):

            attendance.heading(col,text=col)

            attendance.column(col,width=110)

        attendance.pack(fill="both",expand=True)

        for row in self.repo.latest_attendance():

            attendance.insert("", "end", values=tuple(row))

        # ---------------- Alerts ----------------

        alert_frame = ttk.LabelFrame(

            self.bottom_frame,

            text="Recent Alerts"

        )

        alert_frame.grid(

            row=0,

            column=1,

            sticky="nsew"

        )

        alerts = ttk.Treeview(

            alert_frame,

            columns=("Type","Description","Date","Time"),

            show="headings",

            height=8

        )

        for col in ("Type","Description","Date","Time"):

            alerts.heading(col,text=col)

            alerts.column(col,width=120)

        alerts.pack(fill="both",expand=True)

        for row in self.repo.latest_alerts():

            alerts.insert("", "end", values=tuple(row))

    def destroy(self):
        if self.refresh_after_id is not None:
            try:
                self.after_cancel(self.refresh_after_id)
            except tk.TclError:
                pass
            self.refresh_after_id = None

        super().destroy()
