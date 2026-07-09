# Contributing Guide

Thank you for your interest in contributing to the AI School Surveillance System!

---

## 1. Code Review & Style Standards
* All changes must adhere strictly to **PEP 8**.
* Use explicit type hints and complete docstrings for all added classes/methods.
* Ensure all functions are modular, small, and follow the SOLID principles.
* Verify that SQLite queries are parameterized and database handles are closed inside `finally` blocks.

---

## 2. Development Workflow

1. Fork the repository and create your feature branch: `git checkout -b feature/amazing-feature`.
2. Implement your features in logical, focused commits.
3. Test your changes locally to guarantee no regressions or Tkinter main thread freezes.
4. Open a Pull Request detailing your changes and test results.
