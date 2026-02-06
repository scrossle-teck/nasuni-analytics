# collate_scalability_metrics.py

Purpose: collate lightweight scalability metrics from a run folder and write CSV summaries to `out/analysis`.

Usage:

```bash
python scripts/collate_scalability_metrics.py --run runs/run-20260202-124902 --out out/analysis
```

Outputs written to `<out>`:

- `scalability_metrics.csv` — one-row summary: folder ACL files, ACL entries, total ACEs, avg/max/min ACEs per entry.
- `scalability_per_host.csv` — breakdown aggregated by filer host (acl_entries, total_aces, avg/max/min per host).
- `scalability_per_volume.csv` — breakdown aggregated by volume name (volume_guid kept when available).

Notes:

- The script skips the repository JSON schema file `com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json` and any ACL entries missing a valid `Path`.
- Volume mapping uses heuristics against `shares.csv` (match `share_name` or `volume_name` to the path share component); entries that cannot be mapped are labeled `unknown`.
