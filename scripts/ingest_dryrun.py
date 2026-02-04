#!/usr/bin/env python3
"""Dry-run for ingest_duckdb: print first N target parquet paths without writing."""
import json
from pathlib import Path
from typing import Any

import sys


def find_folderacl_files(run_path: Path):
    p1 = run_path / "folderacls"
    if p1.exists():
        return sorted(p1.glob("*.json"))
    return sorted(Path(run_path).rglob("*folderacls/*.json"))


def extract_has_acl(data: Any):
    # simple heuristic: look for list-valued fields named like acl/access/aces
    if isinstance(data, dict):
        for k, v in data.items():
            kl = k.lower()
            if kl in ("acl", "acls", "aces", "access", "accesslist", "rights", "permissions") and isinstance(v, list):
                return True
            if extract_has_acl(v):
                return True
    elif isinstance(data, list):
        for it in data:
            if extract_has_acl(it):
                return True
    return False


def main():
    if len(sys.argv) < 3:
        print("Usage: ingest_dryrun.py RUN_PATH OUT_DIR [N]")
        raise SystemExit(2)
    run_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    files = find_folderacl_files(run_path)
    print(f"Found {len(files)} JSON files under {run_path}")
    run_id = run_path.name
    target_dir = out_dir / run_id

    printed = 0
    for f in files:
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"Failed to parse {f}: {e}")
            continue
        if not extract_has_acl(data):
            continue
        out_file = target_dir / (f.stem + ".parquet")
        print(out_file)
        printed += 1
        if printed >= n:
            break
    if printed == 0:
        print("No candidate parquet files would be written.")

if __name__ == '__main__':
    main()
