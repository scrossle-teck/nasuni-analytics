# Example run helper for nasuni-analytics (PowerShell)
# Activate venv and run common scripts

Write-Output "Activating venv and running example analyses..."
& .\.venv\Scripts\Activate.ps1

# Ingest JSON -> Parquet (dry-run example)
python .\scripts\ingest_dryrun.py --run runs/run-20260202-124902

# Full ingest (uncomment to run)
# python .\scripts\ingest_duckdb.py --run runs/run-20260202-124902

# Generate Everyone FullControl CSV
python .\scripts\find_everyone_full_control.py

# Generate sensitive shares CSV
python .\scripts\find_sensitive_shares.py

# Generate shares missing admin CSV
python .\scripts\find_shares_missing_admin_full.py

Write-Output "Examples complete."
