# WP01 Addendum — Inventory run manifest and provenance standardization

## What you can leverage today

### Completed work in `nasuni-inventory`

- A consistent run folder structure with predictable artifact naming.
- Strong per-record provenance fields in the forensic JSON (collector/host/collected timestamp), plus per-run logs.
- The visit-list driven collector (`Get-FolderAclsFromVisitList.ps1`) already has the natural “single orchestrator” role.

Key references (inventory repo):

- `Run-All.ps1`
- `Get-FolderAclsFromVisitList.ps1`
- `Get-FolderAcls.ps1`
- `Test-FolderAcls.ps1`
- `Tests/Get-FolderAclsFromVisitList.Tests.ps1`

### Completed work in `nasuni-analytics`

- Ingestion captures provenance-ish metadata when present in JSON and writes it to Parquet.
- Scalability metrics collection exists and can be reused as a manifest input.

Key references:

- `scripts/ingest_duckdb.py`
- `scripts/collate_scalability_metrics.py`
- `docs/SESSION_SUMMARY20260209.md`

## Gaps vs WP01 acceptance criteria

WP01 expects:

- a run-level manifest (`manifest.json` / `run_summary.json`) with counts, versions, inputs, and warnings
- a validator that asserts “ingest-ready” coverage/completeness

Current gaps:

- No single manifest emitted at the run root in `nasuni-inventory`.
- No standardized “coverage/completeness” summary (it exists in logs but not structured).
- No validator that checks a run folder holistically (presence of required CSVs, schema sidecar, expected JSON counts).

## Checklist: steps to reach WP01 acceptance

### Manifest schema

- [ ] Define a minimal manifest schema (fields below) and document it:
  - [ ] `run_id` (folder name)
  - [ ] collection timestamps (start/end)
  - [ ] inventory tool versions (git SHA) and schema version
  - [ ] input file names and hashes (optional)
  - [ ] counts:
    - appliances/volumes/shares/visitlist rows
    - json file count
    - total ACL records and/or ACE counts (if easy)
  - [ ] warnings/errors summary (including unreachable targets)

### Emit the manifest

- [ ] Implement manifest emission in `nasuni-inventory` at the natural orchestrator level:
  - [ ] `Run-All.ps1` writes manifest in the run root
  - [ ] OR `Get-FolderAclsFromVisitList.ps1` writes a per-folderacls manifest (then `Run-All` aggregates)

### Validator

- [ ] Add an “ingest-ready” validator that checks:
  - [ ] required files exist (CSV set, `folderacls/`, schema sidecar)
  - [ ] schema sidecar version matches expectation
  - [ ] json file count matches visit targets (accounting for skips)
  - [ ] warnings are present as structured data (not only text)

### Acceptance demo

- [ ] Add a small fixture run and show:
  - [ ] validator passes
  - [ ] analytics ingest can use manifest counts to sanity-check its own output

## Notes / risks

- Don’t block the project waiting for a perfect manifest: start minimal, then grow fields as operational needs emerge.
- Make sure manifest is explicit about **partial coverage** (skips) so findings aren’t over-interpreted.
