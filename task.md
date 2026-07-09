# Phase 4 Task Checklist: Professional Live Face Recognition

- [ ] 1. Load LBPH Recognizer (`surveillance.py` load `trainer.yml` and `labels.json` metadata safely, check for missing/corrupted files)
- [ ] 2. Thread-Safe Camera Preview (`surveillance.py` worker thread running cv2 capturing loop, reconnect support, graceful exit)
- [ ] 3. Recognition Pipeline (`surveillance.py` background crop face, resize to 200x200, grayscale, histogram equalization, prediction)
- [ ] 4. Visual Feedback & Bounding Boxes (Draw Green for Recognized, Red for Unknown, Yellow for Low Confidence)
- [ ] 5. Performance Metrics (FPS counter, detected count, recognized count, unknown count, speed optimization)
- [ ] 6. Expose Attendance Hooks (API stub/hooks ready for Phase 5)
- [ ] 7. Logging & Exception Safety (Logs recognition events, unknown detections, and errors to `logs/surveillance_log.txt`)
- [ ] 8. Self-Review & Verification (State transitions, thread-safe queue polling, CPU/RAM performance)
