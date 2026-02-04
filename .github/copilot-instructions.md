## Purpose

This repo analyzes point-in-time Nasuni appliance ACL snapshots. These instructions help AI coding agents become productive quickly by highlighting the high‑value files, workflows, conventions, and examples specific to this codebase.

**What to prioritize:** ingesting the run Parquet/JSON, using Parquet/DuckDB-backed analysis, and preserving ACL fidelity (SIDs, masks, inherited flags).

## Quick Context

- **Dataset:** see [runs/run-20260202-124902](runs/run-20260202-124902/) (JSON folder ACLs and index CSVs).
- **Canonical schema / columns:** `folder_path`, `ace_name`, `ace_sid`, `ace_mask`, `ace_inherited`, `ace_raw` (used across scripts; do not drop or rename).
- **Primary outputs:** `out/parquet/run-20260202-124902`, `out/analysis/sensitive_shares_broad_perms.csv`, `out/analysis/shares_missing_admin_full.csv`.

## Key Files to Read First

- [AGENTS.md](AGENTS.md) — priming checklist and quickstart; contains the explicit agent onboarding steps.
- [README.md](README.md) — project overview, script patterns, and PowerShell examples.
- [scripts/ruleset.json](scripts/ruleset.json) — identity patterns and rule ids used by many checks (use this to avoid false positives for admin/service principals).
- [scripts/ingest_duckdb.py](scripts/ingest_duckdb.py) and [scripts/find_sensitive_shares.py](scripts/find_sensitive_shares.py) — canonical ingestion and analysis examples.

## Typical Workflows / Commands

- Create venv, install deps (Windows PowerShell):

  ```powershell
  python -m venv .venv
  & .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- Ingest JSON -> Parquet (preferred for queries):

  ```bash
  python scripts/ingest_duckdb.py --run runs/run-20260202-124902 --out out/parquet
  ```

- Run packaged analyses (PowerShell wrapper):

  ```powershell
  ./scripts/run-analytics.ps1 -RunPath .\runs\run-20260202-124902 -OutDir .\out -Checks BroadPerms,AccessibleBy -Ruleset .\scripts\ruleset.json
  ```

## Project Conventions & Patterns

- Prefer Parquet-backed analysis for speed and normalization (see [AGENTS.md](AGENTS.md)).
- Keep raw ACL fidelity: preserve `ace_raw`, numeric masks, and SIDs; document any transformation assumptions.
- Rules & identities are centralized in `scripts/ruleset.json`; use rule ids for consistent filtering across scripts.
- Scripts accept a `-RunPath` / `--run` parameter to point at a run folder; follow that pattern for new tooling.

## Testing & Debugging

- PowerShell tests use Pester: `Invoke-Pester -Script .\tests\pester`.
- Python tests: `pytest -q`.
- Use `scripts/inspect_nan_rows.py` and `out/analysis/nan_rows_debug.csv` to debug ingestion anomalies.

## Integration Points / External Dependencies

- DuckDB / pyarrow / pandas are central for ingestion and queries (`requirements.txt`).
- SID→name translation may require AD/domain access — code assumes heuristic parsing of `ace_raw` when necessary.

## What an AI Agent Should Do First

1. Read [AGENTS.md](AGENTS.md) and [docs/acl_vulnerability_patterns.md](/docs/acl_vulnerability_patterns.md).
2. Verify `out/parquet/run-20260202-124902` exists or run the ingest example to create Parquet.
3. Run a small DuckDB query (example in AGENTS.md) to confirm the data shapes.

## Helpful Examples to Copy / Reuse

- DuckDB quick inspect (from README):

  ```sql
  SELECT folder_path, ace_name, ace_mask
  FROM read_parquet('out/parquet/run-20260202-124902/*.parquet')
  WHERE lower(ace_name) LIKE '%everyone%'
  LIMIT 50;
  ```

## When to Ask for Clarification

- Ask if you need AD/domain access for SID resolution, intent for a new output CSV naming convention, or permission to modify `scripts/ruleset.json` (it affects many analyses).

---

If you want, I can: run the ingest locally, generate a short checklist for contributing new scripts, or refine this file with more command examples. Which would you like next?
