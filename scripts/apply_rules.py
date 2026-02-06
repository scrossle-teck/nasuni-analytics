"""Apply rules from scripts/ruleset.json to a pandas DataFrame of ACE rows.

Functions exposed for tests: `load_rules`, `apply_rules_df`.

Expected dataframe columns (lowercase): folder_path, ace_name, ace_sid, ace_mask, ace_inherited, ace_raw
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


RULES_PATH = Path(__file__).parent / "ruleset.json"


def load_rules(path: Path = RULES_PATH) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        j = json.load(fh)
    return j.get("rules", [])


def resolve_name_from_row(row: pd.Series) -> str:
    n = row.get("ace_name")
    if n and str(n).strip():
        return str(n).strip()
    raw = row.get("ace_raw")
    if not raw:
        return ""
    try:
        obj = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(obj, dict):
            for key in ("name", "displayName", "identity", "account", "accountName", "sid"):
                v = obj.get(key) or obj.get(key.lower())
                if v:
                    return str(v).strip()
    except Exception:
        return str(raw).strip()
    return ""


def _matches_identity(name: str, rule: Dict[str, Any]) -> bool:
    nl = (name or "").lower()
    # include positive patterns
    pats = rule.get("identity_patterns") or []
    for p in pats:
        try:
            if re.search(p, name, flags=re.I):
                return True
        except re.error:
            if p.lower() in nl:
                return True
    # identity_regex
    ir = rule.get("identity_regex")
    if ir:
        try:
            if re.search(ir, name):
                return True
        except re.error:
            pass
    return False


def _matches_perm(mask, rule: Dict[str, Any]) -> bool:
    pm = rule.get("perm_match")
    if not pm:
        return True
    s = "" if mask is None else str(mask)
    try:
        return re.search(pm, s, flags=re.I) is not None
    except re.error:
        return pm.lower() in s.lower()


def apply_rules_df(df: pd.DataFrame, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # normalize columns
    cols = {c.lower(): c for c in df.columns}
    for needed in ("folder_path", "ace_name", "ace_sid", "ace_mask", "ace_inherited", "ace_raw"):
        if needed not in cols:
            df[needed] = None

    df = df.copy()
    df["res_name"] = df.apply(resolve_name_from_row, axis=1)

    # precompute folder-level aggregates
    folder_counts = df.groupby(df["folder_path"]).size().to_dict()
    # duplicates per folder+identity
    dup_map = {}
    for (fld, nm), g in df.groupby([df["folder_path"], df["res_name"]]):
        c = len(g)
        if c > 1:
            dup_map.setdefault(fld, {})[nm] = c

    matches: List[Dict[str, Any]] = []

    admin_excludes = set(["administrators", "domain admins", "builtin\\administrators", "nt authority\\system", "s-1-22-1-0", "s-1-5-18"])

    for idx, row in df.iterrows():
        folder = row.get("folder_path") or ""
        ace_name = row.get("res_name") or ""
        ace_sid = row.get("ace_sid") or ""
        ace_mask = row.get("ace_mask")
        ace_inh = row.get("ace_inherited")

        for rule in rules:
            rid = rule.get("id")
            # path keyword checks
            pk = rule.get("path_keywords") or []
            if pk:
                fl = (folder or "").lower()
                if not any(k.lower() in fl for k in pk):
                    continue

            # ace_count_gt
            if rule.get("ace_count_gt") is not None:
                if (folder_counts.get(folder, 0) <= int(rule.get("ace_count_gt"))):
                    continue

            # requires_aggregation: check duplicates map
            if rule.get("requires_aggregation"):
                if not dup_map.get(folder):
                    continue

            # identity_exclude_patterns
            excl = rule.get("identity_exclude_patterns") or []
            excluded = False
            for p in excl:
                try:
                    if re.search(p, ace_name, flags=re.I):
                        excluded = True
                        break
                except re.error:
                    if p.lower() in ace_name.lower():
                        excluded = True
                        break
            if excluded:
                continue

            # identity patterns / regex
            id_match = True
            if rule.get("identity_patterns") or rule.get("identity_regex"):
                # match against resolved name OR SID (for raw SID rules)
                id_match = _matches_identity(ace_name, rule)
                if not id_match:
                    ir = rule.get("identity_regex")
                    if ir and ace_sid and re.search(ir, str(ace_sid)):
                        id_match = True
            if not id_match:
                continue

            # perm match
            if not _matches_perm(ace_mask, rule):
                continue

            # ace_inherited check
            if "ace_inherited" in rule:
                want = bool(rule.get("ace_inherited"))
                if bool(ace_inh) != want:
                    continue

            # duplicate detection: if requires_aggregation, ensure duplicate exists for this identity
            if rule.get("requires_aggregation"):
                d = dup_map.get(folder, {})
                if not d.get(ace_name):
                    continue

            # passed rule
            matches.append({
                "rule_id": rid,
                "folder_path": folder,
                "ace_name": ace_name,
                "ace_sid": ace_sid,
                "ace_mask": ace_mask,
                "ace_inherited": ace_inh,
            })

    return matches


if __name__ == "__main__":
    # simple CLI: read parquet(s) from out/parquet/<run> and apply rules
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--run", "-r", type=Path, default=Path("out/parquet/run-20260202-124902"))
    p.add_argument("--rules", "-R", type=Path, default=RULES_PATH)
    p.add_argument("--out", "-o", type=Path, default=None, help="Output CSV path for rule matches")
    args = p.parse_args()

    rules = load_rules(args.rules)
    files = sorted(args.run.glob("*.parquet"))
    if not files:
        print("No parquet files found")
        raise SystemExit(1)
    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(f)
            df.columns = [c.lower() for c in df.columns]
            dfs.append(df)
        except Exception:
            continue
    if not dfs:
        print("No parquet content")
        raise SystemExit(1)
    df = pd.concat(dfs, ignore_index=True)
    matches = apply_rules_df(df, rules)
    print(f"Found {len(matches)} matches")
    if args.out:
        outp = args.out
        outp.parent.mkdir(parents=True, exist_ok=True)
        try:
            import pandas as _pd
            _pd.DataFrame(matches).to_csv(outp, index=False)
            print(f"Wrote rule matches to {outp}")
        except Exception:
            # fallback: write minimal CSV
            with outp.open("w", encoding="utf-8", newline="") as fh:
                fh.write("rule_id,folder_path,ace_name,ace_sid,ace_mask,ace_inherited\n")
                for m in matches:
                    fh.write(','.join([str(m.get(k, '')) for k in ('rule_id','folder_path','ace_name','ace_sid','ace_mask','ace_inherited')]) + "\n")
