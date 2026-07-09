"""
dashboard.py
AI School Surveillance System
"""

from __future__ import annotations

import os
import sqlite3
import tkinter as tk
import threading
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from config import *
from dashboard_repository import DashboardRepository
from settings_manager import SettingsManager


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

    def configure_styles(self):
        style = ttk.Style()
        style.configure("Dashboard.TFrame", background=BG_COLOR)
        style.configure("DashboardTitle.TLabel", background=BG_COLOR, foreground=HEADER_COLOR, font=("Arial", 24, "bold"))
        style.configure("DashboardCard.TFrame", background="white", relief="ridge")
        style.configure("DashboardCardTitle.TLabel", background="white", foreground="#555555", font=("Arial", 12, "bold"))
        style.configure("DashboardCardValue.TLabel", background="white", foreground=BUTTON_COLOR, font=("Arial", 28, "bold"))
        style.configure("DashboardClock.TLabel", background=BG_COLOR, foreground=HEADER_COLOR, font=("Arial", 12, "bold"))
        
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

    def create_widgets(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header Section
        header = ttk.Frame(self, style="Dashboard.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ttk.Label(
            header,
            text="AI SCHOOL SURVEILLANCE ENGINE",
            style="DashboardTitle.TLabel"
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        # Cards Panel
        self.cards_frame = ttk.Frame(self, style="Dashboard.TFrame")
        self.cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Bottom Area
        self.bottom_frame = ttk.Frame(self, style="Dashboard.TFrame")
        self.bottom_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
        self.bottom_frame.grid_columnconfigure((0, 1), weight=2)
        self.bottom_frame.grid_columnconfigure(2, weight=3) # Larger width for charts
        self.bottom_frame.grid_rowconfigure(0, weight=1)

    def create_card(self, parent, title, value, row, column, color="#1976D2"):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid", padx=10, pady=8)
        card.grid(row=row, column=column, padx=6, pady=5, sticky="nsew")

        tk.Label(
            card,
            text=title,
            bg="white",
            fg="#555555",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(2, 4))

        value_label = tk.Label(
            card,
            text=str(value),
            bg="white",
            fg=color,
            font=("Segoe UI", 20, "bold")
        )
        value_label.pack(pady=(0, 2))
        return value_label

    def refresh_dashboard(self):
        if not self.winfo_exists():
            return

        if self.refresh_after_id is not None:
            try:
                self.after_cancel(self.refresh_after_id)
            except tk.TclError:
                pass
            self.refresh_after_id = None

        # Fetch standard count metrics and advanced analytics
        metrics = self.repo.metrics()
        stats = self.repo.get_advanced_analytics()

        # Clear previous cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Row 0 metrics: core registered counts & daily logs
        self.create_card(self.cards_frame, "Total Students", metrics["students"], 0, 0, "#1976D2")
        self.create_card(self.cards_frame, "Total Teachers", metrics["teachers"], 0, 1, "#1976D2")
        self.create_card(self.cards_frame, "Attendance Marked", stats["attendance_today"], 0, 2, SUCCESS_COLOR)
        self.create_card(self.cards_frame, "Security Alerts", stats["unknown_today"], 0, 3, DANGER_COLOR)

        # Row 1 metrics: rate statistics & active configs
        self.create_card(self.cards_frame, "Attendance Rate", f"{stats['attendance_pct']:.1f}%", 1, 0, "#EF6C00")
        self.create_card(self.cards_frame, "Model Accuracy", f"{stats['accuracy']:.1f}%", 1, 1, SUCCESS_COLOR)
        self.create_card(self.cards_frame, "Average Confidence", f"{stats['avg_confidence']:.1f}%", 1, 2, "#9C27B0")
        self.create_card(self.cards_frame, "New Registrations", stats["registrations_today"], 1, 3, "#009688")

        self.build_recent_tables(stats)

        self.refresh_after_id = self.after(5000, self.refresh_dashboard)

    def build_recent_tables(self, stats: dict):
        # Clear old widgets
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()

        # 1. Recent Attendance Table (Col 0)
        attendance_frame = ttk.LabelFrame(self.bottom_frame, text="Recent Attendance")
        attendance_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        attendance = ttk.Treeview(
            attendance_frame,
            columns=("Name", "Type", "Date", "Time", "Status"),
            show="headings",
            height=6
        )
        for col in ("Name", "Type", "Date", "Time", "Status"):
            attendance.heading(col, text=col)
            attendance.column(col, width=80, anchor="center")
        attendance.pack(fill="both", expand=True, padx=4, pady=4)

        for row in self.repo.latest_attendance(6):
            attendance.insert("", "end", values=tuple(row))

        # 2. Recent Alerts Table (Col 1)
        alert_frame = ttk.LabelFrame(self.bottom_frame, text="Security Alerts Log")
        alert_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        alerts = ttk.Treeview(
            alert_frame,
            columns=("Type", "Description", "Date", "Time"),
            show="headings",
            height=6
        )
        for col in ("Type", "Description", "Date", "Time"):
            alerts.heading(col, text=col)
            alerts.column(col, width=95, anchor="center")
        alerts.pack(fill="both", expand=True, padx=4, pady=4)

        for row in self.repo.latest_alerts(6):
            alerts.insert("", "end", values=tuple(row))

        # 3. Canvas Analytics Chart (Col 2)
        chart_frame = ttk.LabelFrame(self.bottom_frame, text="7-Day Attendance Trend")
        chart_frame.grid(row=0, column=2, sticky="nsew")

        chart = AttendanceChart(chart_frame, data=stats["weekly_trend"])
        chart.pack(fill="both", expand=True, padx=5, pady=5)

    def destroy(self):
        if self.refresh_after_id is not None:
            try:
                self.after_cancel(self.refresh_after_id)
            except tk.TclError:
                pass
            self.refresh_after_id = None
        super().destroy()


class AttendanceChart(tk.Canvas):
    """Draw dynamic rounded bar charts inside native Canvas."""

    def __init__(self, parent, data=None, **kwargs):
        super().__init__(parent, bg="white", highlightthickness=0, **kwargs)
        self.data = data or []
        self.draw_chart()

    def draw_chart(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50 or h < 50:
            self.after(200, self.draw_chart)
            return

        margin_x = 40
        margin_y = 30
        plot_w = w - margin_x - 15
        plot_h = h - margin_y - 20

        # Draw grid axes
        self.create_line(margin_x, h - margin_y, w - 10, h - margin_y, fill="#E0E0E0", width=1.5)
        self.create_line(margin_x, 15, margin_x, h - margin_y, fill="#E0E0E0", width=1.5)

        if not self.data:
            self.create_text(w/2, h/2, text="No weekly logs recorded.", fill="#888888", font=("Arial", 10))
            return

        max_val = max([item[1] for item in self.data]) if self.data else 1
        if max_val == 0:
            max_val = 1

        num_items = len(self.data)
        bar_gap = 8
        bar_w = (plot_w - (bar_gap * (num_items + 1))) / num_items

        for idx, (label, val) in enumerate(self.data):
            x1 = margin_x + bar_gap + idx * (bar_w + bar_gap)
            x2 = x1 + bar_w
            
            # Map val to height
            val_h = (val / max_val) * plot_h
            y1 = h - margin_y - val_h
            y2 = h - margin_y

            # Bar Fill
            self.create_rectangle(x1, y1, x2, y2, fill="#1976D2", outline="#1565C0")

            # Value tags
            self.create_text((x1 + x2)/2, y1 - 8, text=str(val), fill="#1976D2", font=("Arial", 8, "bold"))

            # Bottom dates (MM-DD)
            short_lbl = label[-5:] if len(label) >= 5 else label
            self.create_text((x1 + x2)/2, h - margin_y + 12, text=short_lbl, fill="#555555", font=("Arial", 8))


class SettingsFrame(ttk.Frame):
    """System Settings and Backup Manager Panel."""

    def __init__(self, parent, app=None) -> None:
        super().__init__(parent)
        self.app = app
        self.repo = DashboardRepository()
        self.settings_manager = SettingsManager()

        self.dataset_path_var = tk.StringVar()
        self.model_path_var = tk.StringVar()
        self.export_path_var = tk.StringVar()
        self.cooldown_var = tk.StringVar()
        self.camera_index_var = tk.StringVar()
        self.threshold_var = tk.DoubleVar()

        self.db_backup_var = tk.BooleanVar(value=True)
        self.dataset_backup_var = tk.BooleanVar(value=False)
        self.models_backup_var = tk.BooleanVar(value=True)
        self.logs_backup_var = tk.BooleanVar(value=True)

        self.configure(style="Dashboard.TFrame")
        self.create_widgets()
        self.load_settings()

    def create_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Title
        header = ttk.Frame(self, style="Dashboard.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        tk.Label(
            header, 
            text="SETTINGS & SYSTEM UTILITIES", 
            bg=BG_COLOR, 
            fg=HEADER_COLOR, 
            font=("Arial", 20, "bold")
        ).pack(side="left")

        # Notebook
        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Config Frame
        config_tab = ttk.Frame(notebook, padding=18)
        notebook.add(config_tab, text="System Configurations")

        # Backup Frame
        backup_tab = ttk.Frame(notebook, padding=18)
        notebook.add(backup_tab, text="Backup & Restore Manager")

        # --- Configurations Tab Layout ---
        config_tab.grid_columnconfigure(1, weight=1)

        self.add_config_row(config_tab, "Dataset Base Path:", self.dataset_path_var, 0)
        self.add_config_row(config_tab, "Trained Model Path:", self.model_path_var, 1)
        self.add_config_row(config_tab, "Reports Export Path:", self.export_path_var, 2)
        self.add_config_row(config_tab, "Attendance Cooldown (seconds):", self.cooldown_var, 3)

        # Camera selection
        tk.Label(config_tab, text="Active Camera Index:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=8)
        self.camera_combo = ttk.Combobox(config_tab, textvariable=self.camera_index_var, values=["0", "1", "2", "3"], state="readonly")
        self.camera_combo.grid(row=4, column=1, sticky="w", pady=8)

        # Recognition threshold slider
        tk.Label(config_tab, text="LBPH Matching Threshold:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=8)
        threshold_frame = ttk.Frame(config_tab)
        threshold_frame.grid(row=5, column=1, sticky="ew", pady=8)
        threshold_frame.grid_columnconfigure(0, weight=1)
        
        self.threshold_slider = ttk.Scale(threshold_frame, from_=30.0, to=120.0, variable=self.threshold_var, orient="horizontal")
        self.threshold_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.threshold_lbl = tk.Label(threshold_frame, text="65.0", font=("Arial", 10, "bold"))
        self.threshold_lbl.grid(row=0, column=1, sticky="e")
        self.threshold_var.trace_add("write", lambda *a: self.threshold_lbl.configure(text=f"{self.threshold_var.get():.1f}"))

        # Save Button
        ttk.Button(config_tab, text="Save System Configurations", command=self.save_settings, style="Success.TButton").grid(row=6, column=0, columnspan=2, pady=(20, 0))

        # --- Backup Tab Layout ---
        backup_tab.grid_columnconfigure(0, weight=1)
        
        tk.Label(backup_tab, text="Create System Archive Backup", font=("Arial", 12, "bold"), fg=HEADER_COLOR).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        tk.Checkbutton(backup_tab, text="Include Database file (school.db)", variable=self.db_backup_var).grid(row=1, column=0, sticky="w", pady=4)
        tk.Checkbutton(backup_tab, text="Include Face Dataset images", variable=self.dataset_backup_var).grid(row=2, column=0, sticky="w", pady=4)
        tk.Checkbutton(backup_tab, text="Include Trained Models (trainer.yml)", variable=self.models_backup_var).grid(row=3, column=0, sticky="w", pady=4)
        tk.Checkbutton(backup_tab, text="Include System Logs", variable=self.logs_backup_var).grid(row=4, column=0, sticky="w", pady=4)

        ttk.Button(backup_tab, text="Create Backup Archive (.zip)", command=self.run_backup, style="Primary.TButton").grid(row=5, column=0, sticky="w", pady=(14, 20))

        # Restore Section
        ttk.Separator(backup_tab, orient="horizontal").grid(row=6, column=0, sticky="ew", pady=10)
        
        tk.Label(backup_tab, text="Restore System Archive Backup", font=("Arial", 12, "bold"), fg=HEADER_COLOR).grid(row=7, column=0, sticky="w", pady=(10, 10))
        tk.Label(backup_tab, text="WARNING: Restoring will replace your current databases, models, datasets, and logs with the backup content.", fg=DANGER_COLOR, font=("Arial", 9, "italic")).grid(row=8, column=0, sticky="w", pady=(0, 12))
        
        ttk.Button(backup_tab, text="Select & Restore Backup Archive", command=self.run_restore, style="Danger.TButton").grid(row=9, column=0, sticky="w")

    def add_config_row(self, parent, label_text, var, row):
        tk.Label(parent, text=label_text, font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=var, width=50).grid(row=row, column=1, sticky="ew", pady=8, padx=(10, 0))

    def load_settings(self) -> None:
        self.dataset_path_var.set(self.settings_manager.get("dataset_path"))
        self.model_path_var.set(self.settings_manager.get("model_path"))
        self.export_path_var.set(self.settings_manager.get("export_path"))
        self.cooldown_var.set(self.settings_manager.get("attendance_cooldown"))
        self.camera_index_var.set(self.settings_manager.get("camera_index"))
        self.threshold_var.set(float(self.settings_manager.get("recognition_threshold")))

    def save_settings(self) -> None:
        if not self.settings_manager.set("dataset_path", self.dataset_path_var.get()) or \
           not self.settings_manager.set("model_path", self.model_path_var.get()) or \
           not self.settings_manager.set("export_path", self.export_path_var.get()) or \
           not self.settings_manager.set("attendance_cooldown", self.cooldown_var.get()) or \
           not self.settings_manager.set("camera_index", self.camera_index_var.get()) or \
           not self.settings_manager.set("recognition_threshold", f"{self.threshold_var.get():.1f}"):
            messagebox.showerror("Validation Error", "Failed to save settings. Please verify inputs (cooldown and camera index must be integers).")
            return

        # Synchronize global config namespace dynamically
        import config
        try:
            config.CAMERA_INDEX = int(self.camera_index_var.get())
            config.DATASET_FOLDER = self.dataset_path_var.get()
            config.MODEL_FOLDER = self.model_path_var.get()
            config.REPORT_FOLDER = self.export_path_var.get()
        except Exception:
            pass

        messagebox.showinfo("Success", "Configurations saved successfully.")

    def run_backup(self) -> None:
        backup_dir = filedialog.askdirectory(title="Choose Directory to Save Backup Archive")
        if not backup_dir:
            return

        threading.Thread(
            target=self.bg_backup_task,
            args=(backup_dir,),
            daemon=True
        ).start()

    def bg_backup_task(self, backup_dir: str) -> None:
        try:
            zip_path = self.repo.create_backup(
                backup_dir=backup_dir,
                db=self.db_backup_var.get(),
                dataset=self.dataset_backup_var.get(),
                models=self.models_backup_var.get(),
                logs=self.logs_backup_var.get()
            )
            messagebox.showinfo("Backup Success", f"Backup zip file created successfully:\n{zip_path}")
        except Exception as e:
            messagebox.showerror("Backup Error", f"An error occurred during backup creation:\n{e}")

    def run_restore(self) -> None:
        zip_path = filedialog.askopenfilename(
            title="Select Backup Archive to Restore",
            filetypes=[("Backup ZIP file", "*.zip")]
        )
        if not zip_path:
            return

        if not messagebox.askyesno("Confirm Restore", "Restore data? This will overwrite your current settings."):
            return

        try:
            self.repo.restore_backup(zip_path)
            messagebox.showinfo("Restore Success", "Surveillance data restored successfully.")
        except Exception as e:
            messagebox.showerror("Restore Error", f"Failed to restore backup:\n{e}")


# Compatibility bindings
Dashboard = DashboardFrame
