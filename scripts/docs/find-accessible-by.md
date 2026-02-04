# find-accessible-by.ps1

Purpose: Enumerate folders where a supplied identity (name or SID) has non-zero access.

Usage:

```powershell
./scripts/find-accessible-by.ps1 -RunPath <run-folder> -Identity 'Domain Users' -OutPath results/access.csv -Ruleset scripts/ruleset.json
```

Notes:

- `-Identity` may be a rule id from the ruleset; the script will expand to the rule's `identity_patterns`.
- `-IncludeInherited` will include inherited ACEs in results.
