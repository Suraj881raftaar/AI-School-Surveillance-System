"""
surveillance.py
AI School Surveillance System
"""

from __future__ import annotations

import json
import os
import queue
import sqlite3
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from config import *


ALERT_COOLDOWN_SECONDS = 5.0


@dataclass(frozen=True)
class DetectionResult:
    name: str
    confidence: float | None
    is_known: bool


class SurveillanceDB:
    """Database helper for surveillance alerts."""

    def __init__(self) -> None:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        os.makedirs(LOG_FOLDER, exist_ok=True)
        self.ensure_alerts_table()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_alerts_table(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    time TEXT,
                    message TEXT,
                    image TEXT,
                    alert_type TEXT,
                    description TEXT
                )
                """
            )

            required_columns = {
                "date": "TEXT",
                "time": "TEXT",
                "message": "TEXT",
                "image": "TEXT",
                "alert_type": "TEXT",
                "description": "TEXT",
            }
            existing_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(alerts)")
            }

            for column_name, column_type in required_columns.items():
                if column_name not in existing_columns:
                    conn.execute(
                        f"ALTER TABLE alerts ADD COLUMN {column_name} {column_type}"
                    )

            conn.commit()

    def add_alert(self, message: str, image_path: str) -> None:
        now = datetime.now()
        date_text = now.strftime("%Y-%m-%d")
        time_text = now.strftime("%H:%M:%S")

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO alerts(
                    date, time, message, image, alert_type, description
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    date_text,
                    time_text,
                    message,
                    image_path,
                    "Unknown Face",
                    message,
                ),
            )
            conn.commit()

    def get_alerts(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT id,
                           date,
                           time,
                           COALESCE(NULLIF(message, ''), description, '') AS message,
                           COALESCE(image, '') AS image
                    FROM alerts
                    ORDER BY id DESC
                    """
                ).fetchall()
            )

    def clear_alerts(self) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM alerts")
            conn.commit()


class FutureFaceRecognizer:
    """Optional recognizer hook for future trained models."""

    def __init__(self, cv2_module) -> None:
        self.cv2 = cv2_module
        self.recognizer = None
        self.labels: dict[int, str] = {}
        self.available = False
        self.load()

    def load(self) -> None:
        model_path = Path(MODEL_FOLDER) / "face_recognizer.yml"
        labels_path = Path(MODEL_FOLDER) / "labels.json"

        if not model_path.exists():
            return

        if not hasattr(self.cv2, "face"):
            return

        try:
            recognizer = self.cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(str(model_path))
            self.recognizer = recognizer
            self.available = True
        except Exception:
            self.recognizer = None
            self.available = False
            return

        if labels_path.exists():
            try:
                raw_labels = json.loads(labels_path.read_text(encoding="utf-8"))
                self.labels = {
                    int(label_id): str(name)
                    for label_id, name in raw_labels.items()
                }
            except (OSError, ValueError, TypeError):
                self.labels = {}

    def recognize(self, face_gray) -> DetectionResult:
        if not self.available or self.recognizer is None:
            return DetectionResult("Unknown", None, False)

        try:
            label_id, confidence = self.recognizer.predict(face_gray)
        except Exception:
            return DetectionResult("Unknown", None, False)

        if confidence <= 70:
            return DetectionResult(
                self.labels.get(int(label_id), f"Person {label_id}"),
                float(confidence),
                True,
            )

        return DetectionResult("Unknown", float(confidence), False)


class SurveillanceFrame(ttk.Frame):
    """Live surveillance and unknown-face alerting frame."""

    def __init__(self, parent, app=None) -> None:
        super().__init__(parent)

        self.app = app
        self.db = SurveillanceDB()

        self.cv2 = None
        self.image_module = None
        self.image_tk_module = None
        self.face_detector = None
        self.face_recognizer = None
        self.camera = None
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.frame_queue: queue.Queue = queue.Queue(maxsize=3)
        self.ui_after_id = None
        self.camera_running = False
        self.preview_image = None
        self.last_frame = None
        self.last_alert_time = 0.0
        self.detection_total = 0
        self.current_fps = 0.0

        self.status_text = tk.StringVar(value="Camera stopped.")
        self.face_status = tk.StringVar(value="No Face")
        self.counter_text = tk.StringVar(value="Detections: 0")
        self.fps_text = tk.StringVar(value="FPS: 0.0")

        self.configure(style="Surveillance.TFrame")
        self.configure_styles()
        self.create_widgets()
        self.load_alerts()
        self.process_queue()

    def configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Surveillance.TFrame", background=BG_COLOR)
        style.configure("SurveillancePanel.TFrame", background=WHITE)
        style.configure(
            "SurveillanceTitle.TLabel",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 20, "bold"),
        )
        style.configure(
            "SurveillanceSubtitle.TLabel",
            background=BG_COLOR,
            foreground="#667085",
            font=("Arial", 10),
        )
        style.configure(
            "SurveillancePanelTitle.TLabel",
            background=WHITE,
            foreground=HEADER_COLOR,
            font=("Arial", 13, "bold"),
        )
        style.configure(
            "SurveillanceLabel.TLabel",
            background=WHITE,
            foreground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
        )
        style.configure(
            "SurveillanceStatus.TLabel",
            background=WHITE,
            foreground="#667085",
            font=("Arial", 10),
        )
        style.configure(
            "SurveillanceMetric.TLabel",
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
            "Surveillance.Treeview",
            font=("Arial", 10),
            rowheight=28,
            background=WHITE,
            fieldbackground=WHITE,
            foreground=TEXT_COLOR,
        )
        style.configure(
            "Surveillance.Treeview.Heading",
            font=("Arial", 10, "bold"),
            foreground=HEADER_COLOR,
        )

    def create_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Surveillance.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="SURVEILLANCE",
            style="SurveillanceTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Live face detection and unknown-person alert monitoring.",
            style="SurveillanceSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.create_preview_panel()
        self.create_alert_panel()
        self.create_status_bar()

    def create_preview_panel(self) -> None:
        panel = ttk.Frame(self, style="SurveillancePanel.TFrame", padding=18)
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        top = ttk.Frame(panel, style="SurveillancePanel.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure(0, weight=1)

        ttk.Label(
            top,
            text="Live Camera Preview",
            style="SurveillancePanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        metrics = ttk.Frame(top, style="SurveillancePanel.TFrame")
        metrics.grid(row=0, column=1, sticky="e")

        ttk.Label(
            metrics,
            textvariable=self.counter_text,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=0, padx=(0, 14))
        ttk.Label(
            metrics,
            textvariable=self.fps_text,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=1)

        preview_container = tk.Frame(panel, bg="#0B1220", bd=0, highlightthickness=0)
        preview_container.grid(row=1, column=0, sticky="nsew")
        preview_container.grid_columnconfigure(0, weight=1)
        preview_container.grid_rowconfigure(0, weight=1)

        self.preview_label = tk.Label(
            preview_container,
            text="Camera preview will appear here",
            bg="#0B1220",
            fg=WHITE,
            font=("Arial", 14, "bold"),
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        controls = ttk.Frame(panel, style="SurveillancePanel.TFrame")
        controls.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        controls.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="buttons")

        ttk.Button(
            controls,
            text="Start Camera",
            command=self.start_camera,
            style="Success.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(
            controls,
            text="Stop Camera",
            command=self.stop_camera,
            style="Danger.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(
            controls,
            text="Capture Screenshot",
            command=self.capture_screenshot,
            style="Primary.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=5)
        ttk.Button(
            controls,
            text="Clear Alerts",
            command=self.clear_alerts,
        ).grid(row=0, column=3, sticky="ew", padx=(5, 0))

    def create_alert_panel(self) -> None:
        panel = ttk.Frame(self, style="SurveillancePanel.TFrame", padding=18)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ttk.Label(
            panel,
            text="Alerts",
            style="SurveillancePanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        table_frame = ttk.Frame(panel, style="SurveillancePanel.TFrame")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Date", "Time", "Message", "Image")
        self.alerts_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Surveillance.Treeview",
        )

        for column in columns:
            self.alerts_tree.heading(column, text=column)

        self.alerts_tree.column("ID", width=55, minwidth=45, anchor="center", stretch=False)
        self.alerts_tree.column("Date", width=95, minwidth=85, anchor="center")
        self.alerts_tree.column("Time", width=80, minwidth=70, anchor="center")
        self.alerts_tree.column("Message", width=180, minwidth=130)
        self.alerts_tree.column("Image", width=160, minwidth=120)

        y_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.alerts_tree.yview,
        )
        x_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.alerts_tree.xview,
        )
        self.alerts_tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.alerts_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def create_status_bar(self) -> None:
        status_bar = ttk.Frame(self, style="SurveillancePanel.TFrame", padding=(14, 8))
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        status_bar.grid_columnconfigure(1, weight=1)

        ttk.Label(
            status_bar,
            textvariable=self.face_status,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=(0, 16))
        ttk.Label(
            status_bar,
            textvariable=self.status_text,
            style="SurveillanceStatus.TLabel",
        ).grid(row=0, column=1, sticky="w")

    def load_cv_dependencies(self) -> bool:
        if self.cv2 is not None and self.image_module is not None:
            return True

        try:
            import cv2
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror(
                "Camera Error",
                "OpenCV and Pillow are required for surveillance.",
            )
            return False

        self.cv2 = cv2
        self.image_module = Image
        self.image_tk_module = ImageTk
        return True

    def load_face_detector(self):
        cascade_name = "haarcascade_frontalface_default.xml"
        possible_paths = [
            Path(HAARCASCADE_FOLDER) / cascade_name,
            Path(self.cv2.data.haarcascades) / cascade_name,
        ]

        for cascade_path in possible_paths:
            if cascade_path.exists():
                detector = self.cv2.CascadeClassifier(str(cascade_path))
                if not detector.empty():
                    return detector

        return None

    def start_camera(self) -> None:
        if self.camera_running:
            self.status_text.set("Camera is already running.")
            return

        if not self.load_cv_dependencies():
            return

        self.face_detector = self.load_face_detector()
        if self.face_detector is None:
            messagebox.showerror("Camera Error", "Haar cascade face detector not found.")
            return

        self.face_recognizer = FutureFaceRecognizer(self.cv2)
        self.stop_event.clear()
        self.camera_running = True
        self.status_text.set("Starting camera...")

        self.worker_thread = threading.Thread(target=self.detect_faces, daemon=True)
        self.worker_thread.start()

    def stop_camera(self) -> None:
        if not self.camera_running and self.worker_thread is None:
            self.status_text.set("Camera stopped.")
            return

        self.stop_event.set()

        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.5)

        worker_alive = (
            self.worker_thread is not None
            and self.worker_thread.is_alive()
        )

        if worker_alive:
            self.status_text.set("Stopping camera...")
            return

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        self.worker_thread = None
        self.camera_running = False
        self.face_status.set("No Face")
        self.status_text.set("Camera stopped.")

    def detect_faces(self) -> None:
        camera = self.cv2.VideoCapture(CAMERA_INDEX)
        self.camera = camera

        try:
            if not camera.isOpened():
                self.queue_status("Camera not available.")
                return

            camera.set(self.cv2.CAP_PROP_FRAME_WIDTH, 960)
            camera.set(self.cv2.CAP_PROP_FRAME_HEIGHT, 540)
            self.queue_status("Camera started.")

            last_tick = time.perf_counter()
            fps_average = 0.0

            while not self.stop_event.is_set():
                success, frame = camera.read()
                if not success:
                    self.queue_status("Unable to read camera frame.")
                    time.sleep(0.05)
                    continue

                frame = self.cv2.flip(frame, 1)
                processed_frame, has_face, label_text, unknown_detected = self.process_frame(
                    frame
                )

                now_tick = time.perf_counter()
                elapsed = max(now_tick - last_tick, 0.001)
                instant_fps = 1.0 / elapsed
                last_tick = now_tick
                fps_average = instant_fps if fps_average == 0.0 else (
                    (fps_average * 0.85) + (instant_fps * 0.15)
                )

                self.queue_frame(processed_frame, has_face, label_text, fps_average)

                if unknown_detected:
                    self.create_unknown_alert(processed_frame)

                time.sleep(0.01)
        except Exception as error:
            self.queue_status(f"Camera error: {error}")
        finally:
            camera.release()
            if self.camera is camera:
                self.camera = None
            self.camera_running = False
            if self.stop_event.is_set():
                self.queue_status("Camera stopped.")

    def process_frame(self, frame):
        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(70, 70),
        )

        if len(faces) == 0:
            self.cv2.putText(
                frame,
                "No Face",
                (20, 35),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
            )
            return frame, False, "No Face", False

        unknown_detected = False

        for (x, y, w, h) in faces:
            face_gray = gray[y : y + h, x : x + w]
            face_gray = self.cv2.resize(face_gray, (FACE_WIDTH, FACE_HEIGHT))
            result = self.face_recognizer.recognize(face_gray)

            if result.is_known:
                label = result.name
            else:
                label = "Unknown"
                unknown_detected = True

            confidence_label = ""
            if result.confidence is not None:
                confidence_label = f" ({result.confidence:.1f})"

            self.cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 180, 0), 2)
            self.cv2.putText(
                frame,
                "Face Detected",
                (x, max(y - 34, 24)),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 180, 0),
                2,
            )
            self.cv2.putText(
                frame,
                f"{label}{confidence_label}",
                (x, y + h + 28),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        return frame, True, "Face Detected", unknown_detected

    def queue_frame(
        self,
        frame,
        has_face: bool,
        label_text: str,
        fps_value: float,
    ) -> None:
        try:
            if self.frame_queue.full():
                self.frame_queue.get_nowait()
            self.frame_queue.put_nowait(("frame", frame, has_face, label_text, fps_value))
        except queue.Empty:
            pass
        except queue.Full:
            pass

    def queue_status(self, text: str) -> None:
        try:
            self.frame_queue.put_nowait(("status", text))
        except queue.Full:
            pass

    def create_unknown_alert(self, frame) -> None:
        current_time = time.monotonic()
        if current_time - self.last_alert_time < ALERT_COOLDOWN_SECONDS:
            return

        self.last_alert_time = current_time
        now = datetime.now()
        filename = f"unknown_face_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(LOG_FOLDER, filename)

        try:
            self.cv2.imwrite(image_path, frame)
            self.db.add_alert("Unknown face detected", image_path)
            self.queue_status("Unknown face detected. Alert saved.")
            self.queue_alert_refresh()
        except Exception:
            self.queue_status("Unknown face detected, but alert could not be saved.")

    def queue_alert_refresh(self) -> None:
        try:
            self.frame_queue.put_nowait(("refresh_alerts",))
        except queue.Full:
            pass

    def process_queue(self) -> None:
        try:
            while True:
                item = self.frame_queue.get_nowait()
                item_type = item[0]

                if item_type == "frame":
                    _, frame, has_face, label_text, fps_value = item
                    self.update_preview(frame)
                    self.last_frame = frame.copy()
                    self.face_status.set(label_text)
                    self.current_fps = fps_value
                    self.fps_text.set(f"FPS: {fps_value:.1f}")

                    if has_face:
                        self.detection_total += 1
                        self.counter_text.set(f"Detections: {self.detection_total}")

                elif item_type == "status":
                    self.status_text.set(item[1])

                elif item_type == "refresh_alerts":
                    self.load_alerts()
                    self.refresh_dashboard()
        except queue.Empty:
            pass

        self.ui_after_id = self.after(30, self.process_queue)

    def update_preview(self, frame) -> None:
        if self.cv2 is None or self.image_module is None:
            return

        rgb_frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        image = self.image_module.fromarray(rgb_frame)

        preview_width = max(self.preview_label.winfo_width(), 640)
        preview_height = max(self.preview_label.winfo_height(), 420)
        image.thumbnail((preview_width, preview_height))

        self.preview_image = self.image_tk_module.PhotoImage(image=image)
        self.preview_label.configure(image=self.preview_image, text="")

    def capture_screenshot(self) -> None:
        if self.last_frame is None:
            messagebox.showwarning("Screenshot", "No camera frame available.")
            return

        if self.cv2 is None:
            messagebox.showerror("Screenshot", "OpenCV is not available.")
            return

        os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)
        now = datetime.now()
        image_path = os.path.join(
            SCREENSHOT_FOLDER,
            f"surveillance_{now.strftime('%Y%m%d_%H%M%S')}.jpg",
        )

        if self.cv2.imwrite(image_path, self.last_frame):
            self.status_text.set(f"Screenshot saved: {image_path}")
            messagebox.showinfo("Screenshot", "Screenshot captured successfully.")
        else:
            messagebox.showerror("Screenshot", "Unable to save screenshot.")

    def load_alerts(self) -> None:
        if not hasattr(self, "alerts_tree"):
            return

        for row_id in self.alerts_tree.get_children():
            self.alerts_tree.delete(row_id)

        for alert in self.db.get_alerts():
            self.alerts_tree.insert(
                "",
                "end",
                values=(
                    alert["id"],
                    alert["date"] or "",
                    alert["time"] or "",
                    alert["message"] or "",
                    alert["image"] or "",
                ),
            )

    def clear_alerts(self) -> None:
        if not messagebox.askyesno("Clear Alerts", "Delete all surveillance alerts?"):
            return

        try:
            self.db.clear_alerts()
            self.load_alerts()
            self.refresh_dashboard()
            self.status_text.set("Alerts cleared.")
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def refresh_dashboard(self) -> None:
        if self.app is None:
            return

        try:
            if hasattr(self.app, "refresh_dashboard_metrics"):
                self.app.refresh_dashboard_metrics()
            elif (
                hasattr(self.app, "refresh_dashboard")
                and hasattr(self.app, "page_title")
                and self.app.page_title.cget("text") == "Dashboard"
            ):
                self.app.refresh_dashboard()
        except tk.TclError:
            pass

    def destroy(self) -> None:
        if self.ui_after_id is not None:
            try:
                self.after_cancel(self.ui_after_id)
            except tk.TclError:
                pass
            self.ui_after_id = None

        self.stop_camera()
        super().destroy()


SurveillanceSystem = SurveillanceFrame


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Surveillance")
    root.geometry("1200x700")
    root.configure(bg=BG_COLOR)
    page = SurveillanceFrame(root)
    page.pack(fill="both", expand=True, padx=20, pady=20)
    root.mainloop()
