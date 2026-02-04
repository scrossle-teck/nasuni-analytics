# Running tests

Python unit tests (pytest)

- Create and activate a virtual environment in the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Install Python test dependencies:

```powershell
pip install -r requirements.txt
```

- Run tests:

```powershell
pytest -q
```

PowerShell tests (Pester)

- The repo contains Pester tests under `tests/pester/`.
- Run Pester (PowerShell 7 recommended):

```powershell
Import-Module Pester -ErrorAction SilentlyContinue
Invoke-Pester -Script .\tests\pester -EnableExit
```

Notes

- The Python tests exercise the ingestion pipeline (`scripts/ingest_duckdb.py`).
- The Pester tests create short-lived sample run folders and execute the PowerShell helpers in `scripts/`.
- Pester may produce a compatibility warning depending on your installed version; the tests in `tests/pester/` are written to work with Pester 5+.
