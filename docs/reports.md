# Reports & Exporters Documentation

This document describes the search, filters, SQL Joins, and multi-format exporters of the Reporting Module.

---

## 1. Advanced Filters

The Reporting Panel provides left-side controls to filter dataset exports:
* **Keyword Search**: Matches names or identity codes (Student Roll Number / Teacher Employee ID).
* **Date Combobox**: Selects "All", "Today", "Yesterday", "Last 7 Days", "Last 30 Days", or "Custom Range".
* **Category**: Filters students vs teachers.
* **Status**: Filters Presence states.

---

## 2. Relational SQL Queries

To search and retrieve identity codes, a `LEFT JOIN` is executed between `attendance`, `students`, and `teachers` tables:
```sql
SELECT 
    a.id, a.person_name, a.person_type, 
    COALESCE(s.roll_no, t.employee_id, 'N/A') AS identity_code,
    a.date, a.time, a.confidence, a.camera_id, a.recognition_method, a.status
FROM attendance a
LEFT JOIN students s ON a.person_type = 'Student' AND a.person_id = s.id
LEFT JOIN teachers t ON a.person_type = 'Teacher' AND a.person_id = t.id
ORDER BY a.id DESC;
```

---

## 3. Multi-Format Exporters

### CSV Export
Writes standard comma-delimited templates containing raw relational database tables.

### Excel Export (.xlsx)
Generates structured workbooks with styled layouts using `openpyxl`:
* Colors header cells blue (`#0B3D91`).
* Centers column alignments and sets Segoe UI typography.
* Auto-adjusts column cell margins to fit text length.
* Runs in background daemon thread to avoid blocking the main UI loop.

### PDF Export (.pdf)
Builds formatted reports using `reportlab`:
* Appends document headings, generator metadata, and timestamp tags.
* Adds a school surveillance logo placeholder.
* Restores attendance and alert logs into color-coded table cells.
* Runs in background thread to avoid freezing Tkinter forms.
