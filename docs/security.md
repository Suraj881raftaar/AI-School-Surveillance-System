# Security Guidelines & Controls

This document details the security principles and controls implemented in the system.

---

## Security Practices

### 1. Path Traversal Prevention
To prevent path traversal vulnerability (e.g. escaping the dataset directory structure), all paths processed by the preprocessor loop are validated:
```python
abs_img_path = os.path.abspath(img_path)
abs_dataset_folder = os.path.abspath(DATASET_FOLDER)
if not abs_img_path.startswith(abs_dataset_folder):
    # Reject operation...
```

### 2. Parameterized SQL Statements
All communication with SQLite avoids string formatting to block SQL injection:
```python
cur.execute("SELECT COUNT(*) FROM students")
cur.execute("UPDATE students SET image_path = ? WHERE id = ?", (folder, person_id))
```

### 3. Folder Name Sanitization
To prevent shell command injection or file system corruption, all folder paths are sanitized when creating directories:
```python
# Keep only alphanumeric characters, spaces, dashes, or underscores
safe_name = "".join(c for c in person_name if c.isalnum() or c in (" ", "_", "-")).strip()
safe_name = safe_name.replace(" ", "_")
folder_name = f"{person_id}_{safe_name}"
```

### 4. Concurrency Integrity
All database transactions are executed strictly inside the Tkinter main thread, eliminating thread-sharing race conditions or database locks.
Background tasks write to temporary model configuration buffers before replacing files, ensuring atomic disk writes.
