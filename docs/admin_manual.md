# Administrator Manual

This manual details the system configurations, settings adjustments, backup operations, and database maintenance protocols.

---

## 1. System Configurations
Click **Settings** in the sidebar to configure the system:
* **Dataset Base Path**: Target folder for raw cropped training images.
* **Trained Model Path**: Folder location where `trainer.yml` and `labels.json` are serialized.
* **Reports Export Path**: Export folder location for CSV, Excel, and PDF reports.
* **Attendance Cooldown**: Seconds threshold (default 60s) preventing duplicate logging entries.
* **Active Camera Index**: Selected index (0 to 3) for camera captures.
* **LBPH Matching Threshold**: Confidence threshold limit (30.0 to 120.0) for face recognition matches.

---

## 2. Backup Management
To build system archives:
1. Navigate to the **Settings** panel, and select **Backup & Restore Manager** tab.
2. Select the elements to back up (Database file, Face dataset, Trained models, and System logs).
3. Click **Create Backup Archive (.zip)**.
4. Select the destination directory. The manager runs in the background and saves a zip archive.

---

## 3. Restore Procedures
To restore surveillance assets:
1. Navigate to **Backup & Restore Manager** tab in settings.
2. Click **Select & Restore Backup Archive**.
3. Choose the target zip archive.
4. The system validates the zip layout before replacing files, ensuring directory integrity.
