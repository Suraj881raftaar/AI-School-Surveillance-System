# Attendance Management System

This document outlines the Phase 5 Intelligent Attendance Management system, including database configurations, background processes, thread safety, and reporting capabilities.

---

## 1. Attendance Workflow

1. **Detection & Prediction**: Live camera feeds track faces. LBPH recognises a face and matches it to a relational Student or Teacher record.
2. **Identity Verification**: Checks model confidence mapping against configurable thresholds (Green status).
3. **Duplicate Filter**: Compares registration attempt to cooldown caches (`60` seconds default) and calendar date filters.
4. **Asynchronous Commit**: Offloads database writes to isolated background worker threads.
5. **Real-Time Notification**: Updates GUI console status logs and metrics counters dynamically.

---

## 2. Duplicate Prevention

To avoid multiple logs of the same person during a class window:
* **Active Cooldown**: A memory-mapped lookup cache tracks the timestamp of last recorded identity. ডিফল্ট cooldown limits are set to `60` seconds. If repeated recognitions happen inside this window, writing is ignored and a warning status is set.
* **Daily Calendar Filter**: Before writing, a database validation check (`has_attendance_today`) queries if the target student/teacher was marked present today.

---

## 3. Database Schema

The SQLite schema is dynamically updated during initialization:

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary key (Autoincrement) |
| `person_id` | `INTEGER` | Base Student or Teacher relational ID |
| `person_name` | `TEXT` | Full name of verified individual |
| `person_type` | `TEXT` | `Student` or `Teacher` category |
| `date` | `TEXT` | Calendar date (YYYY-MM-DD) |
| `time` | `TEXT` | Log time (HH:MM:SS) |
| `confidence` | `REAL` | LBPH distance metric output |
| `camera_id` | `INTEGER` | Target hardware capture port index |
| `recognition_method` | `TEXT` | AI model type (e.g. `LBPH`) |
| `status` | `TEXT` | Presence state (e.g. `Present`) |

---

## 4. Report Exports

* **CSV Exporter**: Writes all columns (including technical relational keys) to standard comma-separated templates.
* **Excel Exporter**: Compiles reports using `openpyxl`, applying blue styling headers, custom row fonts, alignments, and auto-adjusting column widths.
