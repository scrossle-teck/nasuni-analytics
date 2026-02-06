"""Apply rules from scripts/ruleset.json to a pandas DataFrame of ACE rows.

Functions exposed for tests: `load_rules`, `apply_rules_df`.

Expected dataframe columns (lowercase): folder_path, ace_name, ace_sid, ace_mask, ace_inherited, ace_raw
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict, Any, cast, Tuple

import pandas as pd


RULES_PATH = Path(__file__).parent / "ruleset.json"


def load_rules(path: Path = RULES_PATH) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        j = json.load(fh)
    raw_rules = j.get("rules", [])
    # normalize top-level admin identities (global excludes) and inject into each rule
    admin_list = j.get("admin_identities") or j.get("admin_id_patterns") or []
    norm_rules: List[Dict[str, Any]] = []
    for r in raw_rules:
        nr: Dict[str, Any] = dict(r)
        # attach global admin list to each rule for ease of use during matching
        if isinstance(admin_list, list):
            nr["admin_identities"] = [str(x) for x in admin_list]
        else:
            nr["admin_identities"] = [str(admin_list)] if admin_list else []
        # normalize list fields into list[str]
        for list_key in ("identity_patterns", "identity_exclude_patterns", "path_keywords"):
            val = nr.get(list_key)
            if val is None:
                nr[list_key] = []
            elif isinstance(val, list):
                nr[list_key] = [str(x) for x in cast(List[Any], val)]
            else:
                nr[list_key] = [str(val)]
        # normalize ace_count_gt
        acg = nr.get("ace_count_gt")
        try:
            nr["ace_count_gt"] = int(acg) if acg is not None and acg != "" else None
        except Exception:
            nr["ace_count_gt"] = None
        # compile identity_regex when present
        ir = nr.get("identity_regex")
        if ir:
            try:
                nr["identity_regex_compiled"] = re.compile(ir)
            except re.error:
                nr["identity_regex_compiled"] = None
        else:
            nr["identity_regex_compiled"] = None

        # ensure perm_match is a string if present
        pm = nr.get("perm_match")
        nr["perm_match"] = str(pm) if pm is not None else None

        norm_rules.append(nr)
    return norm_rules


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
            objd = cast(Dict[str, Any], obj)
            for key in ("name", "displayName", "identity", "account", "accountName", "sid"):
                v = objd.get(key) or objd.get(key.lower())
                if v:
                    return str(v).strip()
    except Exception:
        return str(raw).strip()
    return ""


def _matches_identity(name: str, rule: Dict[str, Any]) -> bool:
    nl = (name or "").lower()
    # include positive patterns (normalized to list[str])
    pats_raw = rule.get("identity_patterns")
    if not pats_raw:
        pats: List[str] = []
    elif isinstance(pats_raw, list):
        pats = [str(x) for x in cast(List[Any], pats_raw)]
    else:
        pats = [str(pats_raw)]

    for p in pats:
        if not p:
            continue
        try:
            # treat p as regex first
            if re.search(str(p), name or "", flags=re.I):
                return True
        except re.error:
            if str(p).lower() in nl:
                return True

    # identity_regex_compiled (preferred)
    irc = rule.get("identity_regex_compiled")
    if irc:
        try:
            if irc.search(name or ""):
                return True
        except Exception:
            pass

    # fallback to raw identity_regex string
    ir = rule.get("identity_regex")
    if ir:
        try:
            if re.search(str(ir), name or ""):
                return True
        except re.error:
            pass

    return False


def _matches_perm(mask: Any, rule: Dict[str, Any]) -> bool:
    pm = rule.get("perm_match")
    if not pm:
        return True
    s = "" if mask is None else str(mask)
    try:
        return re.search(str(pm), s, flags=re.I) is not None
    except re.error:
        return str(pm).lower() in s.lower()


def apply_rules_df(df: pd.DataFrame, rules: List[Dict[str, Any]], min_severity: str | None = None) -> List[Dict[str, Any]]:
    # normalize expected columns and types
    for needed in ("folder_path", "ace_name", "ace_sid", "ace_mask", "ace_inherited", "ace_raw"):
        if needed not in df.columns:
            df[needed] = None

    df = df.copy()
    df["folder_path"] = df["folder_path"].fillna("").astype(str)  # type: ignore[pandas-stubs]
    df["ace_name"] = df["ace_name"].fillna("").astype(str)  # type: ignore[pandas-stubs]
    df["ace_sid"] = df["ace_sid"].fillna("").astype(str)  # type: ignore[pandas-stubs]
    df["ace_mask"] = df["ace_mask"].fillna("").astype(str)  # type: ignore[pandas-stubs]
    df["ace_inherited"] = df["ace_inherited"].fillna(False).astype(bool)  # type: ignore[pandas-stubs]

    df["res_name"] = df.apply(resolve_name_from_row, axis=1).fillna("").astype(str)  # type: ignore[pandas-stubs]

    # precompute folder-level aggregates
    folder_counts = df.groupby("folder_path").size().to_dict()  # type: ignore[pandas-stubs]
    # duplicates per folder+identity
    dup_map: Dict[str, Dict[str, int]] = {}
    for group in df.groupby(["folder_path", "res_name"]):
        tup, g = cast(Tuple[Tuple[Any, Any], pd.DataFrame], group)
        # groupby may yield non-str types; coerce
        fld = str(tup[0])
        nm = str(tup[1])
        c = len(g)
        if c > 1:
            dup_map.setdefault(fld, {})[nm] = c

    matches: List[Dict[str, Any]] = []

    # known admin identities (kept for reference)
    _admin_excludes = set(["administrators", "domain admins", "builtin\\administrators", "nt authority\\system", "s-1-22-1-0", "s-1-5-18"])

    for _, row in df.iterrows():
        folder = row.get("folder_path") or ""
        ace_name = row.get("res_name") or ""
        ace_sid = row.get("ace_sid") or ""
        ace_mask = row.get("ace_mask")
        ace_inh = row.get("ace_inherited")

        for rule in rules:
            rid = rule.get("id")
            # path keyword checks
            # path keyword checks (path_keywords normalized by load_rules)
            pk_raw = rule.get("path_keywords")
            if pk_raw:
                fl = (folder or "").lower()
                if isinstance(pk_raw, list):
                    pkl = [str(k).lower() for k in cast(List[Any], pk_raw)]
                else:
                    pkl = [str(pk_raw).lower()]
                if not any(k in fl for k in pkl):
                    continue

            # ace_count_gt
            # ace_count_gt was normalized by load_rules to int or None
            thr_val = rule.get("ace_count_gt")
            if isinstance(thr_val, int):
                if folder_counts.get(folder, 0) <= thr_val:
                    continue

            # requires_aggregation: check duplicates map
            if rule.get("requires_aggregation"):
                if not dup_map.get(folder):
                    continue

            # identity_exclude_patterns
            excl_raw = rule.get("identity_exclude_patterns")
            excluded = False
            excl: List[str] = []
            if excl_raw:
                excl = [str(x) for x in cast(List[Any], excl_raw)] if isinstance(excl_raw, list) else [str(excl_raw)]
            # combine with global/admin identities injected by load_rules
            admin_excl = rule.get("admin_identities") or []
            if admin_excl:
                excl.extend([str(x) for x in admin_excl])
            for p in excl:
                if not p:
                    continue
                try:
                    if re.search(str(p), ace_name or "", flags=re.I):
                        excluded = True
                        break
                except re.error:
                    if str(p).lower() in ace_name.lower():
                        excluded = True
                        break
            if excluded:
                continue

            # identity matching: support match_admin_identities flag, identity_patterns, and identity_regex
            id_match = True
            if rule.get("match_admin_identities"):
                id_match = False
                admin_list = rule.get("admin_identities") or []
                for p in admin_list:
                    if not p:
                        continue
                    try:
                        if re.search(str(p), ace_name or "", flags=re.I):
                            id_match = True
                            break
                    except re.error:
                        if str(p).lower() in (ace_name or "").lower():
                            id_match = True
                            break
                if not id_match and ace_sid:
                    for p in admin_list:
                        if not p:
                            continue
                        try:
                            if re.search(str(p), str(ace_sid), flags=re.I):
                                id_match = True
                                break
                        except re.error:
                            if str(p).lower() in str(ace_sid).lower():
                                id_match = True
                                break

            if not id_match and (rule.get("identity_patterns") or rule.get("identity_regex") or rule.get("identity_regex_compiled")):
                id_match = _matches_identity(ace_name, rule)
                if not id_match:
                    irc = rule.get("identity_regex_compiled")
                    if irc and ace_sid and irc.search(str(ace_sid)):
                        id_match = True
                    else:
                        ir = rule.get("identity_regex")
                        if ir and ace_sid and re.search(str(ir), str(ace_sid)):
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
                if not d.get(str(ace_name)):
                    continue

            # passed rule (include severity for triage)
            matches.append({
                "rule_id": rid,
                "severity": rule.get("severity", "medium"),
                "folder_path": folder,
                "ace_name": ace_name,
                "ace_sid": ace_sid,
                "ace_mask": ace_mask,
                "ace_inherited": ace_inh,
            })

    # apply min_severity filter if requested
    if min_severity:
        ranks = {"low": 1, "medium": 2, "high": 3}
        min_rank = ranks.get(str(min_severity).lower(), 0)
        matches = [m for m in matches if ranks.get(str(m.get("severity", "medium")).lower(), 0) >= min_rank]

    return matches


if __name__ == "__main__":
    # simple CLI: read parquet(s) from out/parquet/<run> and apply rules
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--run", "-r", type=Path, default=Path("out/parquet/run-20260202-124902"))
    p.add_argument("--rules", "-R", type=Path, default=RULES_PATH)
    p.add_argument("--out", "-o", type=Path, default=None, help="Output CSV path for rule matches")
    p.add_argument("--min-severity", "-m", choices=["low", "medium", "high"], default=None,
                   help="Minimum severity to include in output (low|medium|high)")
    args = p.parse_args()

    rules = load_rules(args.rules)
    files = sorted(args.run.glob("*.parquet"))
    if not files:
        print("No parquet files found")
        raise SystemExit(1)
    dfs: List[pd.DataFrame] = []
    for f in files:
        try:
            df = pd.read_parquet(f)  # type: ignore[pandas-stubs]
            df.columns = [c.lower() for c in df.columns]
            dfs.append(df)  # type: ignore[pandas-stubs]
        except Exception:
            continue
    if not dfs:
        print("No parquet content")
        raise SystemExit(1)
    df = pd.concat(dfs, ignore_index=True)  # type: ignore[pandas-stubs]
    matches = apply_rules_df(df, rules, min_severity=args.min_severity)
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
                fh.write("rule_id,severity,folder_path,ace_name,ace_sid,ace_mask,ace_inherited\n")
                for m in matches:
                    fh.write(','.join([str(m.get(k, '')) for k in ('rule_id','severity','folder_path','ace_name','ace_sid','ace_mask','ace_inherited')]) + "\n")
