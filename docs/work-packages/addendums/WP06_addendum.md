# WP06 Addendum — Membership closure (transitive group expansion)

## What you can leverage today

### Completed work (inputs)

- WP05 defines membership edges; WP06 is a pure transform on that dataset.
- DuckDB is available and can be used either to compute closure (carefully) or to validate closure outputs.

### Useful scoping input from ACL evidence

From `nasuni-inventory` + ingest:

- You already have a real-world “principal scope set” from ACEs.
- This allows closure computation to start evidence-driven (only compute closure for principals that appear in ACLs), which can dramatically reduce cost.

## Gaps vs WP06 acceptance criteria

WP06 acceptance requires:

- `membership_closure.parquet` exists for a snapshot
- closure semantics are documented (nested groups, cycles)
- closure computation is cycle-safe and tested

Current gaps:

- No closure generator implementation exists yet.
- No cycle-handling fixture tests.

## Checklist: steps to reach WP06 acceptance

### Define closure semantics

- [ ] Decide and document:
  - [ ] closure direction (user→groups or group→members)
  - [ ] whether to include self edges
  - [ ] how to handle disabled users/groups (filter now vs later)

### Implement closure computation

- [ ] Implement closure generation from `membership_edges` with:
  - [ ] cycle detection
  - [ ] deterministic output ordering
  - [ ] snapshot partitioning (`snapshot_id` column)

### Evidence-driven scope (recommended)

- [ ] Optionally compute closure only for principals referenced by ACL evidence:
  - [ ] derive unique `ace_sid` set
  - [ ] compute closure for those SIDs

### Tests

- [ ] Add a small synthetic fixture:
  - [ ] nested groups depth > 2
  - [ ] at least one cycle
- [ ] Assert expected transitive memberships exist and that cycles don’t explode.

### Acceptance validation

- [ ] Demonstrate a simple query:
  - [ ] given a user SID, list all groups from closure

## Notes

- If you plan effective-access queries, a user→groups closure tends to be the most convenient.
- If you plan blast radius queries, having a group→members view (or a derived inversion) is also useful.
