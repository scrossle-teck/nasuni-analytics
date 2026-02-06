#!/usr/bin/env python3
"""Collate simple scalability metrics for an ingest run.

Counts:
- number of folder ACL files
- number of ACL entries (folders) across all files
- total ACEs (access control entries) across all ACL entries

Writes a one-row CSV to the output directory and prints a summary.
"""
from __future__ import annotations

import argparse
import json
import csv
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional


def _load_shares(run_path: Path) -> List[Dict[str, str]]:
    shares_file = run_path / "shares.csv"
    if not shares_file.exists():
        return []
    rows: List[Dict[str, str]] = []
    with shares_file.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            # normalize keys to known names (some CSVs include odd quoting)
            rows.append({k: (v or "") for k, v in r.items()})
    return rows


def process_run(run_path: Path) -> Tuple[int, int, int, List[int], Dict[str, Any], Dict[str, Any]]:
    folderacls_dir = run_path / "folderacls"
    if not folderacls_dir.exists():
        raise FileNotFoundError(f"folderacls directory not found: {folderacls_dir}")

    json_files = sorted(folderacls_dir.glob("*.json"))
    SCHEMA_FILENAME = "com.teckcominco.scrossle.forensic-acl-1.0.0.schema.json"
    files_count = len(json_files)

    acl_entries_count = 0
    total_aces = 0
    aces_per_entry: List[int] = []

    shares_rows = _load_shares(run_path)

    # build quick index of shares by filer_name -> list of share rows
    shares_by_filer: Dict[str, List[Dict[str, str]]] = {}
    for r in shares_rows:
        filer = (r.get("filer_name") or "").lower()
        shares_by_filer.setdefault(filer, []).append(r)

    per_host: Dict[str, Dict[str, Any]] = {}
    per_volume: Dict[str, Dict[str, Any]] = {}

    for jf in json_files:
        # skip known schema files or non-ACL JSON artifacts
        if jf.name == SCHEMA_FILENAME:
            continue
        try:
            with jf.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            # skip malformed files but report
            continue

        # data is expected to be a list of ACL entries (one per folder)
        if isinstance(data, dict):
            # some files might be a single object; coerce to list
            entries = [data]
        elif isinstance(data, list):
            entries = data
        else:
            entries = []

        for entry in entries:
            # skip entries without a valid Path
            path = (entry.get("Path") or entry.get("path") or "")
            if not isinstance(path, str) or not path.strip():
                continue

            access = entry.get("Access") or entry.get("access") or []
            if not isinstance(access, list):
                continue

            acl_entries_count += 1
            ac_count = len(access)
            total_aces += ac_count
            aces_per_entry.append(ac_count)

            # derive filer and share from Path if available
            path = (entry.get("Path") or entry.get("path") or "")
            filer_short = None
            share_comp = None
            if isinstance(path, str) and path.startswith("\\\\"):
                parts = path.strip("\\").split("\\")
                if len(parts) >= 2:
                    filer_dns = parts[0]
                    filer_short = filer_dns.split(".")[0].lower()
                    share_comp = parts[1].lower()

            host_key = filer_short or "unknown"
            h = per_host.setdefault(host_key, {"acl_entries": 0, "total_aces": 0, "aces_per_entry": []})
            h["acl_entries"] += 1
            h["total_aces"] += ac_count
            h["aces_per_entry"].append(ac_count)

            # map to volume via shares.csv heuristics
            volume_key: Optional[str] = None
            volume_guid: Optional[str] = None
            if filer_short and share_comp:
                candidates = shares_by_filer.get(filer_short, [])
                # exact match on share_name
                for s in candidates:
                    sn = (s.get("share_name") or "").lower()
                    vn = (s.get("volume_name") or "").lower()
                    if sn == share_comp or vn == share_comp or share_comp in sn or share_comp in vn:
                        volume_key = vn or sn or "unknown"
                        volume_guid = s.get("volume_guid") or ""
                        break

            if not volume_key:
                volume_key = "unknown"

            v = per_volume.setdefault(volume_key, {"volume_guid": volume_guid or "", "acl_entries": 0, "total_aces": 0, "aces_per_entry": []})
            v["acl_entries"] += 1
            v["total_aces"] += ac_count
            v["aces_per_entry"].append(ac_count)

    return files_count, acl_entries_count, total_aces, aces_per_entry, per_host, per_volume


def write_csv(out_dir: Path, run_name: str, files_count: int, acl_entries: int, total_aces: int, aces_per_entry: List[int], per_host: Dict[str, Any], per_volume: Dict[str, Any]):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "scalability_metrics.csv"
    avg_aces = round((sum(aces_per_entry) / len(aces_per_entry)), 2) if aces_per_entry else 0
    max_aces = max(aces_per_entry) if aces_per_entry else 0
    min_aces = min(aces_per_entry) if aces_per_entry else 0

    with out_file.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "run",
            "folderacl_files",
            "acl_entries",
            "total_aces",
            "avg_aces_per_entry",
            "max_aces_per_entry",
            "min_aces_per_entry",
        ])
        writer.writerow([run_name, files_count, acl_entries, total_aces, avg_aces, max_aces, min_aces])

    return out_file


def write_breakdowns(out_dir: Path, run_name: str, per_host: Dict[str, Any], per_volume: Dict[str, Any]):
    # per-host
    host_file = out_dir / "scalability_per_host.csv"
    with host_file.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "host", "acl_entries", "total_aces", "avg_aces_per_entry", "max_aces_per_entry", "min_aces_per_entry"])
        for host, stats in sorted(per_host.items(), key=lambda x: x[0]):
            ap = stats.get("aces_per_entry") or []
            avg = round(sum(ap) / len(ap), 2) if ap else 0
            mx = max(ap) if ap else 0
            mn = min(ap) if ap else 0
            w.writerow([run_name, host, stats.get("acl_entries", 0), stats.get("total_aces", 0), avg, mx, mn])

    # per-volume
    vol_file = out_dir / "scalability_per_volume.csv"
    with vol_file.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "volume_guid", "volume_name", "acl_entries", "total_aces", "avg_aces_per_entry", "max_aces_per_entry", "min_aces_per_entry"])
        for volname, stats in sorted(per_volume.items(), key=lambda x: x[0]):
            ap = stats.get("aces_per_entry") or []
            avg = round(sum(ap) / len(ap), 2) if ap else 0
            mx = max(ap) if ap else 0
            mn = min(ap) if ap else 0
            w.writerow([run_name, stats.get("volume_guid", ""), volname, stats.get("acl_entries", 0), stats.get("total_aces", 0), avg, mx, mn])

    return host_file, vol_file


def main():
    p = argparse.ArgumentParser(description="Collate scalability metrics from a run folder")
    p.add_argument("--run", "-r", type=Path, default=Path("runs/run-20260202-124902"), help="Path to run folder")
    p.add_argument("--out", "-o", type=Path, default=Path("out/analysis"), help="Output directory for CSV")
    args = p.parse_args()

    run_path: Path = args.run
    out_dir: Path = args.out

    files_count, acl_entries_count, total_aces, aces_per_entry, per_host, per_volume = process_run(run_path)

    out_file = write_csv(out_dir, run_path.name, files_count, acl_entries_count, total_aces, aces_per_entry, per_host, per_volume)
    host_file, vol_file = write_breakdowns(out_dir, run_path.name, per_host, per_volume)

    print(f"Run: {run_path}")
    print(f"Folder ACL files: {files_count}")
    print(f"ACL entries (folders): {acl_entries_count}")
    print(f"Total ACEs: {total_aces}")
    if aces_per_entry:
        print(f"Avg ACEs per ACL entry: {sum(aces_per_entry)/len(aces_per_entry):.2f}")
        print(f"Max ACEs per ACL entry: {max(aces_per_entry)}")
        print(f"Min ACEs per ACL entry: {min(aces_per_entry)}")
    print(f"Wrote: {out_file}")
    print(f"Wrote: {host_file}")
    print(f"Wrote: {vol_file}")


if __name__ == "__main__":
    main()
