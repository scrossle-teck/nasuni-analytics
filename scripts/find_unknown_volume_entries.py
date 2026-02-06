#!/usr/bin/env python3
"""Find folder ACL entries that map to the 'unknown' volume (no matching share).

Writes out/analysis/unknown_volume_entries.csv with columns: file,folder_path,aces_count
and prints a short summary.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict


def load_shares(run_path: Path) -> Dict[str, List[Dict[str, str]]]:
    shares_file = run_path / "shares.csv"
    out: Dict[str, List[Dict[str, str]]] = {}
    if not shares_file.exists():
        return out
    with shares_file.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            filer = (r.get("filer_name") or "").lower()
            out.setdefault(filer, []).append(r)
    return out


def find_unknowns(run_path: Path) -> List[Dict[str, str]]:
    folderacls_dir = run_path / "folderacls"
    if not folderacls_dir.exists():
        raise FileNotFoundError(folderacls_dir)

    shares_by_filer = load_shares(run_path)
    results: List[Dict[str, str]] = []

    SCHEMA_FILENAME = "com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json"
    for jf in sorted(folderacls_dir.glob("*.json")):
        # skip schema or artifact files
        if jf.name == SCHEMA_FILENAME:
            continue
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            entries = [data]
        elif isinstance(data, list):
            entries = data
        else:
            continue

        for entry in entries:
            path = (entry.get("Path") or entry.get("path") or "")
            # skip entries with empty Path
            if not isinstance(path, str) or not path.strip():
                continue

            access = entry.get("Access") or entry.get("access") or []
            ac_count = len(access) if isinstance(access, list) else 0

            filer_short = None
            share_comp = None
            if isinstance(path, str) and path.startswith("\\\\"):
                parts = path.strip("\\").split("\\")
                if len(parts) >= 2:
                    filer_dns = parts[0]
                    filer_short = filer_dns.split(".")[0].lower()
                    share_comp = parts[1].lower()

            matched = False
            if filer_short and share_comp:
                candidates = shares_by_filer.get(filer_short, [])
                for s in candidates:
                    sn = (s.get("share_name") or "").lower()
                    vn = (s.get("volume_name") or "").lower()
                    if sn == share_comp or vn == share_comp or share_comp in sn or share_comp in vn:
                        matched = True
                        break

            if not matched:
                results.append({"file": jf.name, "folder_path": path, "aces_count": str(ac_count)})

    return results


def write_results(out_dir: Path, run_name: str, rows: List[Dict[str, str]]):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "unknown_volume_entries.csv"
    with out_file.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "file", "folder_path", "aces_count"])
        for r in rows:
            w.writerow([run_name, r["file"], r["folder_path"], r["aces_count"]])
    return out_file


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", "-r", type=Path, default=Path("runs/run-20260202-124902"))
    p.add_argument("--out", "-o", type=Path, default=Path("out/analysis"))
    args = p.parse_args()

    rows = find_unknowns(args.run)
    out_file = write_results(args.out, args.run.name, rows)
    print(f"Found {len(rows)} unknown-volume ACL entries")
    for r in rows:
        print(r["folder_path"])
    print(f"Wrote: {out_file}")


if __name__ == "__main__":
    main()
