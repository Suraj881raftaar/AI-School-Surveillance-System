# Troubleshooting Guide

Common issues and recovery resolutions for the School Surveillance system.

---

## 1. Camera Issues

### Camera Feed Black Screen or Missing
* **Cause**: Camera index mismatch or hardware occupied.
* **Solution**: Navigate to the **Settings** panel and adjust the **Active Camera Index** (0, 1, 2, or 3) and check that no other software is using the camera.

---

## 2. Face Recognizer Issues

### Recognizer Accuracy Low or Not Recognizing Profiles
* **Cause**: Models have not been trained on the latest registered user dataset.
* **Solution**: Navigate to **Face Training** tab and click **Start Training**. This compiles `trainer.yml` and updates profile matching keys.

---

## 3. Database & File Locks

### Database Locked Error (`sqlite3.OperationalError`)
* **Cause**: Multiple threads attempting write transactions concurrently.
* **Solution**: Restart the application. Connection managers automatically close files safely to resolve locks.
