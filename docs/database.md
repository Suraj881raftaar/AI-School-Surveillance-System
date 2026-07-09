# Database Documentation

## Database Configuration

The application uses **SQLite** as its relational database engine, saved to a single file at `database/school.db`. 

---

## Schema Reference

### 1. `students` Table
Stores student profiles and registration paths.
```sql
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    roll_no TEXT NOT NULL UNIQUE,
    stream TEXT,
    class TEXT,
    mobile TEXT,
    gender TEXT,
    image_path TEXT
);
```

### 2. `teachers` Table
Stores teacher profiles and registration paths.
```sql
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT NOT NULL,
    employee_id TEXT NOT NULL UNIQUE,
    subject TEXT,
    mobile TEXT,
    image_path TEXT
);
```

### 3. `attendance` Table
Logs daily surveillance recognitions and automated roll-call details.
```sql
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    person_name TEXT,
    person_type TEXT,
    date TEXT,
    time TEXT,
    confidence REAL,
    camera_id INTEGER,
    recognition_method TEXT,
    status TEXT
);
```

---

## Database Access Rules

1. **Explicit Connection Teardowns**:
   Always close connections in a `finally` block to prevent descriptor leaks. In Python, the context manager `with sqlite3.connect` manages transaction commits/rollbacks but does not close the connection file descriptor.
   ```python
   conn = None
   try:
       conn = sqlite3.connect(DATABASE_PATH)
       # Database operations...
   finally:
       if conn is not None:
           conn.close()
   ```

2. **Parameterized Queries**:
   To prevent SQL injection, never write raw string-interpolated queries. Always parameterize queries:
   ```python
   cur.execute(
       "UPDATE students SET image_path = ? WHERE id = ?",
       (folder, person_id)
   )
   ```
