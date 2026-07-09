# Developer Guide

This document details the codebase design, styling guidelines, threading patterns, and settings manager observer registers.

---

## 1. Class Architectures

* **`SettingsManager` (Singleton / Observer)**: Co-ordinates configurations and broadcasts changes dynamically to registered callbacks.
* **`DashboardRepository` (SQL Telemetry / Utilities)**: Executes optimized database transactions and backup utilities.
* **`AttendanceChart` (Natives Canvas graphics)**: Visualizes 7-day attendance trend lines without using external libraries.
* **`ReportsFrame` (Reporting engine)**: Filters lists and compiles CSV, openpyxl, and ReportLab PDF documents.

---

## 2. Observer Notification Pattern

Modules can subscribe to configurations hot-reloads using `SettingsManager`:
```python
from settings_manager import SettingsManager

def my_callback(key, value):
    print(f"Setting updated: {key} -> {value}")

# Register listener
mgr = SettingsManager()
mgr.register_listener(my_callback)
```

---

## 3. Threading Standards

* **Worker threads**: Long-running operations (such as camera frame acquisitions, model training, report compiling, and zip back-ups) must execute in isolated worker threads.
* **Tkinter widgets**: Never update widgets directly from worker threads. Communicate variables to main threads using queues or Tkinter `after()` loops to prevent concurrency deadlocks.
