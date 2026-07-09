# Analytics Documentation

This manual outlines the math models, telemetry gathering, database indexing, and query optimizations used for the analytics system.

---

## 1. Analytics Architecture

Analytics queries are run every 5 seconds on the main thread via a non-blocking `after()` loop inside the dashboard.
To ensure the UI remains responsive and loads in $<2.0$ seconds:
1. All queries are fully optimized and parameterized.
2. Relational index keys are applied to high-traffic search columns.
3. Compound queries are wrapped inside lightweight SQLite read transactions.

---

## 2. Telemetry Formulas

### Attendance Rate
Defines the ratio of present students compared to the total student population:
\[\text{Attendance Rate (\%)} = \left( \frac{\text{Students Marked Today}}{\text{Total Students Registered}} \right) \times 100\]

### Model Accuracy
Calculates the accuracy rate of live camera recognitions:
\[\text{Accuracy (\%)} = \left( \frac{\text{Recognized Detections}}{\text{Recognized Detections} + \text{Unknown Alerts}} \right) \times 100\]

### LBPH Confidence Mapping
OpenCV's LBPH Face Recognizer returns prediction distance metrics where **lower values** signify higher confidence. Distance `0.0` represents an exact pixel-histogram match. The system maps distance to confidence percentages using:
\[\text{Confidence (\%)} = \max(0.0, 100.0 - \text{Average Distance})\]

---

## 3. Database Indexes

Speed indexes are automatically created in `DashboardRepository.ensure_indexes()`:
```sql
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_attendance_person ON attendance(person_id, person_type);
CREATE INDEX IF NOT EXISTS idx_alerts_date ON alerts(date);
```
These indices ensure search operations complete in $<500$ ms even with huge datasets.
