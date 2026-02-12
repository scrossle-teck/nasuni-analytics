# WP05 Addendum — AD snapshot ingest (principals + membership edges)

## What you can leverage today

### Completed work (design/spec)

- The target identity tables and join semantics are already clearly described in:
  - `docs/PROJECT_GUIDELINES_acl_inventory_and_effective_access.md`
  - `docs/work-packages/WP05_ad_snapshot_ingest.md`

### Completed work in `nasuni-inventory` (useful inputs)

- ACL evidence provides a natural “scope set” of principals:
  - unique `Access[].Identity` strings (often `DOMAIN\\Name`, sometimes SIDs)
- Strong provenance makes it easy to report what was (and wasn’t) resolvable.

### Completed work in `nasuni-analytics` (foundation)

- Parquet ingest exists; once AD data is exported, landing it into Parquet is straightforward.
- DuckDB is already part of the workflow and can power join demos and validation queries.

## Gaps vs WP05 acceptance criteria

WP05 acceptance requires:

- `principals.parquet` and `membership_edges.parquet` produced for a `snapshot_id`
- joins from `ace_sid` to `principals.sid` should work for sample SIDs

Current gaps:

- No AD snapshot extractor is implemented yet.
- `ace_sid` is not guaranteed to exist for all ACEs (collector may emit names more often than SIDs).
- No `snapshot_id` convention is enforced by code.

## Checklist: steps to reach WP05 acceptance

### Decide the ingestion approach (and document it)

- [ ] Choose one:
  - [ ] PowerShell AD module export (Windows runner)
  - [ ] Python LDAP export (cross-platform)
- [ ] Document auth strategy (service account, scheduled job, least privilege, where secrets live).

### Produce baseline tables

- [ ] Implement snapshot export to Parquet:
  - [ ] `out/identity/snap-<snapshot_id>/principals.parquet`
  - [ ] `out/identity/snap-<snapshot_id>/membership_edges.parquet`
- [ ] Ensure required columns exist:
  - principals: `snapshot_id`, `sid`, `samaccountname`, `distinguished_name`, `principal_type`, `enabled`, `collected_at`
  - edges: `snapshot_id`, `member_sid`, `group_sid`

### Join validation

- [ ] Add a validation query/script that:
  - [ ] selects a sample of `ace_sid` values from an ingested run
  - [ ] joins to principals
  - [ ] reports unmatched SIDs (and how many)

### Address the `ace_sid` reality

- [ ] Decide and document an interim approach if `ace_sid` isn’t available:
  - [ ] best-effort SID extraction from `ace_raw` if present
  - [ ] name-to-SID resolution strategy (requires AD lookup) with explicit failure reporting

## Notes

- A practical way to control AD snapshot size is “evidence-driven” export:
  1. compute unique principals from ACL evidence
  2. fetch only those principals + their group memberships

That can be a phase-2 optimization; full domain snapshot is acceptable if operationally simpler.
