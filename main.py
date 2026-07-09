"""
main.py
AI School Surveillance System
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import importlib

from config import *


class MainApplication:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(APP_NAME + " - Dashboard")

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.root.configure(bg=BG_COLOR)

        self.root.state("zoomed")

        self.current_frame = None

        self.build_sidebar()

        self.build_header()

        self.content = tk.Frame(
            self.root,
            bg=BG_COLOR
        )

        self.content.place(
            x=220,
            y=80,
            relwidth=1,
            relheight=1,
            width=-220,
            height=-80
        )

        self.show_dashboard()

        self.update_clock()

        self.root.mainloop()
            # ============================
    # Sidebar
    # ============================

    def build_sidebar(self):

        self.sidebar = tk.Frame(
            self.root,
            bg=HEADER_COLOR,
            width=220
        )

        self.sidebar.place(
            x=0,
            y=0,
            width=220,
            relheight=1
        )

        title = tk.Label(
            self.sidebar,
            text="AI SCHOOL\nSURVEILLANCE",
            bg=HEADER_COLOR,
            fg="white",
            font=("Arial",18,"bold"),
            justify="center"
        )

        title.pack(pady=20)

        self.add_nav_button("Dashboard", self.show_dashboard)
        self.add_nav_button("Students", self.show_students)
        self.add_nav_button("Teachers", self.show_teachers)
        self.add_nav_button("Register Face", self.show_register_face)
        self.add_nav_button("Face Training", self.show_face_training)
        self.add_nav_button("Surveillance", self.show_surveillance)
        self.add_nav_button("Attendance", self.show_attendance)
        self.add_nav_button("Reports", self.show_reports)

        tk.Button(
            self.sidebar,
            text="Exit",
            bg=DANGER_COLOR,
            fg="white",
            font=("Arial",11,"bold"),
            command=self.root.destroy
        ).pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=20
        )

    def add_nav_button(self,text,command):

        tk.Button(
            self.sidebar,
            text=text,
            bg=BUTTON_COLOR,
            fg="white",
            relief="flat",
            font=("Arial",11,"bold"),
            command=command
        ).pack(
            fill="x",
            padx=15,
            pady=5,
            ipady=8
        )

    # ============================
    # Header
    # ============================

    def build_header(self):

        self.header = tk.Frame(
            self.root,
            bg="white",
            height=80
        )

        self.header.place(
            x=220,
            y=0,
            relwidth=1,
            width=-220
        )

        self.page_title = tk.Label(
            self.header,
            text="Dashboard",
            bg="white",
            fg=HEADER_COLOR,
            font=("Arial",22,"bold")
        )

        self.page_title.pack(
            side="left",
            padx=20
        )

        self.clock = tk.Label(
            self.header,
            bg="white",
            fg=HEADER_COLOR,
            font=("Arial",12,"bold")
        )

        self.clock.pack(
            side="right",
            padx=20
        )

    def update_clock(self):

        self.clock.config(
            text=datetime.now().strftime(
                "%d-%m-%Y   %I:%M:%S %p"
            )
        )

        self.root.after(
            1000,
            self.update_clock
        )
            # =========================================
    # Clear Content
    # =========================================

    def clear_content(self):

        for widget in self.content.winfo_children():
            widget.destroy()

        self.current_frame = None

    # =========================================
    # Dashboard
    # =========================================

    def show_dashboard(self):

     self.load_module(

        "dashboard",

        "DashboardFrame",

        "Dashboard"

    )
    def create_card(self,parent,title):

        card = tk.Frame(
            parent,
            bg="white",
            width=180,
            height=120,
            relief="ridge",
            bd=2
        )

        card.pack(
            side="left",
            padx=15
        )

        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            font=("Arial",16,"bold"),
            bg="white",
            fg=HEADER_COLOR
        ).pack(pady=15)

        tk.Label(
            card,
            text="0",
            font=("Arial",28,"bold"),
            bg="white",
            fg=BUTTON_COLOR
        ).pack()

    # =========================================
    # Load Module
    # =========================================

    def load_module(self,module_name,class_name,title):

        self.page_title.config(text=title)

        self.clear_content()

        try:

            module = importlib.import_module(module_name)

            frame_class = getattr(module,class_name)

            frame = frame_class(self.content,self)

            frame.pack(
                fill="both",
                expand=True
            )

            self.current_frame = frame

        except Exception as e:

            import traceback

            traceback.print_exc()

            messagebox.showerror(
                "Module Error",
                str(e)
            )
                # =========================================
    # Navigation
    # =========================================

    def show_students(self):

        self.load_module(
            "students",
            "StudentsFrame",
            "Student Management"
        )

    def show_teachers(self):

        self.load_module(
            "teachers",
            "TeachersFrame",
            "Teacher Management"
        )

    def show_register_face(self):

        self.load_module(
            "register_face",
            "RegisterFaceFrame",
            "Face Registration"
        )

    def show_face_training(self):

        self.load_module(
            "train_face",
            "FaceTrainingFrame",
            "Face Recognition Training"
        )

    def show_surveillance(self):

        self.load_module(
            "surveillance",
            "SurveillanceFrame",
            "Surveillance"
        )

    def show_attendance(self):

        self.load_module(
            "attendance",
            "AttendanceFrame",
            "Attendance"
        )

    def show_reports(self):

        self.load_module(
            "reports",
            "ReportsFrame",
            "Reports"
        )

    # =========================================
    # Dashboard Refresh
    # =========================================

    def refresh_dashboard(self):

        if self.current_frame:

            try:

                self.current_frame.destroy()

            except:

                pass

        self.show_dashboard()
            # =========================================
    # Refresh Dashboard Counts
    # =========================================

    def refresh_dashboard_metrics(self):
        """
        Called by other modules after add/update/delete.
        If the dashboard is open, reload it.
        """

        if self.page_title.cget("text") == "Dashboard":
            self.show_dashboard()

    # =========================================
    # Exit Application
    # =========================================

    def exit_application(self):

        if messagebox.askyesno(
            "Exit",
            "Do you really want to exit?"
        ):
            self.root.destroy()
# =========================================
# Run Application
# =========================================

def run_application():

    MainApplication()


if __name__ == "__main__":

    run_application()
