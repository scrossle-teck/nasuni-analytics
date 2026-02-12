# WP08 Addendum — Effective NTFS access MVP (“view as user”)

## What you can leverage today

### Completed work in `nasuni-inventory`

- Forensic ACL snapshots preserve rich raw evidence (including identity strings, inheritance flags, SDDL/owner context in raw payloads).
- Collection is already reproducible and path-scoped via visit lists.

### Completed work in `nasuni-analytics`

- Parquet ingest creates a canonical ACE-row view.
- DuckDB queries are already part of the workflow.
- Rule engine and output patterns exist (CSV outputs with severity and evidence fields).

Key references:

- `scripts/ingest_duckdb.py`
- `scripts/duckdb_queries.sql`
- `run.py`

## Gaps vs WP08 acceptance criteria

WP08 requires:

- a command/query to compute effective access for a user SID
- an explanation model (why access is granted)

Current gaps:

- No identity snapshot dataset (WP05) and closure (WP06) to build the user’s security context set.
- No explicit rights bucket mapping for effective-access queries.
- The pipeline is not yet optimized for ACL-definition-level evaluation (WP03).

## Checklist: steps to reach WP08 acceptance

### Prerequisites

- [ ] WP05: principals + membership edges (at minimum)
- [ ] WP06: membership closure (strongly recommended)
- [ ] WP02: canonical `ace_mask` or an agreed rights bucket

### Define MVP semantics

- [ ] Choose minimum rights bucket:
  - [ ] “write-like” access first (most actionable)
  - [ ] then add “read-like”
- [ ] Explicitly scope: NTFS-only snapshot-based effective rights

### Implement the query path

- [ ] Build the security context set for a user:
  - [ ] user SID
  - [ ] group SIDs from closure
  - [ ] optionally well-known SIDs
- [ ] Filter ACE rows where `ace_sid IN context_set`.
- [ ] Aggregate to produce a per-folder outcome:
  - [ ] effective bucket (read/write)
  - [ ] at least one matched ACE as evidence
  - [ ] optionally the group that provided membership

### Prefer fingerprint-level evaluation (scale)

- [ ] If WP03 exists, evaluate per `acl_fingerprint` first then expand to folders.

### Acceptance validation

- [ ] Add synthetic fixtures:
  - [ ] user in nested group
  - [ ] allow/deny edge case (if deny available)
- [ ] Prove output includes “why” (matched ACE + via group).

## Notes

- You can ship a very useful MVP without perfect semantics. The key is:
  - conservative interpretation,
  - clear scoping statements,
  - and evidence-first outputs.
