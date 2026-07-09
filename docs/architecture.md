# Architecture Documentation

## System Architecture

The AI School Surveillance System is built on a modular desktop application architecture powered by **Python**, **Tkinter**, **SQLite**, and **OpenCV**.

The application enforces a strict separation of concerns, separating the user interface (running on the main thread) from intensive operations (such as video capturing, face detection, image quality preprocessing, and LBPH model training) which execute on dedicated background worker threads.

```
+--------------------------------------------------------------+
|                         GUI Layer                            |
|                     (Tkinter Main Thread)                    |
+------------------------------+-------------------------------+
                               |
                   Event Queue / Thread Signals
                               |
                               v
+------------------------------+-------------------------------+
|                       Controller Layer                       |
|                   (Background Worker Threads)                |
+------------------------------+-------------------------------+
                               |
                     OpenCV / SQLite / Files
                               |
                               v
+------------------------------+-------------------------------+
|                        Resource Layer                        |
|                  (Dataset / SQLite DB / Models)              |
+--------------------------------------------------------------+
```

---

## Component Separation

1. **User Interface (Tkinter)**:
   - Manages responsive page layouts and user controls (inputs, dropdowns, statistics).
   - Polls inter-thread communication queues using non-blocking Tkinter `after()` loops.
   - Restricts operations to the main thread to prevent thread violations.

2. **Model Training Engine (cv2.face.LBPHFaceRecognizer)**:
   - Spawns background worker thread `TrainingWorker` to process image reading, verification checks, and math training operations.
   - Communicates live progress log updates and performance speed telemetry (e.g. `images/sec`, `estimated remaining time`) to the UI queue.
   - Automatically generates decodable label mappings (`1000+ID` for Students, `2000+ID` for Teachers) and serializes results.

3. **Data Storage & Serialization**:
   - **SQLite**: Stores metadata profiles for students and teachers (name, ID, roll/employee code, status).
   - **File System**:
     - Raw cropped faces: `dataset/students/<ID>_<Name>/` and `dataset/teachers/<ID>_<Name>/`.
     - Face Recognition Model: `models/trainer.yml` (Single source of truth).
     - Label Mapping Metadata: `models/labels.json`.
     - Logging outputs: `logs/training_log.txt`.
