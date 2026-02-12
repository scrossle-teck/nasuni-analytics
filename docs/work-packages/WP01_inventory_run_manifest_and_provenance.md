# WP01 — Inventory run manifest and provenance standardization

## Goal

Make each inventory run self-describing, auditable, and easy to ingest and diff.

## Why this matters

Risk and effective-access results are only defensible if you can explain:

- what was collected,
- when it was collected,
- from which assets,
- using which versions of tooling and schemas.

## Outcomes

- Every inventory run has a manifest (counts, timings, versions, inputs).
- Provenance fields are present and consistent in the ingested Parquet.

## Deliverables

- A `manifest.json` (or `run_summary.json`) in each inventory run directory containing:
  - `run_id`, `collected_utc` range
  - inputs used (appliances/shares/visitlist sources)
  - tool versions / git commit hashes
  - schema versions
  - counts:
    - number of appliances
    - number of volumes
    - number of shares
    - number of folders enumerated
    - number of ACE rows
    - number of JSON files produced
  - warnings / partial failures (if any)
- A small validator that checks a run is “ingest-ready” (presence of required files, schema sidecar, etc.).

## Non-goals

- Changing analytics or rule logic.

## Dependencies

- WP00 data contracts.

## Acceptance criteria

- Given only a run folder, you can determine:
  - coverage (what was included/excluded)
  - completeness (what failed)
  - schema/tool versions
- Analytics ingest can use the manifest to compute integrity checks (e.g., expected file counts).

## Suggested timeline

- Day 1: define manifest schema + required fields.
- Day 2–3: implement manifest generation in inventory pipeline (and/or add a post-run summarizer).

## Implementation notes

- Prefer explicit lists over implicit assumptions (e.g., list shares enumerated).
- Include a place for “known limitations for this run” (e.g., AD unreachable, some appliances skipped).
- Include hashes if cheap (collection sha256, per-file sha256 optional).
