# WP07 Addendum — Blast radius scoring (identity-aware risk)

## What you can leverage today

### Completed work in `nasuni-analytics`

- You already generate rule matches with severities (`rule_matches.csv`).
- You have a ruleset and unit tests for the rule engine.

Key references:

- `scripts/ruleset.json`
- `scripts/apply_rules.py`
- `tests/test_apply_rules*.py`

### Completed work in `nasuni-inventory` (useful precursor)

- Principal frequency rollups exist (useful for early triage and as a sanity check once blast radius is implemented).

Key references:

- `Analyze-FolderAcls.ps1`

## Gaps vs WP07 acceptance criteria

WP07 requires:

- an identity-aware join to count enabled users affected by a principal
- output fields like `blast_radius_*` attached to findings

Current gaps:

- No AD principals dataset (WP05) and no closure (WP06), so blast radius cannot be computed accurately.
- No rights-bucket mapping spec for turning `ace_mask` into read/write/fullcontrol classes.

## Checklist: steps to reach WP07 acceptance

### Prerequisites

- [ ] Complete WP05 (principals + membership edges).
- [ ] Complete WP06 (closure) or accept a slower approach.

### Define blast radius semantics

- [ ] Document:
  - [ ] what counts as a “human user” (enabled users, exclude service accounts?)
  - [ ] how to classify rights into buckets (read vs write)

### Implement joins

- [ ] For each finding instance principal:
  - [ ] if principal is a user SID: blast radius = 1 (if enabled)
  - [ ] if principal is a group SID: blast radius = count(enabled users in transitive members)

### Attach to findings

- [ ] Extend findings output with:
  - [ ] `principal_type`, `principal_name`
  - [ ] `blast_radius_read`, `blast_radius_write` (or one field per finding’s rights bucket)

### Acceptance validation

- [ ] Add a synthetic fixture identity graph and a small ACE set.
- [ ] Ensure blast radius matches expected counts.
- [ ] Produce a “top 20 highest blast radius write grants” report.

## Notes

- Blast radius transforms “broad access” from a keyword match into an impact metric.
- The evidence-driven AD export approach (WP05 note) can keep blast radius compute tractable in large domains.
