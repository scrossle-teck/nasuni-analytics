# WP09 Addendum — Deltas and drift reporting (run-to-run)

## What you can leverage today

### Completed work in `nasuni-inventory`

- Strong drift detection exists for “forensic JSON vs live filesystem”:
  - fingerprint recomputation
  - field-level diffs
  - explicit exit codes

This provides a proven model for explainable delta reporting.

Key references:

- `Compare-FolderAcls.ps1`

### Completed work in `nasuni-analytics`

- Fingerprint fields exist as provenance and can be summarized.
- Rule matches are produced with severities.

Key references:

- `scripts/duckdb_queries.sql`
- `scripts/apply_rules.py`

## Gaps vs WP09 acceptance criteria

WP09 expects:

- run A vs run B comparison
- outputs like “new broad write grants”, “risk increased”, “ACL changed objects”

Current gaps:

- No `object_id` + `acl_fingerprint` tables (WP03 dependency), so diffs cannot be fingerprint-centric.
- No standardized delta outputs.
- Rule drift needs versioning (ruleset SHA) to interpret changes.

## Checklist: steps to reach WP09 acceptance

### Prerequisites

- [ ] WP03: `object_acl` and `acl_definitions` tables with stable `acl_fingerprint`.
- [ ] WP04: stable findings schema for rule outputs.

### Define delta outputs

- [ ] Decide the minimum CSV set:
  - [ ] `acl_changed_objects.csv` (object_id, old/new fingerprint)
  - [ ] `new_high_severity_findings.csv`
  - [ ] `risk_increased.csv` (severity or blast radius increased)

### Implement fingerprint-centric diffs

- [ ] Compare `object_acl` between run A and run B:
  - [ ] identify changed fingerprints
  - [ ] identify new/removed objects

### Implement findings diffs

- [ ] Compare findings outputs:
  - [ ] rule matches added
  - [ ] rule matches removed

### Acceptance validation

- [ ] Create a small fixture with two runs:
  - [ ] one ACL change
  - [ ] one new broad grant
- [ ] Ensure delta outputs are deterministic and explainable.

## Notes

- Capture metadata in delta outputs:
  - run IDs
  - ruleset version
  - canonicalization version
- Once WP07 exists, delta prioritization should include blast radius.
