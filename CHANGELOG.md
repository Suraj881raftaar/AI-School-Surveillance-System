# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-07-09

### Added
- Pre-seeded database runtime bootstrapper in [config.py](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/config.py) to duplicate template assets into writeable persistent directory spaces.

### Changed
- Configured PyInstaller spec to build with console enabled to bypass false-positive antivirus quarantines on Windows endpoints.

### Fixed
- **PyInstaller dynamic views crash**: Injected static module imports inside [main.py](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/main.py) and added files to the `hiddenimports` listing inside [build.spec](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/build.spec) to compile dynamic modules statically.
- **Temporary folder data loss**: Split `BASE_DIR` paths in [config.py](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/config.py) to prevent databases, datasets, and logs from being written into temporary `sys._MEIPASS` folders.
- **Surveillance sidebar crash**: Declared and initialized `self.camera_index_var` in the `SurveillanceFrame` constructor inside [surveillance.py](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/surveillance.py) to prevent `AttributeError`.
- **SQLite connection handle leaks**: Wrapped table setup migrations in [attendance.py](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/attendance.py) and alerts queries in [surveillance.py](file:///c:/Users/ABL%20STORE/Desktop/AI-School-Surveillance-System/surveillance.py) in `try/finally` blocks with explicit connection-closing methods.

### Security
- Closed all SQLite database connection leaks, preventing handle exhaustion and folder access locking.

### Performance
- Compiled using clean, optimized dependency graphs to reduce binary bundle size.

### Documentation
- Updated [walkthrough.md](file:///C:/Users/ABL%20STORE/.gemini/antigravity/brain/256ef284-2691-400c-a33f-bc8f49dd73d9/walkthrough.md) with details for PyInstaller packaging and database copy setup.

### Known Issues
- Real-time webcam streams might suffer minor framerate lag when processing complex overlay frames on old hardware.

---

## [1.0.0] - 2026-07-09

### Added
- **Phase 1 (Stabilization)**: Implemented structural refactoring, verified core dependencies, and established stable database connections.
- **Phase 2 (Face Registration)**: Coded thread-safe OpenCV camera controllers, 100-crop image capturer state machines, Laplacian focus validation, and crop normalization ($200 \times 200$ pixels grayscale).
- **Phase 3 (Face Training)**: Developed background model compilation scripts generating `trainer.yml` and `labels.json` mapping parameters.
- **Phase 4 (Live Recognition)**: Created real-time surveillance rendering interfaces, video stream switching, and automatic alerts for unrecognized faces.
- **Phase 5 (Intelligent Attendance)**: Programmed automated attendance logs with a 60-second duplicate logging prevention filter.
- **Phase 6 (Analytics & Reporting)**: Programmed weekly graphs, filters sidebars, and CSV/Excel/PDF exporters.
- **Phase 7 (Release Polish)**: Set up `SettingsManager` observer pattern configurations, PyInstaller builds, licensing documents, user manuals, and contributing guidelines.

### Performance
- Decoupled frame grab loops, training, and database connections to run on background workers, preserving main thread responsiveness.

### Documentation
- Published detailed administration, testing, developer, and architecture reference guidelines under `docs/`.

---

[1.0.1]: https://github.com/Suraj881raftaar/AI-School-Surveillance-System/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Suraj881raftaar/AI-School-Surveillance-System/releases/tag/v1.0.0
