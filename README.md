# nasuni-analytics

## Overview

- **Purpose:** Store and analyze point-in-time forensic snapshots of Nasuni Edge Appliances to surface security and permission insights across a large estate (~1PB scanned).

## Dataset

- **Snapshot files:** JSON folder ACL exports located under [runs/run-20260202-124902/folderacls/](runs/run-20260202-124902/folderacls/)
- **Sample file:** [runs/run-20260202-124902/folderacls/az-centralus-ank01-ank01.json](runs/run-20260202-124902/folderacls/az-centralus-ank01-ank01.json)
- **CSV indexes:** Summary CSVs are under [runs/run-20260202-124902/](runs/run-20260202-124902/) (e.g., appliances.csv, volumes.csv, shares.csv, visitlist.csv, latency.csv)

## Schema

- **JSON Schema:** The forensic ACL JSON files conform to [com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json](com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json)

## Analytics Goals

- **Broad permissions:** Find folders where large groups (e.g., Domain Users) have excessive rights.
- **Missing admin access:** Detect folders without expected admin group permissions.
- **Absent required groups:** Identify folders lacking membership by specified security groups.
- **Targeted access queries:** List folders accessible to a named account or group supplied at runtime.

## Scripts (planned)

- **find-broad-perms.ps1:** Locate folders with over-broad ACEs (e.g., FullControl to everyone/domain users).
- **find-missing-admins.ps1:** Report folders missing entries from configured admin groups.
- **find-accessible-by.ps1:** Given an account or group, enumerate folders where that identity has non-zero access.
- **summarize-run.ps1:** Produce a CSV summary (counts by appliance, volume, share, folder) from a run folder.

## Usage (PowerShell examples)

- **Basic pattern:** All scripts accept a `-RunPath` parameter pointing to a run directory (e.g., `runs/run-20260202-124902`).

```powershell
$ runPath = 'runs/run-20260202-124902'
> ./scripts/find-broad-perms.ps1 -RunPath $runPath -OutPath results/broad-perms.csv
```

## Quick Start

- **Run all checks (wrapper):**

```powershell
./scripts/run-analytics.ps1 -RunPath .\runs\run-20260202-124902 -OutDir .\out -Checks BroadPerms,AccessibleBy,Summarize -Identity 'Domain Users' -Ruleset .\scripts\ruleset.json
```

- **Run a single rule by id:**

```powershell
# will produce <rule-id>.csv (for perm rules) or run a presence check for expect_presence rules
./scripts/run-analytics.ps1 -RunPath .\runs\run-20260202-124902 -OutDir .\out -Checks DomainUsersFullControl -Ruleset .\scripts\ruleset.json
```

- **Ingest JSON to DuckDB (Python):**

```bash
python3 scripts/ingest_duckdb.py --run runs/run-20260202-124902 --out out/duckdb
```

## Script Reference & Examples

- `find-broad-perms.ps1` — parameters: `-RunPath`, `-OutPath`, `-Targets`, `-Ruleset`, `-IncludeInherited`.
- `find-accessible-by.ps1` — parameters: `-RunPath`, `-Identity`, `-OutPath`, `-Ruleset`, `-IncludeInherited`. `-Identity` accepts a rule id from `ruleset.json`.
- `summarize-run.ps1` — parameters: `-RunPath`, `-OutPath`.
- `run-analytics.ps1` — wrapper; accepts `-Checks` values that can be names (`BroadPerms`,`AccessibleBy`,`Summarize`) or rule ids from `scripts/ruleset.json`.

## Script documentation

Detailed docs for each script are available under `scripts/docs/`:

- `scripts/docs/find-broad-perms.md`
- `scripts/docs/find-accessible-by.md`
- `scripts/docs/find-missing-admins.md`
- `scripts/docs/summarize-run.md`
- `scripts/docs/run-analytics.md`
- `scripts/docs/ace-utils.md`
- `scripts/docs/ingest_duckdb.md`

- `scripts/docs/collate_scalability_metrics.md`
- `scripts/docs/find_unknown_volume_entries.md`

## Tests

- **PowerShell (Pester):**

```powershell
Import-Module Pester; Invoke-Pester -Script .\tests\pester
```

- **Python (pytest):**

```bash
pytest -q
```

## Design notes for implementers / LLMs

- **Preserve fidelity:** Do not normalize away ACL details—keep SIDs, resolved names, ACE types, inherited flags, and permission masks.
- **Shallow, wide scans:** This dataset is designed for broad estate-wide insight, not exhaustive deep ACL inheritance resolution; document assumptions when adding recursion.
- **Input parameters:** Allow runtime filters: target groups/accounts, minimum permission mask, include/exclude inherited ACEs, appliance/volume/share filters.

## Files of interest

- **Schema:** [com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json](com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json)
- **Example run folder:** [runs/run-20260202-124902/](runs/run-20260202-124902/)

## Next steps

- **Implement scripts:** Create the PowerShell scripts listed above, test against the sample run, and add unit-style checks where possible.
- **Add examples:** Commit example command outputs to `runs/*/examples/` to aid future analysis and LLM prompting.

---

Small, focused PowerShell helpers are recommended: start by implementing `find-broad-perms.ps1` and `find-accessible-by.ps1`.
