# find-broad-perms.ps1

Purpose: Locate folders where broad identities (e.g., Domain Users, Everyone) have elevated permissions.

Usage:

```powershell
./scripts/find-broad-perms.ps1 -RunPath <run-folder> -OutPath results/broad-perms.csv -Ruleset scripts/ruleset.json
```

Options:

- `-Targets`: override default broad identity patterns
- `-IncludeInherited`: include inherited ACEs
- `-Ruleset`: JSON ruleset to match identities and permission regexes
