# Deployment & Installation Manual

## Prerequisites

* **Operating System**: Windows 10/11 (fully tested) or Linux/macOS.
* **Python Environment**: Python 3.8 through 3.11.

---

## Installation Steps

1. **Clone Repository**:
   ```bash
   git clone https://github.com/YourRepo/AI-School-Surveillance-System.git
   cd AI-School-Surveillance-System
   ```

2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows activation
   venv\Scripts\activate
   # Linux/macOS activation
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   Install OpenCV with contrib modules to ensure LBPH Recognizer is available:
   ```bash
   pip install opencv-contrib-python pillow openpyxl numpy
   ```

4. **Initialize Directory Tree**:
   Run the database migration initializer script or start the app (which automatically creates required directories):
   ```bash
   python main.py
   ```

---

## Folder Tree Layout

```
AI-School-Surveillance-System/
├── config.py             # System Configurations
├── main.py               # Main Navigation GUI
├── register_face.py      # Camera Capturing & Registrations
├── train_face.py         # LBPH Face Recognizer Model Training
├── surveillance.py       # Live Recognition Dashboard
├── database/             # SQLite DB File Storage
├── dataset/              # Students & Teachers Crops
│   ├── students/
│   └── teachers/
├── models/               # trainer.yml & labels.json Output
├── logs/                 # training_log.txt & system logs
└── docs/                 # Documentation Markdown Manuals
```
