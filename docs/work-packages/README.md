# Work Packages — ACL Inventory + Risk Analytics + Effective Access

This folder breaks the project into multi-day work packages that can be executed in parallel where possible.

These packages implement the architecture described in:

- `docs/PROJECT_GUIDELINES_acl_inventory_and_effective_access.md`

## How to use this

- Treat each file as a mini-project spec.
- Each package has:
  - Goal and outcomes
  - Deliverables
  - Non-goals
  - Dependencies
  - Acceptance criteria
  - Implementation notes
  - Suggested timeline (multi-day)

## Addendums

Addendums capture two things for each work package:

1. What’s already completed in `nasuni-inventory` and `nasuni-analytics` that you can leverage.
2. The concrete steps required to reach WP acceptance.

Start here:

- `docs/work-packages/addendums/README.md`

## Suggested execution order (high-level)

### Foundation

1. WP00 — Program setup and contracts
2. WP01 — Ingest contract + run manifest standardization
3. WP02 — Parquet ingest + canonical tables baseline

### Scale enablers

1. WP03 — ACL canonicalization + fingerprint tables
2. WP04 — DuckDB-first rule execution (avoid full pandas loads)

### Identity + blast radius

1. WP05 — AD snapshot ingest (principals + membership edges)
2. WP06 — Membership closure (transitive group expansion)
3. WP07 — Blast-radius enrichment for findings

### Effective access

1. WP08 — Effective NTFS access MVP (“view as user”)

### Deltas + drift

1. WP09 — Run-to-run diffs and delta processing

### Hardening

1. WP10 — QA, performance, and operationalization

## Work packages

- `WP00_program_setup_and_data_contracts.md`
- `WP01_inventory_run_manifest_and_provenance.md`
- `WP02_parquet_ingest_baseline_tables.md`
- `WP03_acl_canonicalization_and_fingerprints.md`
- `WP04_rule_engine_sql_first.md`
- `WP05_ad_snapshot_ingest.md`
- `WP06_membership_closure.md`
- `WP07_blast_radius_scoring.md`
- `WP08_effective_access_mvp.md`
- `WP09_deltas_and_drift_reporting.md`
- `WP10_quality_performance_ops.md`
