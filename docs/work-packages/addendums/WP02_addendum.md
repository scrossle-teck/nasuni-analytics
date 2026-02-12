# WP02 Addendum — Parquet ingest + baseline canonical tables

## What you can leverage today

### Completed work in `nasuni-analytics`

- JSON → Parquet ingestion exists and is tested.
- Ingest already normalizes schema variants (PascalCase vs legacy forms) and emits canonical column set.
- Provenance/asset metadata capture has been added (collector identity, timestamps, appliance/volume/share metadata, hashes).

Key references:

- `scripts/ingest_duckdb.py`
- `tests/test_ingest.py`
- `docs/SESSION_SUMMARY20260209.md`

### Completed work in `nasuni-inventory`

- Run directory conventions and canonical inputs (`appliances.csv`, `volumes.csv`, `shares.csv`, `visitlist.csv`) are stable.
- Mapping assumptions across these inputs are documented.

Key references:

- `CONTEXT_InventoryFieldMappings.md`
- `README.md`

## Gaps vs WP02 acceptance criteria

WP02 expects:

- repeatable ingest producing canonical columns (lowercased)
- baseline canonical tables that are easy to query

Current gaps / opportunities:

- `run_id` is implied by folder name; not guaranteed as a Parquet column.
- There isn’t a first-class consolidated `objects` table (one row per folder path/object) for stable joins.
- Some fields (notably identity and rights) depend on the shape/quality of collected evidence:
  - `ace_sid` may be absent or inconsistent
  - `ace_mask` normalization requires a defined strategy (numeric vs bucket)

## Checklist: steps to reach WP02 acceptance

### Make run identity explicit

- [ ] Ensure every Parquet row has `run_id` as a column.
- [ ] Ensure every row has `source_file` (or equivalent provenance).

### Baseline tables

- [ ] Produce an explicit `objects.parquet` table per run:
  - [ ] one row per object (`object_id`, `folder_path`, server/share identifiers if available)
  - [ ] stable dedup semantics (e.g., unique on `folder_path` per run)

### Canonical columns enforcement

- [ ] Validate ingest output always includes:
  - [ ] `folder_path`
  - [ ] `ace_name`
  - [ ] `ace_mask` (or a documented alternate)
  - [ ] `ace_inherited`
  - [ ] `ace_raw`
- [ ] For `ace_sid`, decide if it is:
  - [ ] required (then collector must guarantee it), or
  - [ ] optional (then AD enrichment later provides it)

### Acceptance demo queries

- [ ] Add 3–5 DuckDB queries used as acceptance checks:
  - [ ] row counts by appliance/volume/share
  - [ ] top principals by ACE count
  - [ ] missing `folder_path` audit

## Notes / risks

- Keep the ingest schema-driven where possible; heuristic parsing is fine initially but should be bounded by tests and explicit mappings.
- Do not “drop” raw fidelity: keep `ace_raw` for future semantics (deny/allow flags, owner, SDDL, etc.).
