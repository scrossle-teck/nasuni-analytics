# find-missing-admins.ps1

Purpose: Report folders that are missing configured administrative identities (presence check).

Behavior:
- Uses a ruleset entry (default `AdminsMissing`) that lists `identity_patterns` and optionally `perm_match`.
- For a folder to be considered covered, at least one ACE must match an identity pattern and satisfy the permission requirement (either `perm_match` or heuristic high-permission detection).

Usage:

```powershell
./scripts/find-missing-admins.ps1 -RunPath <run-folder> -OutPath results/missing-admins.csv -RuleId AdminsMissing -Ruleset scripts/ruleset.json
```
