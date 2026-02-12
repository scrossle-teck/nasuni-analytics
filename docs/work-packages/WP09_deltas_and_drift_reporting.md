# WP09 — Deltas and drift reporting (run-to-run)

## Goal

Shift reporting from “what exists?” to “what changed?”, using fingerprints and stable IDs to produce high-signal drift alerts.

## Outcomes

- Cheap re-runs: unchanged objects are skipped.
- Reports highlight new exposures and risk increases.

## Deliverables

- A diff process that compares:
  - run A vs run B
  - identity snapshot A vs B (optional)
- Delta outputs:
  - `new_broad_write_grants.csv`
  - `acl_changed_objects.csv`
  - `risk_increased.csv`
- A minimal change model:
  - `object_id`, old_fingerprint, new_fingerprint
  - rule matches added/removed

## Non-goals

- Near-real-time monitoring.

## Dependencies

- WP03 fingerprints
- WP04 rule engine outputs

## Acceptance criteria

- Given two runs, you can produce:
  - list of objects whose ACL fingerprint changed
  - list of new high-severity findings
- Results are deterministic and explainable.

## Suggested timeline

- Day 1: define delta output schemas and thresholds.
- Day 2–4: implement diff logic + tests + sample run validation.

## Implementation notes

### Fingerprint-centric diffs

Primary diff should use:

- `object_acl` (object_id -> fingerprint)

### Rule drift

If rules change, you may want to re-score old runs; therefore track:

- ruleset version

### Prioritization

Prioritize deltas by:

- severity
- blast radius
- sensitivity (path-based)
