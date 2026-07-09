# User Manual

This manual provides guides for school staff and operators using the AI School Surveillance system.

---

## 1. Login Authentication
1. Launch the application.
2. Enter the operator credentials (default is Username: `admin`, Password: `1234`).
3. Click "Login".

---

## 2. Dynamic Dashboard
* **Metrics Cards**: View registered profiles and daily aggregates.
* **Recents Tables**: Shows scrollable logs of recent attendance events and security alerts.
* **Canvas Chart**: Visualizes attendance trend lines natively.

---

## 3. Registering New Profiles
1. Click **Register Face** in the sidebar.
2. Select the category type (Student vs Teacher).
3. Fill out profile details (Name, ID/Roll Number, Stream/Subject, Class, Mobile, Gender).
4. Select the active camera port.
5. Click **Start Registration** to view the live preview canvas.
6. Click **Capture Faces** to start auto crop collection. The system will snap 100 face images and automatically release camera resources.

---

## 4. Live Surveillance & Monitoring
1. Click **Surveillance** in the sidebar.
2. Select the camera port.
3. Click **Start Surveillance Stream** to open live video streams.
4. **Recognized users**: Frame box lights up Green and automatically logs attendance.
5. **Unknown visitors**: Frame box lights up Red, snaps a screenshot to `screenshots/` directory, and raises a security alert.
6. Click **Stop Stream** to turn off camera feeds gracefully.

---

## 5. View & Export Reports
1. Click **Reports** in the sidebar.
2. Use the left-side filters panel to search by keyword, filter categories, select presence states, or input custom date ranges.
3. Use the top toolbar to export results to **CSV**, styled **Excel (.xlsx)** workbooks, or print **PDF** summaries.
