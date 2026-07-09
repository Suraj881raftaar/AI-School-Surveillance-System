"""
register_face.py
AI School Surveillance System
"""

from __future__ import annotations

import cv2
import os
import sqlite3
import tkinter as tk
import time
import queue
import threading

from tkinter import ttk
from tkinter import messagebox

from PIL import Image
from PIL import ImageTk

from config import *


class CameraController:
    """Helper class to isolate OpenCV camera management from Tkinter UI."""

    # Camera States
    STATE_IDLE = "IDLE"
    STATE_STARTING = "STARTING"
    STATE_RUNNING = "RUNNING"
    STATE_PAUSED = "PAUSED"
    STATE_STOPPING = "STOPPING"
    STATE_STOPPED = "STOPPED"
    STATE_ERROR = "ERROR"

    def __init__(self, event_queue: queue.Queue) -> None:
        self.state = self.STATE_IDLE
        self.cap = None
        self.queue = event_queue
        self.stop_event = threading.Event()
        self.worker_thread = None
        self._state_lock = threading.Lock()

        # Capture metrics
        self.is_capturing = False
        self.capture_count = 0
        self.max_images = 50
        self.last_capture_time = 0.0
        self.save_folder = ""
        self.face_detector = None

    def set_state(self, new_state: str) -> None:
        """Validate and transition to a new camera state."""
        with self._state_lock:
            curr = self.state
            valid = False
            
            # Define state transition matrix
            if curr == self.STATE_IDLE and new_state == self.STATE_STARTING:
                valid = True
            elif curr == self.STATE_STARTING and new_state in (
                self.STATE_RUNNING,
                self.STATE_ERROR,
                self.STATE_STOPPING,
            ):
                valid = True
            elif curr == self.STATE_RUNNING and new_state in (
                self.STATE_PAUSED,
                self.STATE_STOPPING,
                self.STATE_ERROR,
            ):
                valid = True
            elif curr == self.STATE_PAUSED and new_state in (
                self.STATE_RUNNING,
                self.STATE_STOPPING,
                self.STATE_ERROR,
            ):
                valid = True
            elif curr == self.STATE_STOPPING and new_state in (
                self.STATE_STOPPED,
                self.STATE_ERROR,
            ):
                valid = True
            elif curr == self.STATE_STOPPED and new_state in (
                self.STATE_STARTING,
                self.STATE_IDLE,
            ):
                valid = True
            elif curr == self.STATE_ERROR and new_state in (
                self.STATE_STOPPING,
                self.STATE_STARTING,
                self.STATE_IDLE,
            ):
                valid = True

            if valid:
                self.state = new_state
                self.queue.put(("state", new_state))
            else:
                print(f"[CameraController] Warning: Invalid transition attempted from {curr} to {new_state}")

    def load_detector(self) -> bool:
        """Load Haar Cascade face detector XML configuration."""
        if self.face_detector is not None:
            return True
        detector = cv2.CascadeClassifier(HAARCASCADE_PATH)
        if detector.empty():
            return False
        self.face_detector = detector
        return True

    def start(self, camera_index: int) -> None:
        """Spawn the background thread to initialize and read from the camera device."""
        if self.state not in (self.STATE_IDLE, self.STATE_STOPPED, self.STATE_ERROR):
            return

        self.set_state(self.STATE_STARTING)
        self.stop_event.clear()
        self.worker_thread = threading.Thread(
            target=self.camera_worker,
            args=(camera_index,),
            daemon=True
        )
        self.worker_thread.start()

    def stop(self) -> None:
        """Signal the background thread to exit and join it safely."""
        if self.state in (self.STATE_IDLE, self.STATE_STOPPED):
            return

        self.set_state(self.STATE_STOPPING)
        self.stop_event.set()

        # Interrupt camera read by releasing VideoCapture
        if self.cap is not None:
            self.cap.release()

        # Join thread with a short timeout to prevent Tkinter freezing
        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)

        self.cap = None
        self.worker_thread = None
        self.is_capturing = False
        self.set_state(self.STATE_STOPPED)

    def start_capture(self, folder_path: str) -> None:
        """Configure folder path and start face capture sequence."""
        self.save_folder = folder_path
        self.capture_count = 0
        self.last_capture_time = 0.0
        self.is_capturing = True

    def stop_capture(self) -> None:
        """Abort current capture sequence."""
        self.is_capturing = False

    def camera_worker(self, camera_index: int) -> None:
        """Background thread target function."""
        if not self.load_detector():
            self.set_state(self.STATE_ERROR)
            self.queue.put(("error", "Cascade Error", "Haar Cascade frontal face default file could not be loaded."))
            return

        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            if self.cap is not None:
                self.cap.release()
            self.cap = None
            self.set_state(self.STATE_ERROR)
            self.queue.put(("error", "Camera Error", f"Unable to open camera index {camera_index}."))
            return

        self.set_state(self.STATE_RUNNING)
        self.queue.put(("status", "Camera started."))

        try:
            while not self.stop_event.is_set():
                success, frame = self.cap.read()
                if not success:
                    if not self.stop_event.is_set():
                        self.set_state(self.STATE_ERROR)
                        self.queue.put(("error", "Camera Disconnected", "Loss of connection to camera device."))
                    break

                # Mirror frame for natural preview
                frame = cv2.flip(frame, 1)

                # Grayscale conversion for detector
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.3,
                    minNeighbors=5,
                    minSize=(80, 80)
                )

                face_ok = False
                face_coords = None

                if len(faces) == 0:
                    cv2.putText(frame, "No Face Detected", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                elif len(faces) > 1:
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, "Multiple Faces Detected", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                else:
                    x, y, w, h = faces[0]
                    # Quality Check: Tiny face rejection is covered by minSize=80 in detector,
                    # but let's double check coordinates
                    if w < 80 or h < 80:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                        cv2.putText(frame, "Face Too Small", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                    else:
                        # Quality Check: Sharpness / Blur rejection
                        face_crop = gray[y:y+h, x:x+w]
                        if face_crop is None or face_crop.size == 0:
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                            cv2.putText(frame, "Corrupted Crop", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                        else:
                            blur_val = cv2.Laplacian(face_crop, cv2.CV_64F).var()
                            if blur_val < 100.0:
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 165, 255), 2)
                                cv2.putText(frame, "Blurry Frame", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
                            else:
                                # Validation passes
                                face_ok = True
                                face_coords = (x, y, w, h)
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # Process capture if auto-capturing is enabled and pace criteria met
                if face_ok and self.is_capturing and self.capture_count < self.max_images:
                    curr_time = time.perf_counter()
                    if curr_time - self.last_capture_time >= 0.3:
                        self.last_capture_time = curr_time

                        x, y, w, h = face_coords
                        face_gray_crop = gray[y:y+h, x:x+w]

                        # Process cropped face: Resize and Equalize Hist
                        face_resized = cv2.resize(face_gray_crop, (200, 200), interpolation=cv2.INTER_AREA)
                        face_equalized = cv2.equalizeHist(face_resized)

                        # Verify final image bounds
                        if face_equalized is not None and face_equalized.size > 0 and face_equalized.shape == (200, 200):
                            self.capture_count += 1
                            filename = os.path.join(
                                self.save_folder,
                                f"{self.capture_count:03d}.jpg"
                            )

                            try:
                                cv2.imwrite(filename, face_equalized)
                                self.queue.put(("progress", self.capture_count))
                                
                                if self.capture_count >= self.max_images:
                                    self.is_capturing = False
                                    self.queue.put(("complete", self.save_folder))
                            except Exception as write_err:
                                self.is_capturing = False
                                self.queue.put(("error", "Disk Write Error", f"Failed to save image: {write_err}"))
                        else:
                            cv2.putText(frame, "Pipeline Processing Error", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Convert BGR frame to RGB for Tkinter compatibility before queueing
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Send frame data to UI safely using non-blocking put with oldest discard
                try:
                    if self.queue.full():
                        self.queue.get_nowait()
                    self.queue.put_nowait(("frame_data", frame_rgb, self.capture_count))
                except (queue.Full, queue.Empty):
                    pass
                time.sleep(0.01)
        except Exception as e:
            if not self.stop_event.is_set():
                self.set_state(self.STATE_ERROR)
                self.queue.put(("error", "Unexpected Camera Error", str(e)))
        finally:
            if self.cap is not None:
                self.cap.release()
                self.cap = None


class RegisterFaceFrame(ttk.Frame):

    def __init__(self, parent, app=None):

        super().__init__(parent)

        self.app = app

        # Threading and camera controller setup
        self.frame_queue = queue.Queue(maxsize=3)
        self.controller = CameraController(self.frame_queue)
        self.ui_after_id = None
        self.people_data = []  # Map selector index to (id, name, roll/employee_id)

        self.person_type = tk.StringVar(value="Student")
        self.person_name = tk.StringVar()
        self.capture_count = 0
        self.max_images = 50

        # UI status indicators
        self.camera_status_text = tk.StringVar(value="Camera: Stopped")
        self.remaining_images_text = tk.StringVar(value="Remaining: 50")

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

        # Camera Selector
        tk.Label(
            left,
            text="Select Camera",
            bg=BG_COLOR
        ).pack(anchor="w", padx=15, pady=(15,5))

        self.camera_index_var = tk.StringVar()
        self.camera_selector = ttk.Combobox(
            left,
            textvariable=self.camera_index_var,
            state="readonly",
            width=20
        )
        self.camera_selector.pack(padx=15)
        self.populate_camera_selector()

        # Camera Status Label
        self.camera_status_label = tk.Label(
            left,
            textvariable=self.camera_status_text,
            bg=BG_COLOR,
            font=("Arial", 10, "bold"),
            fg=HEADER_COLOR
        )
        self.camera_status_label.pack(pady=(10, 5))

        # Progress Label
        self.progress = tk.Label(
            left,
            text="Captured : 0 / 50",
            bg=BG_COLOR,
            font=("Arial", 11, "bold")
        )
        self.progress.pack(pady=(5, 2))

        # Remaining Images Label
        self.remaining_label = tk.Label(
            left,
            textvariable=self.remaining_images_text,
            bg=BG_COLOR,
            font=("Arial", 10),
            fg="gray"
        )
        self.remaining_label.pack(pady=(0, 5))

        # Progress Bar
        self.progress_bar = ttk.Progressbar(
            left,
            orient="horizontal",
            length=180,
            mode="determinate",
            maximum=50
        )
        self.progress_bar.pack(padx=15, pady=(0, 15))

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

        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()

            if self.person_type.get() == "Student":
                cur.execute("""
                    SELECT id, student_name, roll_no
                    FROM students
                    ORDER BY student_name
                """)
                self.people_data = cur.fetchall()
                names = [
                    f"ID: {row[0]} | {row[1]} (Roll: {row[2]})"
                    for row in self.people_data
                ]
            else:
                cur.execute("""
                    SELECT id, teacher_name, employee_id
                    FROM teachers
                    ORDER BY teacher_name
                """)
                self.people_data = cur.fetchall()
                names = [
                    f"ID: {row[0]} | {row[1]} (Emp ID: {row[2]})"
                    for row in self.people_data
                ]

            self.person_combo["values"] = names

            if names:
                self.person_combo.current(0)
            else:
                self.person_combo.set("")
                self.people_data = []

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                str(e)
            )
        finally:
            if conn is not None:
                conn.close()
    def populate_camera_selector(self) -> None:
        """Populate the camera selector with standard port indices, avoiding blocking main-thread scans."""
        available_cameras = ["0", "1", "2", "3"]
        self.camera_selector["values"] = available_cameras
        default_idx = str(CAMERA_INDEX)
        if default_idx in available_cameras:
            self.camera_selector.set(default_idx)
        else:
            self.camera_selector.set(available_cameras[0])
                # ==========================================
    # Start Camera
    # ==========================================

    def start_camera(self) -> None:
        """Start the CameraController and launch the queue polling loop."""
        if self.controller.state not in (self.controller.STATE_IDLE, self.controller.STATE_STOPPED, self.controller.STATE_ERROR):
            return

        try:
            cam_idx = int(self.camera_index_var.get())
        except (ValueError, TypeError):
            cam_idx = CAMERA_INDEX

        self.controller.start(cam_idx)
        
        # Start queue polling loop
        if self.ui_after_id is not None:
            try:
                self.after_cancel(self.ui_after_id)
            except tk.TclError:
                pass
        self.ui_after_id = self.after(30, self.process_queue)

    def stop_camera(self) -> None:
        """Stop the CameraController and clear the preview display."""
        self.controller.stop()
        self.camera_label.configure(image="")
        self.camera_label.image = None

    def process_queue(self) -> None:
        """Poll events from the CameraController's queue and update Tkinter UI."""
        try:
            while True:
                event = self.frame_queue.get_nowait()
                event_type = event[0]

                if event_type == "frame_data":
                    frame = event[1]
                    count = event[2]
                    
                    self.capture_count = count
                    self.progress.configure(text=f"Captured : {count} / 50")
                    self.remaining_images_text.set(f"Remaining: {50 - count}")
                    self.progress_bar["value"] = count

                    img = Image.fromarray(frame)
                    # Resize preview frame to fit layout
                    img = img.resize((700, 500))
                    photo = ImageTk.PhotoImage(image=img)
                    
                    self.camera_label.configure(image=photo)
                    self.camera_label.image = photo

                elif event_type == "progress":
                    count = event[1]
                    self.capture_count = count
                    self.progress.configure(text=f"Captured : {count} / 50")
                    self.remaining_images_text.set(f"Remaining: {50 - count}")
                    self.progress_bar["value"] = count

                elif event_type == "state":
                    state = event[1]
                    self.camera_status_text.set(f"Camera: {state}")

                elif event_type == "status":
                    status_msg = event[1]
                    print(f"[CameraController Status] {status_msg}")

                elif event_type == "error":
                    title, msg = event[1], event[2]
                    messagebox.showerror(title, msg)

                elif event_type == "complete":
                    save_path = event[1]
                    self.db_update_image_path(save_path)
                    messagebox.showinfo("Completed", "50 face images captured and saved successfully.")
                    if self.app and hasattr(self.app, "refresh_dashboard_metrics"):
                        self.app.refresh_dashboard_metrics()

        except queue.Empty:
            pass

        # Continuously schedule next poll if camera is not fully stopped
        if self.controller.state not in (self.controller.STATE_STOPPED, self.controller.STATE_ERROR):
            self.ui_after_id = self.after(30, self.process_queue)
        else:
            self.ui_after_id = None

    def capture_face(self) -> None:
        """Trigger non-blocking face image acquisition sequence for the selected student/teacher."""
        if self.controller.state != self.controller.STATE_RUNNING:
            messagebox.showwarning("Camera Stopped", "Please start the camera first.")
            return

        name_selection = self.person_combo.get()
        if not name_selection:
            messagebox.showwarning("No Selection", "Please select a student/teacher first.")
            return

        try:
            index = self.person_combo.current()
            person_id, person_name, _ = self.people_data[index]
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Invalid selection index.")
            return

        # Sanitize name for directory creation
        safe_name = "".join(c for c in person_name if c.isalnum() or c in (" ", "_", "-")).strip()
        safe_name = safe_name.replace(" ", "_")
        folder_name = f"{person_id}_{safe_name}"

        if self.person_type.get() == "Student":
            save_folder = os.path.join(STUDENT_FOLDER, folder_name)
        else:
            save_folder = os.path.join(TEACHER_FOLDER, folder_name)

        try:
            os.makedirs(save_folder, exist_ok=True)
        except Exception as e:
            messagebox.showerror("File Error", f"Unable to create folder:\n{e}")
            return

        # Initialize progress metrics and start capture
        self.capture_count = 0
        self.progress_bar["value"] = 0
        self.progress.configure(text="Captured : 0 / 50")
        self.remaining_images_text.set("Remaining: 50")
        
        self.controller.start_capture(save_folder)

    def db_update_image_path(self, folder: str) -> None:
        """Update database image path field for selected student/teacher."""
        index = self.person_combo.current()
        if index < 0 or index >= len(self.people_data):
            return
        person_id = self.people_data[index][0]

        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            if self.person_type.get() == "Student":
                cur.execute(
                    "UPDATE students SET image_path = ? WHERE id = ?",
                    (folder, person_id)
                )
            else:
                cur.execute(
                    "UPDATE teachers SET image_path = ? WHERE id = ?",
                    (folder, person_id)
                )
            conn.commit()
            print(f"[Database Sync] Updated image_path to {folder} for ID {person_id}.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update database record:\n{e}")
        finally:
            if conn is not None:
                conn.close()

    def destroy(self) -> None:
        """Cleanup pending timers, stop background threads, and destroy widgets."""
        if self.ui_after_id is not None:
            try:
                self.after_cancel(self.ui_after_id)
            except tk.TclError:
                pass
            self.ui_after_id = None

        self.stop_camera()
        super().destroy()
