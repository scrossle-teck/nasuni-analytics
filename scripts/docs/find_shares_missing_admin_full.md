# find_shares_missing_admin_full.py

Purpose
- Report share root folders that lack an admin identity with FullControl.

Usage
- `python scripts/find_shares_missing_admin_full.py`

Outputs
- `out/analysis/shares_missing_admin_full.csv` (one-per-folder report).

Notes
- Uses conservative name/mask heuristics; see `scripts/ruleset.json` for identity rules.
