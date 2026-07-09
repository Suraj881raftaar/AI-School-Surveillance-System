# Quality Assurance & Testing Plan

This document details the test suites and QA procedures for validating the system.

---

## Testing Checklists

### 1. Security & Authentication Login
- **Procedure**: Navigate to login frame. Enter empty fields, wrong combinations, and correct username (`admin`) / password (`1234`).
- **Expected Outcome**: Rejected fields show clear red warning labels. Correct logins transition cleanly to the Dashboard frame.

### 2. Dashboard Analytics & Charts
- **Procedure**: Open overview panel.
- **Expected Outcome**: Visualizes student counts, teacher counts, today's attendance logs, and alert logs. Check that `AttendanceChart` canvas draws weekly trends bars with proper labels.

### 3. Face Registration (Phase 2)
- **Procedure**: Start registrations, select ports, enter name/ID, start capture.
- **Expected Outcome**: Embedded camera canvas plays smoothly. Auto capture stops exactly at 100 face crops. No main thread lockups occur.

### 4. Dataset Empty State (Phase 3)
- **Procedure**: Rename `dataset/` directory. Start the application and navigate to the **Face Training** tab.
- **Expected Outcome**: Statistics display `0` students, `0` teachers, and `0` folders. Clicking "Start Training" immediate stops and shows a messagebox warning: "No valid dataset folders found." No crash occurs.

### 5. Validation Rejections (Phase 3)
- **Procedure**: Create a valid student directory under `dataset/students/1_Test_User/`. Add one valid image, one empty file, and one text file renamed to `.jpg`. Click "Start Training".
- **Expected Outcome**: Corrupt or invalid files are successfully ignored. The model trains successfully on valid images and writes `trainer.yml` and `labels.json` correctly.

### 6. Live Surveillance (Phase 4)
- **Procedure**: Start camera feeds. Put known and unknown faces in front of the lens.
- **Expected Outcome**: Recognized faces draw green boxes with correct name translation. Unknown subjects draw red boxes and save screenshots to `screenshots/` directory, adding records to tree logs.

### 7. Attendance Cooldown (Phase 5)
- **Procedure**: Set cooldown parameter to `60` seconds. Trigger recognition of the same user.
- **Expected Outcome**: Logs are written once. Subsequent attempts within 60 seconds are blocked and show warning status values.

### 8. Filters & Search (Phase 6)
- **Procedure**: Search reports by Keyword, Preset Date Presets ("Today", "Yesterday", "Last 7 Days"), and category types.
- **Expected Outcome**: Lists return correct matching records instantly.

### 9. Backup & Restore (Phase 6)
- **Procedure**: Run backups (selecting DB, Dataset, Models, and Logs). Restore files.
- **Expected Outcome**: Background zipping runs cleanly. Restoring replaces folders and databases successfully. Corrupted archives are blocked.

### 10. Settings Manager (Phase 7)
- **Procedure**: Open Settings. Update paths, camera ports, and matching thresholds.
- **Expected Outcome**: Inputs validate successfully. Hot-reloads apply dynamic updates instantly.
