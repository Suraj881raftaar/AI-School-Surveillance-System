"""
register_face.py
AI School Surveillance System
"""

from __future__ import annotations

import cv2
import os
import sqlite3
import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

from PIL import Image
from PIL import ImageTk

from config import *


class RegisterFaceFrame(ttk.Frame):

    def __init__(self, parent, app=None):

        super().__init__(parent)

        self.app = app

        self.cap = None
        self.face_detector = None
        self.show_camera_after_id = None

        self.person_type = tk.StringVar(value="Student")

        self.person_name = tk.StringVar()

        self.capture_count = 0

        self.max_images = 50

        self.configure(style="Register.TFrame")

        self.configure_styles()

        self.create_widgets()

        self.load_people()

        self.person_type.trace_add(
    "write",
    lambda *args: self.load_people()
)
            # ==========================================
    # Styles
    # ==========================================

    def configure_styles(self):

        style = ttk.Style()

        style.configure(
            "Register.TFrame",
            background=BG_COLOR
        )

        style.configure(
            "Register.TLabelframe",
            background=BG_COLOR
        )

        style.configure(
            "Register.TLabelframe.Label",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 11, "bold")
        )
            # ==========================================
    # Create Widgets
    # ==========================================

    def create_widgets(self):

        # ---------------- Main ----------------

        main = tk.Frame(
            self,
            bg=BG_COLOR
        )

        main.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # ---------------- Left ----------------

        left = ttk.LabelFrame(
            main,
            text="Registration",
            style="Register.TLabelframe"
        )

        left.pack(
            side="left",
            fill="y",
            padx=(0,20)
        )

        tk.Label(
            left,
            text="Person Type",
            bg=BG_COLOR
        ).pack(anchor="w", padx=15, pady=(15,5))

        ttk.Combobox(
            left,
            textvariable=self.person_type,
            values=["Student", "Teacher"],
            state="readonly",
            width=20
        ).pack(padx=15)

        tk.Label(
            left,
            text="Person Name",
            bg=BG_COLOR
        ).pack(anchor="w", padx=15, pady=(15,5))

        self.person_combo = ttk.Combobox(
            left,
            textvariable=self.person_name,
            width=30,
            state="readonly"
        )

        self.person_combo.pack(padx=15)

        self.progress = tk.Label(
            left,
            text="Captured : 0 / 50",
            bg=BG_COLOR,
            font=("Arial",11,"bold")
        )

        self.progress.pack(pady=20)

        tk.Button(
            left,
            text="Start Camera",
            width=20,
            command=self.start_camera
        ).pack(pady=5)

        tk.Button(
            left,
            text="Capture Face",
            width=20,
            command=self.capture_face
        ).pack(pady=5)

        tk.Button(
            left,
            text="Stop Camera",
            width=20,
            command=self.stop_camera
        ).pack(pady=5)

        # ---------------- Right ----------------

        right = ttk.LabelFrame(
            main,
            text="Camera Preview",
            style="Register.TLabelframe"
        )

        right.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.camera_label = tk.Label(
            right,
            bg="black",
            width=80,
            height=30
        )

        self.camera_label.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )
            # ==========================================
    # Load Students / Teachers
    # ==========================================

    def load_people(self):

        try:

            with sqlite3.connect(DATABASE_PATH) as conn:

                cur = conn.cursor()

                if self.person_type.get() == "Student":

                    cur.execute("""

                        SELECT student_name

                        FROM students

                        ORDER BY student_name

                    """)

                else:

                    cur.execute("""

                        SELECT teacher_name

                        FROM teachers

                        ORDER BY teacher_name

                    """)

                names = [

                    row[0]

                    for row in cur.fetchall()

                ]

            self.person_combo["values"] = names

            if names:

                self.person_combo.current(0)

        except Exception as e:

            messagebox.showerror(

                "Database Error",

                str(e)

            )
                # ==========================================
    # Load Face Detector
    # ==========================================

    def load_face_detector(self):

        detector = cv2.CascadeClassifier(
            HAARCASCADE_PATH
        )

        if detector.empty():

            messagebox.showerror(
                "Camera Error",
                "Face detector could not be loaded."
            )

            return False

        self.face_detector = detector

        return True
                # ==========================================
    # Start Camera
    # ==========================================

    def start_camera(self):

        if self.cap is not None:

            return

        if not self.load_face_detector():

            return

        self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():

            self.cap.release()

            self.cap = None

            messagebox.showerror(
                "Camera Error",
                "Unable to open camera."
            )

            return

        self.show_camera()
            # ==========================================
    # Camera Preview
    # ==========================================

    def show_camera(self):

        if self.cap is None:

            return

        ret, frame = self.cap.read()

        if ret:

            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            image = Image.fromarray(frame)

            image = image.resize((700, 500))

            photo = ImageTk.PhotoImage(image)

            self.camera_label.configure(image=photo)

            self.camera_label.image = photo

        self.show_camera_after_id = self.after(
            10,
            self.show_camera
        )
            # ==========================================
    # Stop Camera
    # ==========================================

    def stop_camera(self):

        if self.show_camera_after_id is not None:

            try:

                self.after_cancel(self.show_camera_after_id)

            except tk.TclError:

                pass

            self.show_camera_after_id = None

        if self.cap:

            self.cap.release()

            self.cap = None

        self.camera_label.configure(
            image=""
        )

        self.camera_label.image = None

        try:

            cv2.destroyWindow("Capturing Faces")

        except cv2.error:

            pass
       # ==========================================
    # Capture 50 Face Images
    # ==========================================

    def capture_face(self):

        if self.cap is None:

            messagebox.showwarning(
                "Camera",
                "Please start the camera first."
            )

            return

        if self.face_detector is None and not self.load_face_detector():

            return

        name = self.person_name.get().strip()

        if not name:

            messagebox.showwarning(
                "Name",
                "Please select a person."
            )

            return

        if self.person_type.get() == "Student":

            save_folder = os.path.join(STUDENT_FOLDER, name)

        else:

            save_folder = os.path.join(TEACHER_FOLDER, name)

        os.makedirs(save_folder, exist_ok=True)

        self.capture_count = 0

        try:

            while self.capture_count < self.max_images:

                ret, frame = self.cap.read()

                if not ret:
                    continue

                gray = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2GRAY
                )

                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.3,
                    minNeighbors=5
                )

                for (x, y, w, h) in faces:

                    face = gray[y:y+h, x:x+w]

                    face = cv2.resize(
                        face,
                        (200, 200)
                    )

                    self.capture_count += 1

                    filename = os.path.join(
                        save_folder,
                        f"{self.capture_count}.jpg"
                    )

                    cv2.imwrite(
                        filename,
                        face
                    )

                    self.progress.config(
                        text=f"Captured : {self.capture_count} / {self.max_images}"
                    )

                    self.update()

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x+w, y+h),
                        (0,255,0),
                        2
                    )

                    break

                cv2.imshow(
                    "Capturing Faces",
                    frame
                )

                cv2.waitKey(50)

        finally:

            try:

                cv2.destroyWindow("Capturing Faces")

            except cv2.error:

                pass

        messagebox.showinfo(
            "Completed",
            f"{self.max_images} face images captured successfully."
        )

    def destroy(self):

        self.stop_camera()

        super().destroy()
