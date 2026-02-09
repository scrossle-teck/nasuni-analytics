#!/usr/bin/env python3
"""Ingest forensic ACL JSON files into Parquet files suitable for DuckDB queries.

Usage:
  python scripts/ingest_duckdb.py --run-path runs/run-20260202-124902 --out-dir out/parquet

Notes:
- Designed to run inside a Python virtualenv created with `python -m venv .venv`.
- Install deps: `pip install -r requirements.txt`
"""
from __future__ import annotations

import argparse
import json
import os
from glob import glob
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd
from tqdm import tqdm


def find_folderacl_files(run_path: Path) -> List[Path]:
    p1 = run_path / "folderacls"
    if p1.exists():
        return sorted(p1.glob("*.json"))
    # fallback: search recursively
    return sorted(Path(run_path).rglob("*folderacls/*.json"))


def extract_acls_from_json(data: Any, source_file: str) -> Iterable[Dict[str, Any]]:
    """Traverse a JSON object and yield flattened ACL rows when ACL lists are found.

    Heuristics: look for keys named 'acl', 'acls', 'aces', or 'aclList' with a list value.
    Attempt to find a folder path in sibling keys like 'path', 'folder', 'name', or 'folderPath'.
    """

    def find_acl_nodes(obj: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_lower = k.lower()
                if key_lower in ("acl", "acls", "aces", "acllist", "access", "accesslist", "rights", "permissions") and isinstance(v, list):
                    yield obj
                else:
                    yield from find_acl_nodes(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from find_acl_nodes(item)

    def _get_ci(d: Dict[str, Any], key: str):
        for k, v in d.items():
            if k.lower() == key.lower():
                return v
        return None

    def _last_path_component(p: str) -> str:
        if not p:
            return ''
        s = str(p).rstrip('/\\')
        parts = [seg for sep in ('\\', '/') for seg in s.split(sep)]
        # filter out empty parts and return last
        parts = [p for p in parts if p]
        return parts[-1] if parts else ''

    for node in find_acl_nodes(data):
        # collect metadata fields (case-insensitive lookup)
        unc_path = _get_ci(node, 'UncPath') or _get_ci(node, 'uncpath') or _get_ci(node, 'path')
        share_path = _get_ci(node, 'SharePath') or _get_ci(node, 'sharepath') or _get_ci(node, 'ShareName') or _get_ci(node, 'sharename')
        appliance_hostname = _get_ci(node, 'ApplianceHostname') or _get_ci(node, 'appliancehostname')

        # compute canonical folder_path: ApplianceHostname + SharePath + last(UncPath)
        last_comp = _last_path_component(unc_path)
        canonical_path = None
        if appliance_hostname and share_path and last_comp:
            canonical_path = f"{appliance_hostname}::{share_path}::{last_comp}"
        elif unc_path:
            canonical_path = unc_path
        else:
            canonical_path = source_file

        # keep original unc_path too
        folder_path = canonical_path

        # find the ACL list value
        acl_list = None
        for k in list(node.keys()):
            kl = k.lower()
            if kl in ("acl", "acls", "aces", "acllist", "access", "accesslist", "rights", "permissions") and isinstance(node[k], list):
                acl_list = node[k]
                break
        if not acl_list:
            # try any list-valued field
            for k, v in node.items():
                if isinstance(v, list):
                    acl_list = v
                    break
        if not acl_list:
            continue

        for ace in acl_list:
            # normalize common fields; support many possible key names produced
            # by different exporters by checking lowercase key variants.
            sid = None
            name = None
            ace_type = None
            mask = None
            inherited = None
            if isinstance(ace, dict):
                low = {k.lower(): v for k, v in ace.items()}

                def pick(*cands):
                    for c in cands:
                        v = low.get(c.lower())
                        if v is not None:
                            return v
                    return None

                sid = pick('sid', 'principalid', 'accountid')
                name = pick('name', 'displayname', 'identity', 'identityreference', 'account', 'accountname', 'principal', 'user', 'group', 'grantee')
                ace_type = pick('type', 'ace_type', 'acetype')
                mask = pick('mask', 'rights', 'permissions', 'access', 'accessmask')
                inherited = pick('inherited', 'isInherited', 'isinherited', 'IsInherited')

            # collect top-level metadata to include in each row
            collected_utc = _get_ci(node, 'CollectedUtc') or _get_ci(node, 'collectedutc')
            collection_host = _get_ci(node, 'CollectionHost') or _get_ci(node, 'collectionhost')
            collector = _get_ci(node, 'Collector') or _get_ci(node, 'collector')
            appliance_description = _get_ci(node, 'ApplianceDescription') or _get_ci(node, 'appliancedescription')
            appliance_serial = _get_ci(node, 'ApplianceSerialNumber') or _get_ci(node, 'applianceserialnumber')
            volume_name = _get_ci(node, 'VolumeName') or _get_ci(node, 'volumename')
            volume_guid = _get_ci(node, 'VolumeGuid') or _get_ci(node, 'volumeguid')
            share_name = _get_ci(node, 'ShareName') or _get_ci(node, 'sharename')
            attributes = _get_ci(node, 'Attributes') or _get_ci(node, 'attributes')
            owner = _get_ci(node, 'Owner') or _get_ci(node, 'owner')
            sddl = _get_ci(node, 'Sddl') or _get_ci(node, 'sddl')
            fingerprint = _get_ci(node, 'FingerprintSha256') or _get_ci(node, 'fingerprintsha256')
            collection_sha = _get_ci(node, 'CollectionSha256') or _get_ci(node, 'collectionsha256')

            yield {
                "source_file": source_file,
                "folder_path": folder_path,
                "unc_path": unc_path,
                "ace_sid": sid,
                "ace_name": name,
                "ace_type": ace_type,
                "ace_mask": mask,
                "ace_inherited": inherited,
                "ace_raw": json.dumps(ace, ensure_ascii=False) if not isinstance(ace, str) else ace,
                # metadata
                "collected_utc": collected_utc,
                "collection_host": collection_host,
                "collector": collector,
                "appliance_hostname": appliance_hostname,
                "appliance_description": appliance_description,
                "appliance_serial": appliance_serial,
                "volume_name": volume_name,
                "volume_guid": volume_guid,
                "share_name": share_name,
                "attributes": attributes,
                "owner": owner,
                "sddl": sddl,
                "fingerprint_sha256": fingerprint,
                "collection_sha256": collection_sha,
            }


def process_run(run_path: str, out_dir: str, preview: bool = False) -> None:
    run_path_p = Path(run_path)
    if not run_path_p.exists():
        raise SystemExit(f"Run path does not exist: {run_path}")

    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    files = find_folderacl_files(run_path_p)
    if not files:
        print(f"No folder ACL JSON files found under {run_path}")
        return

    run_id = Path(run_path).name
    target_dir = out_dir_p / run_id
    # create target directory only when not previewing (preview only lists paths)
    if not preview:
        target_dir.mkdir(parents=True, exist_ok=True)

    for f in tqdm(files, desc="processing files"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            print(f"Failed to parse {f}: {e}")
            continue

        rows = list(extract_acls_from_json(data, str(f)))
        if not rows:
            continue

        df = pd.DataFrame(rows)

        out_file = target_dir / (f.stem + ".parquet")
        # show what would be written
        print(str(out_file))
        if preview:
            continue

        try:
            df.to_parquet(out_file, index=False)
        except Exception as e:
            print(f"Failed to write parquet for {f}: {e}")

    print(f"Finished. Parquet files written to: {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="Ingest ACL JSON files to Parquet for DuckDB")
    parser.add_argument("--run-path", required=True, help="Path to a run directory (e.g., runs/run-20260202-124902)")
    parser.add_argument("--out-dir", required=True, help="Output directory for Parquet files")
    parser.add_argument("--preview", action="store_true", help="Print the target Parquet paths and do not write files")
    args = parser.parse_args()
    process_run(args.run_path, args.out_dir, preview=args.preview)


if __name__ == "__main__":
    main()
