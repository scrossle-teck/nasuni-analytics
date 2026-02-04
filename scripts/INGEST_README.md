# Ingest DuckDB pipeline

Quick start (Windows + PowerShell 7):

1. Create and activate a virtual environment:

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

2. Install dependencies:

    ```powershell
    pip install -r requirements.txt
    ```

3. Run the ingestion script:

    ```powershell
    python scripts/ingest_duckdb.py --run-path runs/run-20260202-124902 --out-dir out/parquet
    ```

Output:

- Parquet files will be placed under `out/parquet/<run_id>/` (one parquet per source JSON file). These can be queried directly with DuckDB.

Notes:

- The ingestion script uses simple heuristics to locate ACL lists in JSON files. If your JSON structure differs, we can refine the parser to match the schema exactly.
