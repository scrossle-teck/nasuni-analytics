# WP00 Addendum — Program setup and data contracts

## What you can leverage today

### Completed work in `nasuni-inventory` (collector)

- A stable, schema-versioned forensic JSON output shape (array of records + schema sidecar).
- A consistent run folder convention (`run-YYYYMMDD-HHMMSS`) with predictable artifacts.
- A written mapping between inventory CSVs and how collection artifacts relate to appliances/volumes/shares.

Key references (inventory repo):

- `README.md`
- `CONTEXT_InventoryFieldMappings.md`
- `Get-FolderAcls.ps1`, `Get-FolderAclsFromVisitList.ps1`
- `Run-All.ps1`

### Completed work in `nasuni-analytics` (analysis)

- A canonical column expectation is already described in docs and reinforced by ingestion (`folder_path`, `ace_*`, `ace_raw`).
- Architecture direction is now captured in `docs/PROJECT_GUIDELINES_acl_inventory_and_effective_access.md`.

Key references (analytics repo):

- `AGENTS.md`
- `README.md`
- `docs/PROJECT_GUIDELINES_acl_inventory_and_effective_access.md`

## Gaps vs WP00 acceptance criteria

WP00 acceptance criteria asks that a new contributor can unambiguously answer:

- canonical columns and join keys
- object/run/snapshot naming conventions
- what changes require version bumps

Current gaps (cross-repo):

- A single, authoritative **data contract doc** that explicitly aligns:
  - inventory JSON fields (e.g., `FolderPath`, `Access[].Identity`, `Access[].Rights`) to
  - analytics canonical columns (`folder_path`, `ace_sid`, `ace_mask`, etc.)
- In practice, **`ace_sid` and numeric `ace_mask`** are not guaranteed to be present in inventory evidence, and the transform strategy is not written as a contract.
- No explicit convention is enforced for writing `run_id` and `source_file` as columns in Parquet (it’s implied today by directory structure).

## Checklist: steps to reach WP00 acceptance

### Contract document

- [ ] Create a short “Data Contract” doc (either a new file, or a dedicated section in `docs/PROJECT_GUIDELINES_acl_inventory_and_effective_access.md`) that states:
  - [ ] Canonical columns (required vs optional)
  - [ ] Join keys and their stability guarantees (`ace_sid` primary; name as display)
  - [ ] ID conventions: `run_id`, `snapshot_id`, and recommended `object_id`
  - [ ] Versioning strategy:
    - [ ] inventory schema version
    - [ ] canonicalization version (affects fingerprints)
    - [ ] ruleset version (git SHA is acceptable)

### Enforcement points

- [ ] Decide where enforcement lives:
  - [ ] ingestion (preferred) enforces column presence and emits warnings when missing
  - [ ] rule execution requires canonical columns and fails fast when missing

### Clarify rights representation

- [ ] Decide and document: how to normalize inventory `Access[].Rights` into:
  - [ ] numeric `ace_mask` and/or
  - [ ] a coarse bucket (`read`/`write`/`fullcontrol`)

### Fingerprints naming

- [ ] Explicitly define two fingerprints (avoid conflation):
  - [ ] **record/collection fingerprint** (path-specific; useful for diffs/tamper detection)
  - [ ] **ACL-definition fingerprint** (path-independent; for dedup and scale)

## Notes / risks

- If `ace_sid` cannot be reliably captured from the collector, plan for a two-step approach:
  1. preserve best-effort identity strings in `ace_name`
  2. later enrich/resolve to SIDs using AD snapshots (WP05) and/or translation heuristics.
