# WP04 Addendum — Rule engine: DuckDB/SQL-first execution

## What you can leverage today

### Completed work in `nasuni-analytics`

- A JSON ruleset exists with severities.
- A Python rule engine exists and produces `rule_matches.csv`.
- There are unit tests around rule evaluation.
- There are DuckDB query artifacts (SQL + runner) for common run-level questions.

Key references:

- `scripts/ruleset.json`
- `scripts/apply_rules.py`
- `run.py` (standard analyze entrypoint)
- `tests/test_apply_rules.py`, `tests/test_apply_rules_min_severity.py`
- `scripts/duckdb_queries.sql`, `scripts/duckdb_queries.py`

### Completed work in `nasuni-inventory`

- Heuristic “broad principals” analysis exists (principal frequency, fingerprints), which can inform the first SQL rule set and fixtures.

Key references:

- `Analyze-FolderAcls.ps1` + `README_Analyze-FolderAcls.md`

## Gaps vs WP04 acceptance criteria

WP04 expects:

- standardized runs that scale without loading all Parquet into pandas
- SQL-first (DuckDB) rule execution where feasible
- consistent findings schema

Current gaps / risks:

- Many scripts load all Parquet into pandas then `concat`, which is not memory-stable at larger scales.
- Rule engine is row-wise (pandas `iterrows`) and not leveraging SQL pushdown.
- Findings output is present, but “reason” and provenance columns are not consistently included.

## Checklist: steps to reach WP04 acceptance

### Define a standard findings schema

- [ ] Define columns required on every finding instance:
  - [ ] `run_id`, `rule_id`, `severity`
  - [ ] `folder_path` (and/or `object_id`)
  - [ ] matched ACE evidence: `ace_sid`, `ace_name`, `ace_mask`, `ace_inherited`
  - [ ] `reason` (short)
  - [ ] minimal provenance (`source_file`, timestamps) where available

### SQL-first rule execution

- [ ] Select an initial set of 5–10 high-signal rules and implement as DuckDB SQL.
  - Example types: Everyone/Authenticated Users write; non-admin full control; sensitive paths + broad write.
- [ ] Execute rules using DuckDB directly over Parquet (`read_parquet('.../*.parquet')`).
- [ ] Only materialize the results to CSV/Parquet at the end.

### Keep Python rules for “hard” semantics

- [ ] If a rule can’t be expressed in SQL cleanly, keep it in Python but ensure inputs are narrowed:
  - [ ] select only needed columns
  - [ ] filter rows early (DuckDB first)

### Add acceptance tests

- [ ] Fixture-based tests that prove:
  - [ ] rules produce expected outputs
  - [ ] output schema stays stable

## Notes / sequencing

- WP03 fingerprints unlock a faster pattern: rule on `acl_definitions` then expand via `object_acl`.
- WP10 perf baselines should be added once SQL-first execution exists.
