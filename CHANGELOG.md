# Changelog

All notable changes to this project will be documented in this file. This project adheres to Semantic Versioning (v1.0.0, v1.1.0, etc.).

---

## [1.0.0-rc3] - 2026-07-09

### Added
* Created new face recognition training module `train_face.py` running asynchronous LBPH model training on background thread.
* Created a custom Tkinter progress control view with speed telemetry, estimated time calculations, and console logs.
* Added a static camera port index selector (0 to 3) in `main.py` and sidebar layout.
* Created detailed manuals under `docs/` (architecture, database, face_training, testing, deployment, security).
* Integrated project governance standards (`CONTRIBUTING.md`, `CHANGELOG.md`).

### Changed
* Refactored `surveillance.py` to point model path to `models/trainer.yml` and parse the new dictionary-based metadata in `labels.json` safely.
* Optimized `main.py` to add `show_face_training()` navigation and button loaders.
* Refactored database connections in `load_people` to close connections safely, preventing file descriptor locks.

### Fixed
* Fixed main thread freeze in `register_face.py` by populating combobox port indices statically.
* Fixed concurrency deadlock in `camera_worker` by replacing blocking queue updates with non-blocking oldest frame discards.
* Fixed main thread CPU bottleneck by moving OpenCV color conversion (BGR to RGB) to background thread.

---

## [0.9.0] - 2026-07-09

### Added
* Implemented camera lifecycle controller state machine in `register_face.py` to manage thread states.
* Implemented embedded Tkinter canvas stream rendering to show frames without focus-stealing popups.

---

## [0.1.0] - Initial Setup

### Added
* Project setup, SQLite schemas migration scripts, and initial forms configuration.
