# Dashboard Documentation

This document describes the design, features, and layout of the real-time AI School Surveillance Dashboard.

---

## 1. Dashboard Layout

The Overview Panel is structured as a responsive layout with three main sections:
1. **Interactive Metrics Cards**: A row of 8 metrics cards showing real-time aggregates.
2. **Recent Activities Tables**: Side-by-side tables listing recent attendance records and security alert logs.
3. **Weekly Trends Chart**: A native Tkinter Canvas component drawing the 7-day attendance count graph.

---

## 2. Real-Time Metrics

The dashboard calculates the following real-time statistics by querying the SQLite repository:

* **Total Students**: Total registered student count.
* **Total Teachers**: Total registered teacher count.
* **Attendance Today**: Total number of attendance records logged on the current date.
* **Security Alerts**: Count of unregistered face alerts logged today.
* **Attendance Rate**: Percentage of registered students marked present today.
* **Model Accuracy**: Ratio of recognized detections to total detections (recognized + alerts) on the camera stream today.
* **Average Confidence**: Distance-to-percentage mapping of LBPH prediction distances.
* **New Registrations**: Number of student/teacher folders created today.

---

## 3. Dynamic Canvas Charting

The **AttendanceChart** class extends `tkinter.Canvas` to draw dynamic graphs without external library requirements:
* **Bar Heights**: Proportional heights mapped to the maximum count of the week.
* **Grid Lines**: Axis ticks and markers drawn for spacing.
* **Data Annotations**: Floating value tags drawn on top of each bar.
* **Labeling**: Abbreviated date indicators (MM-DD) drawn under each vertical bar.
