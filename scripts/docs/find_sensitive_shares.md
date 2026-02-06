# find_sensitive_shares.py

Purpose
- Locate folders whose paths match sensitive keywords (HR, Payroll, Finance, etc.)
  and surface broad permissions while excluding expected admin/service principals.

Usage
- `python scripts/find_sensitive_shares.py`

Outputs
- `out/analysis/sensitive_shares_broad_perms.csv`

Notes
- Keyword patterns and identity exclusions are defined in the script; update with care.
