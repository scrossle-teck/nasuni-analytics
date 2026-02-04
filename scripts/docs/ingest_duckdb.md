# ingest_duckdb.py

Purpose: Ingest `folderacls/*.json` into Parquet files and optionally load into DuckDB for fast querying.

Usage:

```bash
python scripts/ingest_duckdb.py --run runs/run-20260202-124902 --out out/duckdb
```

Outputs:

- per-source Parquet files under the `out` path; ready for DuckDB or Pandas consumption.
