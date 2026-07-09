# Quality Assurance & Testing Plan

This document details the test suites and QA procedures for validating the system.

---

## Testing Checklists

### 1. Dataset Empty State
- **Procedure**: Rename `dataset/` directory. Start the application and navigate to the **Face Training** tab.
- **Expected Outcome**: Statistics display `0` students, `0` teachers, and `0` folders. Clicking "Start Training" immediate stops and shows a messagebox warning: "No valid dataset folders found." No crash occurs.

### 2. Validation Rejections
- **Procedure**: 
  - Create a valid student directory under `dataset/students/1_Test_User/`.
  - Add one valid $200 \times 200$ grayscale face crop.
  - Add one empty file named `002.jpg` (size 0 bytes).
  - Add one text file renamed to `003.jpg`.
  - Add one duplicate file of `001.jpg` named `004.jpg`.
  - Add one blurry image of a landscape named `005.jpg`.
- **Procedure**: Click "Start Training".
- **Expected Outcome**:
  - Valid image `001.jpg` is read.
  - Corrupt or invalid files are successfully ignored and skipped.
  - Logging console output logs each skipped file path with reason.
  - The model trains successfully on `1` image, and writes files correctly.

### 3. Concurrency & Cancellations
- **Procedure**: Run training on a large dataset. While loading images, click the "Cancel" button.
- **Expected Outcome**:
  - GUI state immediately sets status to `"CANCELING"`.
  - Background thread receives the flag, logs exit, and terminates loop.
  - Controls unlock safely. No orphan daemon threads leak.

### 4. Database Sync & Surveillance Verification
- **Procedure**: 
  - Run full training pipeline.
  - Verify that `models/trainer.yml` and `models/labels.json` exist.
  - Start live surveillance from the dashboard.
  - Verify that the camera feed runs smoothly and labels translate ID keys to correct names dynamically.
