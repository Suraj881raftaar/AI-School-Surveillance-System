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
    person_type: str = "Unknown"
    status: str = "Unknown"
    person_id: int | None = None


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
        conn = None
        try:
            conn = self.connect()
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
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

    def add_alert(self, message: str, image_path: str) -> None:
        now = datetime.now()
        date_text = now.strftime("%Y-%m-%d")
        time_text = now.strftime("%H:%M:%S")

        conn = None
        try:
            conn = self.connect()
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
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

    def get_alerts(self) -> list[sqlite3.Row]:
        conn = None
        try:
            conn = self.connect()
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
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def clear_alerts(self) -> None:
        conn = None
        try:
            conn = self.connect()
            conn.execute("DELETE FROM alerts")
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()


class FutureFaceRecognizer:
    """Loads trained LBPH model trainer.yml and retrieves labels.json metadata mapping."""

    def __init__(self, cv2_module, confidence_threshold=65.0, low_confidence_threshold=85.0) -> None:
        self.cv2 = cv2_module
        self.recognizer = None
        self.labels: dict[int, str] = {}
        self.labels_metadata: dict[int, dict] = {}
        self.available = False
        self.confidence_threshold = confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold
        self.load()

    def load(self) -> None:
        model_path = Path(MODEL_FOLDER) / "trainer.yml"
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
                self.labels = {}
                self.labels_metadata = {}
                for label_id, val in raw_labels.items():
                    if isinstance(val, dict):
                        person_name = val.get("name", f"Person {label_id}")
                        self.labels_metadata[int(label_id)] = val
                    else:
                        person_name = str(val)
                        self.labels_metadata[int(label_id)] = {
                            "name": person_name,
                            "person_type": "Student"
                        }
                    self.labels[int(label_id)] = person_name
            except (OSError, ValueError, TypeError):
                self.labels = {}
                self.labels_metadata = {}

    def recognize(self, face_gray) -> DetectionResult:
        if not self.available or self.recognizer is None:
            return DetectionResult("Unknown", None, False, "Unknown", "Unknown", None)

        try:
            label_id, confidence = self.recognizer.predict(face_gray)
        except Exception:
            return DetectionResult("Unknown", None, False, "Unknown", "Unknown", None)

        metadata = self.labels_metadata.get(int(label_id), {})
        name = metadata.get("name", f"Person {label_id}")
        person_type = metadata.get("person_type", "Student")
        person_id = metadata.get("id", None)

        # Retrieve base integer ID if not present in JSON
        if person_id is None:
            if label_id >= 2000:
                person_id = label_id - 2000
            elif label_id >= 1000:
                person_id = label_id - 1000

        # LBPH output is distance metric (smaller = more confident)
        if confidence < self.confidence_threshold:
            return DetectionResult(name, float(confidence), True, person_type, "Recognized", person_id)
        elif confidence < self.low_confidence_threshold:
            return DetectionResult(name, float(confidence), True, person_type, "Low Confidence", person_id)
        else:
            return DetectionResult("Unknown", float(confidence), False, "Unknown", "Unknown", None)


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
        self.recognized_counter_text = tk.StringVar(value="Recognized: 0")
        self.unknown_counter_text = tk.StringVar(value="Unknown: 0")
        self.average_confidence_text = tk.StringVar(value="Conf Distance: N/A")
        self.confidence_threshold_var = tk.DoubleVar(value=65.0)
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
        ).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Label(
            metrics,
            textvariable=self.recognized_counter_text,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(
            metrics,
            textvariable=self.unknown_counter_text,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Label(
            metrics,
            textvariable=self.average_confidence_text,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=3, padx=(0, 10))
        
        ttk.Label(
            metrics,
            textvariable=self.fps_text,
            style="SurveillanceMetric.TLabel",
        ).grid(row=0, column=4)

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

        # Slider and Switcher controls frame
        slider_frame = ttk.Frame(controls, style="SurveillancePanel.TFrame")
        slider_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        slider_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            slider_frame, 
            text="Conf Threshold:", 
            bg=WHITE, 
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.confidence_slider = ttk.Scale(
            slider_frame,
            from_=30.0,
            to=120.0,
            value=65.0,
            variable=self.confidence_threshold_var,
            orient="horizontal",
            command=self.update_threshold_from_slider
        )
        self.confidence_slider.grid(row=0, column=1, sticky="ew", padx=10)
        
        self.slider_val_lbl = tk.Label(slider_frame, text="65.0", bg=WHITE, font=("Arial", 10, "bold"), fg=BUTTON_COLOR)
        self.slider_val_lbl.grid(row=0, column=2, sticky="e", padx=(10, 20))

        tk.Label(
            slider_frame, 
            text="Device Index:", 
            bg=WHITE, 
            font=("Arial", 10, "bold")
        ).grid(row=0, column=3, sticky="w", padx=(10, 10))

        self.camera_selector = ttk.Combobox(
            slider_frame,
            textvariable=self.camera_index_var,
            values=["0", "1", "2", "3"],
            state="readonly",
            width=5
        )
        self.camera_selector.grid(row=0, column=4, sticky="w")

    def update_threshold_from_slider(self, val) -> None:
        try:
            threshold = float(val)
            self.slider_val_lbl.configure(text=f"{threshold:.1f}")
            if self.face_recognizer is not None:
                self.face_recognizer.confidence_threshold = threshold
                self.face_recognizer.low_confidence_threshold = threshold + 20.0
        except Exception:
            pass

    def trigger_attendance_logging(self, person_id: int | None, person_type: str, name: str, confidence: float | None = None) -> None:
        """
        API Hook for attendance logging module (Phase 5).
        Logs a recognized student/teacher transaction with duplicate prevention cooldown.
        """
        if person_id is None:
            return

        if not hasattr(self, "attendance_cooldowns"):
            self.attendance_cooldowns: dict[tuple[int, str], float] = {}

        # Configurable Cooldown (Default 60 seconds)
        cooldown_seconds = 60.0
        key = (person_id, person_type)
        now = time.monotonic()
        last_time = self.attendance_cooldowns.get(key, 0.0)

        if now - last_time < cooldown_seconds:
            # Duplicate detection: ignore record, write warning to console status
            self.queue_status(f"Attendance Already Recorded for {name} ({person_type}) recently.")
            return

        self.attendance_cooldowns[key] = now

        # Thread-safe async insertion
        threading.Thread(
            target=self.bg_record_attendance,
            args=(person_id, name, person_type, confidence),
            daemon=True
        ).start()

    def bg_record_attendance(self, person_id: int, name: str, person_type: str, confidence: float | None) -> None:
        """Executes database attendance insertion in a background thread."""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # Exposing status (Late vs Present)
        # Future attendance schedules can make this dynamic. Default: "Present"
        status = "Present"

        try:
            from attendance import AttendanceDB
            db = AttendanceDB()

            # Prevent writing duplicate entries on the same calendar date
            if db.has_attendance_today(person_id, person_type, date_str):
                self.queue_status(f"Attendance Already Recorded for {name} today.")
                return

            try:
                cam_id = int(self.camera_index_var.get())
            except Exception:
                cam_id = 0

            db.insert_record(
                person_name=name,
                person_type=person_type,
                date=date_str,
                time_value=time_str,
                status=status,
                person_id=person_id,
                confidence=confidence,
                camera_id=cam_id,
                recognition_method="LBPH"
            )
            self.queue_status(f"Recorded attendance: {name} ({person_type})")
            
            # Notify alert list to refresh
            self.queue_alert_refresh()
        except Exception as e:
            self.log_event(f"Failed to save background attendance: {e}", "ERROR")

    def log_event(self, message: str, level: str = "INFO") -> None:
        """Log event message to logs/surveillance_log.txt."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}\n"
        log_file = os.path.join(LOG_FOLDER, "surveillance_log.txt")
        try:
            os.makedirs(LOG_FOLDER, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass

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

        # Check model files exist first
        model_path = Path(MODEL_FOLDER) / "trainer.yml"
        labels_path = Path(MODEL_FOLDER) / "labels.json"
        if not model_path.exists() or not labels_path.exists():
            messagebox.showerror(
                "Model Error",
                "Trained face recognition model not found.\n\nPlease go to 'Face Training' tab first and build the model."
            )
            return

        if not self.load_cv_dependencies():
            return

        self.face_detector = self.load_face_detector()
        if self.face_detector is None:
            messagebox.showerror("Camera Error", "Haar cascade face detector not found.")
            return

        # Load Face recognizer using slider threshold
        try:
            threshold = float(self.confidence_threshold_var.get())
        except Exception:
            threshold = 65.0

        try:
            self.face_recognizer = FutureFaceRecognizer(
                self.cv2,
                confidence_threshold=threshold,
                low_confidence_threshold=threshold + 20.0
            )
            if not self.face_recognizer.available:
                raise ValueError("Model initialization error.")
        except Exception as e:
            self.log_event(f"Model load failure: {e}", "ERROR")
            messagebox.showerror("Model Loading Failure", f"Failed to load trained model files:\n{e}")
            return

        self.stop_event.clear()
        self.camera_running = True
        self.status_text.set("Starting camera...")
        self.log_event("Starting surveillance camera stream.", "INFO")

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
        self.log_event("Surveillance camera stream stopped.", "INFO")

    def detect_faces(self) -> None:
        # Get index dynamically from Combobox Var
        try:
            cam_idx = int(self.camera_index_var.get())
        except Exception:
            cam_idx = CAMERA_INDEX

        camera = self.cv2.VideoCapture(cam_idx)
        self.camera = camera

        try:
            if not camera.isOpened():
                self.queue_status("Camera not available.")
                self.log_event(f"Camera index {cam_idx} is not available.", "ERROR")
                return

            camera.set(self.cv2.CAP_PROP_FRAME_WIDTH, 960)
            camera.set(self.cv2.CAP_PROP_FRAME_HEIGHT, 540)
            self.queue_status("Camera started.")
            self.log_event(f"Camera index {cam_idx} started successfully.", "INFO")

            last_tick = time.perf_counter()
            fps_average = 0.0
            reconnect_attempts = 0

            while not self.stop_event.is_set():
                success, frame = camera.read()
                if not success:
                    # Connection loss: Attempt reconnect
                    self.queue_status("Loss of camera connection. Attempting to reconnect...")
                    self.log_event("Camera read error. Attempting camera reconnection...", "WARNING")
                    camera.release()
                    time.sleep(2.0)

                    camera = self.cv2.VideoCapture(cam_idx)
                    if not camera.isOpened():
                        reconnect_attempts += 1
                        self.queue_status(f"Reconnect attempt {reconnect_attempts} failed...")
                        continue

                    camera.set(self.cv2.CAP_PROP_FRAME_WIDTH, 960)
                    camera.set(self.cv2.CAP_PROP_FRAME_HEIGHT, 540)
                    self.camera = camera
                    self.queue_status("Camera reconnected.")
                    self.log_event("Camera reconnected successfully.", "INFO")
                    reconnect_attempts = 0
                    continue

                frame = self.cv2.flip(frame, 1)
                
                # Run recognition pipeline
                (
                    processed_frame,
                    detected_count,
                    recognized_count,
                    unknown_count,
                    avg_confidence,
                    unknown_detected
                ) = self.process_frame(frame)

                now_tick = time.perf_counter()
                elapsed = max(now_tick - last_tick, 0.001)
                instant_fps = 1.0 / elapsed
                last_tick = now_tick
                fps_average = instant_fps if fps_average == 0.0 else (
                    (fps_average * 0.85) + (instant_fps * 0.15)
                )

                self.queue_frame(
                    processed_frame,
                    detected_count,
                    recognized_count,
                    unknown_count,
                    avg_confidence,
                    fps_average
                )

                if unknown_detected:
                    self.create_unknown_alert(processed_frame)

                time.sleep(0.01)
        except Exception as error:
            self.queue_status(f"Camera error: {error}")
            self.log_event(f"Unexpected camera exception: {error}", "ERROR")
        finally:
            camera.release()
            if self.camera is camera:
                self.camera = None
            self.camera_running = False

    def process_frame(self, frame):
        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(70, 70),
        )

        detected_count = len(faces)
        if detected_count == 0:
            self.cv2.putText(
                frame,
                "No Face",
                (20, 35),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
            )
            return frame, 0, 0, 0, None, False

        processed_frame = frame.copy()
        recognized_count = 0
        unknown_count = 0
        total_confidence = 0.0
        confidence_samples = 0
        unknown_detected = False

        for (x, y, w, h) in faces:
            # Crop face region
            face_crop = gray[y : y + h, x : x + w]
            
            # Preprocess crop: resize to 200x200 & histogram equalize
            try:
                face_resized = self.cv2.resize(face_crop, (FACE_WIDTH, FACE_HEIGHT), interpolation=self.cv2.INTER_AREA)
                face_equalized = self.cv2.equalizeHist(face_resized)
                result = self.face_recognizer.recognize(face_equalized)
            except Exception as ex:
                self.log_event(f"Face processing error: {ex}", "WARNING")
                continue

            # Determine colors and text based on recognition status:
            # Green (Recognized), Yellow (Low Confidence), Red (Unknown)
            if result.status == "Recognized":
                box_color = (0, 255, 0) # Green
                recognized_count += 1
                label = f"{result.name} ({result.person_type})"
                # Log recognition event
                self.log_event(f"Recognized student/teacher: {result.name} (Type: {result.person_type}, Dist: {result.confidence:.1f})", "INFO")
                # Trigger attendance logging hook API
                self.trigger_attendance_logging(result.person_id, result.person_type, result.name, result.confidence)
            elif result.status == "Low Confidence":
                box_color = (0, 255, 255) # Yellow
                recognized_count += 1
                label = f"Low Conf: {result.name}"
                self.log_event(f"Low confidence match: {result.name} (Dist: {result.confidence:.1f})", "WARNING")
            else:
                box_color = (0, 0, 255) # Red
                unknown_count += 1
                label = "Unknown"
                unknown_detected = True
                self.log_event(f"Unknown face detected (Dist: {result.confidence:.1f if result.confidence is not None else 'N/A'})", "WARNING")

            if result.confidence is not None:
                total_confidence += result.confidence
                confidence_samples += 1
                confidence_label = f"Dist: {result.confidence:.1f}"
            else:
                confidence_label = ""

            # Draw box & labels on the colored frame
            self.cv2.rectangle(processed_frame, (x, y), (x + w, y + h), box_color, 2)
            self.cv2.putText(
                processed_frame,
                label,
                (x, max(y - 10, 15)),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                box_color,
                2,
            )
            if confidence_label:
                self.cv2.putText(
                    processed_frame,
                    confidence_label,
                    (x, y + h + 20),
                    self.cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    box_color,
                    2,
                )

        avg_confidence = total_confidence / confidence_samples if confidence_samples > 0 else None
        status_text = "Face Detected"

        return (
            processed_frame,
            detected_count,
            recognized_count,
            unknown_count,
            avg_confidence,
            unknown_detected
        )

    def queue_frame(
        self,
        frame,
        detected_count: int,
        recognized_count: int,
        unknown_count: int,
        avg_confidence: float | None,
        fps_value: float,
    ) -> None:
        try:
            if self.frame_queue.full():
                self.frame_queue.get_nowait()
            self.frame_queue.put_nowait((
                "frame",
                frame,
                detected_count,
                recognized_count,
                unknown_count,
                avg_confidence,
                fps_value
            ))
        except (queue.Empty, queue.Full):
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
            self.log_event("Saved unknown face alert screenshot to disk.", "WARNING")
            self.queue_alert_refresh()
        except Exception as e:
            self.queue_status("Unknown face detected, but alert could not be saved.")
            self.log_event(f"Failed to write alert screenshot: {e}", "ERROR")

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
                    (
                        _,
                        frame,
                        detected_count,
                        recognized_count,
                        unknown_count,
                        avg_confidence,
                        fps_value
                    ) = item
                    self.update_preview(frame)
                    self.last_frame = frame.copy()
                    
                    self.counter_text.set(f"Detected: {detected_count}")
                    self.recognized_counter_text.set(f"Recognized: {recognized_count}")
                    self.unknown_counter_text.set(f"Unknown: {unknown_count}")
                    self.fps_text.set(f"FPS: {fps_value:.1f}")

                    if avg_confidence is not None:
                        self.average_confidence_text.set(f"Avg Dist: {avg_confidence:.1f}")
                    else:
                        self.average_confidence_text.set("Avg Dist: N/A")

                    status_str = f"Tracking: {detected_count} face(s)" if detected_count > 0 else "No Face"
                    self.face_status.set(status_str)

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
            self.log_event(f"Manual screenshot saved successfully to {image_path}.", "INFO")
            messagebox.showinfo("Screenshot", "Screenshot captured successfully.")
        else:
            self.log_event(f"Manual screenshot write failed: {image_path}", "ERROR")
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
            self.log_event("Alert database cleared by user.", "INFO")
        except sqlite3.Error as error:
            self.log_event(f"Failed to clear alerts database: {error}", "ERROR")
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
