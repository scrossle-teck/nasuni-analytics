# find_unknown_volume_entries.py

Purpose: identify folder ACL entries in a run that cannot be mapped to a volume using `shares.csv`.

Usage:

```bash
python scripts/find_unknown_volume_entries.py --run runs/run-20260202-124902 --out out/analysis
```

Output:

- `unknown_volume_entries.csv` — rows describing folder ACL entries where no matching share/volume was found. Useful for diagnosing ingestion artifacts (e.g., schema files or malformed entries).

Notes:

- The script ignores the repository JSON schema file and entries with empty `Path` values.
