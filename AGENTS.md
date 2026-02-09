# AGENTS Reference — nasuni-analytics

Purpose: provide a concise reference for agents to quickly understand the repository state, where to find documentation and outputs, what each script does, and which artifacts should be primed into context when loading the repo.

--

## Priming checklist (first actions for a fresh agent)

1. Read `docs/SESSION_SUMMARY_20260204.md` — session snapshot of what was produced on 2026-02-04.
2. Read `docs/acl_vulnerability_patterns.md` — canonical vulnerability patterns and which identities are considered admin/service principals.
3. Ensure `out/parquet/run-20260202-124902` is accessible (Parquet files are the canonical dataset for queries).
4. Confirm `out/analysis/rule_matches.csv` and `out/analysis/scalability_metrics.csv` (new rule and metrics outputs) are available after running analytics — `rule_matches.csv` includes a `severity` column for triage.
5. Load `out/analysis/sensitive_shares_broad_perms.csv` and `out/analysis/shares_missing_admin_full.csv` for quick actionable hits.
6. Inspect `scripts/ruleset.json` to see identity patterns used to exclude admin/service principals.
7. Note the repository supports schema version `1.0.1` alongside `1.0.0` — run JSON files may use PascalCase names (`UncPath`, `Access`, `Identity`, `Rights`, `IsInherited`). PowerShell scripts have been updated to detect both naming styles and normalize to the canonical column set.

## Quickstart (run these locally in PowerShell)

- Activate virtual environment and run example analyses:

```powershell
& .\.venv\Scripts\Activate.ps1
python .\scripts\ingest_duckdb.py --run runs/run-20260202-124902     # ingest JSON -> Parquet (example)
python .\scripts\find_everyone_full_control.py                    # generate everyone_full_control.csv
python .\scripts\find_sensitive_shares.py                         # generate sensitive_shares_broad_perms.csv
python .\scripts\find_shares_missing_admin_full.py               # generate shares_missing_admin_full.csv
python .\scripts\collate_scalability_metrics.py --run runs/run-20260202-124902 --out out/analysis  # new: scalability metrics
python .\scripts\apply_rules.py --run out/parquet/run-20260202-124902 --out out/analysis/rule_matches.csv  # new: rule engine
```

Run helper: `scripts/run_examples.ps1` contains example PowerShell commands to activate the venv and run common scripts.

## Canonical CSV/Parquet schema

The analysis scripts produce and expect the following canonical columns (lowercased):

- `folder_path`, `ace_name`, `ace_sid`, `ace_mask`, `ace_inherited`, `ace_raw`

Notes:
- The ingestion pipeline (`scripts/ingest_duckdb.py`) maps `UncPath`/`SharePath` -> `folder_path` and `Access`/`Identity`/`Rights` -> `ace_name`/`ace_mask` when present.
- PowerShell scripts were updated to parse JSON with `-Depth 20` to avoid truncated `ace_raw` JSON when serializing/deserializing nested ACE objects.

Agents should assume these columns exist or use the script helpers that normalize them.

## Key documentation (read next)

- `README.md` — project overview and basic usage.
- `docs/SESSION_SUMMARY_20260204.md` — session-level snapshot of what was produced on 2026-02-04 (current state summary).
- `docs/acl_vulnerability_patterns.md` — canonical vulnerability patterns, detection hints, and which identities are treated as admin/service principals.

## Primary outputs (analysis CSVs / Parquet)

- Parquet run directory: `out/parquet/run-20260202-124902` — normalized ACE Parquet files (primary data for queries).
- `out/analysis/everyone_full_control.csv` — ACE rows where `Everyone` has FullControl.
- `out/analysis/sensitive_shares_broad_perms.csv` — sensitive-folder matches (English + Spanish keywords) with broad ACEs; admin/service groups excluded.
- `out/analysis/shares_missing_admin_full.csv` — folders missing an admin group with FullControl (one-per-folder report).
- `out/analysis/nan_rows_debug.csv` — debugging output for ingestion issues (if present).

## Scripts (what they do)

- `scripts/ingest_duckdb.py` — ingest/run JSON folder ACL snapshots and normalize ACEs into Parquet files. Canonicalizes `ace_name`, `ace_mask`, `ace_sid`, `ace_inherited`, `ace_raw`.
- `scripts/ingest_dryrun.py` — helper/dry-run variant for ingestion testing (non-destructive preview).
- `scripts/inspect_nan_rows.py` — identify Parquet rows with missing `folder_path` values for debugging; writes `out/analysis/nan_rows_debug.csv`.
- `scripts/find_everyone_full_control.py` — extract ACEs where `Everyone` has FullControl and write `out/analysis/everyone_full_control.csv`.
- `scripts/find_sensitive_shares.py` — find folders whose paths match sensitive keywords (HR, Payroll, Finance, Legal, PII, Health, SOX, etc.), detect broad ACEs, exclude expected admin/service principals, and write `out/analysis/sensitive_shares_broad_perms.csv`.
- `scripts/find_shares_missing_admin_full.py` — report folders that do not have an admin identity with FullControl (writes `out/analysis/shares_missing_admin_full.csv`). Recognizes appliance root SID and SYSTEM SIDs.
 
PowerShell scripts updated for schema parity (examples):
- `scripts/find-broad-perms.ps1`, `scripts/find-accessible-by.ps1`, `scripts/find-missing-admins.ps1` — now recognize `Access` top-level lists and map `Identity`/`Rights`/`IsInherited` to canonical fields.
- `scripts/summarize-run.ps1`, `scripts/inspect_json.ps1`, `scripts/check_ace_conditions.ps1` — updated to use `-Depth 20` and to prefer `UncPath`/`SharePath`/`ShareName` when deriving `folder_path`.
- `scripts/analysis_broad_perms.py` — exploratory/aggregation analyses for broad permissions (identity frequency, folder counts).
- `scripts/analysis_parquet_broad_perms.py` — alternative/parquet-first analysis to compute top identities and broad-perm summaries.
- `scripts/show_aces_for_folder.py` — utility to display ACEs for a specific folder path from Parquet.
- `scripts/find_aces_root.py` — helper to surface ACEs at share roots (useful for admin owner checks).
- `scripts/collate_scalability_metrics.py` — collate run-level scalability metrics (counts of folder ACL files, ACL entries, ACEs) and per-host/per-volume breakdown CSVs (`out/analysis/scalability_metrics.csv`, `scalability_per_host.csv`, `scalability_per_volume.csv`).
- `scripts/find_unknown_volume_entries.py` — diagnostics to find ACL entries that fail to map to a known volume (writes `out/analysis/unknown_volume_entries.csv`).
- `scripts/apply_rules.py` — rule engine that loads `scripts/ruleset.json`, evaluates rules against Parquet/ACE rows, and writes `out/analysis/rule_matches.csv` (CLi: `--run` and `--out`).

## Rules & configuration

- `scripts/ruleset.json` — JSON rules used by PowerShell/Python checks; contains identity patterns and permission-match rules. Updated to include SIDs such as `S-1-22-1-0` (appliance root) and `S-1-5-18` (SYSTEM).
- `scripts/ruleset.json` — JSON rules used by PowerShell/Python checks; contains identity patterns and permission-match rules. Updated with additional rules (NonAdminFullControl, SensitiveFoldersWrite, DuplicateAceEntries, etc.) and SIDs such as `S-1-22-1-0` (appliance root) and `S-1-5-18` (SYSTEM).

## Environment & dependencies

- Minimal Python packages required (see `requirements.txt`): `pandas`, `pyarrow`, `duckdb`.
- Minimal Python packages required (see `requirements.txt`): `pandas`, `pyarrow`, `duckdb`. For improved static typing when editing, `pandas-stubs` is included as a dev dependency.
- Create/activate a venv (Windows PowerShell):

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage notes for agents

- Prefer the Parquet-backed scripts for analysis (Parquet is normalized and faster for DuckDB/pandas queries).
- When detecting admin/service identities, use the explicit list documented in `docs/acl_vulnerability_patterns.md` and `scripts/ruleset.json` to avoid false positives.
- For temporal analysis, keep a copy of previous run Parquet/CSV outputs to enable diffs and spike detection.
- The orchestration script `scripts/run-analytics.ps1` was updated to call the Python rule engine (`apply_rules.py`), prefer a `.venv` Python, and return a non-zero exit code on failures (CI-friendly). Use it as the single entrypoint for packaged analyses.

## DuckDB / quick inspect example

Query the Parquet set quickly with `duckdb` (Python or CLI):

```sql
-- from duckdb CLI or Python 'duckdb.query'
SELECT folder_path, ace_name, ace_mask
FROM read_parquet('out/parquet/run-20260202-124902/*.parquet')
WHERE lower(ace_name) LIKE '%everyone%'
LIMIT 50;
```

## Caveats & known limitations

- SID→name translation requires domain/AD access; some `ace_name` values are parsed heuristically from `ace_raw`.
- `ace_mask` heuristics are conservative; numeric masks may need manual interpretation.
- Ingestion normalizes many raw forms but may miss extremely non-standard JSON shapes — inspect `ace_raw` when in doubt.

## Planned outputs / next actions

- Deduplicated one-row-per-folder sensitive exposure list: `out/analysis/sensitive_folders_prioritized.csv` (recommended).
- Orphaned-SID report: `out/analysis/orphaned_sids.csv`.
- Run-to-run diffs and change alerts: store previous run artifacts under `out/parquet/run-<timestamp>-prev` for diffs.

--

If you add more scripts or outputs, update this file so agents can find the right entrypoints quickly.
This file is intended as the single-file agent entrypoint describing repository structure, key artifacts, and where to look first. Amend if you add new scripts or outputs.
