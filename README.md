# AI School Surveillance System

AI-based School Surveillance and Attendance System built with Python, OpenCV (LBPH Recognizer), SQLite, Pillow, and Tkinter. Developed as a BCA Final Year Project and engineered for production-quality desktop deployment.

---

## Features

* **Student & Teacher Management**: CRUD database registers with SQLite.
* **Professional Face Registration**: Thread-safe embedded Tkinter camera preview with real-time Haar Cascade face detection, single-face validation, blur check (Laplacian variance), and automatic crop scaling ($200 \times 200$ grayscale histogram equalized).
* **Face Recognition Training**: Background training thread that validates image assets, eliminates duplicates via md5 hashing, and compiles the LBPH recognizer configuration.
* **Live Surveillance**: Video stream overlay tracking registered names and raising alert pop-ups for unregistered faces.
* **Attendance Automation**: Commits real-time class lists, logs, and dates to CSV reporting templates.

---

## Architecture Overview

The system runs on a decoupled multithreaded architecture. Intensive operations (OpenCV capture frames, database sync, disk I/O, image processing, model training) execute on background thread loops, leaving the Tkinter main UI thread fully responsive.

Detailed architectural drawings, schema definitions, and design workflows are available in the documentation:

* [Architecture Documentation](docs/architecture.md)
* [Database Schema Specs](docs/database.md)
* [Face Training Manual](docs/face_training.md)
* [QA & Test Cases](docs/testing.md)
* [Deployment Guide](docs/deployment.md)
* [Security Controls](docs/security.md)
* [Attendance Manual](docs/attendance.md)

---

## Folder Tree Layout

```
AI-School-Surveillance-System/
├── config.py             # System configurations
├── main.py               # Main Tkinter Navigation Shell
├── register_face.py      # Face Capture & Registration module
├── train_face.py         # LBPH Face Recognition Training module
├── surveillance.py       # Live stream Face Recognition dashboard
├── database/             # SQLite DB File Storage
├── dataset/              # Students & Teachers cropped images
├── models/               # trainer.yml & labels.json Output
├── logs/                 # training_log.txt & system logs
└── docs/                 # Documentation manuals
```

---

## Getting Started

Refer to the [Deployment & Installation Manual](docs/deployment.md) for quick-start commands, dependency details, and run configurations.
