# WP00 — Program setup and data contracts

## Goal

Create the shared “contracts” and conventions that keep collection, analytics, and downstream tools aligned over time.

This work package is intentionally heavy on _definitions_ and _stability_.

## Outcomes

- A stable set of canonical tables/columns and join keys.
- A versioning strategy (schema versions, canonicalization versions, rule engine versions).
- A repo-level convention for run IDs, identity snapshot IDs, and artifact locations.

## Deliverables

- A short “contract” section in documentation (or a dedicated contract file) defining:
  - Canonical columns: `folder_path`, `ace_name`, `ace_sid`, `ace_mask`, `ace_inherited`, `ace_raw` (plus any agreed additions).
  - Join keys:
    - `ace_sid` ↔ `principals.sid`
    - `run_id` ↔ run folder name
    - `snapshot_id` ↔ identity snapshot folder/table partition
  - Required provenance fields (what must be present on each record/table).
- A versioning spec:
  - `inventory_schema_version`
  - `canonicalization_version` (affects fingerprints)
  - `ruleset_version` / git commit hash
  - `identity_snapshot_version` (if needed)
- A file/folder layout spec:
  - `out/parquet/run-<run_id>/...`
  - `out/identity/snap-<snapshot_id>/...`
  - `out/analysis/run-<run_id>_...csv`

## Non-goals

- Implementing ingestion or analytics logic.
- Implementing AD collection.

## Dependencies

- None (this is the first package).

## Acceptance criteria

- A new contributor can answer these questions unambiguously from docs:
  - “What columns can downstream tools rely on?”
  - “What is a stable ID for objects?”
  - “How are runs and identity snapshots named and referenced?”
  - “What changes require a version bump?”

## Suggested timeline

- Day 1: audit current columns and outputs; draft contract.
- Day 2: align contract with existing scripts; update docs to match; get stakeholder sign-off.

## Implementation notes / decisions to make

### Object identifiers

Decide how to represent an object reliably:

- Option A: derived `object_id = hash(server + share + folder_path)`
- Option B: (preferred if available) use a stable GUID from the source system

### Canonicalization version

Fingerprints must be reproducible. Version anything that affects canonical ACL serialization.

### Provenance requirements

At minimum, ensure each record can be tied back to:

- collection run
- appliance/server/share
- source file (or source API call)
- collected timestamp

### Compatibility stance

Decide upfront whether this is:

- “forward-only” (simplifies everything), or
- “supports historical schema variants” (adds complexity but can be worth it).
