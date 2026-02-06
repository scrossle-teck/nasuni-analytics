# apply_rules.py

Purpose: load `scripts/ruleset.json` and evaluate rules against Parquet/ACE rows; write rule match results to CSV for downstream analysis.

Usage:

```bash
python scripts/apply_rules.py --run out/parquet/run-20260202-124902 --rules scripts/ruleset.json --out out/analysis/rule_matches.csv
```

Notes:

- `--run` accepts a directory containing Parquet files produced by the ingestion step (`out/parquet/<run>`).
- `--rules` points at `scripts/ruleset.json` (rules are normalized by the script at load time).
- Matches are written as rows with the following columns:
  - `rule_id`: the rule identifier from `scripts/ruleset.json`
  - `severity`: per-rule severity (e.g., `high`, `medium`, `low`) — useful for triage
  - `folder_path`, `ace_name`, `ace_sid`, `ace_mask`, `ace_inherited`
- The rule engine normalizes list fields and compiles regexes; adding new rules should follow the structure in `scripts/ruleset.json`.

Example output and usage:

```csv
rule_id,severity,folder_path,ace_name,ace_sid,ace_mask,ace_inherited
DomainUsersFullControl,high,/shares/finance/payroll,Domain Users,S-1-5-21-...,"FullControl",False
SensitiveFoldersWrite,high,/shares/hr/policies,HR-Docs,S-1-5-21-...,"Modify",False
```

You can filter the CSV for high-severity matches for prioritized triage, for example:

```bash
grep ",high," out/analysis/rule_matches.csv | head -n 50
```
