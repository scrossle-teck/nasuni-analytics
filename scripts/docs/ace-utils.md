# ace-utils.ps1

Utilities for parsing and evaluating ACE permission masks.

Key functions:

- `Convert-ToIntMask`: parse hex or decimal mask strings to integers.
- `Test-HighPermission`: heuristic test for elevated rights (looks for Full/Modify or common write bits).
- `Normalize-MaskString`: canonicalize mask representation.

These helpers are used by `find-broad-perms.ps1` and `find-missing-admins.ps1`.
