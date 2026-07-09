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
   Install OpenCV with contrib modules to ensure LBPH Recognizer, ReportLab, and OpenPyXL are available:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize System**:
   Start the app to auto-create directory trees, schemas, and configurations:
   ```bash
   python main.py
   ```

---

## PyInstaller Packaging Steps

To bundle the application into a standalone Windows executable (`.exe`):

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Run PyInstaller with the spec file**:
   ```bash
   pyinstaller build.spec
   ```

3. **Locate Executable**:
   The standalone executable will be generated inside the `dist/` directory.

4. **Resource Assets**:
   The `build.spec` automatically bundles the Haar Cascade XML files, icons, and PNG assets inside the binary.
