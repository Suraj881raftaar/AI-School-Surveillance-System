# Configurations & Settings Documentation

This document describes the database configurations mechanism, settings storage, and startup injection hooks.

---

## 1. Relational Settings Storage

System configurations are saved to a dedicated database table `system_settings` inside `school.db`:
```sql
CREATE TABLE IF NOT EXISTS system_settings(
    key TEXT PRIMARY KEY,
    value TEXT
);
```

This ensures settings remain persistent across application restarts without relying on additional file modifications.

---

## 2. Startup Settings Injection

To dynamically inject persistent settings on application startup without modifying legacy code:
1. `MainApplication.inject_settings()` is run inside `__init__` in `main.py` before loading frames.
2. The method queries settings from the database and injects them directly into the `config` module properties.
3. Legacy modules (like `register_face.py` and `surveillance.py`) automatically import and use these active variables when launched.

---

## 3. Configurable Settings Reference

* **Dataset Base Path**: Target folder for raw cropped training images.
* **Trained Model Path**: Folder location where `trainer.yml` and `labels.json` are serialized.
* **Reports Export Path**: Export folder location for CSV, Excel, and PDF reports.
* **Attendance Cooldown**: Seconds threshold (default 60s) preventing duplicate logging entries.
* **Active Camera Index**: Selected index (0 to 3) for camera captures.
* **LBPH Matching Threshold**: Confidence threshold limit (30.0 to 120.0) for face recognition matches.
