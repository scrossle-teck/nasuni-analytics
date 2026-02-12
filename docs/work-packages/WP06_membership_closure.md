# WP06 — Membership closure (transitive group expansion)

## Goal

Compute and persist transitive group membership so effective access and blast radius can be answered via joins instead of graph traversal.

## Outcomes

- A `membership_closure` dataset that answers: “what groups is user X in (directly or indirectly)?”
- Stable performance for downstream queries.

## Deliverables

- `out/identity/snap-<snapshot_id>/membership_closure.parquet`
- Closure semantics documented:
  - includes nested groups
  - handles cycles safely
  - defines whether it includes the identity itself (usually not)
- Optional helper tables:
  - `group_members.parquet` (group_sid → member_sid transitive)

## Non-goals

- Access simulation logic (WP08).

## Dependencies

- WP05 (membership edges)

## Acceptance criteria

- Given a test fixture with nested groups, closure contains expected transitive memberships.
- Closure computation completes within acceptable time for your domain scale (or is incremental).

## Suggested timeline

- Day 1: choose algorithm + representation.
- Day 2–4: implement closure + tests + performance profiling.

## Implementation notes

### Algorithms

- Iterative expansion (BFS/DFS) per principal
- Bulk SQL approach in DuckDB (recursive CTE support exists, but test limits carefully)
- Precompute using Python and write Parquet

### Storage representation

Two equivalent views:

- user-centric closure: `member_sid (user) -> group_sid`
- group-centric closure: `group_sid -> member_sid`

Pick one as canonical; derive the other as needed.

### Cycle handling

AD group graphs can contain cycles; closure must be cycle-safe.

### Incremental updates

For large domains, consider incremental closure:

- compute closure once per snapshot
- or compute closure only for principals referenced in the ACL dataset
