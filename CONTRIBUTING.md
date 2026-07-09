# Contributing Guidelines

Thank you for contributing to the AI School Surveillance System! Please adhere to the following project standards and workflow guidelines.

---

## Coding Standards

* **Python Guidelines**: Follow PEP8 formatting. Use type hints for method definitions and specify docstrings for public classes and methods.
* **Tkinter Best Practices**: Never execute blocking tasks (sleeps, DB requests, camera calls, loops) on the main thread. Always offload to background threads and communicate via thread-safe queues.
* **Resource Lifecycles**: Ensure files, SQLite connections, and OpenCV camera resources are explicitly closed or released in `finally` blocks.

---

## Git Workflow

We use a one-feature-per-commit branching strategy to keep history clean.

### Commit Messages format
Prefix commit messages with the target Phase indicator:
```
Phase <X>: <Brief Feature Summary>
```
* Example: `Phase 3: Implement Face recognition training module`

---

## Pull Request Policy

1. Always compile check code before submitting:
   ```bash
   python -m py_compile target_file.py
   ```
2. Verify that unit test cases pass.
3. Keep changes minimal and isolated. Avoid repository-wide refactoring inside individual feature additions.
