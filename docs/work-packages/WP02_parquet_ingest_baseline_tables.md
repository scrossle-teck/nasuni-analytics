# WP02 — Parquet ingest + baseline canonical tables

## Goal

Ensure every inventory run ingests into a standardized Parquet dataset that downstream queries can rely on.

## Outcomes

- A repeatable ingest step that produces canonical columns and basic “objects + ACE rows” tables.
- Parquet is partitioned and queryable with DuckDB.

## Deliverables

- A repeatable command (or `run.py analyze` stage) that produces:
  - `out/parquet/run-<run_id>/*.parquet` (or a stable layout)
- Canonical columns lowercased in Parquet.
- A documented mapping from raw JSON fields to canonical columns.

## Non-goals

- Fingerprinting and deduplication (WP03).
- AD ingestion (WP05).

## Dependencies

- WP00 (contracts)
- WP01 (manifest/provenance) is recommended but not strictly required.

## Acceptance criteria

- Ingesting the same run twice yields the same row counts and column set.
- DuckDB can run basic queries over the dataset without loading into pandas.

## Suggested timeline

- Day 1–2: confirm ingest supports all schema variants you care about.
- Day 3: add tests with fixtures for edge cases; document any normalizations.

## Implementation notes

- Keep `ace_raw` and avoid lossy conversions.
- Prefer one “ACE rows” table rather than many tiny tables unless there’s a proven scalability need.
- Preserve a stable `folder_path` canonicalization strategy and document it.

## Example baseline queries (for acceptance)

- Row counts:
  - ACE rows per appliance/volume
  - folders per share
- Sanity checks:
  - top principals by ACE count
  - check for missing `folder_path`
