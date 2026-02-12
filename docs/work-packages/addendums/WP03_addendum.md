# WP03 Addendum — ACL canonicalization + fingerprint tables

## What you can leverage today

### Completed work in `nasuni-inventory`

- Deterministic SHA-256 fingerprinting exists (`FingerprintSha256`) and is already used for fast comparison.
- The collector/comparator already defines a canonical “ACE line” representation and sorts it before hashing.
- Analyzer can produce fingerprint frequency rollups.

Key references (inventory repo):

- `Get-FolderAcls.ps1` (fingerprint creation)
- `Compare-FolderAcls.ps1` (diffs/fingerprint checks)
- `Analyze-FolderAcls.ps1` (rollups)
- `Test-FolderAcls.ps1` (validation)

### Completed work in `nasuni-analytics`

- Collector fingerprint fields are preserved into Parquet (`fingerprint_sha256`, `collection_sha256` etc.).
- DuckDB queries already explore fingerprint variants.

Key references:

- `scripts/ingest_duckdb.py`
- `scripts/duckdb_queries.sql`

## Gaps vs WP03 acceptance criteria

WP03 expects:

- a stable canonical ACL representation for **ACL definitions**
- `acl_fingerprint` that represents ACL semantics **independent of object identity**
- two tables:
  - `acl_definitions.parquet`
  - `object_acl.parquet`

Current gaps:

- Inventory’s `FingerprintSha256` appears path-specific (or includes non-policy metadata); it’s not guaranteed to be a path-independent ACL-definition fingerprint.
- There is no explicit `canonicalization_version`.
- The two tables do not exist yet.

## Checklist: steps to reach WP03 acceptance

### Define canonicalization + versioning

- [ ] Write a canonicalization spec that answers:
  - [ ] Which ACE fields are included in ACL-definition fingerprint?
  - [ ] How to treat name vs SID differences?
  - [ ] How to normalize ordering and nulls?
  - [ ] How to incorporate allow/deny if available?
- [ ] Introduce `canonicalization_version` (string) and persist it.

### Implement ACL-definition fingerprint

- [ ] Implement `acl_fingerprint = sha256(canonical_acl_representation)` where representation:
  - [ ] excludes path/object identity
  - [ ] excludes non-security metadata unless explicitly desired
- [ ] Store the canonical string (or canonical JSON) used for hashing for auditability.

### Produce tables

- [ ] Generate `acl_definitions.parquet`:
  - [ ] keyed by `acl_fingerprint`
  - [ ] includes canonical representation + ACE count
- [ ] Generate `object_acl.parquet`:
  - [ ] `object_id`, `folder_path`, `acl_fingerprint`
  - [ ] include `is_protected` / owner fields if available (optional)

### Acceptance checks

- [ ] Determinism test: same input → same fingerprint.
- [ ] Re-ordering invariance test: permuted ACE order does not change fingerprint.
- [ ] Scale check: report `unique_acl_count` and top N ACLs by object count.

## Notes / risks

- Keep inventory’s existing fingerprint as a **record fingerprint**; WP03 introduces a second fingerprint for dedup.
- If collector evidence lacks structured allow/deny information, capture it in `ace_raw` now so fingerprints can evolve later (with version bumps).
