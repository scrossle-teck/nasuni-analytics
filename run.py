#!/usr/bin/env python3
"""Single entrypoint for analysis and tests.

Usage:
  python run.py analyze --run-path runs/run-20260202-124902 --out-parquet out/parquet --out-csv out/analysis/rule_matches.csv
  python run.py test
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def split_rule_matches(inpath: Path, out_dir: Path) -> None:
    import csv

    out_dir.mkdir(parents=True, exist_ok=True)
    outs = {
        'low': out_dir / 'rule_matches_low.csv',
        'medium': out_dir / 'rule_matches_medium.csv',
        'high': out_dir / 'rule_matches_high.csv',
    }

    with inpath.open('r', encoding='utf-8', newline='') as inf:
        rdr = csv.DictReader(inf)
        fieldnames = list(rdr.fieldnames or [])
        writers = {}
        files = {}
        for sev, path in outs.items():
            f = path.open('w', encoding='utf-8', newline='')
            files[sev] = f
            writers[sev] = csv.DictWriter(f, fieldnames=fieldnames)
            if fieldnames:
                writers[sev].writeheader()

        for row in rdr:
            sev = (row.get('severity') or '').lower()
            if sev in writers:
                writers[sev].writerow(row)

        for f in files.values():
            f.close()


def run_analyze(args: argparse.Namespace) -> int:
    # import local modules
    from scripts import ingest_duckdb, apply_rules
    import pandas as pd

    run_path = args.run_path
    out_parquet = args.out_parquet
    out_csv = Path(args.out_csv) if args.out_csv else Path('out/analysis/rule_matches.csv')
    rules_path = Path(args.rules) if args.rules else Path('scripts/ruleset.json')

    # ingest -> parquet
    if not args.skip_ingest:
        print(f"Ingesting run {run_path} -> {out_parquet}")
        ingest_duckdb.process_run(run_path, out_parquet, preview=args.preview)

    # determine parquet dir for this run
    run_id = Path(run_path).name
    parquet_dir = Path(out_parquet) / run_id
    if not parquet_dir.exists():
        print(f"Parquet directory not found: {parquet_dir}")
        return 2

    # load rules and parquet files
    rules = apply_rules.load_rules(rules_path)
    files: List[Path] = sorted(parquet_dir.glob('*.parquet'))
    if not files:
        print("No parquet files found for rule application")
        return 3
    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(f)
            df.columns = [c.lower() for c in df.columns]
            dfs.append(df)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
    if not dfs:
        print("No parquet content to apply rules")
        return 4
    df_all = pd.concat(dfs, ignore_index=True)

    matches = apply_rules.apply_rules_df(df_all, rules, min_severity=args.min_severity)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    try:
        pd.DataFrame(matches).to_csv(out_csv, index=False)
        print(f"Wrote rule matches to {out_csv}")
    except Exception:
        with out_csv.open('w', encoding='utf-8', newline='') as fh:
            fh.write('rule_id,severity,folder_path,ace_name,ace_sid,ace_mask,ace_inherited\n')
            for m in matches:
                fh.write(','.join([str(m.get(k, '')) for k in ('rule_id', 'severity', 'folder_path', 'ace_name', 'ace_sid', 'ace_mask', 'ace_inherited')]) + '\n')

    if args.split:
        split_rule_matches(out_csv, out_csv.parent)
        print(f"Wrote severity split files to {out_csv.parent}")

    return 0


def run_tests(args: argparse.Namespace) -> int:
    # Run pytest using the same Python interpreter
    print("Running pytest...")
    res = subprocess.run([sys.executable, '-m', 'pytest', '-q'])
    py_res = res.returncode

    # Run pyright if available
    from shutil import which

    pr = which('pyright') or which(str(Path('.venv') / 'Scripts' / 'pyright'))
    if pr:
        print("Running pyright...")
        pr_res = subprocess.run([pr])
        return pr_res.returncode or py_res
    return py_res


def main():
    p = argparse.ArgumentParser(prog='run.py')
    sp = p.add_subparsers(dest='cmd')

    a = sp.add_parser('analyze')
    a.add_argument('--run-path', required=True)
    a.add_argument('--out-parquet', default='out/parquet')
    a.add_argument('--out-csv', default='out/analysis/rule_matches.csv')
    a.add_argument('--rules', default='scripts/ruleset.json')
    a.add_argument('--min-severity', choices=['low', 'medium', 'high'], default=None)
    a.add_argument('--split', action='store_true', help='Write severity split CSVs')
    a.add_argument('--preview', action='store_true')
    a.add_argument('--skip-ingest', action='store_true', help='Skip ingestion and use existing parquet')

    t = sp.add_parser('test')
    # no args for test yet

    args = p.parse_args()
    if args.cmd == 'analyze':
        return_code = run_analyze(args)
        raise SystemExit(return_code)
    elif args.cmd == 'test':
        return_code = run_tests(args)
        raise SystemExit(return_code)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
