"""
teachers.py
AI School Surveillance System
"""

from __future__ import annotations

import os
import re
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from config import *


DATABASE = DATABASE_PATH


class TeacherDB:
    """SQLite helper for teacher records."""

    def __init__(self) -> None:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        self.conn = sqlite3.connect(DATABASE)
        self.cur = self.conn.cursor()
        self.create_table()

    def create_table(self) -> None:
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS teachers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_name TEXT,
                employee_id TEXT,
                subject TEXT,
                mobile TEXT,
                image_path TEXT
            )
            """
        )

        self.cur.execute("PRAGMA table_info(teachers)")
        columns = {row[1] for row in self.cur.fetchall()}

        required_columns = {
            "teacher_name": "TEXT",
            "employee_id": "TEXT",
            "subject": "TEXT",
            "mobile": "TEXT",
            "image_path": "TEXT",
        }

        for column_name, column_type in required_columns.items():
            if column_name not in columns:
                self.cur.execute(
                    f"ALTER TABLE teachers ADD COLUMN {column_name} {column_type}"
                )

        try:
            self.cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_teachers_employee_id
                ON teachers(employee_id)
                WHERE employee_id IS NOT NULL AND employee_id != ''
                """
            )
        except sqlite3.IntegrityError:
            pass
        self.conn.commit()

    def employee_id_exists(
        self,
        employee_id: str,
        exclude_teacher_id: int | None = None,
    ) -> bool:
        if exclude_teacher_id is None:
            self.cur.execute(
                "SELECT 1 FROM teachers WHERE employee_id = ? LIMIT 1",
                (employee_id,),
            )
        else:
            self.cur.execute(
                """
                SELECT 1 FROM teachers
                WHERE employee_id = ? AND id != ?
                LIMIT 1
                """,
                (employee_id, exclude_teacher_id),
            )

        return self.cur.fetchone() is not None

    def add_teacher(
        self,
        teacher_name: str,
        employee_id: str,
        subject: str,
        mobile: str,
        image_path: str,
    ) -> None:
        self.cur.execute(
            """
            INSERT INTO teachers
            (teacher_name, employee_id, subject, mobile, image_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (teacher_name, employee_id, subject, mobile, image_path),
        )
        self.conn.commit()

    def update_teacher(
        self,
        teacher_id: int,
        teacher_name: str,
        employee_id: str,
        subject: str,
        mobile: str,
        image_path: str,
    ) -> None:
        self.cur.execute(
            """
            UPDATE teachers
            SET teacher_name = ?,
                employee_id = ?,
                subject = ?,
                mobile = ?,
                image_path = ?
            WHERE id = ?
            """,
            (teacher_name, employee_id, subject, mobile, image_path, teacher_id),
        )
        self.conn.commit()

    def delete_teacher(self, teacher_id: int) -> None:
        self.cur.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
        self.conn.commit()

    def update_image(self, teacher_id: int, image_path: str) -> None:
        self.cur.execute(
            "UPDATE teachers SET image_path = ? WHERE id = ?",
            (image_path, teacher_id),
        )
        self.conn.commit()

    def get_teacher(self, teacher_id: int) -> tuple | None:
        self.cur.execute(
            """
            SELECT id, teacher_name, employee_id, subject, mobile, image_path
            FROM teachers
            WHERE id = ?
            """,
            (teacher_id,),
        )
        return self.cur.fetchone()

    def get_teachers(self) -> list[tuple]:
        self.cur.execute(
            """
            SELECT id, teacher_name, employee_id, subject, mobile, image_path
            FROM teachers
            ORDER BY id DESC
            """
        )
        return self.cur.fetchall()

    def search(self, text: str) -> list[tuple]:
        search_text = f"%{text.strip()}%"
        self.cur.execute(
            """
            SELECT id, teacher_name, employee_id, subject, mobile, image_path
            FROM teachers
            WHERE teacher_name LIKE ?
               OR employee_id LIKE ?
               OR subject LIKE ?
               OR mobile LIKE ?
            ORDER BY id DESC
            """,
            (search_text, search_text, search_text, search_text),
        )
        return self.cur.fetchall()

    def close(self) -> None:
        self.conn.close()


class TeachersFrame(ttk.Frame):
    """Teacher management UI."""

    def __init__(self, parent, app=None) -> None:
        super().__init__(parent)

        self.app = app
        self.db = TeacherDB()
        self.selected_id = None

        self.teacher_name = tk.StringVar()
        self.employee_id = tk.StringVar()
        self.subject = tk.StringVar()
        self.mobile = tk.StringVar()
        self.image_path = tk.StringVar()
        self.search = tk.StringVar()

        self.configure(style="Teachers.TFrame")
        self.configure_styles()
        self.create_widgets()
        self.load_teachers()

    def configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Teachers.TFrame", background=BG_COLOR)
        style.configure("TeachersPanel.TFrame", background=WHITE)
        style.configure(
            "TeachersTitle.TLabel",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 20, "bold"),
        )
        style.configure(
            "TeachersPanelTitle.TLabel",
            background=WHITE,
            foreground=HEADER_COLOR,
            font=("Arial", 13, "bold"),
        )
        style.configure(
            "TeachersLabel.TLabel",
            background=WHITE,
            foreground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
        )
        style.configure(
            "TeachersMuted.TLabel",
            background=WHITE,
            foreground="#667085",
            font=("Arial", 9),
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
            "Teachers.Treeview",
            font=("Arial", 10),
            rowheight=30,
            background=WHITE,
            fieldbackground=WHITE,
            foreground=TEXT_COLOR,
        )
        style.configure(
            "Teachers.Treeview.Heading",
            font=("Arial", 10, "bold"),
            foreground=HEADER_COLOR,
        )

    def create_widgets(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        heading = ttk.Label(
            self,
            text="TEACHER MANAGEMENT",
            style="TeachersTitle.TLabel",
        )
        heading.grid(row=0, column=0, columnspan=2, pady=(0, 16), sticky="w")

        self.create_form_panel()
        self.create_table_panel()

    def create_form_panel(self) -> None:
        left = ttk.Frame(self, style="TeachersPanel.TFrame", padding=18)
        left.grid(row=1, column=0, sticky="ns", padx=(0, 16), pady=(0, 0))
        left.grid_columnconfigure(1, weight=1)

        ttk.Label(
            left,
            text="Teacher Details",
            style="TeachersPanelTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.add_field(left, "Teacher Name", self.teacher_name, 1)
        self.add_field(left, "Employee ID", self.employee_id, 2)
        self.add_field(left, "Subject", self.subject, 3)
        self.add_field(left, "Mobile", self.mobile, 4)

        ttk.Label(left, text="Face Data", style="TeachersLabel.TLabel").grid(
            row=5,
            column=0,
            padx=(0, 10),
            pady=8,
            sticky="w",
        )
        self.face_status = ttk.Label(
            left,
            text="Not Captured",
            style="TeachersMuted.TLabel",
        )
        self.face_status.grid(row=5, column=1, pady=8, sticky="w")

        button_frame = ttk.Frame(left, style="TeachersPanel.TFrame")
        button_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        button_frame.grid_columnconfigure((0, 1), weight=1, uniform="buttons")

        ttk.Button(
            button_frame,
            text="Add Teacher",
            command=self.add_teacher,
            style="Success.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)

        ttk.Button(
            button_frame,
            text="Update Teacher",
            command=self.update_teacher,
            style="Primary.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)

        ttk.Button(
            button_frame,
            text="Delete Teacher",
            command=self.delete_teacher,
            style="Danger.TButton",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=5)

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear,
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=5)

        ttk.Button(
            button_frame,
            text="Capture Face",
            command=self.capture_face,
            style="Primary.TButton",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 5))

    def add_field(
        self,
        parent: ttk.Frame,
        label_text: str,
        variable: tk.StringVar,
        row: int,
    ) -> None:
        ttk.Label(parent, text=label_text, style="TeachersLabel.TLabel").grid(
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
        right = ttk.Frame(self, style="TeachersPanel.TFrame", padding=18)
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        ttk.Label(
            right,
            text="Teacher Records",
            style="TeachersPanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        search_frame = ttk.Frame(right, style="TeachersPanel.TFrame")
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        search_frame.grid_columnconfigure(0, weight=1)

        search_entry = ttk.Entry(search_frame, textvariable=self.search)
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        search_entry.bind("<Return>", lambda _event: self.search_teacher())

        ttk.Button(
            search_frame,
            text="Search",
            command=self.search_teacher,
            style="Primary.TButton",
        ).grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            search_frame,
            text="Refresh",
            command=self.load_teachers,
        ).grid(row=0, column=2)

        table_frame = ttk.Frame(right, style="TeachersPanel.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Name", "Employee ID", "Subject", "Mobile", "Image")
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Teachers.Treeview",
        )

        for col in columns:
            self.table.heading(col, text=col)

        self.table.column("ID", width=60, minwidth=50, anchor="center", stretch=False)
        self.table.column("Name", width=180, minwidth=130)
        self.table.column("Employee ID", width=120, minwidth=100, anchor="center")
        self.table.column("Subject", width=150, minwidth=110)
        self.table.column("Mobile", width=130, minwidth=110, anchor="center")
        self.table.column("Image", width=120, minwidth=100, anchor="center")

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

        self.table.bind("<<TreeviewSelect>>", self.select_teacher)

    def load_teachers(self) -> None:
        for row in self.table.get_children():
            self.table.delete(row)

        data = self.db.get_teachers()

        for teacher in data:
            values = list(teacher)
            values[5] = "Captured" if values[5] else "Not Captured"
            self.table.insert("", "end", values=values)

        self.refresh_dashboard()

    def add_teacher(self) -> None:
        if not self.validate_form():
            return

        if self.db.employee_id_exists(self.employee_id.get().strip()):
            messagebox.showerror("Error", "Employee ID Already Exists")
            return

        try:
            self.db.add_teacher(
                self.teacher_name.get().strip(),
                self.employee_id.get().strip(),
                self.subject.get().strip(),
                self.mobile.get().strip(),
                self.image_path.get().strip(),
            )
            messagebox.showinfo("Success", "Teacher Added Successfully")
            self.clear()
            self.load_teachers()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Employee ID Already Exists")
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def update_teacher(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Warning", "Select Teacher")
            return

        if not self.validate_form():
            return

        if self.db.employee_id_exists(
            self.employee_id.get().strip(),
            self.selected_id,
        ):
            messagebox.showerror("Error", "Employee ID Already Exists")
            return

        try:
            self.db.update_teacher(
                self.selected_id,
                self.teacher_name.get().strip(),
                self.employee_id.get().strip(),
                self.subject.get().strip(),
                self.mobile.get().strip(),
                self.image_path.get().strip(),
            )
            messagebox.showinfo("Updated", "Teacher Updated")
            self.clear()
            self.load_teachers()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Employee ID Already Exists")
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_teacher(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Warning", "Select Teacher")
            return

        if messagebox.askyesno("Delete", "Delete this Teacher?"):
            try:
                self.db.delete_teacher(self.selected_id)
                self.clear()
                self.load_teachers()
            except sqlite3.Error as error:
                messagebox.showerror("Database Error", str(error))

    def search_teacher(self) -> None:
        for row in self.table.get_children():
            self.table.delete(row)

        data = self.db.search(self.search.get())

        for teacher in data:
            values = list(teacher)
            values[5] = "Captured" if values[5] else "Not Captured"
            self.table.insert("", "end", values=values)

    def select_teacher(self, event=None) -> None:
        selected = self.table.focus()

        if not selected:
            return

        values = self.table.item(selected, "values")

        if not values:
            return

        self.selected_id = int(values[0])
        teacher = self.db.get_teacher(self.selected_id)

        if teacher is None:
            return

        self.teacher_name.set(teacher[1] or "")
        self.employee_id.set(teacher[2] or "")
        self.subject.set(teacher[3] or "")
        self.mobile.set(teacher[4] or "")
        self.image_path.set(teacher[5] or "")

        if teacher[5]:
            self.face_status.configure(text="Captured")
        else:
            self.face_status.configure(text="Not Captured")

    def clear(self) -> None:
        self.selected_id = None
        self.teacher_name.set("")
        self.employee_id.set("")
        self.subject.set("")
        self.mobile.set("")
        self.image_path.set("")
        self.search.set("")
        self.face_status.configure(text="Not Captured")

        selected_items = self.table.selection()
        if selected_items:
            self.table.selection_remove(*selected_items)

    def capture_face(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Warning", "Please Select Teacher First")
            return

        try:
            import cv2
        except ImportError:
            messagebox.showerror("Error", "OpenCV not installed")
            return

        save_folder = self.get_teacher_folder(self.selected_id)
        os.makedirs(save_folder, exist_ok=True)

        face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        if face_detector.empty():
            messagebox.showerror("Error", "Face detector could not be loaded")
            return

        camera = cv2.VideoCapture(CAMERA_INDEX)

        if not camera.isOpened():
            camera.release()
            messagebox.showerror("Error", "Camera not available")
            return

        count = 0

        try:
            while True:
                ret, frame = camera.read()

                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_detector.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces:
                    count += 1
                    face = gray[y : y + h, x : x + w]
                    face = cv2.resize(face, (FACE_WIDTH, FACE_HEIGHT))

                    cv2.imwrite(
                        os.path.join(save_folder, f"{count}.jpg"),
                        face,
                    )

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        str(count),
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                    )

                cv2.imshow("Capture Face", frame)
                key = cv2.waitKey(1)

                if key == 13 or count >= 30:
                    break
        finally:
            camera.release()
            cv2.destroyAllWindows()

        self.image_path.set(save_folder)
        self.face_status.configure(text="Captured")
        self.db.update_image(self.selected_id, save_folder)
        self.load_teachers()

        messagebox.showinfo("Success", "Face Images Saved Successfully")

    def validate_form(self) -> bool:
        if not self.teacher_name.get().strip():
            messagebox.showerror("Error", "Teacher Name Required")
            return False

        if not self.employee_id.get().strip():
            messagebox.showerror("Error", "Employee ID Required")
            return False

        if not self.subject.get().strip():
            messagebox.showerror("Error", "Subject Required")
            return False

        mobile = self.mobile.get().strip()
        if mobile and re.fullmatch(r"[0-9+\-\s()]{7,20}", mobile) is None:
            messagebox.showerror("Error", "Invalid Mobile Number")
            return False

        return True

    def get_teacher_folder(self, teacher_id: int) -> str:
        return os.path.join(TEACHER_FOLDER, str(teacher_id))

    def refresh_dashboard(self) -> None:
        if self.app and hasattr(self.app, "refresh_dashboard_metrics"):
            self.app.refresh_dashboard_metrics()

    def destroy(self) -> None:
        try:
            self.db.close()
        finally:
            super().destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Teachers")
    root.geometry("1200x700")
    root.configure(bg=BG_COLOR)
    page = TeachersFrame(root)
    page.pack(fill="both", expand=True)
    root.mainloop()
