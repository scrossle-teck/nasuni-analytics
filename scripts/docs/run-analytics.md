# run-analytics.ps1

Purpose: Wrapper orchestrator for running named checks or rule-ids defined in `scripts/ruleset.json`.

Usage:

```powershell
./scripts/run-analytics.ps1 -RunPath <run-folder> -OutDir out -Checks BroadPerms,Summarize -Identity 'Domain Users' -Ruleset scripts/ruleset.json
```

Notes:

- `-Checks` may list named checks (`BroadPerms`, `AccessibleBy`, `Summarize`) or rule ids from the ruleset.
- When a rule id is supplied, the wrapper will call the appropriate underlying script and filter results.

Additional flags:

- `-MinSeverity <string>`: Optional. One of `low`, `medium`, or `high`. When supplied the Python rule engine invoked by the wrapper will only include matches at or above the specified severity. This is passed to `apply_rules.py` as `--min-severity`.

- `-SeveritySplit`: Optional switch. When provided, after `apply_rules.py` writes `rule_matches.csv` the wrapper will split that CSV into separate files per severity (for example `rule_matches_high.csv`, `rule_matches_medium.csv`, `rule_matches_low.csv`) under the specified `-OutDir`.
