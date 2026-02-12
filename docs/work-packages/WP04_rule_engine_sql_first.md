# WP04 — Rule engine: DuckDB/SQL-first execution

## Goal

Make standardized analytics runs scale by moving rule execution toward DuckDB SQL over Parquet in-place, avoiding full dataset loads into pandas.

## Outcomes

- Standard runs remain fast and memory-stable as data grows.
- A subset of high-signal rules implemented as SQL queries.

## Deliverables

- A rules execution framework that supports:
  - SQL rules (DuckDB queries)
  - optional Python rules (narrowed inputs only)
- A standard findings output table/CSV with consistent columns.
- A library of initial SQL rules (examples):
  - Everyone/Authenticated Users/Domain Users have write/modify/fullcontrol
  - Non-admin FullControl on share roots
  - Sensitive path + broad write

## Non-goals

- Blast radius (WP07).
- Effective access (WP08).

## Dependencies

- WP02 baseline ingest
- WP03 fingerprints recommended (rules can run either on ACE rows or ACL definitions)

## Acceptance criteria

- Running rules against a large run does not require loading all Parquet into memory.
- Findings output is stable and includes enough evidence to triage.

## Suggested timeline

- Day 1: pick 5–10 high-signal rules and express them as SQL.
- Day 2–3: implement execution harness + tests.

## Implementation notes

### Where to run rules

Two approaches:

- Run rules on raw `aces` rows keyed by `folder_path` (simple)
- Run rules on `acl_definitions` (fingerprint-level) then expand via `object_acl` (faster at scale)

### Rule metadata

Each rule should have:

- `rule_id`
- severity
- description
- query text
- expected output columns

### Explainability

Every finding instance should include:

- which ACE(s) triggered the match
- the folder/share context
- a short `reason`
