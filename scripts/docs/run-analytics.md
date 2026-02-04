# run-analytics.ps1

Purpose: Wrapper orchestrator for running named checks or rule-ids defined in `scripts/ruleset.json`.

Usage:

```powershell
./scripts/run-analytics.ps1 -RunPath <run-folder> -OutDir out -Checks BroadPerms,Summarize -Identity 'Domain Users' -Ruleset scripts/ruleset.json
```

Notes:

- `-Checks` may list named checks (`BroadPerms`, `AccessibleBy`, `Summarize`) or rule ids from the ruleset.
- When a rule id is supplied, the wrapper will call the appropriate underlying script and filter results.
