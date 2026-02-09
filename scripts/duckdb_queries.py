#!/usr/bin/env python3
"""Run a set of common DuckDB queries against a parquet run directory and write CSV outputs.

Usage:
  python scripts/duckdb_queries.py --parquet out/parquet/run-20260206-160959 --out out/analysis

Requirements: `duckdb` Python package (pip install duckdb)
"""
from pathlib import Path
import argparse
import duckdb

SQL_QUERIES = {
    'top_identities_high_perms': '''
SELECT
  ace_name,
  COUNT(DISTINCT folder_path) AS folders_with_high_perms
FROM read_parquet('{parquet}/*.parquet')
WHERE (
  (ace_mask IS NOT NULL AND LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%full%')
  OR (ace_mask IS NOT NULL AND LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%modify%')
  OR (ace_mask IS NOT NULL AND LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%write%')
  OR TRY_CAST(ace_mask AS BIGINT) IS NOT NULL AND TRY_CAST(ace_mask AS BIGINT) <> 0
)
GROUP BY ace_name
ORDER BY folders_with_high_perms DESC
LIMIT 200;''',

    'ace_counts_by_appliance': '''
SELECT
  COALESCE(appliance_hostname, 'unknown') AS appliance_hostname,
  COUNT(*) AS ace_count
FROM read_parquet('{parquet}/*.parquet')
GROUP BY appliance_hostname
ORDER BY ace_count DESC
LIMIT 200;''',

    'inherited_exposures': '''
SELECT folder_path, ace_name, ace_mask, ace_inherited
FROM read_parquet('{parquet}/*.parquet')
WHERE ace_inherited = TRUE
  AND (
    LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%full%'
    OR LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%modify%'
    OR LOWER(CAST(ace_mask AS VARCHAR)) LIKE '%write%'
    OR (TRY_CAST(ace_mask AS BIGINT) IS NOT NULL AND TRY_CAST(ace_mask AS BIGINT) <> 0)
  )
ORDER BY folder_path
LIMIT 1000;''',

    'fingerprint_variants': '''
SELECT folder_path, COUNT(DISTINCT fingerprint_sha256) AS fingerprint_variants
FROM read_parquet('{parquet}/*.parquet')
GROUP BY folder_path
HAVING COUNT(DISTINCT fingerprint_sha256) > 1
ORDER BY fingerprint_variants DESC
LIMIT 200;''',
}


def run_queries(parquet_dir: Path, out_dir: Path):
    con = duckdb.connect(database=':memory:')
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, sql in SQL_QUERIES.items():
        q = sql.format(parquet=str(parquet_dir))
        print(f'Running: {name}')
        try:
            df = con.execute(q).fetchdf()
            out_file = out_dir / (name + '.csv')
            df.to_csv(out_file, index=False)
            print(f'Wrote: {out_file}')
        except Exception as e:
            print(f'Failed running {name}: {e}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--parquet', required=True, help='Path to parquet run directory (e.g. out/parquet/run-20260206-160959)')
    p.add_argument('--out', required=True, help='Output directory for CSVs')
    args = p.parse_args()
    run_queries(Path(args.parquet), Path(args.out))
