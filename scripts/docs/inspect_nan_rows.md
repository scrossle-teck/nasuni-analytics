# inspect_nan_rows.py

Purpose

- Identify Parquet rows with missing or NaN `folder_path` values and aid debugging.

Usage

- `python scripts/inspect_nan_rows.py`

Outputs

- Writes (when extended) `out/analysis/nan_rows_debug.csv` containing problematic rows.

Notes

- Intended as a quick debugging utility when ingestion produces missing folder paths.
