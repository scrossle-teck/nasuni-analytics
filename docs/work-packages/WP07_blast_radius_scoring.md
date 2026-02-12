# WP07 — Blast radius scoring (identity-aware risk)

## Goal

Augment findings with blast radius: how many enabled humans get a given right via a principal (directly or through nested groups).

## Outcomes

- Findings are prioritized by impact, not just rule matches.
- Reduced false positives: “broad group” becomes quantifiable.

## Deliverables

- A blast-radius computation module that can output, per finding instance:
  - `blast_radius_read` and/or `blast_radius_write`
  - `principal_type` (user/group) and `principal_name`
  - optionally “top contributing groups” chain
- A set of reference queries that compute:
  - users affected by a given group
  - high-blast-radius write grants

## Non-goals

- Full effective access simulation (WP08).

## Dependencies

- WP04 rule engine outputs
- WP05 AD principals
- WP06 membership closure (recommended; otherwise blast radius is expensive)

## Acceptance criteria

- For a known test fixture, blast radius matches expected counts.
- For a sample real-world run, you can produce a “top 20 highest blast radius write grants” report.

## Suggested timeline

- Day 1: define blast radius semantics per right class (read vs write vs full control).
- Day 2–3: implement joins and output schema.

## Implementation notes

### Rights classification

Decide and document a mapping from `ace_mask` to coarse rights buckets:

- read-ish
- write-ish
- fullcontrol-ish

### Enabled user definition

Define what counts as a “user” for blast radius:

- enabled AD user objects
- exclude service accounts?
- exclude disabled accounts

### Performance

Prefer:

- precomputed closure
- DuckDB joins over Parquet

### Explainability

For triage, store:

- which principal caused the blast radius
- optionally the path of group nesting for sampled users
