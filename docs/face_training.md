# Face Recognition Training Documentation

## Face Training Workflow

```
[UI: Click Start Training]
     |
     v
[Background Thread: TrainingWorker]
     |
     +---> [Scan dataset/students and dataset/teachers]
     |          |
     |          +---> [Filter invalid, empty, or unreadable directories]
     |
     +---> [Filter individual image files]
     |          |
     |          +---> Check file extension (.jpg, .jpeg, .png, .bmp)
     |          +---> Check image corruptions or empty content
     |          +---> Validate dimensions (exactly 200x200 pixels)
     |          +---> Validate blur check (Laplacian variance >= 100.0)
     |          +---> Validate face presence (Haar Cascade detection)
     |          +---> Check for duplicates within person directory (MD5 hashing)
     |
     +---> [Map unique labels: Student = 1000+ID, Teacher = 2000+ID]
     |
     +---> [Run LBPH recognizer train operation]
     |
     +---> [Write models/trainer.yml & models/labels.json]
     |
     v
[UI: Complete & Reload Statistics]
```

---

## Quality Validation Rules

1. **Grayscale & Dimensions**:
   Every image is read as grayscale and checked against `FACE_WIDTH` and `FACE_HEIGHT` (defined as $200 \times 200$ pixels). Non-conforming shapes are skipped and logged.
2. **Sharpness & Blur**:
   Computes the variance of the Laplacian:
   $$\text{variance} = \sigma^2(\nabla^2 I)$$
   If $\text{variance} < 100.0$, the image is skipped as blurry.
3. **Face Verification**:
   Runs OpenCV Haar Cascade Face Detector. If zero bounding boxes are returned, the image is skipped.
4. **Duplicate Exclusion**:
   Computes md5 hash of raw image pixel buffers:
   `hashlib.md5(img.tobytes()).hexdigest()`
   If duplicate hashes are detected within the same person's directory, they are discarded.

---

## Data Structure Specs

### Model File (`models/trainer.yml`)
Binary configuration model compiled by OpenCV `LBPHFaceRecognizer`.

### Labels File (`models/labels.json`)
Saves person metadata mapping dictionary using string representation of label IDs:
```json
{
    "1001": {
        "id": 1,
        "name": "Jane Doe",
        "person_type": "Student",
        "dataset_folder": "dataset/students/1_Jane_Doe",
        "image_count": 50,
        "timestamp": "2026-07-09T14:36:12",
        "version": "1.0"
    }
}
```
* **Label Coding Scheme**:
  - Students: `1000 + student_id`
  - Teachers: `2000 + teacher_id`
  This enables zero-lookup decodability inside the surveillance parser to instantly identify person type and database ID from a detected numeric label.
