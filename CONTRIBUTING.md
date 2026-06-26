# Contributing Guidelines

Thank you for helping develop the LinkedIn AI Analytics Platform! Follow these guidelines to keep code quality high.

---

## Developer Environment Setup
1. **Virtual Environment**:
   Initialize and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Configure Settings**:
   Copy `.env.example` to `.env` and fill in paths and configurations.

---

## Coding Standards

### Python & OOP Pattern
- Use strict type hinting.
- Organize database connections using the Repository Pattern (`src/database/repository.py`).
- Implement scraping, analytics, and AI logic inside dedicated services.
- Never write hardcoded values in calculations; pull configurations from `.env` or tables.

### Logging
- Use structured logging via `src/utils/logger.py`.
- Log transaction boundaries, record insertions, and warnings/errors with stack traces.
- Logs are written to `logs/application.log`.

---

## Testing & Verifications
- Every module phase has a dedicated test script prefixed with `run_`. E.g.:
  - `run_phase6_test.py`
  - `run_powerbi_test.py`
  - `run_phase9_test.py`
  - `run_phase10_test.py`
- Run test scripts to verify additions before committing changes.
