# AI School Surveillance System

[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)

An AI-powered School Surveillance and Automated Attendance Management System built with Python, OpenCV (Haar Cascades & LBPH Face Recognizer), SQLite, Pillow, and Tkinter. Developed as a BCA Final Year Project and engineered for production-quality desktop deployment.

---

## 📸 Screenshots Section
*Dashboard, Live Surveillance Feed, Analytics Graphs, and Settings modules are captured below:*

```
┌────────────────────────────────────────────────────────┐
│ [Dashboard Overview Screen]                            │
│ 8-Cards: Total Students, Accuracy, Confidence, etc.     │
│ Chart: 7-Day Attendance Trend Canvas Graphic           │
└────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────┐
│ [Surveillance Live Monitoring Screen]                  │
│ Video Preview Canvas (Green Box: Recognised, Red: Alert)│
└────────────────────────────────────────────────────────┘
```
*(Screenshots can be added inside the `screenshots/` directory for GitHub asset hosting.)*

---

## 🚀 Key Features

* **Student & Teacher Management**: Relational CRUD operations backed by SQLite database records.
* **Professional Face Registration**: Thread-safe embedded Tkinter camera preview with Haar Cascade face detection, single-face focus verification, Laplacian blur checks, and crop normalizations ($200 \times 200$ grayscale histogram equalized).
* **Face Recognition Training**: Background training threads that prune invalid files and serialize the LBPH config.
* **Intelligent Attendance**: Real-time roll-call logs mapped dynamically via database joins, equipped with 60-second duplicate prevention cooldown filters.
* **Advanced Reports**: Left filters sidebar matching keywords, category types, presence states, and date presets. Supports exporting to CSV, styled Excel workbooks (`openpyxl`), and PDF summaries (`reportlab`).
* **Settings & Backup**: Configures matching thresholds, camera ports, and directory locations. Compresses databases, crops, models, and system logs to timestamped zip archives.

---

## 🛠️ System Architectures

The system uses a decoupled multithreaded architecture. Intensive operations (OpenCV capture frames, database sync, disk I/O, image processing, model training) execute on background thread loops, leaving the Tkinter main UI thread fully responsive.

### Documentation Manuals

Explore the detailed component manuals inside the `docs/` folder:

* 📚 [User Manual](docs/user_manual.md)
* ⚙️ [Administrator Manual](docs/admin_manual.md)
* 💻 [Developer Guide](docs/developer_guide.md)
* 📐 [Architecture Documentation](docs/architecture.md)
* 🗄️ [Database Schema Specs](docs/database.md)
* 🧪 [Testing & QA checklists](docs/testing.md)
* 📦 [Deployment & Packaging Guide](docs/deployment.md)
* 🔍 [Troubleshooting FAQ](docs/troubleshooting.md)
* 🏷️ [Changelog Releases](CHANGELOG.md)

---

## 🏗️ Folder Tree Layout

```
AI-School-Surveillance-System/
├── config.py             # System Configurations
├── main.py               # Main Navigation GUI Shell
├── settings_manager.py   # Settings Load/Save Observer Broker
├── register_face.py      # Camera Capturing & Registrations
├── train_face.py         # LBPH Face Recognizer Model Training
├── surveillance.py       # Live Recognition Dashboard
├── database/             # SQLite DB File Storage
├── dataset/              # Students & Teachers Crops
├── models/               # trainer.yml & labels.json Output
├── logs/                 # training_log.txt & system logs
└── docs/                 # Documentation Markdown Manuals
```

---

## ⚙️ Quick Start

### Installation
1. **Clone repository**:
   ```bash
   git clone https://github.com/YourRepo/AI-School-Surveillance-System.git
   cd AI-School-Surveillance-System
   ```
2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run Application**:
   ```bash
   python main.py
   ```

### PyInstaller Executable Compilation
To package the app into a standalone Windows binary, run:
```bash
pip install pyinstaller
pyinstaller build.spec
```
Locate the generated executable inside the `dist/` directory.

---

## ❓ FAQ & Troubleshooting

**Q: Black screen or camera occupied?**
* **A**: Go to the **Settings** panel, adjust the camera index dropdown, and check that no other software is using your webcam.

**Q: Database locked error?**
* **A**: Close and restart the application. Connections are automatically managed with connection-closing wrappers.

## 📅 Release History

See [CHANGELOG.md](CHANGELOG.md) for detailed version logs.
* **v1.0.1** (2026-07-09): Production Packaging & Runtime Stability Release.
* **v1.0.0** (2026-07-09): Initial Stable Production Release.

---

## 💳 Credits & License
* **Author**: AI School Surveillance Team
* **License**: Distributed under the [MIT License](LICENSE).
