"""
train_face.py
AI School Surveillance System
Phase 3: Face Recognition Training
"""

import os
import sys
import time
import json
import queue
import hashlib
import threading
import subprocess
import sqlite3
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from config import *


class TrainingWorker(threading.Thread):
    """Background worker thread to perform face training without blocking Tkinter UI."""

    def __init__(self, event_queue: queue.Queue, stop_event: threading.Event) -> None:
        super().__init__(daemon=True)
        self.queue = event_queue
        self.stop_event = stop_event
        self.log_file_path = os.path.join(LOG_FOLDER, "training_log.txt")
        self.face_detector = cv2.CascadeClassifier(HAARCASCADE_PATH)

    def log(self, message: str, level: str = "INFO") -> None:
        """Helper to write timestamped log record to file and append to GUI log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}"
        try:
            os.makedirs(LOG_FOLDER, exist_ok=True)
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception:
            pass
        self.queue.put(("log", log_line))

    def run(self) -> None:
        self.log("Face Recognition Training Thread started.")
        start_time = time.perf_counter()

        # Pre-checks
        if self.face_detector.empty():
            self.log("Haar Cascade file empty or missing. Face detection verification is disabled.", "WARNING")

        if not hasattr(cv2, "face"):
            self.log("OpenCV 'face' module is missing. Make sure you installed 'opencv-contrib-python'.", "ERROR")
            self.queue.put(("error", "Dependency Error", "OpenCV 'cv2.face' module is missing.\n\nPlease install using: pip install opencv-contrib-python"))
            return

        # 1. Dataset Scan and Discovery
        self.log("Scanning dataset folders...")
        self.queue.put(("status", "Scanning dataset folders..."))

        students_path = Path(STUDENT_FOLDER)
        teachers_path = Path(TEACHER_FOLDER)

        people_dirs = []

        def collect_dirs(base_path: Path, person_type: str):
            if not base_path.exists():
                return
            for item in base_path.iterdir():
                if item.is_dir():
                    # Validate folder format <ID>_<Name>
                    parts = item.name.split("_", 1)
                    if len(parts) >= 2 and parts[0].isdigit():
                        people_dirs.append({
                            "path": item,
                            "person_type": person_type,
                            "id": int(parts[0]),
                            "name": parts[1]
                        })
                    else:
                        self.log(f"Skipped invalid folder name pattern: {item.name}", "WARNING")

        try:
            collect_dirs(students_path, "Student")
            collect_dirs(teachers_path, "Teacher")
        except Exception as ex:
            self.log(f"Error scanning directories: {ex}", "ERROR")
            self.queue.put(("error", "Directory Read Error", f"Failed to scan datasets:\n{ex}"))
            return

        total_people = len(people_dirs)
        self.log(f"Found {total_people} directories.")
        if total_people == 0:
            self.log("No valid student or teacher folders found in the dataset.", "ERROR")
            self.queue.put(("error", "No Dataset", "No valid dataset folders found.\n\nPlease register faces first."))
            return

        # Collect images and absolute paths
        all_image_paths = []
        for p in people_dirs:
            folder_path = p["path"]
            try:
                for entry in os.scandir(folder_path):
                    if entry.is_file():
                        # Validate format extension
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in (".jpg", ".jpeg", ".png", ".bmp"):
                            all_image_paths.append((entry.path, entry.name, p))
                        else:
                            self.log(f"Skipping unsupported file extension: {entry.path}", "WARNING")
            except Exception as ex:
                self.log(f"Skipping folder {folder_path} due to read error: {ex}", "ERROR")

        total_images = len(all_image_paths)
        self.log(f"Discovered {total_images} total image files.")
        if total_images == 0:
            self.log("No valid images found in the dataset folders.", "ERROR")
            self.queue.put(("error", "Empty Dataset", "Dataset folders contain no valid image files."))
            return

        self.queue.put(("total_images", total_images))

        # 2. Image Loading and Preprocessing
        faces_data = []
        labels_data = []
        labels_metadata = {}

        processed_count = 0
        skipped_count = 0
        image_pacing_start = time.perf_counter()

        for img_path, img_name, person_info in all_image_paths:
            if self.stop_event.is_set():
                self.log("Training canceled by user.")
                self.queue.put(("status", "Training canceled."))
                return

            person_type = person_info["person_type"]
            person_id = person_info["id"]
            person_name = person_info["name"]
            folder_path = person_info["path"]

            # Generate label: Student = 1000+ID, Teacher = 2000+ID
            label_id = (1000 + person_id) if person_type == "Student" else (2000 + person_id)

            try:
                # Security: Path traversal validation
                abs_img_path = os.path.abspath(img_path)
                abs_dataset_folder = os.path.abspath(DATASET_FOLDER)
                if not abs_img_path.startswith(abs_dataset_folder):
                    self.log(f"Security Traversal attempt blocked: {img_path}", "ERROR")
                    skipped_count += 1
                    processed_count += 1
                    continue

                # Read image
                img = cv2.imread(abs_img_path, cv2.IMREAD_GRAYSCALE)
                if img is None or img.size == 0:
                    self.log(f"Skipped corrupted/empty image: {img_path}", "WARNING")
                    skipped_count += 1
                    processed_count += 1
                    continue

                # Reject wrong dimensions
                if img.shape != (FACE_WIDTH, FACE_HEIGHT):
                    self.log(f"Skipped image with wrong dimensions {img.shape}: {img_path}", "WARNING")
                    skipped_count += 1
                    processed_count += 1
                    continue

                # Reject blurry images
                blur_val = cv2.Laplacian(img, cv2.CV_64F).var()
                if blur_val < 100.0:
                    self.log(f"Skipped blurry face (Laplacian var {blur_val:.1f} < 100.0): {img_path}", "WARNING")
                    skipped_count += 1
                    processed_count += 1
                    continue

                # Reject no face detection
                if not self.face_detector.empty():
                    faces = self.face_detector.detectMultiScale(img, scaleFactor=1.1, minNeighbors=2)
                    if len(faces) == 0:
                        self.log(f"Skipped image - no face detected: {img_path}", "WARNING")
                        skipped_count += 1
                        processed_count += 1
                        continue

                # Reject duplicate images (hash comparison)
                person_key = f"{person_type}_{person_id}"
                if person_key not in labels_metadata:
                    labels_metadata[person_key] = {
                        "id": person_id,
                        "name": person_name,
                        "person_type": person_type,
                        "dataset_folder": os.path.relpath(folder_path, BASE_DIR),
                        "image_count": 0,
                        "timestamp": datetime.now().isoformat(),
                        "version": "1.0",
                        "seen_hashes": set()
                    }

                img_hash = hashlib.md5(img.tobytes()).hexdigest()
                if img_hash in labels_metadata[person_key]["seen_hashes"]:
                    self.log(f"Skipped duplicate image: {img_path}", "WARNING")
                    skipped_count += 1
                    processed_count += 1
                    continue

                # Store image
                labels_metadata[person_key]["seen_hashes"].add(img_hash)
                labels_metadata[person_key]["image_count"] += 1

                faces_data.append(img)
                labels_data.append(label_id)

            except Exception as ex:
                self.log(f"Failed to process image {img_path}: {ex}", "ERROR")
                skipped_count += 1

            processed_count += 1

            # Performance & metric outputs
            elapsed_time = time.perf_counter() - image_pacing_start
            speed = processed_count / elapsed_time if elapsed_time > 0 else 0
            remaining = total_images - processed_count
            est_remaining = remaining / speed if speed > 0 else 0

            self.queue.put((
                "progress",
                img_name,
                person_name,
                os.path.basename(folder_path),
                processed_count,
                total_images,
                elapsed_time,
                est_remaining,
                speed
            ))

        valid_samples = len(faces_data)
        self.log(f"Completed image loading. Valid samples: {valid_samples}, Skipped: {skipped_count}.")

        if valid_samples == 0:
            self.log("No valid images remained after quality checks.", "ERROR")
            self.queue.put(("error", "Validation Error", "All images were rejected due to dimensions, blur, duplicates, or missing faces."))
            return

        # 3. Model Training
        self.log("Training LBPH Model...")
        self.queue.put(("status", "Training model... Please wait."))

        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(faces_data, np.array(labels_data))
        except Exception as ex:
            self.log(f"LBPH Training failed: {ex}", "ERROR")
            self.queue.put(("error", "Training Engine Error", f"Failed to train LBPH model:\n{ex}"))
            return

        # 4. Serialize Model configuration
        self.log("Saving trainer.yml and labels.json files...")
        model_path = os.path.join(MODEL_FOLDER, "trainer.yml")
        labels_path = os.path.join(MODEL_FOLDER, "labels.json")

        try:
            os.makedirs(MODEL_FOLDER, exist_ok=True)
            
            # Save trainer.yml
            recognizer.write(model_path)
            self.log(f"Model saved successfully to {model_path}")

            # Format json output metadata
            json_labels = {}
            for k, meta in labels_metadata.items():
                clean_meta = meta.copy()
                clean_meta.pop("seen_hashes", None)  # remove set object
                person_id = clean_meta["id"]
                person_type = clean_meta["person_type"]
                label_id = (1000 + person_id) if person_type == "Student" else (2000 + person_id)
                json_labels[str(label_id)] = clean_meta

            # Save labels.json
            with open(labels_path, "w", encoding="utf-8") as json_f:
                json.dump(json_labels, json_f, indent=4)
            self.log(f"Labels mapping metadata saved to {labels_path}")

        except Exception as ex:
            self.log(f"Failed to write model files: {ex}", "ERROR")
            self.queue.put(("error", "File Write Error", f"Failed to save trainer.yml or labels.json:\n{ex}"))
            return

        total_duration = time.perf_counter() - start_time
        summary = {
            "duration": total_duration,
            "total_images": total_images,
            "valid_samples": valid_samples,
            "skipped": skipped_count,
            "people_count": len(labels_metadata)
        }

        self.log(f"Training completed successfully in {total_duration:.2f} seconds.")
        self.log(f"Final Statistics: People trained: {summary['people_count']}, Valid Images: {summary['valid_samples']}, Skipped: {summary['skipped']}.")

        self.queue.put(("complete", summary))


class FaceTrainingFrame(ttk.Frame):
    """Face Recognition Training tab interface."""

    def __init__(self, parent, app=None) -> None:
        super().__init__(parent)
        self.app = app
        self.frame_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.ui_after_id = None

        self.configure(style="Training.TFrame")
        self.configure_styles()
        self.create_widgets()
        self.load_dataset_stats()

    def configure_styles(self) -> None:
        style = ttk.Style()
        style.configure("Training.TFrame", background=BG_COLOR)
        style.configure("TrainingPanel.TFrame", background=BG_COLOR)
        style.configure(
            "TrainingTitle.TLabel",
            background=BG_COLOR,
            foreground=HEADER_COLOR,
            font=("Arial", 18, "bold")
        )

    def create_widgets(self) -> None:
        # Title
        title_frame = tk.Frame(self, bg=BG_COLOR)
        title_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        ttk.Label(
            title_frame,
            text="Face Recognition Model Training",
            style="TrainingTitle.TLabel"
        ).pack(side="left")

        # Main Layout container
        main = tk.Frame(self, bg=BG_COLOR)
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # ---------------- Left panel (Metrics & Controls) ----------------
        left = ttk.LabelFrame(main, text="Controls & Status")
        left.pack(side="left", fill="both", padx=(0, 10), pady=5, ipadx=10)

        # Dataset metrics
        metrics_frame = tk.LabelFrame(left, text="Dataset Statistics", bg=WHITE, fg=HEADER_COLOR, font=("Arial", 10, "bold"))
        metrics_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(metrics_frame, text="Registered Students:", bg=WHITE).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.students_val_label = tk.Label(metrics_frame, text="0", bg=WHITE, font=("Arial", 11, "bold"), fg=BUTTON_COLOR)
        self.students_val_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        tk.Label(metrics_frame, text="Registered Teachers:", bg=WHITE).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.teachers_val_label = tk.Label(metrics_frame, text="0", bg=WHITE, font=("Arial", 11, "bold"), fg=BUTTON_COLOR)
        self.teachers_val_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        tk.Label(metrics_frame, text="Dataset Folders:", bg=WHITE).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.folders_val_label = tk.Label(metrics_frame, text="0 folders", bg=WHITE, font=("Arial", 11, "bold"), fg=BUTTON_COLOR)
        self.folders_val_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Control buttons
        btn_frame = tk.Frame(left, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=15, pady=10)

        self.start_btn = tk.Button(
            btn_frame,
            text="Start Training",
            font=("Arial", 11, "bold"),
            bg=SUCCESS_COLOR,
            fg="white",
            width=20,
            command=self.start_training
        )
        self.start_btn.pack(pady=5)

        self.cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 11, "bold"),
            bg=DANGER_COLOR,
            fg="white",
            width=20,
            state="disabled",
            command=self.cancel_training
        )
        self.cancel_btn.pack(pady=5)

        self.refresh_btn = tk.Button(
            btn_frame,
            text="Refresh Stats",
            font=("Arial", 11),
            bg="white",
            width=20,
            command=self.load_dataset_stats
        )
        self.refresh_btn.pack(pady=5)

        self.open_dataset_btn = tk.Button(
            btn_frame,
            text="Open Dataset Directory",
            font=("Arial", 11),
            bg="white",
            width=20,
            command=self.open_dataset_folder
        )
        self.open_dataset_btn.pack(pady=5)

        self.open_models_btn = tk.Button(
            btn_frame,
            text="Open Models Directory",
            font=("Arial", 11),
            bg="white",
            width=20,
            command=self.open_models_folder
        )
        self.open_models_btn.pack(pady=5)

        # ---------------- Right panel (Progress & Console Log) ----------------
        right = ttk.LabelFrame(main, text="Progress Output")
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Progress tracking fields
        details_frame = tk.Frame(right, bg=BG_COLOR)
        details_frame.pack(fill="x", padx=15, pady=10)

        self.status_lbl = tk.Label(details_frame, text="Status: IDLE", font=("Arial", 12, "bold"), bg=BG_COLOR, fg=HEADER_COLOR)
        self.status_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(details_frame, text="Current Folder:", bg=BG_COLOR).grid(row=1, column=0, sticky="w", pady=2)
        self.current_folder_lbl = tk.Label(details_frame, text="-", bg=BG_COLOR, font=("Arial", 10, "bold"))
        self.current_folder_lbl.grid(row=1, column=1, sticky="w", padx=10, pady=2)

        tk.Label(details_frame, text="Current File:", bg=BG_COLOR).grid(row=2, column=0, sticky="w", pady=2)
        self.current_file_lbl = tk.Label(details_frame, text="-", bg=BG_COLOR, font=("Arial", 10, "bold"))
        self.current_file_lbl.grid(row=2, column=1, sticky="w", padx=10, pady=2)

        tk.Label(details_frame, text="Processed:", bg=BG_COLOR).grid(row=3, column=0, sticky="w", pady=2)
        self.processed_lbl = tk.Label(details_frame, text="0 / 0", bg=BG_COLOR, font=("Arial", 10, "bold"))
        self.processed_lbl.grid(row=3, column=1, sticky="w", padx=10, pady=2)

        tk.Label(details_frame, text="Elapsed Time:", bg=BG_COLOR).grid(row=4, column=0, sticky="w", pady=2)
        self.elapsed_lbl = tk.Label(details_frame, text="00:00", bg=BG_COLOR, font=("Arial", 10, "bold"))
        self.elapsed_lbl.grid(row=4, column=1, sticky="w", padx=10, pady=2)

        tk.Label(details_frame, text="Time Remaining:", bg=BG_COLOR).grid(row=5, column=0, sticky="w", pady=2)
        self.remaining_lbl = tk.Label(details_frame, text="Calculating...", bg=BG_COLOR, font=("Arial", 10, "bold"))
        self.remaining_lbl.grid(row=5, column=1, sticky="w", padx=10, pady=2)

        tk.Label(details_frame, text="Speed:", bg=BG_COLOR).grid(row=6, column=0, sticky="w", pady=2)
        self.speed_lbl = tk.Label(details_frame, text="0.0 img/sec", bg=BG_COLOR, font=("Arial", 10, "bold"))
        self.speed_lbl.grid(row=6, column=1, sticky="w", padx=10, pady=2)

        self.progress_bar = ttk.Progressbar(right, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", padx=15, pady=(5, 10))

        # Console Logs box
        log_title = tk.Label(right, text="Training Activity Log:", bg=BG_COLOR, font=("Arial", 10, "bold"))
        log_title.pack(anchor="w", padx=15, pady=(5, 0))

        self.log_text = scrolledtext.ScrolledText(right, height=12, bg="black", fg="#00FF00", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(2, 15))
        self.log_text.configure(state="disabled")

    def load_dataset_stats(self) -> None:
        """Fetch rows and folders to count dataset files."""
        students_count = 0
        teachers_count = 0
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM students")
            students_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM teachers")
            teachers_count = cur.fetchone()[0]
            conn.close()
        except Exception:
            pass

        student_dirs = 0
        teacher_dirs = 0
        if os.path.exists(STUDENT_FOLDER):
            student_dirs = len([d for d in os.listdir(STUDENT_FOLDER) if os.path.isdir(os.path.join(STUDENT_FOLDER, d))])
        if os.path.exists(TEACHER_FOLDER):
            teacher_dirs = len([d for d in os.listdir(TEACHER_FOLDER) if os.path.isdir(os.path.join(TEACHER_FOLDER, d))])

        self.students_val_label.configure(text=str(students_count))
        self.teachers_val_label.configure(text=str(teachers_count))
        self.folders_val_label.configure(text=f"{student_dirs + teacher_dirs} folders")

    def start_training(self) -> None:
        """Trigger background face training thread and initialize UI locks."""
        # Disable controls, enable cancel button
        self.start_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        self.open_dataset_btn.configure(state="disabled")
        self.open_models_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")

        self.status_lbl.configure(text="Status: STARTING")
        self.progress_bar["value"] = 0

        # Clear text box logs
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

        # Spawn worker
        self.stop_event.clear()
        self.worker_thread = TrainingWorker(self.frame_queue, self.stop_event)
        self.worker_thread.start()

        # Start UI event polling loop
        self.ui_after_id = self.after(50, self.poll_queue)

    def cancel_training(self) -> None:
        """Send cancel flag to background thread."""
        self.stop_event.set()
        self.cancel_btn.configure(state="disabled")
        self.status_lbl.configure(text="Status: CANCELING")

    def open_dataset_folder(self) -> None:
        """Explore dataset directory in system GUI."""
        if not os.path.exists(DATASET_FOLDER):
            messagebox.showwarning("Missing Folder", "Dataset directory does not exist yet.")
            return
        try:
            os.startfile(DATASET_FOLDER)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory:\n{e}")

    def open_models_folder(self) -> None:
        """Explore models directory in system GUI."""
        if not os.path.exists(MODEL_FOLDER):
            messagebox.showwarning("Missing Folder", "Models directory does not exist yet.")
            return
        try:
            os.startfile(MODEL_FOLDER)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory:\n{e}")

    def format_time(self, seconds: float) -> str:
        """Format elapsed seconds as MM:SS string."""
        if seconds is None or seconds < 0:
            return "--:--"
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"

    def poll_queue(self) -> None:
        """Pull and apply background updates from training queue."""
        try:
            while True:
                event = self.frame_queue.get_nowait()
                event_type = event[0]

                if event_type == "status":
                    self.status_lbl.configure(text=f"Status: {event[1]}")

                elif event_type == "log":
                    log_line = event[1]
                    self.log_text.configure(state="normal")
                    self.log_text.insert(tk.END, log_line + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.configure(state="disabled")

                elif event_type == "total_images":
                    total = event[1]
                    self.progress_bar.configure(maximum=total, mode="determinate")

                elif event_type == "progress":
                    img_name, name, folder, current, total, elapsed, remaining, speed = event[1:]
                    
                    self.current_folder_lbl.configure(text=folder)
                    self.current_file_lbl.configure(text=f"{name} / {img_name}")
                    self.processed_lbl.configure(text=f"{current} / {total}")
                    self.elapsed_lbl.configure(text=self.format_time(elapsed))
                    self.remaining_lbl.configure(text=self.format_time(remaining))
                    self.speed_lbl.configure(text=f"{speed:.1f} img/sec")
                    
                    self.progress_bar["value"] = current

                elif event_type == "error":
                    title, msg = event[1], event[2]
                    self.status_lbl.configure(text="Status: ERROR")
                    messagebox.showerror(title, msg)
                    self.reset_controls()
                    return

                elif event_type == "complete":
                    stats = event[1]
                    self.status_lbl.configure(text="Status: COMPLETED")
                    
                    msg = (
                        f"Model training finished successfully.\n\n"
                        f"Trained People: {stats['people_count']}\n"
                        f"Valid Images: {stats['valid_samples']}\n"
                        f"Skipped Images: {stats['skipped']}\n"
                        f"Total Duration: {stats['duration']:.2f} seconds."
                    )
                    messagebox.showinfo("Completed", msg)
                    self.reset_controls()
                    return

        except queue.Empty:
            pass

        # Reschedule queue polling
        if self.worker_thread and self.worker_thread.is_alive():
            self.ui_after_id = self.after(50, self.poll_queue)
        else:
            self.reset_controls()

    def reset_controls(self) -> None:
        """Unlock control interface on thread termination."""
        self.start_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")
        self.open_dataset_btn.configure(state="normal")
        self.open_models_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        
        self.ui_after_id = None
        self.worker_thread = None
        self.load_dataset_stats()

    def destroy(self) -> None:
        """Cleanup thread handlers and cancels active timers on tab destroy."""
        if self.ui_after_id is not None:
            try:
                self.after_cancel(self.ui_after_id)
            except tk.TclError:
                pass
            self.ui_after_id = None

        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_event.set()
            self.worker_thread.join(timeout=1.0)

        super().destroy()
