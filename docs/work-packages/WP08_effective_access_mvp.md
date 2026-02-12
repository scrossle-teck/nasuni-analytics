# WP08 — Effective NTFS access MVP (“view as user”)

## Goal

Provide a snapshot-based “view as user” query that answers what folders a given user can access (at least for read and write-like rights), with an explanation.

## Outcomes

- A repeatable query/command: given a user, produce a list of folders and why access is granted.
- An explicit scoping statement: this is NTFS-effective access over snapshots (not real-time, not share-permission-complete unless modeled).

## Deliverables

- A CLI or script entrypoint (example):
  - `python run.py effective --run-parquet out/parquet/run-... --identity-parquet out/identity/snap-... --user-sid S-1-... --min-right write`
- Output formats:
  - CSV: folder_path, effective_rights_bucket, reason, matched_ace_sid, matched_ace_mask, matched_via_group (optional)
  - optional JSON for tooling
- Explanation model:
  - include at least one matching ACE and whether it was direct user SID or via group membership

## Non-goals

- Modeling share permissions.
- Modeling privilege-based bypass.
- Modeling DAC / claims.

## Dependencies

- WP02 baseline ingest
- WP05 principals
- WP06 membership closure (strongly recommended)
- WP03 fingerprints (recommended for scale)

## Acceptance criteria

- For a synthetic fixture dataset, the effective access result matches expected.
- For a real dataset, you can answer:
  - “show all folders where Alice has write-like rights”
  - “show all folders where Alice has any access”

## Suggested timeline

- Day 1: define minimal semantics and output shape.
- Day 2–4: implement + test + validate on a sample run.

## Implementation notes

### Security context set

Build `S`:

- user SID
- all group SIDs from closure
- optionally include well-known SIDs that apply to everyone in the domain

### Rights semantics

At MVP, focus on a coarse bucket:

- `read`, `write`, `fullcontrol`

Be explicit about limitations:

- If the source evidence doesn’t capture allow vs deny type, or some flags, results are best-effort.

### Efficient evaluation

Prefer evaluating at ACL-definition level:

- Determine which `acl_fingerprint` grants write to the user’s context set
- Expand to folders via `object_acl`

### Deny precedence

If deny ACEs are available, implement a clear precedence model and test it.
