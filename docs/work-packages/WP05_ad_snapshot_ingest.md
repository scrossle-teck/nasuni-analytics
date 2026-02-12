# WP05 — AD snapshot ingest (principals + membership edges)

## Goal

Ingest an on-prem AD snapshot into Parquet tables so ACL evidence can be joined to identity truth.

## Outcomes

- `principals` and `membership_edges` produced for a snapshot ID.
- Basic SID resolution available for findings (turn SIDs into recognizable names).

## Deliverables

- A repeatable snapshot command that writes to:
  - `out/identity/snap-<snapshot_id>/principals.parquet`
  - `out/identity/snap-<snapshot_id>/membership_edges.parquet`
- `principals` table with at least:
  - `snapshot_id`, `sid`, `object_guid`, `samaccountname`, `distinguished_name`, `principal_type`, `enabled`, `collected_at`
- `membership_edges` with:
  - `snapshot_id`, `member_sid`, `group_sid`
- Documentation:
  - how authentication works
  - which OUs/domains are included
  - how often this runs

## Non-goals

- Transitive closure (WP06).
- Effective access (WP08).

## Dependencies

- WP00 contracts.

## Acceptance criteria

- For a sample set of ACE SIDs, you can join to principals and get names/types.
- Snapshot output is deterministic and labeled with `snapshot_id`.

## Suggested timeline

- Day 1: decide ingestion approach (PowerShell AD module vs Python LDAP).
- Day 2–4: implement extraction + Parquet write + tests.

## Implementation notes

### Approach decision

**Option A — PowerShell (AD module)**

- Pros: straightforward in Microsoft shops.
- Cons: may require Windows runners and RSAT.

**Option B — Python (LDAP)**

- Pros: cross-platform; lives in analytics repo.
- Cons: more LDAP complexity.

### Required joins

- Primary join key is `sid`.
- Keep `object_guid` for correlation and future enhancements.

### Scope boundaries

- Be explicit whether you’re snapshotting:
  - the entire domain,
  - specific OUs,
  - only groups referenced by ACL evidence.

### Minimizing load

A useful optimization is to ingest principals/groups “on demand”:

- first collect unique `ace_sid` set from ACLs
- then query AD only for those SIDs (and their group memberships)

This can become a later improvement if full-domain snapshots are acceptable initially.
