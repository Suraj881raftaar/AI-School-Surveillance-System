# Backup & Restore Manager Documentation

This manual documents the Backup Manager architecture, archive layout formats, verification tests, and safety procedures.

---

## 1. Archive Structure

The Backup Manager builds standard zip archives with the following naming format:
`backup_YYYYMMDD_HHMMSS.zip`

The zip file contains selected system folders located relative to the application base folder:
* **Database**: `school.db` (commits, profiles, alerts, settings).
* **Dataset**: `dataset/` (students and teachers crop folders).
* **Models**: `models/` (trained `trainer.yml` and `labels.json`).
* **Logs**: `logs/` (training, system, and attendance txt logs).

---

## 2. Asynchronous Operations

To prevent freezing the Tkinter main thread during large image datasets compression:
1. File operations execute on a background daemon worker thread.
2. Progress states are logged to console status bars.
3. System blocks remain responsive allowing users to switch screens during active backups.

---

## 3. Restoration Safety

To prevent corrupting the application during restores:
* **Pre-Verification**: The restore task verifies that the target archive is a valid surveillance backup containing the core database (`school.db`) and structure directories before replacing files.
* **Confirmation Dialogs**: Explicit warning notifications prompt the user before any existing directories are overwritten.
* **Connection Re-init**: Restored databases are instantly bound to active repository drivers.
