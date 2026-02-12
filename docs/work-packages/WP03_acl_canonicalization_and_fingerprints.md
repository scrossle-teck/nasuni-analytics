# WP03 — ACL canonicalization + fingerprint tables

## Goal

Introduce ACL deduplication via stable canonicalization and `acl_fingerprint` so that both risk scoring and effective access can run over unique ACL definitions.

## Outcomes

- A stable canonical ACL representation.
- `acl_fingerprint` computed for each object.
- Tables for `acl_definitions` and `object_acl`.

## Deliverables

- Canonicalization spec (in docs) that defines:
  - how ACEs are sorted
  - how null/empty fields are normalized
  - how inheritance/protection flags are represented
  - (if available) how allow/deny is represented
- Implementation that produces:
  - `acl_definitions.parquet` with columns:
    - `run_id`, `acl_fingerprint`, `canonical_acl_json` (or canonical ACE rows), `acl_ace_count`, `canonicalization_version`
  - `object_acl.parquet` with columns:
    - `run_id`, `object_id`, `folder_path`, `acl_fingerprint`, `is_protected`, `owner_sid` (if available)

## Non-goals

- Full effective access semantics (WP08).
- AD joins (WP05+).

## Dependencies

- WP02 (baseline ingest)

## Acceptance criteria

- Fingerprints are deterministic:
  - same input => same fingerprint
  - trivial re-ordering in raw input does not change fingerprint if semantics are unchanged
- You can answer:
  - “How many unique ACLs exist in this run?”
  - “Which ACLs apply to the most folders?”

## Suggested timeline

- Day 1: design canonicalization + fingerprint function.
- Day 2–3: implement + validate on real data; add tests.

## Implementation notes

### Canonicalization granularity

Be explicit:

- If `ace_name` differs but `ace_sid` matches, what wins?
- Prefer `ace_sid` as the identity key; treat name as display.

### Hash choice

- Use SHA-256 over a canonical bytes representation.
- Store the canonical string used for hashing (or a debug representation) for auditability.

### Storage choices

- Canonical ACL JSON per fingerprint is convenient for debugging.
- For maximum queryability, also consider a normalized `acl_ace_rows` table keyed by `acl_fingerprint`.
